"""SEO Audit Orchestrator: executes audit evaluations against crawl snapshots."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJob
from app.models.crawled_page import CrawledPage
from app.models.seo_audit_category_score import SEOAuditCategoryScore
from app.models.seo_audit_finding import SEOAuditFinding
from app.models.seo_audit_run import SEOAuditRun
from app.models.sitemap_document import SitemapDocument
from app.models.website_project import WebsiteProject
from app.services.audit.comparison_service import AuditComparisonService
from app.services.audit.registry import get_default_registry
from app.services.audit.score_calculator import AuditScoreCalculator
from app.services.audit.types import AuditEvaluationContext

logger = logging.getLogger(__name__)


class SEOAuditOrchestrator:
    """Executes rule-based technical SEO auditing against a crawl snapshot."""

    def __init__(self, db: Session, audit_run_id: str):
        self.db = db
        self.audit_run_id = audit_run_id

    def run(self) -> None:
        """Executes the complete audit evaluation lifecycle."""
        audit_run = self.db.query(SEOAuditRun).filter(SEOAuditRun.id == self.audit_run_id).first()
        if not audit_run:
            logger.error("SEOAuditRun %s not found in database.", self.audit_run_id)
            return

        if audit_run.status == "cancelled":
            logger.info("Audit run %s was already cancelled.", self.audit_run_id)
            return

        # Mark as running
        audit_run.status = "running"
        audit_run.started_at = datetime.now(timezone.utc)
        self.db.commit()

        try:
            # 1. Fetch website and crawl job data
            project = (
                self.db.query(WebsiteProject)
                .filter(WebsiteProject.id == audit_run.website_project_id)
                .first()
            )
            crawl_job = (
                self.db.query(CrawlJob).filter(CrawlJob.id == audit_run.crawl_job_id).first()
            )

            if not project or not crawl_job:
                raise ValueError("Associated WebsiteProject or CrawlJob not found.")

            # 2. Fetch crawled pages and sitemaps
            crawled_pages = (
                self.db.query(CrawledPage).filter(CrawledPage.job_id == crawl_job.id).all()
            )
            sitemaps = (
                self.db.query(SitemapDocument).filter(SitemapDocument.job_id == crawl_job.id).all()
            )

            # 3. Construct evaluation context
            context = AuditEvaluationContext.from_crawl_data(
                project_id=project.id,
                primary_domain=project.domain,
                pages=crawled_pages,
                sitemaps=sitemaps,
            )

            # 4. Evaluate rules
            registry = get_default_registry()
            results = registry.evaluate_all(context)

            # 5. Calculate scores and metrics
            calculator = AuditScoreCalculator()
            score_result = calculator.calculate(
                results=results,
                pages_evaluated=context.pages_evaluated,
                total_pages=len(crawled_pages),
            )

            # 6. Check for cancellation checkpoint
            self.db.refresh(audit_run)
            if audit_run.status == "cancelled":
                logger.info("Audit run %s was cancelled during processing.", self.audit_run_id)
                return

            # 7. Clean previous findings / scores if re-running
            self.db.query(SEOAuditFinding).filter(
                SEOAuditFinding.audit_run_id == self.audit_run_id
            ).delete()
            self.db.query(SEOAuditCategoryScore).filter(
                SEOAuditCategoryScore.audit_run_id == self.audit_run_id
            ).delete()

            # 8. Persist findings
            for res in results:
                for f in res.findings:
                    finding_record = SEOAuditFinding(
                        audit_run_id=self.audit_run_id,
                        organization_id=audit_run.organization_id,
                        website_project_id=audit_run.website_project_id,
                        rule_id=f.rule_id,
                        rule_version=f.rule_version,
                        page_url=f.page_url,
                        severity=f.severity.value,
                        category=f.category.value,
                        title=f.title,
                        description=f.description,
                        evidence_json=f.evidence,
                        recommendation=f.recommendation,
                        finding_fingerprint=f.finding_fingerprint,
                    )
                    self.db.add(finding_record)

            # 9. Persist category scores
            for cat, cat_res in score_result.category_scores.items():
                cat_score_record = SEOAuditCategoryScore(
                    audit_run_id=self.audit_run_id,
                    category=cat.value,
                    score=cat_res.score,
                    weight=cat_res.weight,
                    findings_count=cat_res.findings_count,
                    passed_checks_count=cat_res.passed_checks_count,
                    details_json=cat_res.details,
                )
                self.db.add(cat_score_record)

            # 10. Update audit run metadata
            audit_run.score = score_result.overall_score
            audit_run.score_coverage = score_result.score_coverage
            if not score_result.is_sufficient_coverage:
                audit_run.status = "insufficient_coverage"
            else:
                audit_run.status = "completed"

            audit_run.pages_evaluated = context.pages_evaluated
            audit_run.pages_not_evaluated = context.pages_not_evaluated
            audit_run.findings_count = score_result.total_findings
            audit_run.critical_count = score_result.severity_counts["critical"]
            audit_run.high_count = score_result.severity_counts["high"]
            audit_run.medium_count = score_result.severity_counts["medium"]
            audit_run.low_count = score_result.severity_counts["low"]
            audit_run.info_count = score_result.severity_counts["informational"]
            audit_run.completed_at = datetime.now(timezone.utc)

            # Summary JSON
            audit_run.summary_json = {
                "categories": {
                    cat.value: sc.to_dict() for cat, sc in score_result.category_scores.items()
                },
                "severity_counts": score_result.severity_counts,
                "pages_evaluated": context.pages_evaluated,
                "pages_not_evaluated": context.pages_not_evaluated,
                "coverage": score_result.score_coverage,
            }

            self.db.commit()
            logger.info(
                "SEOAuditRun %s finished successfully. Score: %s, Findings: %d",
                self.audit_run_id,
                audit_run.score,
                audit_run.findings_count,
            )

            # 11. Run comparison if a previous completed audit exists
            prev_audit = (
                self.db.query(SEOAuditRun)
                .filter(
                    SEOAuditRun.website_project_id == audit_run.website_project_id,
                    SEOAuditRun.id != audit_run.id,
                    SEOAuditRun.status == "completed",
                )
                .order_by(SEOAuditRun.completed_at.desc())
                .first()
            )

            if prev_audit:
                try:
                    AuditComparisonService.compare_audits(
                        db=self.db,
                        current_audit_id=audit_run.id,
                        previous_audit_id=prev_audit.id,
                        organization_id=audit_run.organization_id,
                    )
                except Exception as comp_err:
                    logger.warning(
                        "Audit comparison failed for %s vs %s: %s",
                        audit_run.id,
                        prev_audit.id,
                        comp_err,
                    )

        except Exception as exc:
            logger.exception(
                "Audit execution failed for audit_run_id=%s: %s", self.audit_run_id, exc
            )
            audit_run.status = "failed"
            audit_run.error_message = str(exc)[:1000]
            self.db.commit()
            raise
