"""Alerting utilities for proactive monitoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.core.logging import app_logger


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


ConditionFunc = Callable[[Optional[Dict[str, Any]]], bool]
AlertChannel = Callable[["Alert"], None]


@dataclass
class Alert:
    name: str
    message: str
    severity: AlertSeverity
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AlertRule:
    name: str
    condition: ConditionFunc
    severity: AlertSeverity
    description: str = ""


class AlertManager:
    """Manage alert rules and dispatch notifications when triggered."""

    def __init__(self) -> None:
        self.alert_rules: List[AlertRule] = []
        self.alert_channels: List[AlertChannel] = []
        self.alert_history: List[Alert] = []

    def add_rule(self, rule: AlertRule) -> None:
        if rule not in self.alert_rules:
            self.alert_rules.append(rule)

    def add_channel(self, channel: AlertChannel) -> None:
        if channel not in self.alert_channels:
            self.alert_channels.append(channel)

    def check_alerts(self, data: Optional[Dict[str, Any]] = None) -> List[Alert]:
        triggered: List[Alert] = []
        for rule in self.alert_rules:
            try:
                if rule.condition(data):
                    alert = Alert(
                        name=rule.name,
                        message=rule.description or rule.name,
                        severity=rule.severity,
                        metadata=data or {},
                    )
                    triggered.append(alert)
            except Exception as exc:  # pragma: no cover - defensive logging
                app_logger.warning(
                    "Failed to evaluate alert rule",
                    rule=rule.name,
                    error=str(exc),
                )

        for alert in triggered:
            self.send_alert(alert)

        return triggered

    def send_alert(self, alert: Alert) -> None:
        self.alert_history.append(alert)
        for channel in self.alert_channels or (email_alert_channel, telegram_alert_channel):
            try:
                channel(alert)
            except Exception as exc:  # pragma: no cover - defensive logging
                app_logger.error(
                    "Alert channel delivery failed",
                    channel=getattr(channel, "__name__", str(channel)),
                    error=str(exc),
                )

    def get_history(self, limit: int = 100) -> List[Alert]:
        return self.alert_history[-limit:]


# ---------------------------------------------------------------------------
# Default alert condition helpers
# ---------------------------------------------------------------------------

def _high_error_rate(data: Optional[Dict[str, Any]]) -> bool:
    return float((data or {}).get("error_rate", 0.0)) > 0.05


def _low_balance(data: Optional[Dict[str, Any]]) -> bool:
    return float((data or {}).get("balance", 0.0)) < 100


def _large_loss(data: Optional[Dict[str, Any]]) -> bool:
    return abs(float((data or {}).get("pnl", 0.0))) > 1000


class AlertRules:
    HIGH_ERROR_RATE = AlertRule(
        name="高错误率",
        condition=_high_error_rate,
        severity=AlertSeverity.HIGH,
        description="API 错误率超过 5%",
    )

    LOW_BALANCE = AlertRule(
        name="余额不足",
        condition=_low_balance,
        severity=AlertSeverity.MEDIUM,
        description="账户余额低于 100",
    )

    LARGE_LOSS = AlertRule(
        name="单笔大额亏损",
        condition=_large_loss,
        severity=AlertSeverity.CRITICAL,
        description="单笔交易损失超过 1000",
    )


def email_alert_channel(alert: Alert) -> None:
    app_logger.warning(
        "Email alert dispatched",
        name=alert.name,
        severity=alert.severity.value,
        message=alert.message,
    )


def telegram_alert_channel(alert: Alert) -> None:
    app_logger.warning(
        "Telegram alert dispatched",
        name=alert.name,
        severity=alert.severity.value,
        message=alert.message,
    )


__all__ = [
    "AlertSeverity",
    "Alert",
    "AlertRule",
    "AlertManager",
    "AlertRules",
    "email_alert_channel",
    "telegram_alert_channel",
]
