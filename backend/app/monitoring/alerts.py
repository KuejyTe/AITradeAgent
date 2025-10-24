"""
告警系统
"""
from typing import Callable, List, Dict
from datetime import datetime
from enum import Enum

class AlertSeverity(str, Enum):
"""告警严重程度"""
LOW = "low"
MEDIUM = "medium"
HIGH = "high"
CRITICAL = "critical"

class Alert:
"""告警对象"""

def __init__(
    self,
    name: str,
    message: str,
    severity: AlertSeverity,
    metadata: Dict = None
):
    self.name = name
    self.message = message
    self.severity = severity
    self.metadata = metadata or {}
    self.timestamp = datetime.utcnow()
class AlertRule:
"""告警规则"""

def __init__(
    self,
    name: str,
    condition: Callable,
    severity: AlertSeverity,
    description: str = ""
):
    self.name = name
    self.condition = condition
    self.severity = severity
    self.description = description
class AlertManager:
"""告警管理器"""

def __init__(self):
    self.rules: List[AlertRule] = []
    self.alert_channels: List[Callable] = []
    self.alert_history: List[Alert] = []

def add_rule(self, rule: AlertRule):
    """添加告警规则"""
    self.rules.append(rule)

def add_channel(self, channel: Callable):
    """添加告警通道"""
    self.alert_channels.append(channel)

def check_rules(self, data: Dict = None):
    """检查所有告警规则"""
    alerts = []
    
    for rule in self.rules:
        try:
            if rule.condition(data):
                alert = Alert(
                    name=rule.name,
                    message=rule.description,
                    severity=rule.severity,
                    metadata=data
                )
                alerts.append(alert)
        except Exception as e:
            print(f"Error checking rule {rule.name}: {e}")
    
    # 发送告警
    for alert in alerts:
        self.send_alert(alert)
    
    return alerts

def send_alert(self, alert: Alert):
    """发送告警到所有通道"""
    self.alert_history.append(alert)
    
    for channel in self.alert_channels:
        try:
            channel(alert)
        except Exception as e:
            print(f"Error sending alert to channel: {e}")

def get_history(self, limit: int = 100) -> List[Alert]:
    """获取告警历史"""
    return self.alert_history[-limit:]
告警通道示例
def email_alert_channel(alert: Alert):
"""邮件告警通道"""
print(f"[EMAIL] {alert.severity}: {alert.name} - {alert.message}")

def telegram_alert_channel(alert: Alert):
"""Telegram告警通道"""
print(f"[TELEGRAM] {alert.severity}: {alert.name} - {alert.message}")

预定义告警规则
def high_error_rate_condition(data: Dict) -> bool:
"""高错误率条件"""
error_rate = data.get("error_rate", 0)
return error_rate > 0.05

def low_balance_condition(data: Dict) -> bool:
"""余额不足条件"""
balance = data.get("balance", 0)
return balance < 100

def large_loss_condition(data: Dict) -> bool:
"""大额亏损条件"""
pnl = data.get("pnl", 0)
return pnl < -1000

创建默认告警规则
HIGH_ERROR_RATE = AlertRule(
name="high_error_rate",
condition=high_error_rate_condition,
severity=AlertSeverity.HIGH,
description="API错误率超过5%"
)

LOW_BALANCE = AlertRule(
name="low_balance",
condition=low_balance_condition,
severity=AlertSeverity.MEDIUM,
description="账户余额低于100 USDT"
)

LARGE_LOSS = AlertRule(
name="large_loss",
condition=large_loss_condition,
severity=AlertSeverity.CRITICAL,
description="单笔交易亏损超过1000 USDT"
)
