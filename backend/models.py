from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

class AccountType(str, enum.Enum):
    PENSION = "연금계좌"
    IRP = "IRP계좌"
    ISA = "ISA계좌"
    CMA = "CMA계좌"
    COMPREHENSIVE = "종합매매계좌"
    US_STOCK = "미국주식계좌"

class TransactionType(str, enum.Enum):
    DEPOSIT = "입금"
    WITHDRAWAL = "출금"
    BUY = "매수"
    SELL = "매도"
    DIVIDEND = "배당금"
    INTEREST = "이자"

class Currency(str, enum.Enum):
    KRW = "KRW"
    USD = "USD"

class MarketType(str, enum.Enum):
    KRX = "한국"
    HKS = "홍콩"
    NYS = "뉴욕"
    NAS = "나스닥"
    AMS = "아멕스"
    TSE = "도쿄"
    SHS = "상해"
    SZS = "심천"
    SHI = "상해지수"
    SZI = "심천지수"
    HSX = "호치민"
    HNX = "하노이"
    BAY = "뉴욕(주간)"
    BAQ = "나스닥(주간)"
    BAA = "아멕스(주간)"

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String(100), nullable=False)
    broker = Column(String(100), nullable=False)
    account_number = Column(String(50), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    initial_balance = Column(Numeric(15, 2), default=0)
    current_balance = Column(Numeric(15, 2), default=0)
    currency = Column(SQLEnum(Currency), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transactions = relationship("Transaction", back_populates="account")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(15, 2), nullable=True)  # 입금, 출금, 배당금, 이자용
    stock_name = Column(String(200), nullable=True)  # 주식명
    stock_symbol = Column(String(20), nullable=True)  # 주식 심볼
    market = Column(SQLEnum(MarketType), nullable=True) # 거래소
    quantity = Column(Numeric(15, 4), nullable=True)  # 수량
    price_per_share = Column(Numeric(15, 4), nullable=True)  # 주당 가격
    fee = Column(Numeric(15, 2), default=0)  # 수수료
    transaction_currency = Column(SQLEnum(Currency), nullable=False)
    exchange_rate = Column(Numeric(15, 4), nullable=True)  # 환율
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    account = relationship("Account", back_populates="transactions")
    
    @property
    def total_amount(self):
        """매수/매도 거래의 총 거래 금액 계산"""
        if self.quantity and self.price_per_share:
            return self.quantity * self.price_per_share
        return self.amount