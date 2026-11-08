"""Comparison service for differential technical SEO audits."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.seo_audit_comparison import SEOAuditComparison
from app.models.seo_audit_run import SEOAuditRun


class AuditComparisonService:
    """Computes differential analysis between two completed audit runs."""

    @staticmethod
    def compare_audits(
        db: Session,
        current_audit_id: str,
        previous_audit_id: str,
        organization_id: str,
    ) -> Optional[SEOAuditComparison]:
        """
        Compare two completed audit runs and create or update the SEOAuditComparison record.
        Enforces tenant isolation by verifying organization_id.
        """
        # Load current audit
        curr_audit = (
            db.query(SEOAuditRun)
            .filter(
                SEOAuditRun.id == current_audit_id,
                SEOAuditRun.organization_id == organization_id,
            )
            .first()
        )

        # Load previous audit
        prev_audit = (
            db.query(SEOAuditRun)
            .filter(
                SEOAuditRun.id == previous_audit_id,
                SEOAuditRun.organization_id == organization_id,
            )
            .first()
        )

        if not curr_audit or not prev_audit:
            return None

        # Build fingerprint maps
        curr_map = {f.finding_fingerprint: f for f in curr_audit.findings}
        prev_map = {f.finding_fingerprint: f for f in prev_audit.findings}

        new_fps = set(curr_map.keys()) - set(prev_map.keys())
        resolved_fps = set(prev_map.keys()) - set(curr_map.keys())
        persisting_fps = set(curr_map.keys()) & set(prev_map.keys())

        curr_score = curr_audit.score if curr_audit.score is not None else 0
        prev_score = prev_audit.score if prev_audit.score is not None else 0
        score_change = curr_score - prev_score

        # Build comparison summary payload
        comparison_payload: Dict[str, Any] = {
            "current_audit_id": current_audit_id,
            "previous_audit_id": previous_audit_id,
            "score_change": score_change,
            "counts": {
                "new": len(new_fps),
                "resolved": len(resolved_fps),
                "persisting": len(persisting_fps),
            },
            "new_findings": [
                {
                    "rule_id": curr_map[fp].rule_id,
                    "title": curr_map[fp].title,
                    "severity": curr_map[fp].severity,
                    "category": curr_map[fp].category,
                    "page_url": curr_map[fp].page_url,
                    "finding_fingerprint": fp,
                }
                for fp in list(new_fps)[:50]
            ],
            "resolved_findings": [
                {
                    "rule_id": prev_map[fp].rule_id,
                    "title": prev_map[fp].title,
                    "severity": prev_map[fp].severity,
                    "category": prev_map[fp].category,
                    "page_url": prev_map[fp].page_url,
                    "finding_fingerprint": fp,
                }
                for fp in list(resolved_fps)[:50]
            ],
            "persisting_findings": [
                {
                    "rule_id": curr_map[fp].rule_id,
                    "title": curr_map[fp].title,
                    "severity": curr_map[fp].severity,
                    "category": curr_map[fp].category,
                    "page_url": curr_map[fp].page_url,
                    "finding_fingerprint": fp,
                }
                for fp in list(persisting_fps)[:50]
            ],
        }

        # Check if comparison record already exists
        comparison = (
            db.query(SEOAuditComparison)
            .filter(
                SEOAuditComparison.current_audit_id == current_audit_id,
                SEOAuditComparison.previous_audit_id == previous_audit_id,
                SEOAuditComparison.organization_id == organization_id,
            )
            .first()
        )

        if comparison:
            comparison.score_change = score_change
            comparison.new_findings_count = len(new_fps)
            comparison.resolved_findings_count = len(resolved_fps)
            comparison.persisting_findings_count = len(persisting_fps)
            comparison.comparison_data_json = comparison_payload
        else:
            comparison = SEOAuditComparison(
                organization_id=organization_id,
                website_project_id=curr_audit.website_project_id,
                current_audit_id=current_audit_id,
                previous_audit_id=previous_audit_id,
                score_change=score_change,
                new_findings_count=len(new_fps),
                resolved_findings_count=len(resolved_fps),
                persisting_findings_count=len(persisting_fps),
                comparison_data_json=comparison_payload,
            )
            db.add(comparison)

        db.commit()
        db.refresh(comparison)
        return comparison
