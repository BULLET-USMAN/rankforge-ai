# RankForge AI — Recommendation Review & Approval Workflow

## 1. Proposal Status Lifecycle

Recommendations move through an explicit state machine:

```
               [ AI Engine / User Request ]
                             |
                             v
                         +-------+
                         | draft |
                         +-------+
                             |
                             v
                     +--------------+
                     | needs_review | <-------------------+
                     +--------------+                     |
                       /           \                      |
       Approve Action /             \ Reject Action       | Manual Edit
                     v               v                    | or Regeneration
               +----------+     +----------+              |
               | approved |     | rejected |              |
               +----------+     +----------+              |
                     |                                    |
                     +------------------------------------+
```

- **`draft`**: Proposal saved by user for ongoing work without entering the active team review queue.
- **`needs_review`**: Initial state of freshly generated AI proposals or proposals that were modified after approval.
- **`approved`**: Proposal accepted by an authorized team member (Admin or Owner).
- **`rejected`**: Proposal dismissed with an optional recorded rationale.
- **`outdated`**: Set automatically when a subsequent crawl or audit renders the recommendation's underlying baseline obsolete.

## 2. Zero Automatic Live Modifications Guarantee

> [!IMPORTANT]
> An **approved** recommendation in Phase 5 is strictly an approved editorial proposal. Approval does NOT push changes to customer websites, DOM trees, CMS platforms, or DNS records. Automated remediation with explicit consent safeguards belongs to Phase 8.

## 3. Version History & Revision Tracking

- Each recommendation starts at version `v1`.
- Any manual edit increments the version number (`v2`, `v3`, etc.) and creates an immutable snapshot in `ai_recommendation_versions`.
- If an approved recommendation is subsequently edited, its status resets to `needs_review` to prevent unreviewed changes from silently retaining approval status.
- Regeneration requests preserve previous versions, record user guidance notes, and create a new version snapshot.

## 4. Role-Based Authorization (RBAC)

| Role | Generate | Review | Edit | Approve | Reject |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Owner** | Yes | Yes | Yes | Yes | Yes |
| **Admin** | Yes | Yes | Yes | Yes | Yes |
| **Editor** | Yes | Yes | Yes | No (requires Admin) | No |
| **Viewer** | No | Read-only | No | No | No |
