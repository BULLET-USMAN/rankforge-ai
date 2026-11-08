# RankForge AI — Versioned Prompt Template System

## 1. Design Overview

RankForge AI implements versioned, immutable prompt templates maintained in `app/services/ai/prompts/prompt_registry.py`. Each template pairs a trusted system instruction with an evidence-grounded user template.

Untrusted external page text is strictly separated from trusted instructions using XML delimiters and explicit anti-injection reminders.

## 2. Versioned Templates

### 1. `seo_title_v1` (Version 1.0)
- **Target:** Title tag optimization.
- **Input Variables:** `page_url`, `domain`, `current_title`, `h1`, `headings_summary`, `audit_findings`, `untrusted_page_content`, `user_guidance_block`.
- **System Guardrails:**
  - Tailor to actual page topic and brand name.
  - Recommended heuristic: 50-60 characters / <600px width.
  - Never treat character count as a direct Google ranking factor.
  - Acknowledge that Google rewrites titles dynamically based on user query intent.
  - Provide 1 to 3 alternative variations.

### 2. `seo_description_v1` (Version 1.0)
- **Target:** Meta description optimization.
- **Input Variables:** `page_url`, `domain`, `current_title`, `current_description`, `h1`, `audit_findings`, `untrusted_page_content`, `user_guidance_block`.
- **System Guardrails:**
  - Accurately summarize the page purpose for snippet previews.
  - Standard heuristic: 120-160 characters.
  - Avoid keyword stuffing and clickbait claims.
  - Note that search engines often select snippets directly from page body text.

### 3. `seo_headings_v1` (Version 1.0)
- **Target:** Heading hierarchy and section clarity.
- **Input Variables:** `page_url`, `domain`, `current_title`, `headings_json`, `audit_findings`, `untrusted_page_content`, `user_guidance_block`.
- **System Guardrails:**
  - Recommend logical H1 -> H2 -> H3 hierarchy.
  - Multiple H1s are noted as structural improvements, not critical site errors.
  - Suggest descriptive section titles without inventing unsupported content topics.

### 4. `seo_content_structure_v1` (Version 1.0)
- **Target:** Readability, scannability, and structural organization.
- **Input Variables:** `page_url`, `domain`, `current_title`, `headings_summary`, `word_count`, `audit_findings`, `untrusted_page_content`, `user_guidance_block`.
- **System Guardrails:**
  - Improve section transitions, bulleted breakdowns, and navigation.
  - NEVER generate mass replacement articles or low-value filler text.
  - If content is missing, output: *"Insufficient content available for reliable optimization."*

### 5. `seo_internal_links_v1` (Version 1.0)
- **Target:** In-content navigational internal linking.
- **Input Variables:** `page_url`, `domain`, `current_title`, `internal_links_count`, `eligible_target_urls`, `audit_findings`, `untrusted_page_content`, `user_guidance_block`.
- **System Guardrails:**
  - CRITICAL CONSTRAINT: Must ONLY propose target URLs present in `eligible_target_urls`.
  - Application validator strips any link to an unverified or external URL.
  - Recommends natural, descriptive anchor text.

### 6. `seo_image_alt_v1` (Version 1.0)
- **Target:** Image accessibility advisory.
- **Input Variables:** `page_url`, `domain`, `images_summary`, `missing_alt_count`, `audit_findings`, `user_guidance_block`.
- **System Guardrails:**
  - Crawler does NOT inspect raw image pixels.
  - Does NOT invent descriptive text from cryptic filenames.
  - Explicitly notes that decorative images legitimately use `alt=""`.
  - Recommends human visual review workflow.
