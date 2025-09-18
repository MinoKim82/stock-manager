from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Enum as SQLEnum, Index
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
    OVERSEAS_STOCK = "해외주식계좌"

class TransactionType(str, enum.Enum):
    DEPOSIT = "입금"
    WITHDRAWAL = "출금"
    DIVIDEND = "배당금"
    INTEREST = "이자"

class StockTransactionType(str, enum.Enum):
    BUY = "매수"
    SELL = "매도"

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

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)  # 주식 심볼 (고유)
    name = Column(String(200), nullable=False)  # 주식명
    market = Column(SQLEnum(MarketType), nullable=False)  # 거래소
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    stock_transactions = relationship("StockTransaction", back_populates="stock")
    stock_holdings = relationship("StockHolding", back_populates="stock")
    
    # 인덱스 추가
    __table_args__ = (
        Index('idx_stock_symbol', 'symbol'),
        Index('idx_stock_market', 'market'),
    )
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
    stock_transactions = relationship("StockTransaction", back_populates="account")
    stock_holdings = relationship("StockHolding", back_populates="account")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)  # 입금, 출금, 배당금, 이자 금액
    transaction_currency = Column(SQLEnum(Currency), nullable=False)
    exchange_rate = Column(Numeric(15, 4), nullable=True)  # 환율
    exchange_fee = Column(Numeric(15, 2), default=0)  # 환전 수수료
    description = Column(String(500), nullable=True)  # 거래 설명
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    account = relationship("Account", back_populates="transactions")

class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)  # 주식 정보 참조
    transaction_type = Column(SQLEnum(StockTransactionType), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)  # 수량
    price_per_share = Column(Numeric(15, 4), nullable=False)  # 주당 가격
    fee = Column(Numeric(15, 2), default=0)  # 수수료
    transaction_currency = Column(SQLEnum(Currency), nullable=False)
    exchange_rate = Column(Numeric(15, 4), nullable=True)  # 환율
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    account = relationship("Account", back_populates="stock_transactions")
    stock = relationship("Stock", back_populates="stock_transactions")
    
    # 인덱스 추가
    __table_args__ = (
        Index('idx_stock_transaction_account_date', 'account_id', 'date'),
        Index('idx_stock_transaction_stock', 'stock_id'),
    )
    
    @property
    def total_amount(self):
        """총 거래 금액 계산 (수량 × 주당가격)"""
        return self.quantity * self.price_per_share
    
    @property
    def net_amount(self):
        """수수료를 제외한 순 거래 금액"""
        if self.transaction_type == StockTransactionType.BUY:
            return self.total_amount + self.fee  # 매수시 수수료 추가
        else:  # SELL
            return self.total_amount - self.fee  # 매도시 수수료 차감

class StockHolding(Base):
    __tablename__ = "stock_holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)  # 주식 정보 참조
    quantity = Column(Numeric(15, 4), nullable=False, default=0)  # 보유 수량
    average_cost = Column(Numeric(15, 4), nullable=False, default=0)  # 평균 단가
    total_cost = Column(Numeric(15, 2), nullable=False, default=0)  # 총 매입가
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    account = relationship("Account", back_populates="stock_holdings")
    stock = relationship("Stock", back_populates="stock_holdings")
    
    # 유니크 제약조건: 계좌별 주식은 하나의 레코드만 존재
    __table_args__ = (
        Index('idx_stock_holding_account_stock', 'account_id', 'stock_id', unique=True),
    )