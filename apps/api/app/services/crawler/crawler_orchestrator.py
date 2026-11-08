"""Crawler Orchestrator for RankForge AI.

Coordinates crawl job execution:
- Verifies domain ownership before execution
- Fetches and evaluates robots.txt
- Discovers and parses sitemaps
- Manages BFS frontier traversal and politeness pacing
- Records crawled page metadata and links
- Supports cancellation checkpoints and real-time progress updates
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJob
from app.models.crawled_page import CrawledPage
from app.models.sitemap_document import SitemapDocument
from app.models.website_project import WebsiteProject
from app.models.website_verification import WebsiteVerification
from app.services.crawler.frontier import CrawlFrontier
from app.services.crawler.page_parser import PageParser
from app.services.crawler.robots_service import RobotsService
from app.services.crawler.safe_fetcher import SafeHttpFetcher
from app.services.crawler.sitemap_service import SitemapService
from app.services.crawler.url_normalizer import UrlNormalizer

logger = logging.getLogger(__name__)


class CrawlerOrchestrator:
    """Executes an isolated crawl job against an authorized website project."""

    def __init__(self, db: Session, job_id: str):
        self.db = db
        self.job_id = job_id
        self.fetcher = SafeHttpFetcher()

    def run(self) -> None:
        """Executes the crawl job lifecycle."""
        job = self.db.query(CrawlJob).filter(CrawlJob.id == self.job_id).first()
        if not job:
            logger.error("CrawlJob %s not found in database.", self.job_id)
            return

        project = self.db.query(WebsiteProject).filter(WebsiteProject.id == job.project_id).first()
        if not project:
            logger.error("Associated WebsiteProject %s not found.", job.project_id)
            job.status = "failed"
            job.error_message = "Associated website project not found."
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return

        # =========================================================================
        # CRITICAL VERIFICATION GATE:
        # Crawls can only run against verified domain projects!
        # =========================================================================
        verification = self.db.query(WebsiteVerification).filter(
            WebsiteVerification.project_id == project.id,
            WebsiteVerification.status == "verified"
        ).first()

        if not verification:
            logger.warning(
                "Crawl rejected for project %s (domain %s): domain not verified.",
                project.id, project.domain
            )
            job.status = "failed"
            job.error_message = "Website domain ownership is not verified. Crawls are restricted to verified domains."
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return

        # Check if already cancelled before starting
        if job.status == "cancelled":
            logger.info("CrawlJob %s was cancelled before execution.", self.job_id)
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        self.db.commit()

        # Build clean base URL
        domain = project.domain.strip()
        scheme = "https"
        if domain.startswith("http://"):
            scheme = "http"
            domain = domain[7:]
        elif domain.startswith("https://"):
            domain = domain[8:]
        domain = domain.rstrip("/")
        base_url = f"{scheme}://{domain}"

        # 1. Fetch robots.txt
        robots_policy = RobotsService.fetch_policy_sync(base_url)

        # Politeness delay: use crawl-delay if specified, bounded between 1.0 and 5.0 seconds
        delay = 1.0
        if robots_policy.crawl_delay is not None:
            delay = max(1.0, min(5.0, robots_policy.crawl_delay))

        # 2. Discover Sitemaps
        sitemap_res = SitemapService.discover_and_parse_sync(
            base_url=base_url,
            target_domain=project.domain,
            seed_sitemaps=robots_policy.sitemaps,
            job_id=job.id,
            project_id=project.id
        )

        # Persist sitemap documents
        for doc in sitemap_res.sitemap_documents:
            sitemap_doc = SitemapDocument(
                project_id=project.id,
                job_id=job.id,
                url=doc["url"],
                status_code=doc.get("status_code", 0),
                status="parsed" if doc.get("is_valid") else "failed",
                urls_found=doc.get("discovered_urls_count", 0),
                error_details=doc.get("error_details"),
            )
            self.db.add(sitemap_doc)
        self.db.commit()

        # 3. Initialize Frontier
        frontier = CrawlFrontier(
            max_pages=job.max_pages,
            max_depth=job.max_depth,
            politeness_delay=delay
        )

        # Seed homepage
        frontier.enqueue(base_url, depth=0, discovery_method="seed")

        # Seed discovered sitemap URLs
        for s_url in sitemap_res.discovered_urls:
            frontier.enqueue(s_url, depth=1, discovery_method="sitemap")

        job.pages_discovered = frontier.pages_discovered_count
        self.db.commit()

        # 4. Crawl Loop
        while frontier.has_next():
            # Cancellation checkpoint
            self.db.refresh(job)
            if job.status == "cancelled":
                logger.info("CrawlJob %s received cancellation request. Halting.", job.id)
                break

            item = frontier.next_item()
            if not item:
                break

            # Enforce politeness delay
            frontier.wait_politeness()

            # Robots.txt check
            if not robots_policy.can_fetch(item.url):
                blocked_page = CrawledPage(
                    job_id=job.id,
                    project_id=project.id,
                    url=item.url,
                    normalized_url=UrlNormalizer.normalize_url(item.url) or item.url,
                    status_code=403,
                    response_time_ms=0.0,
                    depth=item.depth,
                    discovery_method=item.discovery_method,
                    error_details="Blocked by robots.txt directive"
                )
                self.db.add(blocked_page)
                job.pages_blocked += 1
                frontier.mark_blocked(item.url)
                self.db.commit()
                continue

            # Fetch page safely
            fetch_res = self.fetcher.fetch_sync(item.url, max_size_bytes=2 * 1024 * 1024)

            if not fetch_res.is_success or fetch_res.status_code != 200:
                failed_page = CrawledPage(
                    job_id=job.id,
                    project_id=project.id,
                    url=item.url,
                    normalized_url=UrlNormalizer.normalize_url(item.url) or item.url,
                    status_code=fetch_res.status_code or 0,
                    response_time_ms=fetch_res.response_time_ms,
                    content_type=fetch_res.content_type,
                    byte_size=fetch_res.byte_size,
                    depth=item.depth,
                    discovery_method=item.discovery_method,
                    error_details=fetch_res.error_details or f"HTTP {fetch_res.status_code}"
                )
                self.db.add(failed_page)
                job.pages_failed += 1
                frontier.mark_failed(item.url)
                self.db.commit()
                continue

            content_type = (fetch_res.content_type or "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                # Non-HTML page
                non_html_page = CrawledPage(
                    job_id=job.id,
                    project_id=project.id,
                    url=item.url,
                    normalized_url=UrlNormalizer.normalize_url(item.url) or item.url,
                    status_code=fetch_res.status_code,
                    response_time_ms=fetch_res.response_time_ms,
                    content_type=fetch_res.content_type,
                    byte_size=fetch_res.byte_size,
                    depth=item.depth,
                    discovery_method=item.discovery_method,
                    error_details=f"Skipped non-HTML content type: {fetch_res.content_type}"
                )
                self.db.add(non_html_page)
                frontier.mark_completed(item.url)
                self.db.commit()
                continue

            # Parse HTML and extract SEO metadata
            parsed = PageParser.parse_html(
                fetch_res.text_content or "",
                current_url=item.url,
                target_domain=project.domain
            )

            crawled_page = CrawledPage(
                job_id=job.id,
                project_id=project.id,
                url=item.url,
                normalized_url=UrlNormalizer.normalize_url(item.url) or item.url,
                status_code=fetch_res.status_code,
                response_time_ms=fetch_res.response_time_ms,
                content_type=fetch_res.content_type,
                byte_size=fetch_res.byte_size,
                depth=item.depth,
                discovery_method=item.discovery_method,
                title=parsed.title,
                meta_description=parsed.meta_description,
                canonical_url=parsed.canonical_url,
                meta_robots=parsed.meta_robots,
                h1_count=parsed.h1_count,
                internal_links_count=parsed.internal_links_count,
                external_links_count=parsed.external_links_count,
                links_json=parsed.links_detail,
                content_hash=parsed.content_hash,
                error_details=None,
            )
            self.db.add(crawled_page)
            frontier.mark_completed(item.url)
            job.pages_crawled += 1

            # Discover and enqueue internal links
            meta_robots_lower = (parsed.meta_robots or "").lower()
            if "nofollow" not in meta_robots_lower and item.depth < job.max_depth:
                for link in parsed.internal_links:
                    is_crawlable, _ = UrlNormalizer.is_crawlable_resource(link)
                    if is_crawlable:
                        frontier.enqueue(link, depth=item.depth + 1, discovery_method="hyperlink")

            job.pages_discovered = frontier.pages_discovered_count
            self.db.commit()

        # 5. Finalize Job Status
        self.db.refresh(job)
        if job.status != "cancelled":
            if job.pages_crawled >= job.max_pages or (job.pages_crawled > 0):
                job.status = "completed"
            elif job.pages_crawled == 0 and job.pages_failed > 0:
                job.status = "failed"
                job.error_message = job.error_message or "Failed to crawl target pages."
            else:
                job.status = "completed"

        job.completed_at = datetime.now(timezone.utc)
        project.last_crawl_at = datetime.now(timezone.utc)
        self.db.commit()
        logger.info(
            "CrawlJob %s finished with status %s: %s crawled, %s discovered, %s failed, %s blocked.",
            job.id, job.status, job.pages_crawled, job.pages_discovered, job.pages_failed, job.pages_blocked
        )
