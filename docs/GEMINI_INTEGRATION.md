# RankForge AI — Google Gemini API Integration Guide

## 1. Official SDK & Model Configuration

RankForge AI integrates Google's generative models via the official, supported **Google Gen AI Python SDK** (`google-genai>=1.0.0`, version 3.0.0+).

### Key Dependencies
```txt
google-genai>=1.0.0
pydantic>=2.8.0
```

### Supported Models
- **Default Model:** `gemini-2.5-flash` (balanced latency, reasoning capability, and structured output support).
- **Alternative Configurable Models:** `gemini-1.5-pro`, `gemini-1.5-flash`.
- Obsolete or deprecated models (`gemini-1.0-pro`, PaLM 2) are not used.

## 2. Environment Variables & Backend Configuration

All API credentials remain strictly server-side on the FastAPI backend. API keys are **never** passed to the browser or exposed in frontend bundles.

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | `None` | Google AI Studio or Vertex API key. Backend-only. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Configurable target Gemini model identifier. |
| `AI_PROVIDER` | `gemini` | `gemini` for live production, `mock` for automated testing. |
| `AI_MAX_OUTPUT_TOKENS` | `2048` | Hard output token cap per request. |
| `AI_REQUEST_TIMEOUT_SECONDS` | `30` | Network request timeout before failing fast. |
| `AI_MAX_RETRIES` | `3` | Max retry attempts with exponential backoff on transient errors. |
| `AI_DAILY_ORG_REQUEST_LIMIT` | `100` | Max recommendations generated per organization in 24h. |
| `AI_MONTHLY_ORG_TOKEN_LIMIT` | `500000` | Max total tokens per organization per calendar month. |

## 3. Structured Output Enforcement

To eliminate unpredictable markdown formatting or malformed JSON, Gemini requests utilize native schema validation via `response_mime_type="application/json"` and `response_schema=RawAIOptimizationOutput`:

```python
from google import genai
from google.genai import types
from app.services.ai.types import RawAIOptimizationOutput

client = genai.Client(api_key=settings.GEMINI_API_KEY)
config = types.GenerateContentConfig(
    system_instruction=request.system_instruction,
    temperature=0.2,
    max_output_tokens=request.max_output_tokens,
    response_mime_type="application/json",
    response_schema=RawAIOptimizationOutput,
)

response = await client.aio.models.generate_content(
    model=settings.GEMINI_MODEL,
    contents=request.user_content,
    config=config,
)
```

## 4. Failure & Resilience Handling

1. **Missing API Key:**
   If `GEMINI_API_KEY` is absent when `AI_PROVIDER="gemini"`, the engine explicitly disables live generation and returns HTTP 503 (`AIProviderConfigurationError`). It does NOT silently fabricate fake recommendations.

2. **Rate Limits (HTTP 429):**
   Catches `resource_exhausted` or HTTP 429 and raises `AIRateLimitExceededError` with client-friendly retry headers.

3. **Request Timeouts:**
   Enforces `asyncio.wait_for(..., timeout=30.0)`. On timeout, retries with exponential backoff (`2 ** attempt`) up to `AI_MAX_RETRIES`.

4. **Structured JSON Validation:**
   If raw response fails Pydantic schema validation, it is rejected and logged. Malformed model text is never stored as an approved proposal.
