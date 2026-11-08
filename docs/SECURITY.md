# RankForge AI — Security Architecture & SSRF Guard Specification
**Document Version:** 1.0.0  
**Phase:** 1  
**Classification:** DevSecOps Specification  

---

## 1. Security Philosophy
RankForge AI handles website telemetry, external HTTP inspections, and multi-tenant search intelligence. The platform is designed with default-deny network postures, zero client-side credential persistence, and defense-in-depth isolation between tenants.

---

## 2. Server-Side Request Forgery (SSRF) Defense Architecture

A major risk in SEO crawlers and audit tools is Server-Side Request Forgery (SSRF), where an attacker enters an internal IP, cloud metadata endpoint, or internal microservice hostname to pivot into internal networks.

RankForge AI implements strict pre-flight and run-time validation via `SSRFGuard`:

```mermaid
flowchart TD
    Inbound["User Requests Audit for Target URL"] --> Parse["URL Parser & Scheme Verification"]
    Parse -->|Non-HTTP(S)| RejectScheme["REJECT: Prohibited Scheme"]
    Parse -->|HTTP/HTTPS| Resolve["DNS Resolution (AF_UNSPEC, SOCK_STREAM)"]
    
    Resolve --> CheckIP["IP Address Range Validation"]
    CheckIP -->|RFC 1918 Private (10.x, 172.16.x, 192.168.x)| BlockPrivate["REJECT: Private Subnet (RFC 1918)"]
    CheckIP -->|Loopback (127.x, ::1, 0.0.0.0)| BlockLoopback["REJECT: Loopback Target"]
    CheckIP -->|Link-Local / Metadata (169.254.169.254)| BlockMetadata["REJECT: Cloud Metadata Service"]
    CheckIP -->|Multicast / Reserved / Unspecified| BlockReserved["REJECT: Reserved Network Address"]
    
    CheckIP -->|Public IPv4/IPv6| CheckPort["Public Port Whitelist (80, 443, 8080, 8443)"]
    CheckPort -->|Non-Standard Port| BlockPort["REJECT: Non-Standard Port Prohibited"]
    CheckPort -->|Allowed Port| Dispatch["Execute Safe Request via Async HTTP Client"]
```

### 2.1 Mitigation Checklist

| Threat Vector | Mitigation Strategy in RankForge AI |
| :--- | :--- |
| **Private Subnet Access** | Blocks RFC 1918 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) via `ipaddress.ip_address(ip).is_private`. |
| **Loopback Exploitation** | Rejects `127.0.0.0/8`, `localhost`, `0.0.0.0`, and `::1`. |
| **Cloud Metadata Theft** | Explicitly blocks `169.254.169.254`, `metadata.google.internal`, and `instance-data`. |
| **DNS Rebinding** | Resolves socket address immediately prior to request execution; validates every resolved IP address in multi-homed records. |
| **Redirect Hijacking** | Limits redirects to `max_redirects=3`. In future crawler phases, redirects will be intercepted and re-validated against `SSRFGuard`. |
| **Response Memory Exhaustion** | Enforces hard byte limit (5MB ceiling) on streamed response payloads. |
| **Request Timeouts** | Enforces strict 10-second timeout ceiling to mitigate slowloris connection exhaustion. |
| **Non-HTTP Protocols** | Disallows `file://`, `gopher://`, `ftp://`, `ldap://`, `dict://`. Only `http://` and `https://` are permitted. |
| **Robots.txt & Authorization** | Respects target website `robots.txt` disallow directives and requires domain ownership verification prior to automated remediation. |

---

## 3. Multi-Tenant Authorization & Row-Level Security
- **Tenant Boundaries:** All database models reference an `organization_id` foreign key with cascade deletion.
- **Supabase Compatibility:** Prepared for Supabase Auth JWT tokens (`auth.uid()`). All queries in Phase 2 are filtered by the authenticated user's organization membership.
- **Safe Error Formats:** Unhandled exceptions return sanitized JSON payloads (`INTERNAL_SERVER_ERROR`) with a tracking `request_id`. Stack traces and database internals are never returned to the client.

---

## 4. Ingress Protection & HTTP Security Headers
All HTTP responses from the Next.js frontend and FastAPI backend enforce:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Request-ID`: UUID for distributed log correlation
- Parameterized SQL queries via SQLAlchemy 2.0 preventing SQL injection.
