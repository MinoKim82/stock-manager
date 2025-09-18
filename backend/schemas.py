from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from models import AccountType, TransactionType, StockTransactionType, Currency, MarketType

# Common Config for JSON encoding
class BaseConfig(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: float
        }

# Account Schemas
class AccountBase(BaseModel):
    owner_name: str = Field(..., max_length=100)
    broker: str = Field(..., max_length=100)
    account_number: str = Field(..., max_length=50)
    account_type: AccountType
    initial_balance: Decimal = Field(default=Decimal('0.00'))
    current_balance: Decimal = Field(default=Decimal('0.00'))
    currency: Currency

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    owner_name: Optional[str] = Field(None, max_length=100)
    broker: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    account_type: Optional[AccountType] = None
    initial_balance: Optional[Decimal] = None
    current_balance: Optional[Decimal] = None
    currency: Optional[Currency] = None

class Account(AccountBase, BaseConfig):
    id: int
    created_at: datetime
    updated_at: datetime

# Stock Schemas
class StockBase(BaseModel):
    symbol: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    market: MarketType

class StockCreate(StockBase):
    pass

class StockUpdate(BaseModel):
    symbol: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=200)
    market: Optional[MarketType] = None

class Stock(StockBase, BaseConfig):
    id: int
    created_at: datetime
    updated_at: datetime

# Transaction Schemas (현금 거래만)
class TransactionBase(BaseModel):
    transaction_type: TransactionType
    date: datetime
    amount: Decimal
    transaction_currency: Currency
    exchange_rate: Optional[Decimal] = None
    exchange_fee: Decimal = Field(default=Decimal('0.00'))  # 환전 수수료
    description: Optional[str] = Field(None, max_length=500)

class TransactionCreate(TransactionBase):
    account_id: int

class TransactionUpdate(BaseModel):
    transaction_type: Optional[TransactionType] = None
    date: Optional[datetime] = None
    amount: Optional[Decimal] = None
    transaction_currency: Optional[Currency] = None
    exchange_rate: Optional[Decimal] = None
    exchange_fee: Optional[Decimal] = None
    description: Optional[str] = Field(None, max_length=500)

class Transaction(TransactionBase, BaseConfig):
    id: int
    account_id: int
    created_at: datetime
    updated_at: datetime

# Stock Transaction Schemas
class StockTransactionBase(BaseModel):
    transaction_type: StockTransactionType
    date: datetime
    stock_id: int  # 주식 정보 참조
    quantity: Decimal
    price_per_share: Decimal
    fee: Decimal = Field(default=Decimal('0.00'))
    transaction_currency: Currency
    exchange_rate: Optional[Decimal] = None

class StockTransactionCreate(StockTransactionBase):
    account_id: int

class StockTransactionUpdate(BaseModel):
    transaction_type: Optional[StockTransactionType] = None
    date: Optional[datetime] = None
    stock_id: Optional[int] = None
    quantity: Optional[Decimal] = None
    price_per_share: Optional[Decimal] = None
    fee: Optional[Decimal] = None
    transaction_currency: Optional[Currency] = None
    exchange_rate: Optional[Decimal] = None

class StockTransaction(StockTransactionBase, BaseConfig):
    id: int
    account_id: int
    created_at: datetime
    updated_at: datetime
    total_amount: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    # 관계 필드
    stock: Optional[Stock] = None

# Stock Holding Schemas
class StockHoldingBase(BaseModel):
    stock_id: int  # 주식 정보 참조
    quantity: Decimal = Field(default=Decimal('0'))
    average_cost: Decimal = Field(default=Decimal('0'))
    total_cost: Decimal = Field(default=Decimal('0'))

class StockHoldingCreate(StockHoldingBase):
    account_id: int

class StockHoldingUpdate(BaseModel):
    stock_id: Optional[int] = None
    quantity: Optional[Decimal] = None
    average_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None

class StockHolding(StockHoldingBase, BaseConfig):
    id: int
    account_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # 관계 필드
    stock: Optional[Stock] = None

# Stock Search Schema
class StockSearchResult(BaseModel):
    symbol: str
    name: str
    market: str

# Portfolio Summary Schema
class StockHoldingSummary(BaseConfig):
    symbol: str
    name: str
    quantity: Decimal
    average_cost: Decimal
    current_price: Decimal
    current_value: Decimal
    profit_loss: Decimal
    profit_loss_rate: Decimal

class PortfolioSummary(BaseConfig):
    total_cash: Decimal
    total_stock_value: Decimal
    total_portfolio_value: Decimal
    holdings: List[StockHoldingSummary]

# Transaction Filter Schema
class TransactionFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    transaction_type: Optional[TransactionType] = None

# Stock Transaction Filter Schema
class StockTransactionFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    stock_symbol: Optional[str] = None
    transaction_type: Optional[StockTransactionType] = None
    market: Optional[str] = None