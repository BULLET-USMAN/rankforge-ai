# Technical SEO Health Score & Weighting Specification

## 1. Score Range & Interpretation

RankForge AI scores technical SEO health on a scale from **0 to 100**, or returns **None** (`--`) when crawl snapshot coverage is insufficient:

- **90 – 100 (Optimal Health):** Clean technical implementation; zero critical errors; minimal low-severity advisory items.
- **70 – 89 (Optimization Advised):** Minor technical friction; template opportunities; missing descriptions or minor redirects.
- **50 – 69 (Technical Warning):** Notable technical impediments; broken links, multiple H1 skips, or crawl depth issues.
- **0 – 49 (Critical Faults):** Severe indexation blockers; circular canonical loops, site crashes, or sitemap noindex directives.
- **None / Insufficient Coverage:** Returned when zero pages could be evaluated or crawl data was empty.

---

## 2. Category Weights (Sum: 1.00)

Health scores are calculated as the weighted average of 8 discrete category scores:

| Category | Identifier | Weight | Justification |
| :--- | :--- | :---: | :--- |
| **Indexability** | `indexability` | **25%** | Controls whether pages can appear in search indices at all. Highest priority. |
| **Links & HTTP** | `links_http` | **20%** | Broken links, server crashes, and redirect chains severely harm crawl budget and UX. |
| **Canonical URLs** | `canonical` | **15%** | Duplicate content disambiguation and signal consolidation. |
| **Metadata & Tags** | `metadata` | **15%** | SERP snippet presentation and topic clarity. |
| **Site Structure** | `site_structure` | **10%** | Crawl efficiency and internal PageRank flow. |
| **Heading Hierarchy** | `headings` | **5%** | Semantic content structure and accessibility. |
| **Image Optimization** | `images` | **5%** | Accessibility and image search visibility. |
| **Schema & Sitemaps** | `structured_data_sitemaps` | **5%** | Machine readability and discovery hygiene. |

---

## 3. Severity Base Deductions

Each category starts with a baseline score of **100 points**. Identified findings incur severity-based penalty deductions:

- **Critical:** `-20.0` points
- **High:** `-10.0` points
- **Medium:** `-5.0` points
- **Low:** `-2.0` points
- **Informational:** `0.0` points

---

## 4. Template Repetition Damping Formula

In real-world websites, a single template issue (e.g. omitting a meta description on blog posts) might trigger across 50 or 500 pages. Linearly multiplying the deduction ($50 \times 5 = 250$ points) would reduce the category score to 0 regardless of other healthy factors.

To prevent disproportionate score degradation, RankForge AI applies logarithmic penalty damping for repeated identical rule occurrences:

$$\text{effective\_penalty} = \text{base\_penalty} \times \left(1 + 0.5 \cdot \log_2(n)\right)$$

Where $n$ is the number of pages flagged by that specific rule.

### Example:
- **1 page missing meta description:** Penalty $= 5.0$ points. Category score $= 95$.
- **10 pages missing meta description:** $\log_2(10) \approx 3.32$. Penalty $= 5 \times (1 + 0.5 \times 3.32) \approx 13.3$ points. Category score $= 87$.
- **100 pages missing meta description:** $\log_2(100) \approx 6.64$. Penalty $= 5 \times (1 + 0.5 \times 6.64) \approx 21.6$ points. Category score $= 78$.

This mathematical formulation correctly penalizes template issues while keeping scores calibrated, explainable, and realistic.

---

## 5. Overall Health Score Calculation

$$\text{Overall Score} = \operatorname{round}\left( \sum_{c \in \text{Categories}} \text{Score}_c \times \text{Weight}_c \right)$$

Clamped between `0` and `100`.
