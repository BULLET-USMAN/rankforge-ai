# RankForge AI — AI Optimization System Architecture

## 1. Architectural Principles & Isolation

RankForge AI decouples analytical diagnostics from AI-assisted generative intelligence. The AI Optimization Engine is an independent, evidence-grounded layer situated strictly downstream from the Crawler Engine (Phase 3) and Technical SEO Audit Engine (Phase 4).

```
+-----------------------------------------------------------------------------------+
|                                 RANKFORGE AI SAAS                                 |
+-----------------------------------------------------------------------------------+
|  1. CRAWLER ENGINE (Phase 3)                                                      |
|     - Discovers, fetches, and parses authorized website pages.                    |
|     - Extracts title, meta tags, heading hierarchies, images, and link graph.     |
|     - Enforces SSRF defense and response byte limits.                             |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  2. TECHNICAL SEO AUDIT ENGINE (Phase 4)                                          |
|     - Evaluates 8 deterministic SEO categories against 30+ rules.                 |
|     - Emits structured, verifiable findings with fingerprints and evidence.       |
|     - Calculates transparent category and aggregate health scores.                |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  3. AI OPTIMIZATION ENGINE (Phase 5)                                              |
|     - Ingests verified audit findings, page metadata, and link graph context.     |
|     - Sanitizes untrusted text and wraps inputs in strict security delimiters.    |
|     - Prompts Google Gemini (gemini-2.5-flash) using structured Pydantic schemas. |
|     - Independently validates output values, lengths, and destination URLs.       |
|     - Emits human-reviewable recommendation proposals.                            |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  4. RECOMMENDATION REVIEW & EDIT ENGINE (Phase 5)                                 |
|     - Tracks lifecycle: draft -> needs_review -> approved / rejected / outdated.  |
|     - Side-by-side Before/After diff comparison.                                  |
|     - Human inline editing with immutable version history.                        |
|     - Regeneration with constrained user guidance.                                |
|     - ZERO SITE MODIFICATIONS: Approval is strictly an editorial proposal signoff.|
+-----------------------------------------------------------------------------------+
                                         |
                                         v (Phase 8 Future)
+-----------------------------------------------------------------------------------+
|  5. AUTHORIZED AUTO-FIX ENGINE (Phase 8 - Future Scope)                           |
|     - Applies explicitly authorized changes via CMS connectors & signed webhooks. |
|     - Immutable rollback snapshots.                                               |
+-----------------------------------------------------------------------------------+
```

## 2. Core Components & Service Boundaries

1. **`AIProviderInterface`** (`app/services/ai/provider_interface.py`):
   Abstract contract defining `generate(request: AIProviderRequest) -> AIProviderResponse` and `health_check() -> bool`.

2. **`GeminiProvider`** (`app/services/ai/gemini_provider.py`):
   Production provider using official `google-genai` Python SDK. Connects to `gemini-2.5-flash` with exponential backoff, rate limit backoff (HTTP 429), structured schema outputs, and token usage accounting.

3. **`MockAIProvider`** (`app/services/ai/mock_provider.py`):
   Deterministic, zero-network provider used for offline testing, local sandboxes, and continuous integration. Conforms strictly to all schemas and produces realistic, grounded recommendations.

4. **`OptimizationContextBuilder`** (`app/services/ai/context_builder.py`):
   Extracts authorized crawl metadata and audit findings for a target URL. Sanitizes untrusted crawled content, neutralizes XML delimiters, extracts eligible internal link target URLs, and formats versioned prompts.

5. **`RecommendationValidator`** (`app/services/ai/validator.py`):
   Performs independent application-side validation. Enforces character bounds, strips HTML `<script>` tags, inline event handlers, and `javascript:` URIs, and removes unverified link target URLs.

6. **`RecommendationPrioritizer`** (`app/services/ai/prioritizer.py`):
   Deterministically calculates technical priority (`high`, `medium`, `low`) using source audit severity and page metadata completeness, independent of model self-assessed confidence.

7. **`AIUsageMeter`** (`app/services/ai/usage_meter.py`):
   Tracks daily requests and monthly token quotas. Computes estimated USD costs based on configurable model rates. Implements atomic quota reservations for concurrent background jobs.

8. **`RecommendationReviewService`** (`app/services/ai/review_service.py`):
   Governs proposal status transitions (`draft`, `needs_review`, `approved`, `rejected`, `outdated`), manual edits, version increments, and audit history preservation.

9. **`AIOptimizationOrchestrator`** (`app/services/ai/orchestrator.py`):
   Coordinates single-page generation, regeneration with guidance, and batch jobs via background Celery tasks.
