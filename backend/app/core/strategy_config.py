from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.validators import ConfigValidator


class StrategyConfigManager:
    """Manage trading strategy configuration files."""

    DEFAULT_CONFIGS: Dict[str, Dict[str, Any]] = {
        "sma_crossover": {
            "strategy_type": "sma_crossover",
            "version": "1.0",
            "parameters": {
                "fast_period": 10,
                "slow_period": 30,
                "instrument_id": "BTC-USDT",
                "timeframe": "1H",
            },
            "risk_management": {
                "max_position_size": 1.0,
                "stop_loss_pct": 0.05,
                "take_profit_pct": 0.10,
                "max_daily_loss": 0.10,
            },
            "execution": {
                "order_type": "limit",
                "slippage_tolerance": 0.001,
            },
        }
    }

    def __init__(self, config_dir: Optional[Path | str] = None) -> None:
        self.config_dir = Path(config_dir or settings.strategy_config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.validator = ConfigValidator()

    def _strategy_path(self, strategy_id: str) -> Path:
        return self.config_dir / f"{strategy_id}.json"

    def load_strategy_config(self, strategy_id: str) -> Dict[str, Any]:
        path = self._strategy_path(strategy_id)
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)

        default = self.get_default_config(strategy_id)
        if default:
            return default
        raise FileNotFoundError(f"Strategy configuration '{strategy_id}' not found")

    def save_strategy_config(self, strategy_id: str, config: Dict[str, Any]) -> None:
        strategy_type = config.get("strategy_type", strategy_id)
        if not self.validator.validate_strategy_config(config, strategy_type):
            raise ValueError("Strategy configuration is invalid")

        path = self._strategy_path(strategy_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2, ensure_ascii=False)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        strategy_type = config.get("strategy_type")
        if not strategy_type:
            return False
        return self.validator.validate_strategy_config(config, strategy_type)

    def get_default_config(self, strategy_type: str) -> Dict[str, Any]:
        config = self.DEFAULT_CONFIGS.get(strategy_type)
        return deepcopy(config) if config else {}
