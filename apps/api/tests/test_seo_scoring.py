"""Unit tests for the Technical SEO health score calculator."""

from __future__ import annotations

from app.services.audit.base import BaseAuditRule
from app.services.audit.score_calculator import AuditScoreCalculator
from app.services.audit.types import (
    AuditCategory,
    AuditEvaluationContext,
    AuditFinding,
    FindingSeverity,
    RuleEvaluationResult,
)


class DummyPassedRule(BaseAuditRule):
    rule_id = "PASS-001"
    category = AuditCategory.METADATA
    default_severity = FindingSeverity.MEDIUM
    title = "Test Passed Rule"
    description = "Test rule that passes"

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=True,
            findings=[],
            pages_checked=5,
            pages_passed=5,
        )


def test_perfect_score_when_no_issues():
    calc = AuditScoreCalculator()
    results = [DummyPassedRule().evaluate(None)]  # type: ignore
    res = calc.calculate(results=results, pages_evaluated=5, total_pages=5)

    assert res.is_sufficient_coverage is True
    assert res.overall_score == 100
    assert res.total_findings == 0
    assert res.score_coverage == 1.0


def test_insufficient_coverage_results_in_none_score():
    calc = AuditScoreCalculator()
    results = [DummyPassedRule().evaluate(None)]  # type: ignore
    # 0 pages evaluated
    res = calc.calculate(results=results, pages_evaluated=0, total_pages=5)

    assert res.is_sufficient_coverage is False
    assert res.overall_score is None
    assert res.score_coverage == 0.0


def test_penalty_damping_for_template_repetition():
    calc = AuditScoreCalculator()
    # Simulate a single rule triggering on 50 different pages
    findings = [
        AuditFinding(
            rule_id="META-005",
            rule_version="v1.0.0",
            category=AuditCategory.METADATA,
            severity=FindingSeverity.MEDIUM,  # base penalty = 5
            title="Missing Meta Description",
            description="desc",
            recommendation="rec",
            evidence={},
            page_url=f"https://example.com/p/{i}",
        )
        for i in range(50)
    ]

    res = RuleEvaluationResult(
        rule_id="META-005",
        category=AuditCategory.METADATA,
        passed=False,
        findings=findings,
        pages_checked=50,
        pages_passed=0,
    )

    score_res = calc.calculate(results=[res], pages_evaluated=50, total_pages=50)
    meta_cat = score_res.category_scores[AuditCategory.METADATA]

    # Without damping, 50 * 5 = 250 penalty (would reduce score to 0).
    # With damping: 5 * (1 + 0.5 * log2(50)) = 5 * (1 + 0.5 * 5.64) = ~19.1 penalty.
    # So category score should be around 81, not 0!
    assert meta_cat.score > 70
    assert meta_cat.score < 90
    assert score_res.overall_score is not None
    assert score_res.overall_score > 80
