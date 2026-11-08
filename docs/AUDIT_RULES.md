# Technical SEO Audit Rule Catalog

The RankForge AI Audit Engine evaluates rules across 8 technical SEO categories. Every rule returns actionable recommendations, concrete observed evidence, and generates a deterministic SHA-256 fingerprint.

---

## 1. Metadata & Tags (`metadata`)

| Rule ID | Name | Severity | Condition | Actionable Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **META-001** | Missing Page Title Tag | `critical` | `<title>` is `None` on 200 OK HTML page | Add a descriptive `<title>` tag inside the `<head>` element. |
| **META-002** | Empty Page Title Tag | `high` | `<title>` exists but is whitespace-only | Populate `<title>` with unique, descriptive page topic text. |
| **META-003** | Duplicate Page Title | `medium` | Two or more distinct URLs share identical title text | Craft distinct title tags for each page to prevent cannibalization. |
| **META-004** | Suboptimal Title Length | `low` / `info` | Title length &lt; 30 chars (too short) or &gt; 65 chars (truncates) | Aim for 30–65 characters with primary keywords placed early. |
| **META-005** | Missing Meta Description | `medium` | `<meta name="description">` is absent | Add a concise meta description summarizing page value. |
| **META-006** | Empty Meta Description | `low` | Meta description tag is whitespace-only | Supply a concise summary of page content in description attribute. |
| **META-007** | Duplicate Meta Description | `low` | Multiple pages share identical description | Provide unique meta descriptions reflecting each URL's specific purpose. |
| **META-008** | Suboptimal Description Length | `low` / `info` | Description length &lt; 70 chars or &gt; 160 chars | Aim for 120–160 characters with clear value and call-to-action. |

---

## 2. Heading Hierarchy (`headings`)

| Rule ID | Name | Severity | Condition | Actionable Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **HEAD-001** | Missing H1 Heading | `high` | Page contains zero `<h1>` tags | Add an `<h1>` heading tag that clearly introduces the page topic. |
| **HEAD-002** | Multiple H1 Headings | `info` | Page contains &gt; 1 `<h1>` tags | Consider keeping one primary `<h1>` and converting subheadings to `<h2>`. |
| **HEAD-003** | Empty H1 Heading | `medium` | An `<h1>` tag has empty/blank text | Ensure all `<h1>` tags contain meaningful text describing the subject. |
| **HEAD-004** | Heading Level Skipped | `low` | Page has H1 and H3 but zero H2 tags | Structure content hierarchically: use `<h2>` before `<h3>`. |
| **HEAD-005** | Duplicate H1 Across Pages | `low` | Distinct URLs share identical H1 text | Differentiate primary page headings across distinct URLs. |

---

## 3. Indexability (`indexability`)

| Rule ID | Name | Severity | Condition | Actionable Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **INDX-001** | Meta Robots Noindex | `high` | `<meta name="robots" content="...noindex...">` | Remove `noindex` if page is intended to be indexed in organic search. |
| **INDX-002** | X-Robots-Tag Noindex | `high` | Header `X-Robots-Tag: ...noindex...` present | Adjust server configuration to remove noindex header from indexable routes. |
| **INDX-003** | Meta Robots Nofollow | `medium` | Page specifies `nofollow` directive | Remove `nofollow` unless page strictly hosts untrusted links. |
| **INDX-004** | Sitemap URL Marked Noindex | `critical` | URL in XML sitemap returns `noindex` | Reconcile conflicting signals: remove URL from sitemap or remove `noindex`. |

---

## 4. Canonical URLs (`canonical`)

| Rule ID | Name | Severity | Condition | Actionable Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **CANON-001** | Missing Canonical Tag | `low` | Page lacks `rel="canonical"` link tag | Add a self-referencing or target canonical link to prevent duplicate ambiguity. |
| **CANON-002** | Canonical with Fragment | `high` | Canonical URL contains `#fragment` | Remove hash fragment; canonical targets must be bare document URLs. |
| **CANON-003** | Canonical Points to Broken URL | `critical` | Canonical target returns 4xx or 5xx | Update canonical to point to a valid, live 200 OK document. |
| **CANON-004** | Canonical Points to Redirect | `high` | Canonical target returns 3xx redirect | Point canonical directly to the final 200 OK destination. |
| **CANON-005** | Circular Canonical Loop | `critical` | Page A canonizes to B, B canonizes to A | Break loop by choosing one single definitive URL as canonical version. |
| **CANON-006** | Cross-Domain Canonical | `info` | Canonical targets external hostname | Confirm cross-domain syndication is intentional. |

---

## 5. Links & HTTP (`links_http`)

| Rule ID | Name | Severity | Condition | Actionable Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **HTTP-001** | Internal Dead Link | `critical` | Internal hyperlink targets 4xx dead page | Fix or remove link so crawlers and users do not reach dead pages. |
| **HTTP-002** | Internal Server Error Link | `critical` | Internal hyperlink targets 5xx server crash | Troubleshoot and resolve backend crash on target endpoint. |
| **HTTP-003** | Internal Redirect Link | `medium` | Internal hyperlink targets 3xx redirect | Update link directly to target URL, saving crawl budget and latency. |
| **HTTP-004** | Redirect Chain Observed | `high` | Crawled page underwent &gt; 1 redirect hop | Eliminate intermediate hops; redirect directly to final destination in 301. |
| **HTTP-005** | Slow Server Response | `medium` | Page response latency &gt; 2000 ms | Optimize backend queries and caching to achieve &lt; 800 ms TTFB. |

---

## 6. Site Structure & Internal Linking (`site_structure`)

| Rule ID | Name | Severity | Condition | Actionable Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **LINK-001** | Excessive Crawl Depth | `medium` | Page crawl depth &ge; 4 clicks from root | Add contextual inlinks from category pages to bring within 3 clicks. |
| **LINK-002** | Orphan Page Detected | `medium` | Page has 0 internal inlinks in snapshot | Link from relevant navigation or content to distribute link equity. |
| **LINK-003** | Empty Anchor Text | `low` | Internal link has empty/blank anchor text | Provide descriptive anchor text on internal hyperlinks for context. |

---

## 7. Image Optimization (`images`)

| Rule ID | Name | Severity | Condition | Actionable Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **IMG-001** | Missing Alt Attribute | `medium` | `<img>` tag completely omits `alt` attribute | Add descriptive alt text (or `alt=""` if purely decorative). |
| **IMG-002** | Generic Alt Text | `low` | Alt text is "image", "photo", "logo", etc. | Replace generic placeholder with descriptive context. |

*Fallback Handling:* If a snapshot was generated prior to Phase 4 image extraction, image rules yield status `not_evaluated` with clear explanation rather than false alarms.

---

## 8. Schema & Sitemaps (`structured_data_sitemaps`)

| Rule ID | Name | Severity | Condition | Actionable Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **SD-001** | Malformed JSON-LD Syntax | `high` | `<script type="application/ld+json">` parse error | Fix JSON syntax error so search engines can read structured data. |
| **SD-002** | Missing Schema @type | `medium` | JSON-LD block lacks recognized `@type` | Define appropriate Schema.org `@type` inside structured data block. |
| **SMAP-001** | XML Sitemap Error | `high` | Sitemap URL returns HTTP error or failed status | Ensure XML sitemaps are reachable, return 200, and use XML content-type. |
| **SMAP-002** | Duplicate Sitemap URLs | `low` | Sitemap contains repeated entries for same URL | Deduplicate URLs in XML sitemaps to prevent crawl waste. |
