#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트
기존 Transaction 테이블에서 주식 관련 데이터를 분리하여 새로운 테이블로 이동
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal
import logging
from config import DATABASE_URL

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """데이터베이스 마이그레이션 실행"""
    
    # PostgreSQL 연결
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with engine.connect() as conn:
        try:
            logger.info("데이터베이스 마이그레이션 시작...")
            
            # 1. 기존 Transaction 테이블에서 주식 거래 데이터 조회
            logger.info("1. 기존 주식 거래 데이터 조회 중...")
            result = conn.execute(text("""
                SELECT id, account_id, transaction_type, date, amount, 
                       stock_name, stock_symbol, market, quantity, price_per_share, 
                       fee, transaction_currency, exchange_rate, created_at, updated_at
                FROM transactions 
                WHERE transaction_type IN ('BUY', 'SELL')
            """))
            
            stock_transactions = result.fetchall()
            logger.info(f"발견된 주식 거래: {len(stock_transactions)}건")
            
            # 2. 새로운 테이블 생성
            logger.info("2. 새로운 테이블 생성 중...")
            
            # StockTransaction 테이블 생성
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS stock_transactions (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER NOT NULL,
                    transaction_type VARCHAR(10) NOT NULL,
                    date TIMESTAMP WITH TIME ZONE NOT NULL,
                    stock_symbol VARCHAR(20) NOT NULL,
                    stock_name VARCHAR(200) NOT NULL,
                    market VARCHAR(10) NOT NULL,
                    quantity DECIMAL(15,4) NOT NULL,
                    price_per_share DECIMAL(15,4) NOT NULL,
                    fee DECIMAL(15,2) DEFAULT 0,
                    transaction_currency VARCHAR(3) NOT NULL,
                    exchange_rate DECIMAL(15,4),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            """))
            
            # StockHolding 테이블 생성
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS stock_holdings (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER NOT NULL,
                    stock_symbol VARCHAR(20) NOT NULL,
                    stock_name VARCHAR(200) NOT NULL,
                    market VARCHAR(10) NOT NULL,
                    quantity DECIMAL(15,4) NOT NULL DEFAULT 0,
                    average_cost DECIMAL(15,4) NOT NULL DEFAULT 0,
                    total_cost DECIMAL(15,2) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id),
                    UNIQUE(account_id, stock_symbol)
                )
            """))
            
            # 인덱스 생성
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_transaction_account_date ON stock_transactions (account_id, date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_transaction_symbol ON stock_transactions (stock_symbol)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_holding_account_symbol ON stock_holdings (account_id, stock_symbol)"))
            
            # 3. 주식 거래 데이터를 새로운 테이블로 이동
            logger.info("3. 주식 거래 데이터 이동 중...")
            
            for transaction in stock_transactions:
                (id, account_id, transaction_type, date, amount, stock_name, 
                 stock_symbol, market, quantity, price_per_share, fee, 
                 transaction_currency, exchange_rate, created_at, updated_at) = transaction
                
                # 주식 거래 데이터가 유효한 경우에만 이동
                if stock_symbol and stock_name and market and quantity and price_per_share:
                    conn.execute(text("""
                        INSERT INTO stock_transactions 
                        (account_id, transaction_type, date, stock_symbol, stock_name, 
                         market, quantity, price_per_share, fee, transaction_currency, 
                         exchange_rate, created_at, updated_at)
                        VALUES (:account_id, :transaction_type, :date, :stock_symbol, :stock_name,
                                :market, :quantity, :price_per_share, :fee, :transaction_currency,
                                :exchange_rate, :created_at, :updated_at)
                    """), {
                        'account_id': account_id,
                        'transaction_type': transaction_type,
                        'date': date,
                        'stock_symbol': stock_symbol,
                        'stock_name': stock_name,
                        'market': market,
                        'quantity': quantity,
                        'price_per_share': price_per_share,
                        'fee': fee,
                        'transaction_currency': transaction_currency,
                        'exchange_rate': exchange_rate,
                        'created_at': created_at,
                        'updated_at': updated_at
                    })
            
            # 4. 기존 Transaction 테이블에서 주식 관련 컬럼 제거
            logger.info("4. 기존 Transaction 테이블 정리 중...")
            
            # 새로운 Transaction 테이블 생성 (주식 관련 컬럼 제거)
            conn.execute(text("""
                CREATE TABLE transactions_new (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER NOT NULL,
                    transaction_type VARCHAR(20) NOT NULL,
                    date TIMESTAMP WITH TIME ZONE NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    transaction_currency VARCHAR(3) NOT NULL,
                    exchange_rate DECIMAL(15,4),
                    description VARCHAR(500),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            """))
            
            # 기존 현금 거래 데이터만 새 테이블로 복사
            conn.execute(text("""
                INSERT INTO transactions_new 
                (id, account_id, transaction_type, date, amount, transaction_currency, 
                 exchange_rate, created_at, updated_at)
                SELECT id, account_id, transaction_type, date, amount, transaction_currency, 
                       exchange_rate, created_at, updated_at
                FROM transactions 
                WHERE transaction_type IN ('DEPOSIT', 'WITHDRAWAL', 'DIVIDEND', 'INTEREST')
            """))
            
            # 기존 테이블 삭제 및 새 테이블로 교체
            conn.execute(text("DROP TABLE transactions"))
            conn.execute(text("ALTER TABLE transactions_new RENAME TO transactions"))
            
            # 5. 주식 보유 현황 계산 및 생성
            logger.info("5. 주식 보유 현황 계산 중...")
            
            # 모든 계좌의 주식 거래를 시간순으로 조회
            result = conn.execute(text("""
                SELECT account_id, stock_symbol, stock_name, market, 
                       transaction_type, quantity, price_per_share
                FROM stock_transactions 
                ORDER BY account_id, stock_symbol, date
            """))
            
            stock_transactions_by_account = {}
            for row in result.fetchall():
                account_id, stock_symbol, stock_name, market, transaction_type, quantity, price_per_share = row
                
                key = (account_id, stock_symbol)
                if key not in stock_transactions_by_account:
                    stock_transactions_by_account[key] = {
                        'stock_name': stock_name,
                        'market': market,
                        'quantity': Decimal('0'),
                        'total_cost': Decimal('0')
                    }
                
                if transaction_type == 'BUY':
                    stock_transactions_by_account[key]['quantity'] += Decimal(str(quantity))
                    stock_transactions_by_account[key]['total_cost'] += Decimal(str(quantity)) * Decimal(str(price_per_share))
                elif transaction_type == 'SELL':
                    quantity_sold = Decimal(str(quantity))
                    if stock_transactions_by_account[key]['quantity'] > 0:
                        avg_cost = stock_transactions_by_account[key]['total_cost'] / stock_transactions_by_account[key]['quantity']
                        cost_of_sold_shares = quantity_sold * avg_cost
                        stock_transactions_by_account[key]['total_cost'] -= cost_of_sold_shares
                    stock_transactions_by_account[key]['quantity'] -= quantity_sold
            
            # 0보다 큰 수량만 보유 현황으로 저장
            for (account_id, stock_symbol), data in stock_transactions_by_account.items():
                if data['quantity'] > 0:
                    average_cost = data['total_cost'] / data['quantity'] if data['quantity'] > 0 else Decimal('0')
                    
                    conn.execute(text("""
                        INSERT INTO stock_holdings 
                        (account_id, stock_symbol, stock_name, market, quantity, 
                         average_cost, total_cost)
                        VALUES (:account_id, :stock_symbol, :stock_name, :market, :quantity,
                                :average_cost, :total_cost)
                    """), {
                        'account_id': account_id,
                        'stock_symbol': stock_symbol,
                        'stock_name': data['stock_name'],
                        'market': data['market'],
                        'quantity': data['quantity'],
                        'average_cost': average_cost,
                        'total_cost': data['total_cost']
                    })
            
            # 6. 계좌 잔액 재계산
            logger.info("6. 계좌 잔액 재계산 중...")
            
            # 모든 계좌 조회
            result = conn.execute(text("SELECT id, initial_balance FROM accounts"))
            accounts = result.fetchall()
            
            for account_id, initial_balance in accounts:
                # 초기 잔액으로 리셋
                current_balance = Decimal(str(initial_balance))
                
                # 현금 거래 적용
                result = conn.execute(text("""
                    SELECT transaction_type, amount 
                    FROM transactions 
                    WHERE account_id = :account_id 
                    ORDER BY date
                """), {'account_id': account_id})
                
                for transaction_type, amount in result.fetchall():
                    amount = Decimal(str(amount))
                    if transaction_type == 'DEPOSIT':
                        current_balance += amount
                    elif transaction_type == 'WITHDRAWAL':
                        current_balance -= amount
                    elif transaction_type == 'DIVIDEND':
                        current_balance += amount
                    elif transaction_type == 'INTEREST':
                        current_balance += amount
                
                # 주식 거래 적용
                result = conn.execute(text("""
                    SELECT transaction_type, quantity, price_per_share, fee 
                    FROM stock_transactions 
                    WHERE account_id = :account_id 
                    ORDER BY date
                """), {'account_id': account_id})
                
                for transaction_type, quantity, price_per_share, fee in result.fetchall():
                    quantity = Decimal(str(quantity))
                    price_per_share = Decimal(str(price_per_share))
                    fee = Decimal(str(fee))
                    
                    if transaction_type == 'BUY':
                        total_cost = (quantity * price_per_share) + fee
                        current_balance -= total_cost
                    elif transaction_type == 'SELL':
                        total_revenue = (quantity * price_per_share) - fee
                        current_balance += total_revenue
                
                # 계좌 잔액 업데이트
                conn.execute(text("""
                    UPDATE accounts 
                    SET current_balance = :current_balance 
                    WHERE id = :account_id
                """), {'current_balance': current_balance, 'account_id': account_id})
            
            # 변경사항 커밋
            conn.commit()
            logger.info("데이터베이스 마이그레이션 완료!")
            
            # 마이그레이션 결과 요약
            result = conn.execute(text("SELECT COUNT(*) FROM transactions"))
            cash_transactions = result.fetchone()[0]
            
            result = conn.execute(text("SELECT COUNT(*) FROM stock_transactions"))
            stock_transactions_count = result.fetchone()[0]
            
            result = conn.execute(text("SELECT COUNT(*) FROM stock_holdings"))
            stock_holdings_count = result.fetchone()[0]
            
            logger.info(f"마이그레이션 결과:")
            logger.info(f"  - 현금 거래: {cash_transactions}건")
            logger.info(f"  - 주식 거래: {stock_transactions_count}건")
            logger.info(f"  - 주식 보유: {stock_holdings_count}건")
            
        except Exception as e:
            logger.error(f"마이그레이션 중 오류 발생: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    import sys
    
    print(f"데이터베이스 마이그레이션을 시작합니다: {DATABASE_URL}")
    print("이 작업은 기존 데이터를 수정합니다. 백업을 권장합니다.")
    
    # 자동으로 진행 (개발 환경)
    print("자동으로 마이그레이션을 진행합니다...")
    
    try:
        migrate_database()
        print("마이그레이션이 성공적으로 완료되었습니다!")
    except Exception as e:
        print(f"마이그레이션 실패: {e}")
        sys.exit(1)