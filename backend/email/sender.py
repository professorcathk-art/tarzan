"""Resend-backed mailer."""

from __future__ import annotations

import logging

import resend

from config import get_settings

logger = logging.getLogger(__name__)


def send_multipart(subject: str, html: str, text: str, to: list[str]) -> dict:
    """Send email via Resend. Returns API response or a skip marker when unconfigured."""
    cfg = get_settings()
    api_key = cfg.resend_api_key
    if not api_key:
        logger.warning("RESEND_API_KEY missing — email not delivered")
        return {"skipped": True, "reason": "no-api-key"}

    resend.api_key = api_key
    params: dict[str, object] = {
        "from": cfg.resend_from_email,
        "to": to,
        "subject": subject,
        "html": html,
        "text": text,
    }
    return resend.Emails.send(params)  # type: ignore[no-any-return]
