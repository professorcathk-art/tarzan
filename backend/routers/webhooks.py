"""Stripe webhook handler."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Request

import stripe

from config import get_settings


router = APIRouter(tags=["billing"])

log = logging.getLogger(__name__)


@router.post("/webhooks/stripe")

async def stripe_webhook(request: Request, stripe_signature: str | None = Header(default=None, alias="stripe-signature")):

    payload = await request.body()

    s = get_settings()

    secret = s.stripe_webhook_secret or ""

    if not secret:

        log.warning("STRIPE_WEBHOOK_SECRET not set — rejecting")

        raise HTTPException(status_code=503, detail="Webhook not configured")

    if not stripe_signature:

        raise HTTPException(status_code=400, detail="Missing signature")

    try:

        event = stripe.Webhook.construct_event(payload, stripe_signature, secret)

    except Exception:

        raise HTTPException(status_code=400, detail="Invalid signature")

    evt_type = str(event["type"])

    # Sync subscription tiers with users table in a full deployment.

    return {"received": True, "event": evt_type}
