# RankForge AI — Usage Accounting, Cost Control & Quotas

## 1. Accounting Model & Tenancy Isolation

All AI operations are metered and accounted for at the organization level:
- Every generation request persists an `AIUsageRecord` linking the `organization_id`, `user_id`, `job_id`, `model`, `request_type`, input/output tokens, and estimated cost.
- Usage is strictly isolated: Organization A cannot view, consume, or impact Organization B's quotas.

## 2. Default Limits & Thresholds

| Quota Metric | Default Limit | Reset Window | Scope |
| :--- | :--- | :--- | :--- |
| Daily Request Limit | 100 requests | Rolling 24 hours | Organization |
| Monthly Token Quota | 500,000 tokens | Calendar month | Organization |
| Max Batch Size | 20 pages | Per job | Single execution |
| Max Concurrent Jobs | 3 jobs | Real-time | Organization |

## 3. Concurrency-Safe Atomic Reservations

To prevent race conditions where multiple concurrent batch jobs exceed token quotas:
1. Before job dispatch, the system checks current usage + active reservations.
2. If sufficient quota exists, it creates an `AIQuotaReservation(tokens_reserved=N, status="active")`.
3. Upon job completion, actual usage is logged in `AIUsageRecord` and the reservation status updates to `"committed"`.
4. If the job fails or is cancelled, the reservation updates to `"released"`, freeing reserved capacity.

## 4. Cost Estimation Mechanism

Costs are dynamically calculated using configurable pricing settings in `app/core/config.py`:
- `AI_ESTIMATED_INPUT_COST_PER_MILLION`: Default \$0.075 per 1,000,000 input tokens.
- `AI_ESTIMATED_OUTPUT_COST_PER_MILLION`: Default \$0.30 per 1,000,000 output tokens.

$$\text{Estimated Cost (USD)} = \left(\frac{\text{Input Tokens}}{1,000,000} \times 0.075\right) + \left(\frac{\text{Output Tokens}}{1,000,000} \times 0.30\right)$$

Costs are presented as internal operational estimates and do not represent immediate customer invoicing until subscription billing is activated in Phase 11.
