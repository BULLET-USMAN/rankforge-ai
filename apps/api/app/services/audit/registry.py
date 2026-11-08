"""Registry for managing and executing SEO audit rules."""

from __future__ import annotations

from typing import Dict, List, Optional, Type

from app.services.audit.base import BaseAuditRule
from app.services.audit.rules import ALL_RULES
from app.services.audit.types import (
    AuditCategory,
    AuditEvaluationContext,
    RuleEvaluationResult,
)


class AuditRuleRegistry:
    """Registry holding all active audit rule instances."""

    def __init__(self) -> None:
        self._rules: Dict[str, BaseAuditRule] = {}

    def register(self, rule: BaseAuditRule) -> None:
        """Register a single audit rule instance."""
        self._rules[rule.rule_id] = rule

    def register_class(self, rule_cls: Type[BaseAuditRule]) -> None:
        """Instantiate and register an audit rule class."""
        instance = rule_cls()
        self.register(instance)

    def get_rule(self, rule_id: str) -> Optional[BaseAuditRule]:
        """Look up a rule by its ID."""
        return self._rules.get(rule_id)

    def get_rules_for_category(self, category: AuditCategory) -> List[BaseAuditRule]:
        """Retrieve all rules registered under a specific category."""
        return [r for r in self._rules.values() if r.category == category]

    def all_rules(self) -> List[BaseAuditRule]:
        """Return all registered rules in deterministic order."""
        return sorted(self._rules.values(), key=lambda r: r.rule_id)

    def evaluate_all(self, context: AuditEvaluationContext) -> List[RuleEvaluationResult]:
        """
        Evaluate all registered rules against the audit context.
        Returns a list of RuleEvaluationResult in deterministic rule_id order.
        """
        results: List[RuleEvaluationResult] = []
        for rule in self.all_rules():
            res = rule.evaluate(context)
            results.append(res)
        return results


def get_default_registry() -> AuditRuleRegistry:
    """Create a default registry populated with all standard audit rules."""
    registry = AuditRuleRegistry()
    for rule_cls in ALL_RULES:
        registry.register_class(rule_cls)
    return registry
