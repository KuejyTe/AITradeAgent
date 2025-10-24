from __future__ import annotations

from typing import Any, Dict


class ConfigValidator:
    """Reusable validation helpers for configuration payloads."""

    MIN_KEY_LENGTH = 20

    @staticmethod
    def validate_api_keys(api_key: str, secret: str, passphrase: str) -> bool:
        if not all(isinstance(item, str) and item.strip() for item in (api_key, secret, passphrase)):
            return False
        if len(api_key.strip()) < ConfigValidator.MIN_KEY_LENGTH:
            return False
        if len(secret.strip()) < ConfigValidator.MIN_KEY_LENGTH:
            return False
        return True

    @staticmethod
    def validate_trading_params(params: Dict[str, Any]) -> bool:
        try:
            default_trade_amount = float(params.get("default_trade_amount"))
            max_position_size = float(params.get("max_position_size"))
            risk_percentage = float(params.get("risk_percentage"))
            slippage_tolerance = float(params.get("slippage_tolerance", 0))
        except (TypeError, ValueError):
            return False

        if default_trade_amount <= 0:
            return False
        if max_position_size <= 0 or max_position_size < default_trade_amount:
            return False
        if not 0 < risk_percentage <= 1:
            return False
        if slippage_tolerance < 0:
            return False
        return True

    @staticmethod
    def validate_strategy_config(config: Dict[str, Any], strategy_type: str) -> bool:
        if not isinstance(config, dict):
            return False
        if config.get("strategy_type") != strategy_type:
            return False
        parameters = config.get("parameters")
        if not isinstance(parameters, dict):
            return False
        required_parameters = {"instrument_id", "timeframe"}
        if not required_parameters.issubset(parameters.keys()):
            return False
        risk = config.get("risk_management", {})
        if risk:
            if not isinstance(risk, dict):
                return False
            for key in ("max_position_size", "stop_loss_pct", "take_profit_pct"):
                value = risk.get(key)
                if value is not None and (not isinstance(value, (int, float)) or value < 0):
                    return False
        return True
