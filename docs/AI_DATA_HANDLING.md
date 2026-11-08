# RankForge AI — Data Handling & Privacy Policy

## 1. Data Minimization Principles

RankForge AI follows strict data minimization practices when interacting with external AI providers:

1. **Only Relevant Excerpts:** Only the metadata, headings, and bounded body text required for the specific recommendation type are submitted to Gemini.
2. **Never Transmitted:**
   - User authentication tokens or Supabase JWTs
   - Passwords, hashes, or recovery tokens
   - API keys, database credentials, or secret configuration
   - Customer payment details, credit cards, or Stripe identifiers
   - Private organization memberships or employee emails
   - Unrelated tenant website projects

## 2. External AI Processing Disclosures

- Selected public webpage content and structural SEO metadata are processed by Google's Gemini API according to Google's standard enterprise API data handling terms.
- In production configurations, customer data submitted via standard API tiers is governed by Google Cloud / Google AI enterprise data protection standards (data is not used to train global base models without consent).

## 3. Retention & Storage

- **Stored Proposals:** Generated proposals, explanations, and evidence metadata are retained in PostgreSQL (`ai_recommendations`) for auditability, version tracking, and review.
- **Raw Prompts & Raw Responses:** Ephemeral by default. Raw prompt payloads and verbose LLM responses are discarded after schema parsing to prevent storing unnecessary duplicates.
- **Tenant Control:** When a website project or organization is deleted, all associated `ai_recommendations`, `ai_recommendation_versions`, and `ai_usage_records` are cascaded and permanently removed.
