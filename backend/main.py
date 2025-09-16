from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import crud
import schemas
from stock_service import stock_service
from models import Base
from database import engine
import logging

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stock Manager API",
    description="주식 관리 시스템 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Account endpoints
@app.post("/accounts/", response_model=schemas.Account)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    """새 계좌 생성 (REQ-ACC-001)"""
    return crud.create_account(db=db, account=account)

@app.get("/accounts/", response_model=List[schemas.Account])
def read_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """모든 계좌 목록 조회 (REQ-ACC-002)"""
    return crud.get_accounts(db=db, skip=skip, limit=limit)

@app.get("/accounts/{account_id}", response_model=schemas.Account)
def read_account(account_id: int, db: Session = Depends(get_db)):
    """특정 계좌 상세 정보 조회 (REQ-ACC-003)"""
    account = crud.get_account(db=db, account_id=account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@app.put("/accounts/{account_id}", response_model=schemas.Account)
def update_account(account_id: int, account_update: schemas.AccountUpdate, db: Session = Depends(get_db)):
    """계좌 정보 수정 (REQ-ACC-004)"""
    account = crud.update_account(db=db, account_id=account_id, account_update=account_update)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@app.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """계좌 삭제"""
    success = crud.delete_account(db=db, account_id=account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account deleted successfully"}

# Transaction endpoints
@app.post("/transactions/", response_model=schemas.Transaction)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    """새 거래 추가 (REQ-TRN-001)"""
    return crud.create_transaction(db=db, transaction=transaction)

@app.get("/accounts/{account_id}/transactions/", response_model=List[schemas.Transaction])
def read_transactions(
    account_id: int,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    stock_symbol: Optional[str] = None,
    transaction_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """특정 계좌의 거래 목록 조회 (REQ-TRN-002, REQ-TRN-010)"""
    from datetime import datetime
    
    filters = schemas.TransactionFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        stock_symbol=stock_symbol,
        transaction_type=transaction_type
    )
    
    return crud.filter_transactions(db=db, account_id=account_id, filters=filters, skip=skip, limit=limit)

@app.get("/transactions/{transaction_id}", response_model=schemas.Transaction)
def read_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """특정 거래 상세 정보 조회"""
    transaction = crud.get_transaction(db=db, transaction_id=transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@app.put("/transactions/{transaction_id}", response_model=schemas.Transaction)
def update_transaction(transaction_id: int, transaction_update: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    """거래 정보 수정 (REQ-TRN-003)"""
    transaction = crud.update_transaction(db=db, transaction_id=transaction_id, transaction_update=transaction_update)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """거래 삭제 (REQ-TRN-004)"""
    success = crud.delete_transaction(db=db, transaction_id=transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted successfully"}

# Stock search endpoints
@app.get("/stocks/search", response_model=List[schemas.StockSearchResult])
def search_stocks(
    q: str = Query(..., description="검색어"),
    market: str = Query("all", description="시장 (all, kr, us)"),
    limit: int = Query(20, description="결과 수 제한")
):
    """주식 검색 (REQ-STK-001, REQ-STK-002, REQ-STK-003)"""
    try:
        results = stock_service.search_stocks(query=q, market=market, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        raise HTTPException(status_code=500, detail="Stock search failed")

@app.get("/stocks/price/{symbol}")
def get_stock_price(symbol: str, market: str = Query("kr", description="시장 (kr, us)")):
    """현재 주가 조회 (REQ-STK-005)"""
    try:
        price = stock_service.get_current_price(symbol=symbol, market=market)
        if price is None:
            raise HTTPException(status_code=404, detail="Price not found")
        return {"symbol": symbol, "price": price, "market": market}
    except Exception as e:
        logger.error(f"Error getting stock price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stock price")

# Portfolio summary endpoint
@app.get("/portfolio/summary", response_model=schemas.PortfolioSummary)
def get_portfolio_summary(db: Session = Depends(get_db)):
    """포트폴리오 요약 조회 (REQ-SUM-001, REQ-SUM-002, REQ-SUM-003)"""
    try:
        summary = crud.get_portfolio_summary(db=db)
        return schemas.PortfolioSummary(**summary)
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio summary")

# Health check
@app.get("/health")
def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
