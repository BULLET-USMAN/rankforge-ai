"""Domain Ownership Verification Service for RankForge.

Supports two verification mechanisms:
1. DNS TXT record challenge (_rankforge-challenge.<domain>)
2. HTML verification file challenge (/.well-known/rankforge-verification.txt)

Enforces nonces, expiration, tenant isolation, and SSRF prevention.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Tuple

import dns.exception
import dns.resolver
from sqlalchemy.orm import Session

from app.models.website_project import WebsiteProject
from app.models.website_verification import WebsiteVerification
from app.services.crawler.safe_fetcher import (
    MAX_VERIFICATION_BYTES,
    SafeHttpFetcher,
)

logger = logging.getLogger(__name__)

VERIFICATION_EXPIRY_DAYS = 7


class VerificationService:
    """
    Manages multi-tenant website domain ownership verification via:
      1. DNS TXT record challenge (_rankforge-challenge.<domain>)
      2. HTML verification file challenge (/.well-known/rankforge-verification.txt)
    """

    @classmethod
    def _normalize_method(cls, method: str) -> str:
        clean = method.strip().lower()
        if clean in ("file_upload", "html_file"):
            return "file_upload"
        if clean == "dns_txt":
            return "dns_txt"
        raise ValueError(f"Unsupported verification method '{method}'. Must be 'dns_txt' or 'html_file'.")

    @classmethod
    def get_or_create_challenge(
        cls, db: Session, project: WebsiteProject, method: str = "dns_txt"
    ) -> WebsiteVerification:
        """Retrieves existing active verification challenge or generates a fresh one."""
        method_clean = cls._normalize_method(method)
        now = datetime.now(timezone.utc)

        # Look for existing pending/verified record for this project and method
        verif = (
            db.query(WebsiteVerification)
            .filter(
                WebsiteVerification.project_id == project.id,
                WebsiteVerification.method == method_clean,
            )
            .first()
        )

        # If existing record is unexpired and pending/verified, return it
        if verif and verif.status in {"pending", "verified"} and verif.expires_at:
            exp = verif.expires_at if verif.expires_at.tzinfo else verif.expires_at.replace(tzinfo=timezone.utc)
            if exp > now:
                return verif

        # Otherwise, initiate fresh challenge
        return cls.initiate_challenge(db, project, method_clean)

    @classmethod
    def initiate_challenge(
        cls, db: Session, project: WebsiteProject, method: str = "dns_txt"
    ) -> WebsiteVerification:
        """Generates an unpredictable secure challenge token and sets up instructions."""
        method_clean = cls._normalize_method(method)

        token = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=VERIFICATION_EXPIRY_DAYS)

        txt_name = f"_rankforge-challenge.{project.domain}"
        txt_val = f"rankforge-verification={token}"
        file_path = "/.well-known/rankforge-verification.txt"
        file_content = f"rankforge-verification={token}"

        verif = (
            db.query(WebsiteVerification)
            .filter(
                WebsiteVerification.project_id == project.id,
                WebsiteVerification.method == method_clean,
            )
            .first()
        )

        if not verif:
            verif = WebsiteVerification(
                project_id=project.id,
                method=method_clean,
                token=token,
                status="pending",
                txt_record_name=txt_name if method_clean == "dns_txt" else None,
                txt_record_value=txt_val if method_clean == "dns_txt" else None,
                file_path=file_path if method_clean == "file_upload" else None,
                file_content=file_content if method_clean == "file_upload" else None,
                expires_at=expires_at,
            )
            db.add(verif)
        else:
            verif.token = token
            verif.status = "pending"
            verif.txt_record_name = txt_name if method_clean == "dns_txt" else None
            verif.txt_record_value = txt_val if method_clean == "dns_txt" else None
            verif.file_path = file_path if method_clean == "file_upload" else None
            verif.file_content = file_content if method_clean == "file_upload" else None
            verif.expires_at = expires_at
            verif.failure_reason = None
            verif.last_checked_at = None
            verif.revoked_at = None
            verif.verified_at = None

        project.verification_token = token
        db.commit()
        db.refresh(verif)
        return verif

    @classmethod
    def verify_dns_txt(
        cls, db: Session, project: WebsiteProject
    ) -> Tuple[bool, str, WebsiteVerification]:
        """
        Queries DNS TXT records for _rankforge-challenge.<domain> and validates challenge token.
        """
        verif = cls.get_or_create_challenge(db, project, "dns_txt")
        now = datetime.now(timezone.utc)

        # Check expiration
        if verif.expires_at:
            exp = verif.expires_at if verif.expires_at.tzinfo else verif.expires_at.replace(tzinfo=timezone.utc)
            if exp <= now:
                verif.status = "expired"
                verif.failure_reason = "Verification challenge has expired. Please regenerate a new token."
                db.commit()
                return False, verif.failure_reason, verif

        expected_values = {
            f"rankforge-verification={verif.token}".lower(),
            verif.token.lower(),
        }

        # Query DNS TXT
        resolver = dns.resolver.Resolver()
        resolver.timeout = 4.0
        resolver.lifetime = 6.0

        records_found = []
        dns_query_target = verif.txt_record_name or f"_rankforge-challenge.{project.domain}"

        try:
            answers = resolver.resolve(dns_query_target, "TXT")
            for rdata in answers:
                txt_string = b"".join(rdata.strings).decode("utf-8", errors="ignore").strip().lower()
                records_found.append(txt_string)
        except dns.resolver.NXDOMAIN:
            # Fallback to root domain if challenge subdomain was not created
            try:
                root_answers = resolver.resolve(project.domain, "TXT")
                for rdata in root_answers:
                    txt_string = b"".join(rdata.strings).decode("utf-8", errors="ignore").strip().lower()
                    records_found.append(txt_string)
            except Exception:
                pass
        except dns.resolver.NoAnswer:
            pass
        except dns.resolver.Timeout:
            reason = "DNS query timed out. Please allow time for DNS propagation and retry."
            verif.last_checked_at = now
            verif.failure_reason = reason
            db.commit()
            return False, reason, verif
        except dns.exception.DNSException as e:
            reason = f"DNS resolution error: {str(e)}"
            verif.last_checked_at = now
            verif.failure_reason = reason
            db.commit()
            return False, reason, verif

        # Validate against expected challenge
        is_match = any(
            any(exp in rec for exp in expected_values)
            for rec in records_found
        )

        verif.last_checked_at = now
        if is_match:
            verif.status = "verified"
            verif.verified_at = now
            verif.failure_reason = None
            project.is_verified = True
            project.verification_status = "verified"
            db.commit()
            return True, "Domain ownership successfully verified via DNS TXT record.", verif
        else:
            verif.status = "failed"
            found_summary = f"Found {len(records_found)} TXT records." if records_found else "No TXT records found."
            reason = f"Expected record value containing '{verif.txt_record_value}' at {dns_query_target}. {found_summary} DNS changes may take several minutes to propagate."
            verif.failure_reason = reason
            db.commit()
            return False, reason, verif

    @classmethod
    def verify_html_file(
        cls, db: Session, project: WebsiteProject
    ) -> Tuple[bool, str, WebsiteVerification]:
        """
        Fetches https://<domain>/.well-known/rankforge-verification.txt and validates expected token content.
        """
        verif = cls.get_or_create_challenge(db, project, "file_upload")
        now = datetime.now(timezone.utc)

        if verif.expires_at:
            exp = verif.expires_at if verif.expires_at.tzinfo else verif.expires_at.replace(tzinfo=timezone.utc)
            if exp <= now:
                verif.status = "expired"
                verif.failure_reason = "Verification challenge has expired. Please regenerate a new token."
                db.commit()
                return False, verif.failure_reason, verif

        target_url = f"https://{project.domain}/.well-known/rankforge-verification.txt"
        verif.last_checked_at = now

        response = SafeHttpFetcher.fetch_sync(
            target_url,
            max_bytes=MAX_VERIFICATION_BYTES,
            timeout_seconds=6.0,
            allowed_domains={project.domain},
        )

        if not response.is_success or response.status_code != 200:
            # Fallback to HTTP
            fallback_url = f"http://{project.domain}/.well-known/rankforge-verification.txt"
            fallback_res = SafeHttpFetcher.fetch_sync(
                fallback_url,
                max_bytes=MAX_VERIFICATION_BYTES,
                timeout_seconds=6.0,
                allowed_domains={project.domain},
            )
            if fallback_res.is_success and fallback_res.status_code == 200:
                response = fallback_res
            else:
                verif.status = "failed"
                err_msg = response.error_details or fallback_res.error_details or f"HTTP {response.status_code or fallback_res.status_code}"
                reason = f"Could not retrieve verification file from {target_url} or {fallback_url}: {err_msg}"
                verif.failure_reason = reason
                db.commit()
                return False, reason, verif

        content = response.text.strip()
        expected_patterns = [
            f"rankforge-verification={verif.token}".lower(),
            verif.token.lower(),
        ]

        if any(p in content.lower() for p in expected_patterns):
            verif.status = "verified"
            verif.verified_at = now
            verif.failure_reason = None
            project.is_verified = True
            project.verification_status = "verified"
            db.commit()
            return True, "Domain ownership successfully verified via HTML verification file.", verif
        else:
            verif.status = "failed"
            reason = f"File content mismatch. Expected '{verif.file_content}', received '{content[:100]}'."
            verif.failure_reason = reason
            db.commit()
            return False, reason, verif

    @classmethod
    def revoke_verification(cls, db: Session, project: WebsiteProject) -> WebsiteProject:
        """Revokes domain ownership verification status and halts active crawl authorization."""
        now = datetime.now(timezone.utc)
        project.is_verified = False
        project.verification_status = "revoked"

        verifications = (
            db.query(WebsiteVerification)
            .filter(WebsiteVerification.project_id == project.id)
            .all()
        )
        for v in verifications:
            v.status = "revoked"
            v.revoked_at = now

        db.commit()
        db.refresh(project)
        return project
