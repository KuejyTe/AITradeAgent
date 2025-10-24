"""Create initial trading schema"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID


revision = "7a2b7ef4c9bf"
down_revision = None
branch_labels = None
depends_on = None


class GUID(sa.types.TypeDecorator):
    impl = sa.types.CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        return dialect.type_descriptor(sa.types.CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None or isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


def upgrade() -> None:
    op.create_table(
        "strategies",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "status",
            sa.Enum("active", "inactive", name="strategy_status", native_enum=False),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_strategies"),
    )
    op.create_index("ix_strategies_name", "strategies", ["name"], unique=False)

    op.create_table(
        "strategy_signals",
        sa.Column("id", GUID(), nullable=False),
        sa.Column(
            "strategy_id",
            GUID(),
            sa.ForeignKey("strategies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("instrument_id", sa.String(length=100), nullable=False),
        sa.Column(
            "signal_type",
            sa.Enum("buy", "sell", "hold", name="strategy_signal_type", native_enum=False),
            nullable=False,
        ),
        sa.Column("strength", sa.Numeric(5, 4), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_strategy_signals"),
    )
    op.create_index(
        "ix_strategy_signals_strategy_timestamp",
        "strategy_signals",
        ["strategy_id", "timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_strategy_signals_instrument_id",
        "strategy_signals",
        ["instrument_id"],
        unique=False,
    )

    op.create_table(
        "candles",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("instrument_id", sa.String(length=100), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(24, 12), nullable=False),
        sa.Column("high", sa.Numeric(24, 12), nullable=False),
        sa.Column("low", sa.Numeric(24, 12), nullable=False),
        sa.Column("close", sa.Numeric(24, 12), nullable=False),
        sa.Column("volume", sa.Numeric(28, 12), nullable=False),
        sa.Column("bar", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_candles"),
        sa.UniqueConstraint(
            "instrument_id",
            "timestamp",
            "bar",
            name="uq_candles_instrument_timestamp_bar",
        ),
    )
    op.create_index(
        "ix_candles_instrument_bar_timestamp",
        "candles",
        ["instrument_id", "bar", "timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_candles_instrument_id",
        "candles",
        ["instrument_id"],
        unique=False,
    )

    op.create_table(
        "tickers",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("instrument_id", sa.String(length=100), nullable=False),
        sa.Column("last_price", sa.Numeric(24, 12), nullable=False),
        sa.Column("bid_price", sa.Numeric(24, 12), nullable=False),
        sa.Column("ask_price", sa.Numeric(24, 12), nullable=False),
        sa.Column("volume_24h", sa.Numeric(28, 12), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tickers"),
    )
    op.create_index(
        "ix_tickers_instrument_timestamp",
        "tickers",
        ["instrument_id", "timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_tickers_instrument_id",
        "tickers",
        ["instrument_id"],
        unique=False,
    )

    op.create_table(
        "orders",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("order_id", sa.String(length=128), nullable=False),
        sa.Column("instrument_id", sa.String(length=100), nullable=False),
        sa.Column(
            "side",
            sa.Enum("buy", "sell", name="order_side", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "order_type",
            sa.Enum("market", "limit", name="order_type", native_enum=False),
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(24, 12), nullable=False),
        sa.Column("size", sa.Numeric(24, 12), nullable=False),
        sa.Column(
            "filled_size",
            sa.Numeric(24, 12),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "filled",
                "cancelled",
                name="order_status",
                native_enum=False,
            ),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "strategy_id",
            GUID(),
            sa.ForeignKey("strategies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_orders"),
        sa.UniqueConstraint("order_id", name="uq_orders_order_id"),
    )
    op.create_index(
        "ix_orders_instrument_created_at",
        "orders",
        ["instrument_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_orders_instrument_id",
        "orders",
        ["instrument_id"],
        unique=False,
    )

    op.create_table(
        "trades",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("trade_id", sa.String(length=128), nullable=False),
        sa.Column(
            "order_id",
            GUID(),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("instrument_id", sa.String(length=100), nullable=False),
        sa.Column(
            "side",
            sa.Enum("buy", "sell", name="trade_side", native_enum=False),
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(24, 12), nullable=False),
        sa.Column("size", sa.Numeric(24, 12), nullable=False),
        sa.Column(
            "fee",
            sa.Numeric(24, 12),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_trades"),
        sa.UniqueConstraint("trade_id", name="uq_trades_trade_id"),
    )
    op.create_index(
        "ix_trades_order_timestamp",
        "trades",
        ["order_id", "timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_trades_order_id",
        "trades",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_trades_instrument_id",
        "trades",
        ["instrument_id"],
        unique=False,
    )

    op.create_table(
        "account_balances",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("currency", sa.String(length=20), nullable=False),
        sa.Column("balance", sa.Numeric(24, 12), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "available",
            sa.Numeric(24, 12),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("frozen", sa.Numeric(24, 12), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_account_balances"),
    )
    op.create_index(
        "ix_account_balances_currency_timestamp",
        "account_balances",
        ["currency", "timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_account_balances_currency",
        "account_balances",
        ["currency"],
        unique=False,
    )

    op.create_table(
        "positions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("instrument_id", sa.String(length=100), nullable=False),
        sa.Column(
            "side",
            sa.Enum("long", "short", name="position_side", native_enum=False),
            nullable=False,
        ),
        sa.Column("size", sa.Numeric(24, 12), nullable=False, server_default=sa.text("0")),
        sa.Column("avg_price", sa.Numeric(24, 12), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "current_price",
            sa.Numeric(24, 12),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "unrealized_pnl",
            sa.Numeric(24, 12),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("margin", sa.Numeric(24, 12), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_positions"),
    )
    op.create_index(
        "ix_positions_instrument_side_timestamp",
        "positions",
        ["instrument_id", "side", "timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_positions_instrument_id",
        "positions",
        ["instrument_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_positions_instrument_id", table_name="positions")
    op.drop_index("ix_positions_instrument_side_timestamp", table_name="positions")
    op.drop_table("positions")

    op.drop_index(
        "ix_account_balances_currency_timestamp", table_name="account_balances"
    )
    op.drop_index("ix_account_balances_currency", table_name="account_balances")
    op.drop_table("account_balances")

    op.drop_index("ix_trades_instrument_id", table_name="trades")
    op.drop_index("ix_trades_order_id", table_name="trades")
    op.drop_index("ix_trades_order_timestamp", table_name="trades")
    op.drop_table("trades")

    op.drop_index("ix_orders_instrument_id", table_name="orders")
    op.drop_index("ix_orders_instrument_created_at", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_tickers_instrument_id", table_name="tickers")
    op.drop_index("ix_tickers_instrument_timestamp", table_name="tickers")
    op.drop_table("tickers")

    op.drop_index("ix_candles_instrument_id", table_name="candles")
    op.drop_index("ix_candles_instrument_bar_timestamp", table_name="candles")
    op.drop_table("candles")

    op.drop_index("ix_strategy_signals_instrument_id", table_name="strategy_signals")
    op.drop_index(
        "ix_strategy_signals_strategy_timestamp", table_name="strategy_signals"
    )
    op.drop_table("strategy_signals")

    op.drop_index("ix_strategies_name", table_name="strategies")
    op.drop_table("strategies")
