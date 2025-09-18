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
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React 개발 서버
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

# Transaction endpoints (현금 거래만)
@app.get("/transactions/", response_model=List[schemas.Transaction])
def read_all_transactions(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """모든 현금 거래 목록 조회"""
    from datetime import datetime
    
    filters = schemas.TransactionFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        transaction_type=transaction_type
    )
    
    return crud.get_all_transactions(db=db, filters=filters, skip=skip, limit=limit)

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
    transaction_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """특정 계좌의 현금 거래 목록 조회 (REQ-TRN-002, REQ-TRN-010)"""
    from datetime import datetime
    
    filters = schemas.TransactionFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
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

# Stock Transaction endpoints
@app.get("/stock-transactions/", response_model=List[schemas.StockTransaction])
def read_all_stock_transactions(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    stock_symbol: Optional[str] = None,
    transaction_type: Optional[str] = None,
    market: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """모든 주식 거래 목록 조회"""
    from datetime import datetime
    
    filters = schemas.StockTransactionFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        stock_symbol=stock_symbol,
        transaction_type=transaction_type,
        market=market
    )
    
    return crud.get_all_stock_transactions(db=db, filters=filters, skip=skip, limit=limit)

@app.post("/stock-transactions/", response_model=schemas.StockTransaction)
def create_stock_transaction(stock_transaction: schemas.StockTransactionCreate, db: Session = Depends(get_db)):
    """새 주식 거래 추가"""
    return crud.create_stock_transaction(db=db, stock_transaction=stock_transaction)

@app.get("/accounts/{account_id}/stock-transactions/", response_model=List[schemas.StockTransaction])
def read_stock_transactions(
    account_id: int,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    stock_symbol: Optional[str] = None,
    transaction_type: Optional[str] = None,
    market: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """특정 계좌의 주식 거래 목록 조회"""
    from datetime import datetime
    
    filters = schemas.StockTransactionFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        stock_symbol=stock_symbol,
        transaction_type=transaction_type,
        market=market
    )
    
    return crud.filter_stock_transactions(db=db, account_id=account_id, filters=filters, skip=skip, limit=limit)

@app.get("/stock-transactions/{stock_transaction_id}", response_model=schemas.StockTransaction)
def read_stock_transaction(stock_transaction_id: int, db: Session = Depends(get_db)):
    """특정 주식 거래 상세 정보 조회"""
    stock_transaction = crud.get_stock_transaction(db=db, stock_transaction_id=stock_transaction_id)
    if stock_transaction is None:
        raise HTTPException(status_code=404, detail="Stock transaction not found")
    return stock_transaction

@app.put("/stock-transactions/{stock_transaction_id}", response_model=schemas.StockTransaction)
def update_stock_transaction(stock_transaction_id: int, stock_transaction_update: schemas.StockTransactionUpdate, db: Session = Depends(get_db)):
    """주식 거래 정보 수정"""
    stock_transaction = crud.update_stock_transaction(db=db, stock_transaction_id=stock_transaction_id, stock_transaction_update=stock_transaction_update)
    if stock_transaction is None:
        raise HTTPException(status_code=404, detail="Stock transaction not found")
    return stock_transaction

@app.delete("/stock-transactions/{stock_transaction_id}")
def delete_stock_transaction(stock_transaction_id: int, db: Session = Depends(get_db)):
    """주식 거래 삭제"""
    success = crud.delete_stock_transaction(db=db, stock_transaction_id=stock_transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Stock transaction not found")
    return {"message": "Stock transaction deleted successfully"}

# Stock Holding endpoints
@app.get("/accounts/{account_id}/stock-holdings/", response_model=List[schemas.StockHolding])
def read_stock_holdings(account_id: int, db: Session = Depends(get_db)):
    """특정 계좌의 주식 보유 현황 조회"""
    return crud.get_stock_holdings(db=db, account_id=account_id)

@app.get("/accounts/{account_id}/stock-holdings/{stock_symbol}", response_model=schemas.StockHolding)
def read_stock_holding(account_id: int, stock_symbol: str, db: Session = Depends(get_db)):
    """특정 계좌의 특정 주식 보유 현황 조회"""
    holding = crud.get_stock_holding(db=db, account_id=account_id, stock_symbol=stock_symbol)
    if holding is None:
        raise HTTPException(status_code=404, detail="Stock holding not found")
    return holding

@app.put("/accounts/{account_id}/stock-holdings/{stock_symbol}", response_model=schemas.StockHolding)
def update_stock_holding(account_id: int, stock_symbol: str, holding_update: schemas.StockHoldingUpdate, db: Session = Depends(get_db)):
    """주식 보유 현황 수정"""
    holding = crud.update_stock_holding(db=db, account_id=account_id, stock_symbol=stock_symbol, holding_update=holding_update)
    if holding is None:
        raise HTTPException(status_code=404, detail="Stock holding not found")
    return holding

@app.delete("/accounts/{account_id}/stock-holdings/{stock_symbol}")
def delete_stock_holding(account_id: int, stock_symbol: str, db: Session = Depends(get_db)):
    """주식 보유 현황 삭제"""
    success = crud.delete_stock_holding(db=db, account_id=account_id, stock_symbol=stock_symbol)
    if not success:
        raise HTTPException(status_code=404, detail="Stock holding not found")
    return {"message": "Stock holding deleted successfully"}

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

@app.post("/stocks/cache/refresh")
def refresh_stock_cache():
    """주식 캐시 새로고침"""
    try:
        stock_service.refresh_cache()
        return {"message": "주식 캐시가 새로고침되었습니다."}
    except Exception as e:
        logger.error(f"Error refreshing stock cache: {e}")
        raise HTTPException(status_code=500, detail="캐시 새로고침에 실패했습니다.")

@app.delete("/stocks/cache")
def clear_stock_cache():
    """주식 캐시 초기화"""
    try:
        stock_service.clear_cache()
        return {"message": "주식 캐시가 초기화되었습니다."}
    except Exception as e:
        logger.error(f"Error clearing stock cache: {e}")
        raise HTTPException(status_code=500, detail="캐시 초기화에 실패했습니다.")

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
# Stock endpoints
@app.post("/stocks/", response_model=schemas.Stock)
def create_stock(stock: schemas.StockCreate, db: Session = Depends(get_db)):
    """새 주식 정보 생성"""
    return crud.create_stock(db=db, stock=stock)

@app.get("/stocks/", response_model=List[schemas.Stock])
def read_stocks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """모든 주식 정보 조회"""
    stocks = crud.get_stocks(db, skip=skip, limit=limit)
    return stocks

@app.get("/stocks/{stock_id}", response_model=schemas.Stock)
def read_stock(stock_id: int, db: Session = Depends(get_db)):
    """주식 정보 조회"""
    stock = crud.get_stock(db, stock_id=stock_id)
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock

@app.get("/stocks/symbol/{symbol}", response_model=schemas.Stock)
def read_stock_by_symbol(symbol: str, db: Session = Depends(get_db)):
    """심볼로 주식 정보 조회"""
    stock = crud.get_stock_by_symbol(db, symbol=symbol)
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock

@app.put("/stocks/{stock_id}", response_model=schemas.Stock)
def update_stock(stock_id: int, stock: schemas.StockUpdate, db: Session = Depends(get_db)):
    """주식 정보 수정"""
    db_stock = crud.update_stock(db, stock_id=stock_id, stock=stock)
    if db_stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return db_stock

@app.delete("/stocks/{stock_id}")
def delete_stock(stock_id: int, db: Session = Depends(get_db)):
    """주식 정보 삭제"""
    success = crud.delete_stock(db, stock_id=stock_id)
    if not success:
        raise HTTPException(status_code=404, detail="Stock not found")
    return {"message": "Stock deleted successfully"}

# 통합 거래 목록 엔드포인트
@app.get("/all-transactions/", response_model=List[schemas.Transaction])
def read_all_transactions_combined(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """모든 거래 목록 조회 (현금 + 주식)"""
    from datetime import datetime
    from sqlalchemy.orm import joinedload
    
    # 현금 거래 조회
    cash_filters = schemas.TransactionFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        transaction_type=transaction_type
    )
    cash_transactions = crud.get_all_transactions(db=db, filters=cash_filters, skip=0, limit=1000)
    
    # 주식 거래 조회 (관계 로드 포함)
    stock_transactions = db.query(StockTransaction).options(joinedload(StockTransaction.stock)).order_by(StockTransaction.date.desc()).all()
    
    # 통합하여 반환
    all_transactions = []
    
    # 현금 거래 추가
    for t in cash_transactions:
        all_transactions.append({
            "id": t.id,
            "account_id": t.account_id,
            "transaction_type": t.transaction_type,
            "date": t.date,
            "amount": t.amount,
            "transaction_currency": t.transaction_currency,
            "exchange_rate": t.exchange_rate,
            "exchange_fee": t.exchange_fee,
            "description": t.description,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "stock_name": None,
            "stock_symbol": None,
            "market": None,
            "quantity": None,
            "price_per_share": None,
            "total_amount": None,
            "net_amount": None,
            "fee": None
        })
    
    # 주식 거래 추가
    for t in stock_transactions:
        all_transactions.append({
            "id": t.id,
            "account_id": t.account_id,
            "transaction_type": t.transaction_type,
            "date": t.date,
            "amount": None,
            "transaction_currency": t.transaction_currency,
            "exchange_rate": t.exchange_rate,
            "exchange_fee": None,
            "description": None,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "stock_name": t.stock.name if t.stock else None,
            "stock_symbol": t.stock.symbol if t.stock else None,
            "market": t.stock.market if t.stock else None,
            "quantity": t.quantity,
            "price_per_share": t.price_per_share,
            "total_amount": t.total_amount,
            "net_amount": t.net_amount,
            "fee": t.fee
        })
    
    # 날짜순 정렬
    all_transactions.sort(key=lambda x: x["date"], reverse=True)
    
    return all_transactions[skip:skip+limit]

@app.get("/health")
def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
