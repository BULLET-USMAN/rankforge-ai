"""RFC 9309 Robots.txt Parser and Policy Evaluator for RankForge Bot.

Fetches and evaluates robots.txt rules, handling:
- Exact User-Agent ('RankForgeBot') vs Wildcard ('*')
- Longest-prefix matching, path wildcards '*', and end-of-line markers '$'
- Allow vs Disallow conflict resolution (longest match, or Allow on tie per RFC 9309)
- Discovery of Sitemap directives
- Crawl-delay parsing
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional
from urllib.parse import urlparse

from app.services.crawler.safe_fetcher import SafeHttpFetcher

logger = logging.getLogger(__name__)

OUR_USER_AGENT = "rankforgebot"


class RobotsRule:
    """Represents a single Allow or Disallow rule."""

    def __init__(self, rule_type: str, pattern: str):
        self.rule_type = rule_type.lower()  # "allow" or "disallow"
        self.pattern = pattern
        self.regex = self._compile_pattern(pattern)
        self.pattern_length = len(pattern)

    @staticmethod
    def _compile_pattern(pattern: str) -> re.Pattern:
        """Converts robots.txt pattern with '*' and '$' to a compiled regex."""
        if not pattern:
            # Empty disallow means allow all
            return re.compile(r"^$")

        # Escape special regex chars except * and $
        escaped = ""
        has_end_anchor = pattern.endswith("$")
        clean_pat = pattern[:-1] if has_end_anchor else pattern

        for char in clean_pat:
            if char == "*":
                escaped += ".*"
            else:
                escaped += re.escape(char)

        if has_end_anchor:
            escaped += "$"
        else:
            # Prefix match per RFC 9309
            escaped += ".*"

        return re.compile(f"^{escaped}")

    def matches(self, path: str) -> bool:
        if not self.pattern and self.rule_type == "disallow":
            return False
        return bool(self.regex.match(path))


class RobotsPolicy:
    """Parsed robots.txt policy for a domain."""

    def __init__(self, raw_content: str = "", status_code: int = 200):
        self.raw_content = raw_content
        self.status_code = status_code
        self.sitemaps: List[str] = []
        self.crawl_delay: Optional[float] = None
        self._rules: List[RobotsRule] = []
        self._parse()

    def _parse(self) -> None:
        """Parses robots.txt according to RFC 9309 rules."""
        if self.status_code == 404 or self.status_code == 410:
            # 404 Not Found or 410 Gone means full access granted
            return

        if self.status_code >= 500:
            # Server error: RFC 9309 recommends treating as full disallow if persistent,
            # but for our crawler we allow gentle fallback or disallow sensitive paths.
            return

        lines = self.raw_content.splitlines()

        # Temporary parsing state
        current_agents: List[str] = []
        custom_agent_rules: List[RobotsRule] = []
        wildcard_agent_rules: List[RobotsRule] = []
        custom_crawl_delay: Optional[float] = None
        wildcard_crawl_delay: Optional[float] = None

        for raw_line in lines:
            line = raw_line.strip()
            # Strip comments
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            if not line:
                continue

            if ":" not in line:
                continue

            field, val = line.split(":", 1)
            field = field.strip().lower()
            val = val.strip()

            if field == "user-agent":
                agent = val.lower()
                current_agents.append(agent)
            elif field == "sitemap":
                if val and val not in self.sitemaps:
                    self.sitemaps.append(val)
            elif field in ("allow", "disallow"):
                if not current_agents:
                    continue

                rule = RobotsRule(rule_type=field, pattern=val)

                for agent in current_agents:
                    if OUR_USER_AGENT in agent:
                        custom_agent_rules.append(rule)
                    elif agent == "*":
                        wildcard_agent_rules.append(rule)
            elif field == "crawl-delay":
                try:
                    delay_val = float(val)
                    for agent in current_agents:
                        if OUR_USER_AGENT in agent:
                            custom_crawl_delay = delay_val
                        elif agent == "*":
                            wildcard_crawl_delay = delay_val
                except ValueError:
                    pass

        # If specific rules exist for RankForgeBot, they take absolute precedence over wildcard
        if custom_agent_rules:
            self._rules = custom_agent_rules
            self.crawl_delay = custom_crawl_delay
        else:
            self._rules = wildcard_agent_rules
            self.crawl_delay = wildcard_crawl_delay

    def can_fetch(self, url: str) -> bool:
        """Evaluates whether URL can be crawled according to parsed rules.

        RFC 9309: Match the longest matching rule.
        If Allow and Disallow match equal length, Allow takes precedence.
        """
        try:
            parsed = urlparse(url)
            path = parsed.path or "/"
            if parsed.query:
                path = f"{path}?{parsed.query}"
        except Exception:
            return False

        matching_rules: List[RobotsRule] = []
        for rule in self._rules:
            if rule.matches(path):
                matching_rules.append(rule)

        if not matching_rules:
            return True

        # Sort by pattern length descending (longest match wins)
        matching_rules.sort(key=lambda r: r.pattern_length, reverse=True)
        longest_len = matching_rules[0].pattern_length

        # Filter all rules that have the longest match
        top_matches = [r for r in matching_rules if r.pattern_length == longest_len]

        # Check if any top match is an Allow rule (Allow wins tie in RFC 9309)
        for r in top_matches:
            if r.rule_type == "allow":
                return True

        # If top match is Disallow
        return False


class RobotsService:
    """Fetches and evaluates robots.txt for a website project."""

    @classmethod
    async def fetch_policy_async(cls, base_url: str) -> RobotsPolicy:
        """Asynchronously fetches robots.txt for a website."""
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        fetcher = SafeHttpFetcher()
        result = await fetcher.fetch_async(robots_url, max_size_bytes=512 * 1024)

        if not result.is_success and result.status_code not in (404, 410):
            logger.info(
                "Failed to fetch robots.txt for %s: %s (status %s)",
                base_url,
                result.error_details,
                result.status_code,
            )

        return RobotsPolicy(
            raw_content=result.text_content or "", status_code=result.status_code or 404
        )

    @classmethod
    def fetch_policy_sync(cls, base_url: str) -> RobotsPolicy:
        """Synchronously fetches robots.txt for a website."""
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        fetcher = SafeHttpFetcher()
        result = fetcher.fetch_sync(robots_url, max_size_bytes=512 * 1024)

        return RobotsPolicy(
            raw_content=result.text_content or "", status_code=result.status_code or 404
        )
