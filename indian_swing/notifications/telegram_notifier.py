"""
Telegram notification channel for IndianSwing.

Architecture
------------
This module is intentionally isolated from the rest of the codebase.
It has *no* dependency on the recommendation/strategy/database layer.
The scanner passes plain Python data-structures (dicts) so this module
stays purely a notification sink.

Future channels (Email, WhatsApp, Discord ...) should follow the same
pattern: implement the `NotificationChannel` base-class below and call
it from `scanner.py` after `_complete_scan_job`.
"""
from __future__ import annotations

import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx  # already available via FastAPI / starlette dependency tree

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pluggable base class — future channels (Email, Discord ...) extend this
# ---------------------------------------------------------------------------


class NotificationChannel(ABC):
    """Abstract notification channel.  Implementations must never raise."""

    @abstractmethod
    def send_recommendations(self, recommendations: list[dict[str, Any]]) -> None:
        """Send a list of recommendation dicts to the channel.

        Each dict must contain at least:
            symbol          str  — stock ticker
            company_name    str  — full company name
            action          str  — "BUY" / "SELL" etc.
            entry_price     float
            target_1        float
            target_2        float | None
            stop_loss       float
            confidence_score float
            explanation     dict  — forensic analysis sections (optional)
        """


# ---------------------------------------------------------------------------
# Telegram implementation
# ---------------------------------------------------------------------------

# Environment variable names
_BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
_CHAT_ID_ENV = "TELEGRAM_CHAT_ID"

# Telegram API limits
_MAX_MESSAGE_LENGTH = 4096


def _escape_html(text: str) -> str:
    """Escape characters reserved in Telegram HTML mode."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def _confidence_label(score: float) -> str:
    """Convert a 0-1 confidence score to a human-readable label."""
    if score >= 0.80:
        return "High"
    if score >= 0.60:
        return "Medium"
    return "Low"


class TelegramNotifier(NotificationChannel):
    """
    Sends IndianSwing daily recommendations to a Telegram chat via the
    official Bot API.

    Configuration (environment variables):
        TELEGRAM_BOT_TOKEN  -- Telegram bot token from @BotFather
        TELEGRAM_CHAT_ID    -- numeric chat / channel ID

    If either variable is missing the notifier silently skips sending.
    All API failures are caught, logged, and do *not* propagate.
    """

    API_BASE = "https://api.telegram.org/bot{token}"
    SEND_MESSAGE_ENDPOINT = "/sendMessage"

    def __init__(self) -> None:
        self._token: str | None = os.environ.get(_BOT_TOKEN_ENV)
        self._chat_id: str | None = os.environ.get(_CHAT_ID_ENV)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def send_recommendations(self, recommendations: list[dict[str, Any]]) -> None:
        """Send recommendations to Telegram.  Never raises."""
        try:
            self._send(recommendations)
        except Exception as exc:  # noqa: BLE001  intentional broad catch
            logger.error(
                "telegram.send_failed — %s: %s",
                type(exc).__name__,
                str(exc),
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_configured(self) -> bool:
        if not self._token:
            logger.warning(
                "telegram.skip — %s not set in environment", _BOT_TOKEN_ENV
            )
            return False
        if not self._chat_id:
            logger.warning(
                "telegram.skip — %s not set in environment", _CHAT_ID_ENV
            )
            return False
        return True

    def _send(self, recommendations: list[dict[str, Any]]) -> None:
        if not self._is_configured():
            return

        message = self._build_message(recommendations)

        # Split if the message exceeds Telegram's 4096-char limit
        chunks = self._split_message(message)
        for chunk in chunks:
            self._post_message(chunk)

    def _build_message(self, recommendations: list[dict[str, Any]]) -> str:
        if not recommendations:
            return (
                "📈 <b>IndianSwing</b>\n\n"
                "No recommendations for today.\n\n"
                "Thank you.\n"
                "Have a great day! 😊"
            )

        divider = "━━━━━━━━━━━━━━━━━━━━"
        parts: list[str] = ["📈 <b>IndianSwing Daily Recommendations</b>\n"]

        for idx, rec in enumerate(recommendations, start=1):
            block = self._format_recommendation(idx, rec)
            parts.append(divider)
            parts.append(block)

        parts.append(divider)
        parts.append("\n<i>Generated by IndianSwing</i>")
        return "\n\n".join(parts)

    def _format_recommendation(self, rank: int, rec: dict[str, Any]) -> str:
        symbol = _escape_html(str(rec.get("symbol", "N/A")))
        name = _escape_html(str(rec.get("company_name", rec.get("name", symbol))))
        action = _escape_html(str(rec.get("action", "BUY")).upper())
        entry = rec.get("entry_price", 0.0)
        t1 = rec.get("target_1", 0.0)
        t2 = rec.get("target_2")
        sl = rec.get("stop_loss", 0.0)
        conf_score = float(rec.get("confidence_score", 0.0))
        confidence = _escape_html(_confidence_label(conf_score))

        lines: list[str] = [
            f"<b>Recommendation {rank}</b>",
            "",
            f"<b>Stock:</b> {name}",
            f"<b>Symbol:</b> {symbol}",
            f"<b>Action:</b> {action}",
            "",
            f"<b>Current Price:</b> \u20b9{entry:,.2f}",
            "",
            f"<b>Target 1:</b> \u20b9{t1:,.2f}",
        ]
        if t2 is not None:
            lines.append(f"<b>Target 2:</b> \u20b9{float(t2):,.2f}")

        lines += [
            "",
            f"<b>Stop Loss:</b> \u20b9{sl:,.2f}",
            "",
            f"<b>Confidence:</b> {confidence}",
        ]

        # Forensic analysis section — pulled from the explanation dict
        explanation: dict = rec.get("explanation", {}) or {}
        if explanation:
            lines.append("")
            lines.append("🔍 <b>Forensic Analysis</b>")
            lines.append("")

            section_map = {
                "trend_analysis": "Trend Analysis",
                "trend": "Trend Analysis",
                "volume_analysis": "Volume Analysis",
                "volume": "Volume Analysis",
                "momentum": "Momentum Indicators",
                "momentum_indicators": "Momentum Indicators",
                "breakout": "Breakout Confirmation",
                "breakout_confirmation": "Breakout Confirmation",
                "risk": "Risk Assessment",
                "risk_assessment": "Risk Assessment",
                "reason": "Reason for Recommendation",
                "reasons": "Reason for Recommendation",
                "summary": "Reason for Recommendation",
            }

            rendered_sections: set[str] = set()
            for key, label in section_map.items():
                if label in rendered_sections:
                    continue
                value = explanation.get(key)
                if value:
                    rendered_sections.add(label)
                    text = _escape_html(str(value))
                    lines.append(f"• <b>{label}:</b>")
                    lines.append(f"  {text}")

        return "\n".join(lines)

    def _split_message(self, message: str) -> list[str]:
        """Split a long message at newline boundaries, respecting the 4096-char limit."""
        if len(message) <= _MAX_MESSAGE_LENGTH:
            return [message]

        chunks: list[str] = []
        current = ""
        for line in message.splitlines(keepends=True):
            if len(current) + len(line) > _MAX_MESSAGE_LENGTH:
                if current:
                    chunks.append(current.rstrip("\n"))
                current = line
            else:
                current += line
        if current:
            chunks.append(current.rstrip("\n"))
        return chunks

    def _post_message(self, text: str) -> None:
        """POST a single message chunk to the Telegram Bot API."""
        url = (
            self.API_BASE.format(token=self._token)
            + self.SEND_MESSAGE_ENDPOINT
        )
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)

        if not response.is_success:
            logger.error(
                "telegram.api_error — HTTP %s: %s",
                response.status_code,
                response.text[:500],
            )
        else:
            logger.info("telegram.message_sent — chat_id=%s", self._chat_id)


# ---------------------------------------------------------------------------
# Module-level singleton — import and call directly
# ---------------------------------------------------------------------------

_notifier = TelegramNotifier()


def notify_recommendations(recommendations: list[dict[str, Any]]) -> None:
    """
    Top-level convenience function.

    Call this after the scan pipeline completes.  Pass a list of
    recommendation dicts (see TelegramNotifier.send_recommendations for
    the expected keys).  This function never raises.
    """
    _notifier.send_recommendations(recommendations)
