"""
Lead capture service.
Persists demo/marketing submissions into a JSONL file.
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from app.schemas.lead import LeadCreate

logger = logging.getLogger(__name__)


class LeadService:
    @staticmethod
    async def save_lead(lead: LeadCreate) -> None:
        backend_dir = Path(__file__).resolve().parents[2]
        target_file = backend_dir / "lead_submissions.jsonl"

        payload = lead.model_dump()
        payload["created_at"] = datetime.now(timezone.utc).isoformat()

        with target_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True) + "\n")

        LeadService._notify_email(payload)

    @staticmethod
    def _notify_email(payload: dict) -> None:
        enabled = (os.getenv("LEAD_EMAIL_NOTIFY_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"})
        if not enabled:
            return

        smtp_host = os.getenv("SMTP_HOST", "").strip()
        smtp_port = int(os.getenv("SMTP_PORT", "587").strip())
        smtp_user = os.getenv("SMTP_USER", "").strip()
        smtp_pass = os.getenv("SMTP_PASS", "").strip()
        smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}
        from_email = os.getenv("LEAD_FROM_EMAIL", smtp_user).strip()
        to_email = os.getenv("LEAD_TO_EMAIL", "").strip()

        if not smtp_host or not from_email or not to_email:
            logger.warning("Email config missing. Set SMTP_HOST, LEAD_FROM_EMAIL (or SMTP_USER), and LEAD_TO_EMAIL.")
            return

        subject = f"New Demo Lead: {payload.get('name', '-')}"
        body = (
            "New lead submitted from marketing site.\n\n"
            f"Name: {payload.get('name', '-')}\n"
            f"Company: {payload.get('company') or '-'}\n"
            f"Phone: {payload.get('phone', '-')}\n"
            f"Email: {payload.get('email', '-')}\n"
            f"City: {payload.get('city') or '-'}\n"
            f"Requirement: {payload.get('requirement', '-')}\n"
            f"Preferred Time: {payload.get('preferred_time') or '-'}\n"
            f"Message: {payload.get('message') or '-'}\n"
            f"Source: {payload.get('source') or '-'}\n"
            f"Submitted At: {payload.get('submitted_at') or '-'}\n"
            f"Created At: {payload.get('created_at') or '-'}\n"
        )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content(body)

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                if smtp_use_tls:
                    server.starttls()
                if smtp_user:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        except Exception as exc:
            # Notification is best-effort; lead capture should still succeed.
            logger.error("Lead email notification failed: %s", exc, exc_info=True)
