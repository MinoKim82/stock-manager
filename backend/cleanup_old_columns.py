#!/usr/bin/env python3
"""
기존 중복 컬럼 정리 스크립트
stock_transactions와 stock_holdings 테이블에서 
stock_symbol, stock_name, market 컬럼을 삭제합니다.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

def cleanup_old_columns():
    """기존 중복 컬럼들을 삭제"""
    
    # 데이터베이스 연결
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🧹 기존 중복 컬럼 정리를 시작합니다...")
        
        # 1. stock_transactions 테이블에서 기존 컬럼들 삭제
        print("🗑️  stock_transactions 테이블에서 중복 컬럼을 삭제합니다...")
        
        # stock_symbol 컬럼 삭제
        try:
            db.execute(text("ALTER TABLE stock_transactions DROP COLUMN stock_symbol"))
            print("   ✅ stock_symbol 컬럼 삭제됨")
        except Exception as e:
            print(f"   ⚠️  stock_symbol 컬럼 삭제 실패: {e}")
        
        # stock_name 컬럼 삭제
        try:
            db.execute(text("ALTER TABLE stock_transactions DROP COLUMN stock_name"))
            print("   ✅ stock_name 컬럼 삭제됨")
        except Exception as e:
            print(f"   ⚠️  stock_name 컬럼 삭제 실패: {e}")
        
        # market 컬럼 삭제
        try:
            db.execute(text("ALTER TABLE stock_transactions DROP COLUMN market"))
            print("   ✅ market 컬럼 삭제됨")
        except Exception as e:
            print(f"   ⚠️  market 컬럼 삭제 실패: {e}")
        
        # 2. stock_holdings 테이블에서 기존 컬럼들 삭제
        print("🗑️  stock_holdings 테이블에서 중복 컬럼을 삭제합니다...")
        
        # stock_symbol 컬럼 삭제
        try:
            db.execute(text("ALTER TABLE stock_holdings DROP COLUMN stock_symbol"))
            print("   ✅ stock_symbol 컬럼 삭제됨")
        except Exception as e:
            print(f"   ⚠️  stock_symbol 컬럼 삭제 실패: {e}")
        
        # stock_name 컬럼 삭제
        try:
            db.execute(text("ALTER TABLE stock_holdings DROP COLUMN stock_name"))
            print("   ✅ stock_name 컬럼 삭제됨")
        except Exception as e:
            print(f"   ⚠️  stock_name 컬럼 삭제 실패: {e}")
        
        # market 컬럼 삭제
        try:
            db.execute(text("ALTER TABLE stock_holdings DROP COLUMN market"))
            print("   ✅ market 컬럼 삭제됨")
        except Exception as e:
            print(f"   ⚠️  market 컬럼 삭제 실패: {e}")
        
        # 3. 기존 인덱스 삭제
        print("🗑️  기존 인덱스를 삭제합니다...")
        
        try:
            db.execute(text("DROP INDEX IF EXISTS idx_stock_transaction_symbol"))
            print("   ✅ idx_stock_transaction_symbol 인덱스 삭제됨")
        except Exception as e:
            print(f"   ⚠️  idx_stock_transaction_symbol 인덱스 삭제 실패: {e}")
        
        try:
            db.execute(text("DROP INDEX IF EXISTS idx_stock_holding_account_symbol"))
            print("   ✅ idx_stock_holding_account_symbol 인덱스 삭제됨")
        except Exception as e:
            print(f"   ⚠️  idx_stock_holding_account_symbol 인덱스 삭제 실패: {e}")
        
        db.commit()
        print("🎉 중복 컬럼 정리가 완료되었습니다!")
        
        # 4. 결과 확인
        print("\n📊 정리 후 테이블 구조:")
        
        # stock_transactions 테이블 구조 확인
        print("\n🔍 stock_transactions 테이블:")
        columns = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'stock_transactions' 
            ORDER BY ordinal_position
        """)).fetchall()
        for col_name, data_type in columns:
            print(f"   - {col_name}: {data_type}")
        
        # stock_holdings 테이블 구조 확인
        print("\n🔍 stock_holdings 테이블:")
        columns = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'stock_holdings' 
            ORDER BY ordinal_position
        """)).fetchall()
        for col_name, data_type in columns:
            print(f"   - {col_name}: {data_type}")
        
        # stocks 테이블 구조 확인
        print("\n🔍 stocks 테이블:")
        columns = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' 
            ORDER BY ordinal_position
        """)).fetchall()
        for col_name, data_type in columns:
            print(f"   - {col_name}: {data_type}")
        
    except Exception as e:
        print(f"❌ 컬럼 정리 중 오류가 발생했습니다: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_old_columns()
