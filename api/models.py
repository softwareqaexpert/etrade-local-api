"""Pydantic models for API responses and data validation."""

from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class Account(BaseModel):
    """Account information model."""

    account_id: str
    account_id_key: str
    account_mode: str
    account_desc: str
    account_type: str
    account_nickname: Optional[str] = None


class Balance(BaseModel):
    """Account balance information."""

    account_id: str
    cash_balance: Decimal
    buying_power: Decimal
    margin_balance: Decimal
    equity_value: Decimal


class Position(BaseModel):
    """Stock position model."""

    symbol: str
    quantity: int
    price: Decimal
    value: Decimal
    gain_loss: Decimal
    gain_loss_pct: Decimal


class Portfolio(BaseModel):
    """Portfolio summary model."""

    account_id: str
    total_positions: int
    total_value: Decimal
    cash: Decimal
    total_gain_loss: Decimal
    positions: list[Position]


class Quote(BaseModel):
    """Stock quote model."""

    symbol: str
    last_price: Decimal
    bid: Decimal
    ask: Decimal
    volume: int
    timestamp: datetime


class OrderPreview(BaseModel):
    """Order preview response."""

    order_id: str
    order_type: str
    symbol: str
    quantity: int
    price: Decimal
    estimated_total: Decimal
    estimated_commission: Decimal


class Order(BaseModel):
    """Order model."""

    order_id: str
    symbol: str
    quantity: int
    price: Optional[Decimal]
    order_type: str
    status: str
    created_at: datetime


class Alert(BaseModel):
    """Alert model."""

    alert_id: str
    subject: str
    message: str
    alert_type: str
    create_time: datetime
