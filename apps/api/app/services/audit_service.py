import time
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.audit_job import AuditJob
from app.models.audit_result import AuditResult
from app.models.website_project import WebsiteProject
from app.services.ssrf_guard import SSRFGuard, SSRFSecurityException


class AuditService:
    """
    Performs real, safe, non-destructive technical preflight audits.
    Never fabricates metrics.
    """

    @classmethod
    async def perform_preflight_audit(
        cls, db: Session, job: AuditJob, project: WebsiteProject, target_url: str
    ) -> AuditResult:
        logger.info(f"Initiating preflight audit for job {job.id} on URL {target_url}")

        # 1. SSRF Safety Verification
        is_safe, reason = SSRFGuard.validate_url(target_url)
        if not is_safe:
            raise SSRFSecurityException(f"SSRF Check Rejected URL: {reason}")

        parsed = urlparse(target_url)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        start_time = time.perf_counter()
        headers_dict = {}
        ssl_info = {"is_https": parsed.scheme.lower() == "https"}
        status_code = 0
        issues = []
        robots_found = False
        sitemap_found = False

        # 2. Main URL Inspection
        async with httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=settings.CRAWLER_MAX_REDIRECTS,
            timeout=settings.CRAWLER_TIMEOUT_SECONDS,
            verify=True,
            headers={"User-Agent": "RankForgeAI-Auditor/1.0 (+https://rankforge.ai/bot)"},
        ) as client:
            try:
                resp = await client.get(target_url)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                status_code = resp.status_code
                headers_dict = dict(resp.headers)

                # Check security headers
                if "strict-transport-security" not in resp.headers:
                    issues.append(
                        {
                            "code": "MISSING_HSTS",
                            "severity": "warning",
                            "title": "Missing HSTS Header",
                            "description": "Strict-Transport-Security header is recommended to enforce HTTPS connections.",
                        }
                    )
                if "x-content-type-options" not in resp.headers:
                    issues.append(
                        {
                            "code": "MISSING_X_CONTENT_TYPE_OPTIONS",
                            "severity": "info",
                            "title": "Missing X-Content-Type-Options Header",
                            "description": "Prevents MIME-type sniffing.",
                        }
                    )

                # Check response time
                if duration_ms > 2000:
                    issues.append(
                        {
                            "code": "HIGH_LATENCY",
                            "severity": "warning",
                            "title": "Slow Time-to-First-Byte",
                            "description": f"Initial page response took {duration_ms}ms, which exceeds recommended 2000ms.",
                        }
                    )

            except httpx.ConnectError as ce:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                status_code = 502
                issues.append(
                    {
                        "code": "CONNECTIVITY_FAILED",
                        "severity": "critical",
                        "title": "Connection Error",
                        "description": f"Could not connect to host: {str(ce)}",
                    }
                )
            except httpx.TimeoutException:
                duration_ms = round(settings.CRAWLER_TIMEOUT_SECONDS * 1000, 2)
                status_code = 504
                issues.append(
                    {
                        "code": "REQUEST_TIMEOUT",
                        "severity": "critical",
                        "title": "Audit Request Timed Out",
                        "description": f"Target failed to respond within {settings.CRAWLER_TIMEOUT_SECONDS}s.",
                    }
                )
            except Exception as e:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                status_code = 500
                issues.append(
                    {
                        "code": "AUDIT_FAILURE",
                        "severity": "critical",
                        "title": "Audit Inspection Error",
                        "description": str(e),
                    }
                )

            # 3. Check robots.txt presence
            try:
                robots_url = f"{base_origin}/robots.txt"
                robots_resp = await client.get(robots_url, timeout=5.0)
                if robots_resp.status_code == 200 and "text/plain" in robots_resp.headers.get(
                    "content-type", ""
                ):
                    robots_found = True
                else:
                    issues.append(
                        {
                            "code": "ROBOTS_TXT_MISSING",
                            "severity": "info",
                            "title": "robots.txt Not Accessible",
                            "description": "No valid robots.txt file found at standard root location.",
                        }
                    )
            except Exception:
                pass

            # 4. Check sitemap.xml presence
            try:
                sitemap_url = f"{base_origin}/sitemap.xml"
                sitemap_resp = await client.get(sitemap_url, timeout=5.0)
                if sitemap_resp.status_code == 200:
                    sitemap_found = True
                else:
                    issues.append(
                        {
                            "code": "SITEMAP_MISSING",
                            "severity": "info",
                            "title": "sitemap.xml Not Found at Root",
                            "description": "Standard sitemap.xml was not found at root path.",
                        }
                    )
            except Exception:
                pass

        # Calculate an objective score based on actual findings
        score = 100
        for issue in issues:
            if issue["severity"] == "critical":
                score -= 35
            elif issue["severity"] == "warning":
                score -= 15
            elif issue["severity"] == "info":
                score -= 5
        score = max(0, min(100, score))

        # Persist Result
        result = AuditResult(
            job_id=job.id,
            project_id=project.id,
            url=target_url,
            status_code=status_code,
            response_time_ms=duration_ms,
            headers_json=headers_dict,
            ssl_info_json=ssl_info,
            robots_txt_found=robots_found,
            sitemap_found=sitemap_found,
            issues_json=issues,
            score=score,
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return result
