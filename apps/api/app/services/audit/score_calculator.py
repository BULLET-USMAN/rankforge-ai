"""Scoring engine: weighted category scores, template repetition damping, and coverage checks."""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from app.services.audit.types import (
    CATEGORY_WEIGHTS,
    SEVERITY_BASE_PENALTY,
    AuditCategory,
    AuditFinding,
    FindingSeverity,
    RuleEvaluationResult,
)


class CategoryScoreResult:
    def __init__(
        self,
        category: AuditCategory,
        score: int,
        weight: float,
        findings_count: int,
        passed_checks_count: int,
        details: Dict[str, Any],
    ) -> None:
        self.category = category
        self.score = score
        self.weight = weight
        self.findings_count = findings_count
        self.passed_checks_count = passed_checks_count
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "score": self.score,
            "weight": self.weight,
            "findings_count": self.findings_count,
            "passed_checks_count": self.passed_checks_count,
            "details": self.details,
        }


class AuditScoreResult:
    def __init__(
        self,
        overall_score: Optional[int],
        score_coverage: float,
        is_sufficient_coverage: bool,
        category_scores: Dict[AuditCategory, CategoryScoreResult],
        severity_counts: Dict[str, int],
        total_findings: int,
    ) -> None:
        self.overall_score = overall_score
        self.score_coverage = score_coverage
        self.is_sufficient_coverage = is_sufficient_coverage
        self.category_scores = category_scores
        self.severity_counts = severity_counts
        self.total_findings = total_findings


class AuditScoreCalculator:
    """
    Computes transparent, explainable SEO health scores based on audited findings.
    Applies penalty damping for repeated template flaws and enforces coverage thresholds.
    """

    def __init__(
        self,
        weights: Optional[Dict[AuditCategory, float]] = None,
        base_penalties: Optional[Dict[FindingSeverity, float]] = None,
    ) -> None:
        self.weights = weights or CATEGORY_WEIGHTS
        self.base_penalties = base_penalties or SEVERITY_BASE_PENALTY

    def calculate(
        self,
        results: List[RuleEvaluationResult],
        pages_evaluated: int,
        total_pages: int,
    ) -> AuditScoreResult:
        """
        Calculate health scores across all 8 categories and the overall score.
        If pages_evaluated is 0, score is None and is_sufficient_coverage is False.
        """
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "informational": 0,
        }
        all_findings: List[AuditFinding] = []

        # Group results and findings by category
        category_results: Dict[AuditCategory, List[RuleEvaluationResult]] = {
            cat: [] for cat in AuditCategory
        }
        for res in results:
            category_results[res.category].append(res)
            for f in res.findings:
                all_findings.append(f)
                sev_key = f.severity.value
                if sev_key in severity_counts:
                    severity_counts[sev_key] += 1

        # Check coverage
        coverage = (pages_evaluated / total_pages) if total_pages > 0 else 0.0
        if pages_evaluated == 0:
            # Insufficient coverage
            cat_scores: Dict[AuditCategory, CategoryScoreResult] = {}
            for cat in AuditCategory:
                cat_scores[cat] = CategoryScoreResult(
                    category=cat,
                    score=0,
                    weight=self.weights.get(cat, 0.1),
                    findings_count=0,
                    passed_checks_count=0,
                    details={"status": "insufficient_coverage"},
                )
            return AuditScoreResult(
                overall_score=None,
                score_coverage=0.0,
                is_sufficient_coverage=False,
                category_scores=cat_scores,
                severity_counts=severity_counts,
                total_findings=len(all_findings),
            )

        category_scores: Dict[AuditCategory, CategoryScoreResult] = {}
        weighted_sum = 0.0
        total_weight_used = 0.0

        for cat, rule_res_list in category_results.items():
            cat_weight = self.weights.get(cat, 0.05)
            cat_findings: List[AuditFinding] = []
            passed_count = 0
            for r in rule_res_list:
                cat_findings.extend(r.findings)
                passed_count += r.pages_passed

            # Count rule repetitions for penalty damping
            # e.g., if rule 'META-005' triggers 50 times across 50 pages,
            # effective_penalty = base_penalty * (1 + 0.5 * log2(50))
            rule_counts: Dict[str, Tuple[FindingSeverity, int]] = {}
            for f in cat_findings:
                if f.rule_id not in rule_counts:
                    rule_counts[f.rule_id] = (f.severity, 0)
                sev, cnt = rule_counts[f.rule_id]
                rule_counts[f.rule_id] = (sev, cnt + 1)

            total_penalty = 0.0
            for rule_id, (sev, count) in rule_counts.items():
                base_pen = self.base_penalties.get(sev, 0.0)
                if count <= 1:
                    total_penalty += base_pen
                else:
                    damping = 1.0 + (0.5 * math.log2(count))
                    total_penalty += base_pen * damping

            # Category score is clamped 0 to 100
            score = max(0, min(100, round(100.0 - total_penalty)))

            category_scores[cat] = CategoryScoreResult(
                category=cat,
                score=score,
                weight=cat_weight,
                findings_count=len(cat_findings),
                passed_checks_count=passed_count,
                details={
                    "total_penalty": round(total_penalty, 2),
                    "rule_occurrences": {r: c for r, (_, c) in rule_counts.items()},
                },
            )

            weighted_sum += score * cat_weight
            total_weight_used += cat_weight

        # Normalize overall score against total weight used
        if total_weight_used > 0:
            final_score = max(0, min(100, round(weighted_sum / total_weight_used)))
        else:
            final_score = 100

        return AuditScoreResult(
            overall_score=final_score,
            score_coverage=round(coverage, 2),
            is_sufficient_coverage=True,
            category_scores=category_scores,
            severity_counts=severity_counts,
            total_findings=len(all_findings),
        )
