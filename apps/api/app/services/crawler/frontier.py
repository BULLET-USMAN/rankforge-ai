"""Crawl Frontier and Queue Manager for RankForge Crawler.

Controls URL lifecycle, deduplication, depth tracking, and polite pacing.
"""

from __future__ import annotations

import time
from collections import deque
from typing import List, Optional, Set


class FrontierItem:
    """A URL candidate in the crawl queue."""

    def __init__(self, url: str, depth: int, discovery_method: str = "link"):
        self.url = url
        self.depth = depth
        self.discovery_method = discovery_method  # "seed", "sitemap", "link"
        self.enqueued_at = time.time()


class CrawlFrontier:
    """In-memory BFS crawl frontier for a single crawl job execution."""

    def __init__(self, max_pages: int = 50, max_depth: int = 3, politeness_delay: float = 1.0):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.politeness_delay = politeness_delay

        self._queue: deque[FrontierItem] = deque()
        self._seen_urls: Set[str] = set()
        self._completed_urls: Set[str] = set()
        self._failed_urls: Set[str] = set()
        self._blocked_urls: Set[str] = set()
        self._last_request_time: float = 0.0

    @property
    def pages_discovered_count(self) -> int:
        return len(self._seen_urls)

    @property
    def pages_completed_count(self) -> int:
        return len(self._completed_urls)

    @property
    def pages_failed_count(self) -> int:
        return len(self._failed_urls)

    @property
    def pages_blocked_count(self) -> int:
        return len(self._blocked_urls)

    @property
    def queue_length(self) -> int:
        return len(self._queue)

    def enqueue(self, url: str, depth: int = 0, discovery_method: str = "link") -> bool:
        """Enqueues a URL if it has not been seen and is within max_depth."""
        if not url:
            return False

        if url in self._seen_urls:
            return False

        if depth > self.max_depth:
            return False

        self._seen_urls.add(url)
        item = FrontierItem(url=url, depth=depth, discovery_method=discovery_method)
        self._queue.append(item)
        return True

    def enqueue_many(self, urls: List[str], depth: int = 0, discovery_method: str = "link") -> int:
        """Batch enqueues URLs. Returns count of newly accepted items."""
        added = 0
        for u in urls:
            if self.enqueue(u, depth=depth, discovery_method=discovery_method):
                added += 1
        return added

    def has_next(self) -> bool:
        """Checks if there are items to crawl within page budget."""
        if self.pages_completed_count >= self.max_pages:
            return False
        return len(self._queue) > 0

    def next_item(self) -> Optional[FrontierItem]:
        """Dequeues the next item in BFS order."""
        if not self.has_next():
            return None
        return self._queue.popleft()

    def mark_completed(self, url: str) -> None:
        self._completed_urls.add(url)

    def mark_failed(self, url: str) -> None:
        self._failed_urls.add(url)

    def mark_blocked(self, url: str) -> None:
        self._blocked_urls.add(url)

    def wait_politeness(self) -> None:
        """Enforces inter-request delay to respect target server load."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.politeness_delay:
            time.sleep(self.politeness_delay - elapsed)
        self._last_request_time = time.time()
