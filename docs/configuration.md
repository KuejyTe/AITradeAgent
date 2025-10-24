# 配置管理指南

本文档介绍如何在 AITradeAgent 中安全地管理系统配置、API 密钥以及策略参数。

## 1. 获取 OKX API 密钥

1. 登录 OKX 账户并进入 **API 管理** 页面。
2. 点击 **创建 API Key**，设置名称与权限。
   - 建议勾选 **阅读权限** 与 **交易权限**，不要授予提现权限。
   - 为 API Key 配置 IP 白名单以减少风险。
3. 记录系统生成的 **API Key**、**Secret Key** 和 **Passphrase**。
4. 将密钥填写到前端的 “API 配置” 页面或直接写入 `.env`/配置文件（建议优先使用前端界面，系统会自动加密并保存密钥）。

> **提示：** 可以通过执行 `python -c "from app.core.security import SecureStorage; print(SecureStorage.generate_key())"` 生成用于对 API 密钥加密的 `ENCRYPTION_KEY`，并写入 `.env`。

## 2. 配置项说明

### 2.1 环境变量（`.env` 系列文件）

- `PROJECT_NAME` / `APP_NAME`：应用展示名称。
- `ENVIRONMENT`：运行环境，可选值为 `development`、`staging`、`production`。
- `DEBUG`：是否启用调试模式。
- `DATABASE_URL`：数据库连接字符串，支持 PostgreSQL、SQLite 等。
- `REDIS_URL`：可选，Redis 服务地址。
- `SECRET_KEY`：JWT 加密密钥。
- `ENCRYPTION_KEY`：使用 `SecureStorage` 生成，用于加密 API 密钥。
- `LOG_FILE`、`CONFIG_AUDIT_LOG`：日志与审计文件路径。
- `DEFAULT_TRADE_AMOUNT`、`MAX_POSITION_SIZE`、`RISK_PERCENTAGE`、`SLIPPAGE_TOLERANCE`：交易相关默认参数。
- `CONFIG_STORAGE_DIR`、`CONFIG_BACKUP_DIR`、`STRATEGY_CONFIG_DIR`、`API_KEYS_STORE`：配置文件存储位置。

为便于多环境部署，项目提供了下列模板：

- `.env.example`：完整示例。
- `.env.development`：开发环境覆盖项。
- `.env.staging`：预发布环境覆盖项。
- `.env.production`：生产环境覆盖项。

### 2.2 系统配置（前端设置页面）

通过 **设置 → 系统配置** 可以修改以下信息：

- 默认交易金额
- 最大持仓限制
- 风险百分比
- 滑点容忍度
- 通知偏好（邮件、Telegram、微信）

系统会自动校验配置的合法性并写入 `configs/system/system_config.json`，同时触发审计日志与配置备份。

### 2.3 策略配置

策略配置保存在 `configs/strategies/*.json`。示例：

```json
{
  "strategy_type": "sma_crossover",
  "version": "1.0",
  "parameters": {
    "fast_period": 10,
    "slow_period": 30,
    "instrument_id": "BTC-USDT",
    "timeframe": "1H"
  },
  "risk_management": {
    "max_position_size": 1.0,
    "stop_loss_pct": 0.05,
    "take_profit_pct": 0.10,
    "max_daily_loss": 0.10
  },
  "execution": {
    "order_type": "limit",
    "slippage_tolerance": 0.001
  }
}
```

可通过前端的 JSON 编辑器或直接编辑文件的方式进行修改。系统在保存前会校验策略配置的结构与关键字段。

## 3. 安全最佳实践

- **启用密钥加密**：务必设置 `ENCRYPTION_KEY`，系统会使用 Fernet 算法加密 API 密钥后存储。
- **最小权限原则**：API Key 仅赋予必要的交易与查询权限，并配置 IP 白名单。
- **不在代码库保存明文密钥**：将 `.env` 文件加入 `.gitignore`，通过 CI/CD 或秘密管理服务在部署时注入。
- **定期轮换密钥**：计划性地更新 API 密钥，并在前端重新保存。
- **审计日志**：所有配置变更、备份与还原操作都会写入 `logs/config_audit.log`，建议定期查看。
- **备份策略**：系统每次更新配置后自动在 `configs/backups` 目录生成备份，可通过 API 触发备份与还原。

## 4. 常见问题

### 4.1 保存 API 密钥时报错 “Encryption key is not configured”

未在环境变量中设置 `ENCRYPTION_KEY`。使用上述命令生成后写入 `.env` 并重启服务。

### 4.2 如何热更新配置？

调用 `/api/config/reload` 接口或在前端触发后端热加载，系统会重新读取 `.env` 和 `system_config.json` 并应用。

### 4.3 如何恢复历史配置？

访问 `/api/config/backups` 获取备份列表，并在前端或通过管理脚本调用还原接口（后续版本将开放 API）。

### 4.4 风险百分比应如何填写？

风险百分比为小数，例如 2% 应填写 `0.02`。前端表单会自动转换与校验。

---

如需更多帮助，请查看仓库中的其他文档或联系运维团队。
