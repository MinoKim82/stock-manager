#!/usr/bin/env python3
"""
데이터베이스 정규화 마이그레이션 스크립트
기존 stock_transactions와 stock_holdings 테이블의 중복 주식 정보를 
stocks 테이블로 정규화합니다.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, Stock, StockTransaction, StockHolding
from config import DATABASE_URL

def migrate_to_stocks():
    """기존 데이터를 stocks 테이블로 마이그레이션"""
    
    # 데이터베이스 연결
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🚀 데이터베이스 정규화 마이그레이션을 시작합니다...")
        
        # 1. stocks 테이블 생성
        print("📋 stocks 테이블을 생성합니다...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS stocks (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                market VARCHAR(20) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 인덱스 생성
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_symbol ON stocks(symbol)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_market ON stocks(market)"))
        
        db.commit()
        print("✅ stocks 테이블이 생성되었습니다.")
        
        # 2. 기존 주식 정보 수집 (stock_transactions에서)
        print("📊 stock_transactions에서 주식 정보를 수집합니다...")
        stock_data_query = text("""
            SELECT DISTINCT stock_symbol, stock_name, market
            FROM stock_transactions
            WHERE stock_symbol IS NOT NULL AND stock_name IS NOT NULL AND market IS NOT NULL
        """)
        
        stock_data = db.execute(stock_data_query).fetchall()
        print(f"   - {len(stock_data)}개의 고유 주식 정보를 찾았습니다.")
        
        # 3. stocks 테이블에 주식 정보 삽입
        print("💾 stocks 테이블에 주식 정보를 삽입합니다...")
        stock_mapping = {}  # symbol -> stock_id 매핑
        
        for symbol, name, market in stock_data:
            # 이미 존재하는지 확인
            existing_stock_query = text("SELECT id FROM stocks WHERE symbol = :symbol")
            existing_stock = db.execute(existing_stock_query, {"symbol": symbol}).fetchone()
            
            if not existing_stock:
                # 새 주식 정보 삽입
                insert_query = text("""
                    INSERT INTO stocks (symbol, name, market) 
                    VALUES (:symbol, :name, :market) 
                    RETURNING id
                """)
                result = db.execute(insert_query, {
                    "symbol": symbol, 
                    "name": name, 
                    "market": market
                })
                stock_id = result.fetchone()[0]
                stock_mapping[symbol] = stock_id
                print(f"   - {symbol} ({name}) 추가됨 (ID: {stock_id})")
            else:
                stock_mapping[symbol] = existing_stock[0]
                print(f"   - {symbol} ({name}) 이미 존재함 (ID: {existing_stock[0]})")
        
        db.commit()
        print(f"✅ {len(stock_mapping)}개의 주식 정보가 stocks 테이블에 저장되었습니다.")
        
        # 4. stock_holdings에서도 주식 정보 수집
        print("📊 stock_holdings에서 주식 정보를 수집합니다...")
        holding_stock_data_query = text("""
            SELECT DISTINCT stock_symbol, stock_name, market
            FROM stock_holdings
            WHERE stock_symbol IS NOT NULL AND stock_name IS NOT NULL AND market IS NOT NULL
        """)
        
        holding_stock_data = db.execute(holding_stock_data_query).fetchall()
        print(f"   - {len(holding_stock_data)}개의 고유 주식 정보를 찾았습니다.")
        
        # stock_holdings의 주식 정보도 stocks 테이블에 추가
        for symbol, name, market in holding_stock_data:
            if symbol not in stock_mapping:
                # 새 주식 정보 삽입
                insert_query = text("""
                    INSERT INTO stocks (symbol, name, market) 
                    VALUES (:symbol, :name, :market) 
                    RETURNING id
                """)
                result = db.execute(insert_query, {
                    "symbol": symbol, 
                    "name": name, 
                    "market": market
                })
                stock_id = result.fetchone()[0]
                stock_mapping[symbol] = stock_id
                print(f"   - {symbol} ({name}) 추가됨 (ID: {stock_id})")
            else:
                print(f"   - {symbol} ({name}) 이미 존재함")
        
        db.commit()
        print(f"✅ 총 {len(stock_mapping)}개의 주식 정보가 stocks 테이블에 저장되었습니다.")
        
        # 5. stock_transactions 테이블에 stock_id 컬럼 추가
        print("🔧 stock_transactions 테이블을 업데이트합니다...")
        
        # stock_id 컬럼 추가
        db.execute(text("ALTER TABLE stock_transactions ADD COLUMN stock_id INTEGER"))
        
        # stock_id 업데이트
        for symbol, stock_id in stock_mapping.items():
            db.execute(text("""
                UPDATE stock_transactions 
                SET stock_id = :stock_id 
                WHERE stock_symbol = :symbol
            """), {"stock_id": stock_id, "symbol": symbol})
        
        # 기존 컬럼 제거 (PostgreSQL에서는 컬럼 제거가 복잡하므로 주석 처리)
        # db.execute(text("ALTER TABLE stock_transactions DROP COLUMN stock_symbol"))
        # db.execute(text("ALTER TABLE stock_transactions DROP COLUMN stock_name"))
        # db.execute(text("ALTER TABLE stock_transactions DROP COLUMN market"))
        
        print("✅ stock_transactions 테이블이 업데이트되었습니다.")
        
        # 6. stock_holdings 테이블에 stock_id 컬럼 추가
        print("🔧 stock_holdings 테이블을 업데이트합니다...")
        
        # stock_id 컬럼 추가
        db.execute(text("ALTER TABLE stock_holdings ADD COLUMN stock_id INTEGER"))
        
        # stock_id 업데이트
        for symbol, stock_id in stock_mapping.items():
            db.execute(text("""
                UPDATE stock_holdings 
                SET stock_id = :stock_id 
                WHERE stock_symbol = :symbol
            """), {"stock_id": stock_id, "symbol": symbol})
        
        print("✅ stock_holdings 테이블이 업데이트되었습니다.")
        
        # 7. 외래키 제약조건 추가
        print("🔗 외래키 제약조건을 추가합니다...")
        
        try:
            db.execute(text("""
                ALTER TABLE stock_transactions 
                ADD CONSTRAINT fk_stock_transactions_stock_id 
                FOREIGN KEY (stock_id) REFERENCES stocks(id)
            """))
            print("✅ stock_transactions 외래키 제약조건 추가됨")
        except Exception as e:
            print(f"⚠️  stock_transactions 외래키 제약조건 추가 실패: {e}")
        
        try:
            db.execute(text("""
                ALTER TABLE stock_holdings 
                ADD CONSTRAINT fk_stock_holdings_stock_id 
                FOREIGN KEY (stock_id) REFERENCES stocks(id)
            """))
            print("✅ stock_holdings 외래키 제약조건 추가됨")
        except Exception as e:
            print(f"⚠️  stock_holdings 외래키 제약조건 추가 실패: {e}")
        
        db.commit()
        print("🎉 마이그레이션이 성공적으로 완료되었습니다!")
        
        # 8. 결과 확인
        print("\n📊 마이그레이션 결과:")
        
        stocks_count = db.execute(text("SELECT COUNT(*) FROM stocks")).scalar()
        print(f"   - stocks 테이블: {stocks_count}개 레코드")
        
        transactions_count = db.execute(text("SELECT COUNT(*) FROM stock_transactions")).scalar()
        print(f"   - stock_transactions 테이블: {transactions_count}개 레코드")
        
        holdings_count = db.execute(text("SELECT COUNT(*) FROM stock_holdings")).scalar()
        print(f"   - stock_holdings 테이블: {holdings_count}개 레코드")
        
        # stock_id가 설정된 레코드 수 확인
        transactions_with_stock_id = db.execute(text("""
            SELECT COUNT(*) FROM stock_transactions WHERE stock_id IS NOT NULL
        """)).scalar()
        print(f"   - stock_id가 설정된 거래: {transactions_with_stock_id}개")
        
        holdings_with_stock_id = db.execute(text("""
            SELECT COUNT(*) FROM stock_holdings WHERE stock_id IS NOT NULL
        """)).scalar()
        print(f"   - stock_id가 설정된 보유: {holdings_with_stock_id}개")
        
    except Exception as e:
        print(f"❌ 마이그레이션 중 오류가 발생했습니다: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_to_stocks()
