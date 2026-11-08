# RankForge AI — Recommendation Engine & Grounding Standards

## 1. Recommendation Grounding Principles

Every AI recommendation in RankForge must originate from verifiable crawl and audit evidence. The engine adheres to strict grounding principles:

1. **Zero Fictional Data:** Never invent nonexistent products, services, company locations, case studies, or customer reviews.
2. **Zero Fictional Metrics:** Never invent keyword search volumes, organic search traffic counts, or guaranteed ranking increases.
3. **No Ranking Guarantees:** Search rankings depend on hundreds of algorithmic factors, competitor dynamics, and user intent. AI recommendations are structured proposals designed to improve technical clarity and crawlability, not magic ranking guarantees.
4. **Insufficient Content Honesty:** If a crawled page lacks sufficient body copy, heading structure, or audit context, the system returns:
   > *"Insufficient content available for reliable optimization."*
   It never hallucinates body text to satisfy a prompt.

## 2. Six Supported Recommendation Types

| Type | Target Problem | Input Context | Proposal Format |
| :--- | :--- | :--- | :--- |
| `title_optimization` | Missing, generic, duplicate, or truncated title tags. | Current title, H1, headings, page text sample. | Optimized title string (<60 chars) + 1-3 alternatives. |
| `meta_description` | Missing or uninformative meta description. | Current description, title, H1, page text sample. | Compelling snippet summary (120-160 chars) + 1-2 alternatives. |
| `heading_structure` | Skipped heading levels, missing H1, uninformative headings. | Headings JSON hierarchy (`h1`, `h2`, `h3`). | Structured outline showing logical H1 -> H2 -> H3 re-ordering. |
| `content_structure` | Dense walls of text, low readability, poor topical transitions. | Word count, headings summary, body text sample. | Actionable editorial advisory (bulleted recommendations). |
| `internal_linking` | Orphaned or underlinked pages, generic anchor text. | Verified internal crawl link graph, eligible URLs list. | Target internal URLs + recommended descriptive anchor text. |
| `image_alt_guidance` | Images missing alt text for screen readers. | HTML image attributes (`src`, `alt`). | Accessibility workflow guidance + decorative `alt=""` reminder. |

## 3. Image Accessibility Constraints

Because the Phase 3 website crawler captures HTML metadata without downloading or performing computer vision on raw image binary bytes:
- The engine does NOT guess visual scenes based on filenames (e.g. `img_8921.jpg` is not assumed to be a "team photo").
- The engine clearly informs the reviewer that visual human verification is required.
- The engine explicitly acknowledges that purely decorative images should legitimately use empty alt text (`alt=""`) per W3C Web Content Accessibility Guidelines (WCAG).
