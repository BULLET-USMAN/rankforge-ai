"""Base audit rule abstract class."""

from __future__ import annotations

import abc
import hashlib
from typing import Any, Dict, Optional

from app.services.audit.types import (
    AuditCategory,
    AuditEvaluationContext,
    AuditFinding,
    FindingSeverity,
    RuleEvaluationResult,
)


class BaseAuditRule(abc.ABC):
    """
    Abstract base class for all SEO audit rules.
    Every rule inspects crawl snapshot data deterministically and emits findings.
    """

    rule_id: str
    rule_version: str = "v1.0.0"
    category: AuditCategory
    default_severity: FindingSeverity
    title: str
    description: str

    def create_finding(
        self,
        severity: Optional[FindingSeverity] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        recommendation: str = "",
        evidence: Optional[Dict[str, Any]] = None,
        page_url: Optional[str] = None,
        fingerprint_key: str = "",
    ) -> AuditFinding:
        """Helper to create an AuditFinding with defaults from this rule."""
        sev = severity or self.default_severity
        tit = title or self.title
        desc = description or self.description
        ev = evidence or {}

        # Compute stable fingerprint
        fp_str = f"{self.rule_id}:{page_url or 'site'}:{fingerprint_key}"
        fp = hashlib.sha256(fp_str.encode("utf-8")).hexdigest()

        return AuditFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            category=self.category,
            severity=sev,
            title=tit,
            description=desc,
            recommendation=recommendation,
            evidence=ev,
            page_url=page_url,
            finding_fingerprint=fp,
        )

    @abc.abstractmethod
    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        """Evaluate the rule against the crawl snapshot context."""
        raise NotImplementedError
