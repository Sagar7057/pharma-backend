"""
Settings service
Store and retrieve user-level common quote metrics.
"""

import logging
import json
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class SettingsService:
    """Settings operations for user defaults."""

    DEFAULTS: Dict[str, Any] = {
        "default_gst_pct": 12.0,
        "default_retailer_discount_pct": 0.0,
        "default_stockist_discount_pct": 0.0,
        "default_scheme_discount_pct": 0.0,
        "default_cash_discount_pct": 0.0,
        "default_volume_discount_pct": 0.0,
        "default_freight_amount": 0.0,
        "default_handling_amount": 0.0,
        "default_other_charges_amount": 0.0,
        "default_claim_rebate_amount": 0.0,
    }

    @staticmethod
    def _ensure_table(db: Session) -> None:
        """Create table lazily for existing deployments."""
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS user_common_metrics (
                    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    metrics_json JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        db.commit()

    @staticmethod
    async def get_common_metrics(user_id: str, db: Session) -> Dict[str, Any]:
        """Return user defaults, or system defaults when not configured."""
        try:
            SettingsService._ensure_table(db)
            row = db.execute(
                text(
                    """
                    SELECT metrics_json
                    FROM user_common_metrics
                    WHERE user_id = :user_id
                    """
                ),
                {"user_id": user_id},
            ).fetchone()

            if not row or not row[0]:
                return dict(SettingsService.DEFAULTS)

            merged = dict(SettingsService.DEFAULTS)
            merged.update(row[0] or {})
            return merged
        except Exception as e:
            logger.error(f"Failed to fetch common metrics: {e}")
            return dict(SettingsService.DEFAULTS)

    @staticmethod
    async def upsert_common_metrics(user_id: str, metrics: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Save and return merged common metrics."""
        try:
            SettingsService._ensure_table(db)
            merged = dict(SettingsService.DEFAULTS)
            merged.update(metrics or {})

            db.execute(
                text(
                    """
                    INSERT INTO user_common_metrics (user_id, metrics_json, created_at, updated_at)
                    VALUES (:user_id, CAST(:metrics_json AS JSONB), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id)
                    DO UPDATE SET metrics_json = CAST(:metrics_json AS JSONB), updated_at = CURRENT_TIMESTAMP
                    """
                ),
                {"user_id": user_id, "metrics_json": json.dumps(merged)},
            )
            db.commit()
            return merged
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save common metrics: {e}")
            raise Exception("Failed to save common metrics")
