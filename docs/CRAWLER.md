# Intelligent Website Crawler Architecture

## 1. Overview
RankForge AI includes a dedicated, production-grade asynchronous website crawler designed for technical SEO intelligence discovery. The crawler fetches, parses, and structures web pages belonging exclusively to authorized, verified website projects.

The crawler is built with strict security safeguards, RFC 9309 robots compliance, polite inter-request pacing, URL trap prevention, and safe XML parsing.

---

## 2. Crawler Engine Architecture

```
                          ┌────────────────────────┐
                          │   CrawlJob Created     │
                          │ (Verification Checked) │
                          └───────────┬────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │    RobotsService (RFC9309)│
                        │ Fetch & Parse robots.txt  │
                        └─────────────┬─────────────┘
                                      │
                        ┌─────────────▼─────────────┐
                        │   SitemapService (XML)    │
                        │ Safe defusedxml parsing   │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CrawlFrontier (BFS Queue)                             │
│  - Breadth-first traversal order                                            │
│  - Deduplication via seen URLs set                                          │
│  - Depth tracking & maximum depth budget                                    │
│  - Politeness rate pacing (1.0s default, or Crawl-delay)                    │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │    Cancellation Checkpoint    │
                      └───────────────┬───────────────┘
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │    Robots Policy Evaluator    │
                      │ can_fetch(url) -> Allow/Deny  │
                      └───────────────┬───────────────┘
                                      │ Allow
                                      ▼
                      ┌───────────────────────────────┐
                      │      SafeHttpFetcher          │
                      │ SSRF guard, 2MB budget, 10s   │
                      └───────────────┬───────────────┘
                                      │ HTTP 200 (HTML)
                                      ▼
                      ┌───────────────────────────────┐
                      │         PageParser            │
                      │ Title, Meta, Canonical, H1,   │
                      │ Outbound links, SHA-256 hash  │
                      └───────────────┬───────────────┘
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │    Persist CrawledPage        │
                      │  Enqueue internal hyperlinks  │
                      └───────────────────────────────┘
```

---

## 3. Core Crawler Modules

### 3.1 SafeHttpFetcher (`app.services.crawler.safe_fetcher`)
- **Connection-Level SSRF Protection:** Pre-resolves hostname to IP addresses before initiating TCP connection; rejects loopback (`127.0.0.0/8`, `::1`), private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and cloud metadata (`169.254.169.254`, `metadata.google.internal`).
- **Redirect Hop Inspection:** Disables automated client redirects and inspects each `Location` header up to 3 hops, re-verifying DNS and IP boundaries per hop.
- **Payload Budgets:** Enforces 2 MB limit for HTML documents, 5 MB limit for sitemaps, and 16 KB for verification tokens.
- **Custom User-Agent:** `RankForgeBot/1.0 (+https://rankforge.ai/bot)`.

### 3.2 RobotsService (`app.services.crawler.robots_service`)
- **RFC 9309 Specification:**
  - Evaluates user-agent groups with precedence: `RankForgeBot` takes priority over wildcard `*`.
  - Supports `Allow`, `Disallow`, wildcards `*`, and end-of-path anchors `$`.
  - Longest-matching prefix rule: on equal-length prefix tie, `Allow` takes precedence per RFC 9309.
  - Extracts `Sitemap:` directives and optional `Crawl-delay:` timing.

### 3.3 SitemapService (`app.services.crawler.sitemap_service`)
- **Billion Laughs & XML Bomb Defense:** Uses `defusedxml.ElementTree` to prevent entity expansion and external DTD injection.
- **Formats Handled:** Standard `<urlset>` and nested `<sitemapindex>` hierarchies (depth max 2).
- **Discovery Flow:** Discovers sitemaps from robots.txt directives and fallback standard paths (`/sitemap.xml`, `/sitemap_index.xml`).
- **Budget Enforcements:** Maximum 5 sitemap documents, maximum 500 discovered URLs.

### 3.4 UrlNormalizer (`app.services.crawler.url_normalizer`)
- Resolves relative URLs to absolute.
- Strips fragments (`#...`) and tracking query parameters (`utm_*`, `gclid`, `fbclid`).
- Enforces strict domain scope (exact host match or www/non-www equivalence).
- Detects crawl traps: repeated directory segments, calendar date loops (`/calendar/2026/11/...`), excessive query strings (> 6 params).
- Filters out non-HTML static assets (`.png`, `.jpg`, `.pdf`, `.zip`, `.mp4`, `.css`, `.js`) and sensitive authentication endpoints (`/login`, `/cart`, `/checkout`, `/admin`).

### 3.5 PageParser (`app.services.crawler.page_parser`)
- Extracts document `<title>`, `<meta name="description">`, `<link rel="canonical">`, `<meta name="robots">`.
- Analyzes heading structure: counts `<h1>` tags and captures primary heading text.
- Classifies discovered hyperlinks into **internal** (in-scope) and **external** (out-of-scope).
- Computes SHA-256 fingerprint of page body for deduplication and future change tracking.

### 3.6 CrawlFrontier & Orchestrator (`frontier.py`, `crawler_orchestrator.py`)
- **Frontier:** BFS queue tracking URL states (`queued`, `fetching`, `completed`, `blocked`, `failed`), visited URL sets, and depth levels.
- **Pacing:** Default 1.0 second delay between requests (or respects `Crawl-delay` up to 5.0 seconds).
- **Cancellation Checkpoints:** Checks database job status between page fetches; immediately halts and commits progress when a cancellation request is received.
- **Celery Task Dispatch:** Executed via `tasks.crawler.execute_crawl` with timeout thresholds (5 min hard limit).

---

## 4. Phase 3 Default Budgets & Limits

| Parameter | Default | Maximum |
| :--- | :--- | :--- |
| Max Pages per Job | 50 | 100 |
| Max Crawl Depth | 3 | 5 |
| Request Timeout | 10.0 seconds | 10.0 seconds |
| Politeness Delay | 1.0 second | 5.0 seconds |
| Max Response Size | 2 MB | 2 MB |
| Task Hard Time Limit | 300 seconds (5 min) | 300 seconds |
