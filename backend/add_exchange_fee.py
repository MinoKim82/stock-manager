#!/usr/bin/env python3
"""
환전 수수료 필드 추가 마이그레이션 스크립트
"""

from sqlalchemy import create_engine, text
from config import DATABASE_URL
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_exchange_fee_column():
    """transactions 테이블에 exchange_fee 컬럼 추가"""
    
    # PostgreSQL 연결
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            logger.info("환전 수수료 컬럼 추가 시작...")
            
            # exchange_fee 컬럼 추가
            conn.execute(text("""
                ALTER TABLE transactions 
                ADD COLUMN IF NOT EXISTS exchange_fee DECIMAL(15,2) DEFAULT 0
            """))
            
            # 변경사항 커밋
            conn.commit()
            logger.info("환전 수수료 컬럼 추가 완료!")
            
        except Exception as e:
            logger.error(f"컬럼 추가 중 오류 발생: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("transactions 테이블에 exchange_fee 컬럼을 추가합니다...")
    
    try:
        add_exchange_fee_column()
        print("컬럼 추가가 성공적으로 완료되었습니다!")
    except Exception as e:
        print(f"컬럼 추가 실패: {e}")
        exit(1)
