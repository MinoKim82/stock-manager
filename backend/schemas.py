from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from models import AccountType, TransactionType, Currency

# Account Schemas
class AccountBase(BaseModel):
    owner_name: str = Field(..., max_length=100)
    broker: str = Field(..., max_length=100)
    account_number: str = Field(..., max_length=50)
    account_type: AccountType
    balance: Decimal = Field(default=Decimal('0.00'))
    currency: Currency

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    owner_name: Optional[str] = Field(None, max_length=100)
    broker: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    account_type: Optional[AccountType] = None
    balance: Optional[Decimal] = None
    currency: Optional[Currency] = None

class Account(AccountBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionBase(BaseModel):
    transaction_type: TransactionType
    date: datetime
    amount: Optional[Decimal] = None
    stock_name: Optional[str] = Field(None, max_length=200)
    stock_symbol: Optional[str] = Field(None, max_length=20)
    quantity: Optional[Decimal] = None
    price_per_share: Optional[Decimal] = None
    fee: Decimal = Field(default=Decimal('0.00'))
    transaction_currency: Currency
    exchange_rate: Optional[Decimal] = None

class TransactionCreate(TransactionBase):
    account_id: int

class TransactionUpdate(BaseModel):
    transaction_type: Optional[TransactionType] = None
    date: Optional[datetime] = None
    amount: Optional[Decimal] = None
    stock_name: Optional[str] = Field(None, max_length=200)
    stock_symbol: Optional[str] = Field(None, max_length=20)
    quantity: Optional[Decimal] = None
    price_per_share: Optional[Decimal] = None
    fee: Optional[Decimal] = None
    transaction_currency: Optional[Currency] = None
    exchange_rate: Optional[Decimal] = None

class Transaction(TransactionBase):
    id: int
    account_id: int
    created_at: datetime
    updated_at: datetime
    total_amount: Optional[Decimal] = None
    
    class Config:
        from_attributes = True

# Stock Search Schema
class StockSearchResult(BaseModel):
    symbol: str
    name: str
    market: str

# Portfolio Summary Schema
class StockHolding(BaseModel):
    symbol: str
    name: str
    quantity: Decimal
    average_cost: Decimal
    current_price: Decimal
    current_value: Decimal
    profit_loss: Decimal
    profit_loss_rate: Decimal

class PortfolioSummary(BaseModel):
    total_cash: Decimal
    total_stock_value: Decimal
    total_portfolio_value: Decimal
    holdings: List[StockHolding]

# Transaction Filter Schema
class TransactionFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    stock_symbol: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
