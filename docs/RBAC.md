# RankForge AI — Role-Based Access Control (RBAC) & Authorization

## 1. Role Hierarchy
RankForge AI implements a 4-tier role hierarchy within each organization workspace:

| Role | Hierarchy Level | Target Persona | Description |
| :--- | :---: | :--- | :--- |
| **Owner** | 4 | Agency Founder, CTO | Full administrative control over billing, workspace deletion, team roster, and role promotions. |
| **Admin** | 3 | Lead Technical Director, Project Manager | Can invite team members, adjust editor/viewer roles, add/delete website projects, and configure scans. |
| **Editor** | 2 | SEO Specialist, Content Strategist | Can add websites, trigger technical audits, adjust crawl rules, and update project metadata. |
| **Viewer** | 1 | Client, Executive Stakeholder | Read-only access to audit reports, scores, website projects, and workspace rosters. |

## 2. Permission Matrix

| Capability | Owner | Admin | Editor | Viewer |
| :--- | :---: | :---: | :---: | :---: |
| View Websites & Audit Reports | Yes | Yes | Yes | Yes |
| Trigger SEO Preflight Audits | Yes | Yes | Yes | No |
| Add Website Project | Yes | Yes | Yes | No |
| Edit Website Metadata | Yes | Yes | Yes | No |
| Archive / Restore Website | Yes | Yes | Yes | No |
| Delete Website Project | Yes | Yes | No | No |
| View Workspace Members | Yes | Yes | Yes | Yes |
| Invite Members (Editor, Viewer) | Yes | Yes | No | No |
| Invite Members (Admin, Owner) | Yes | No | No | No |
| Update Roles (Editor, Viewer) | Yes | Yes | No | No |
| Promote Member to Owner | Yes | No | No | No |
| Remove Member (Editor, Viewer)| Yes | Yes | No | No |
| Remove Member (Owner) | Yes | No | No | No |
| Demote or Remove Final Owner | No | No | No | No |
| Update Workspace Name / Slug | Yes | No | No | No |
| Delete Entire Workspace | Yes | No | No | No |

## 3. Privilege Escalation Defenses
1. **No Self-Role Modification**: Users cannot edit their own role via the API.
2. **Admin Ceiling**: Admins cannot promote another user or invite a new user to an equal or higher role (`admin` or `owner`).
3. **Owner Protection**: Admins cannot edit, demote, or remove an owner.
4. **Final Owner Safeguard**: The system enforces that every workspace has at least one active owner. Attempts to remove or demote the last remaining owner are rejected with HTTP 400 Bad Request.

## 4. FastAPI Dependency Implementation (`RequireOrgRole`)
```python
class RequireOrgRole:
    def __init__(self, min_role: str = "viewer"):
        self.min_role = min_role

    def __call__(
        self,
        org_id: str,
        current_user: Profile = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> OrganizationMember:
        # 1. Verify organization exists
        # 2. Verify current user is an active member
        # 3. Verify user's role integer level >= minimum role level
        ...
```
Endpoints declare authorization directly in their signature:
```python
@router.post("/organizations/{org_id}/websites")
def create_website(
    org_id: str,
    payload: WebsiteCreate,
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
    db: Session = Depends(get_db),
):
    ...
```
