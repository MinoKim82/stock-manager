from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional
from models import Account, Transaction, StockTransaction, StockHolding, Stock, TransactionType, StockTransactionType
from schemas import (
    AccountCreate, AccountUpdate, 
    TransactionCreate, TransactionUpdate, TransactionFilter,
    StockTransactionCreate, StockTransactionUpdate, StockTransactionFilter,
    StockHoldingCreate, StockHoldingUpdate,
    StockCreate, StockUpdate
)
from decimal import Decimal

# Account CRUD operations
def create_account(db: Session, account: AccountCreate) -> Account:
    db_account = Account(**account.dict())
    db_account.current_balance = db_account.initial_balance # 초기 금액을 현재 잔액으로 설정
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

def get_accounts(db: Session, skip: int = 0, limit: int = 100) -> List[Account]:
    return db.query(Account).offset(skip).limit(limit).all()

def get_account(db: Session, account_id: int) -> Optional[Account]:
    return db.query(Account).filter(Account.id == account_id).first()

def update_account(db: Session, account_id: int, account_update: AccountUpdate) -> Optional[Account]:
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if db_account:
        update_data = account_update.dict(exclude_unset=True)
        
        # Check if initial_balance is being updated
        initial_balance_updated = 'initial_balance' in update_data

        for field, value in update_data.items():
            setattr(db_account, field, value)
        db.commit()
        db.refresh(db_account)

        # If initial_balance was updated, recalculate the current balance
        if initial_balance_updated:
            _recalculate_account_balance(db, account_id)

    return db_account

def delete_account(db: Session, account_id: int) -> bool:
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if db_account:
        db.delete(db_account)
        db.commit()
        return True
    return False

def _recalculate_account_balance(db: Session, account_id: int):
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        return

    # Reset current balance to initial balance
    db_account.current_balance = db_account.initial_balance

    # Apply all cash transactions to recalculate current balance
    transactions = db.query(Transaction).filter(Transaction.account_id == account_id).order_by(Transaction.date).all()

    for transaction in transactions:
        if transaction.transaction_type == TransactionType.DEPOSIT:
            # 입금 시 환전 수수료는 잔액에 포함하지 않음 (입금 금액만 추가)
            db_account.current_balance += transaction.amount
        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            # 출금 시 환전 수수료 포함 (환전 수수료는 원화 기준이므로 환율로 나누어 USD로 변환)
            if transaction.exchange_rate and transaction.exchange_fee:
                exchange_fee_usd = transaction.exchange_fee / transaction.exchange_rate
                total_amount = transaction.amount + exchange_fee_usd
            else:
                total_amount = transaction.amount
            db_account.current_balance -= total_amount
        elif transaction.transaction_type == TransactionType.DIVIDEND:
            db_account.current_balance += transaction.amount
        elif transaction.transaction_type == TransactionType.INTEREST:
            db_account.current_balance += transaction.amount
    
    # Apply stock transactions to recalculate current balance
    stock_transactions = db.query(StockTransaction).filter(StockTransaction.account_id == account_id).order_by(StockTransaction.date).all()
    
    for stock_transaction in stock_transactions:
        if stock_transaction.transaction_type == StockTransactionType.BUY:
            total_cost = (stock_transaction.quantity * stock_transaction.price_per_share) + stock_transaction.fee
            db_account.current_balance -= total_cost
        elif stock_transaction.transaction_type == StockTransactionType.SELL:
            total_revenue = (stock_transaction.quantity * stock_transaction.price_per_share) - stock_transaction.fee
            db_account.current_balance += total_revenue
    
    db.commit()
    db.refresh(db_account)

# Transaction CRUD operations (현금 거래만)
def create_transaction(db: Session, transaction: TransactionCreate) -> Transaction:
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    # Update account balance
    db_account = db.query(Account).filter(Account.id == db_transaction.account_id).first()
    if db_account:
        if db_transaction.transaction_type == TransactionType.DEPOSIT:
            # 입금 시 환전 수수료는 잔액에 포함하지 않음 (입금 금액만 추가)
            db_account.current_balance += db_transaction.amount
        elif db_transaction.transaction_type == TransactionType.WITHDRAWAL:
            # 출금 시 환전 수수료 포함 (환전 수수료는 원화 기준이므로 환율로 나누어 USD로 변환)
            if db_transaction.exchange_rate and db_transaction.exchange_fee:
                exchange_fee_usd = db_transaction.exchange_fee / db_transaction.exchange_rate
                total_amount = db_transaction.amount + exchange_fee_usd
            else:
                total_amount = db_transaction.amount
            db_account.current_balance -= total_amount
        elif db_transaction.transaction_type == TransactionType.DIVIDEND:
            db_account.current_balance += db_transaction.amount
        elif db_transaction.transaction_type == TransactionType.INTEREST:
            db_account.current_balance += db_transaction.amount
        
        db.commit()
        db.refresh(db_account)
            
    return db_transaction

def get_transactions(db: Session, account_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
    return db.query(Transaction).filter(Transaction.account_id == account_id).order_by(desc(Transaction.date)).offset(skip).limit(limit).all()

def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def update_transaction(db: Session, transaction_id: int, transaction_update: TransactionUpdate) -> Optional[Transaction]:
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if db_transaction:
        account_id = db_transaction.account_id # Store account_id before update
        update_data = transaction_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_transaction, field, value)
        db.commit()
        db.refresh(db_transaction)
        _recalculate_account_balance(db, account_id) # Recalculate balance after update
    return db_transaction

def delete_transaction(db: Session, transaction_id: int) -> bool:
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if db_transaction:
        account_id = db_transaction.account_id
        db.delete(db_transaction)
        db.commit()
        _recalculate_account_balance(db, account_id)
        return True
    return False

def filter_transactions(db: Session, account_id: int, filters: TransactionFilter, skip: int = 0, limit: int = 100) -> List[Transaction]:
    query = db.query(Transaction).filter(Transaction.account_id == account_id)
    
    if filters.start_date:
        query = query.filter(Transaction.date >= filters.start_date)
    if filters.end_date:
        query = query.filter(Transaction.date <= filters.end_date)
    if filters.transaction_type:
        query = query.filter(Transaction.transaction_type == filters.transaction_type)
    
    return query.order_by(desc(Transaction.date)).offset(skip).limit(limit).all()

def get_all_transactions(db: Session, filters: TransactionFilter, skip: int = 0, limit: int = 100) -> List[Transaction]:
    """모든 계좌의 현금 거래 목록 조회"""
    query = db.query(Transaction)
    
    if filters.start_date:
        query = query.filter(Transaction.date >= filters.start_date)
    if filters.end_date:
        query = query.filter(Transaction.date <= filters.end_date)
    if filters.transaction_type:
        query = query.filter(Transaction.transaction_type == filters.transaction_type)
    
    return query.order_by(desc(Transaction.date)).offset(skip).limit(limit).all()

# Stock Transaction CRUD operations
def create_stock_transaction(db: Session, stock_transaction: StockTransactionCreate) -> StockTransaction:
    db_stock_transaction = StockTransaction(**stock_transaction.dict())
    db.add(db_stock_transaction)
    db.commit()
    db.refresh(db_stock_transaction)
    
    # Update account balance
    db_account = db.query(Account).filter(Account.id == db_stock_transaction.account_id).first()
    if db_account:
        if db_stock_transaction.transaction_type == StockTransactionType.BUY:
            total_cost = (db_stock_transaction.quantity * db_stock_transaction.price_per_share) + db_stock_transaction.fee
            db_account.current_balance -= total_cost
        elif db_stock_transaction.transaction_type == StockTransactionType.SELL:
            total_revenue = (db_stock_transaction.quantity * db_stock_transaction.price_per_share) - db_stock_transaction.fee
            db_account.current_balance += total_revenue
        
        db.commit()
        db.refresh(db_account)
    
    # Update stock holdings
    _update_stock_holding(db, db_stock_transaction)
    
    return db_stock_transaction

def get_stock_transactions(db: Session, account_id: int, skip: int = 0, limit: int = 100) -> List[StockTransaction]:
    from sqlalchemy.orm import joinedload
    return db.query(StockTransaction).options(joinedload(StockTransaction.stock)).filter(StockTransaction.account_id == account_id).order_by(desc(StockTransaction.date)).offset(skip).limit(limit).all()

def get_stock_transaction(db: Session, stock_transaction_id: int) -> Optional[StockTransaction]:
    from sqlalchemy.orm import joinedload
    return db.query(StockTransaction).options(joinedload(StockTransaction.stock)).filter(StockTransaction.id == stock_transaction_id).first()

def update_stock_transaction(db: Session, stock_transaction_id: int, stock_transaction_update: StockTransactionUpdate) -> Optional[StockTransaction]:
    db_stock_transaction = db.query(StockTransaction).filter(StockTransaction.id == stock_transaction_id).first()
    if db_stock_transaction:
        account_id = db_stock_transaction.account_id
        update_data = stock_transaction_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_stock_transaction, field, value)
        db.commit()
        db.refresh(db_stock_transaction)
        _recalculate_account_balance(db, account_id)
        _recalculate_stock_holdings(db, account_id)
    return db_stock_transaction

def delete_stock_transaction(db: Session, stock_transaction_id: int) -> bool:
    db_stock_transaction = db.query(StockTransaction).filter(StockTransaction.id == stock_transaction_id).first()
    if db_stock_transaction:
        account_id = db_stock_transaction.account_id
        db.delete(db_stock_transaction)
        db.commit()
        _recalculate_account_balance(db, account_id)
        _recalculate_stock_holdings(db, account_id)
        return True
    return False

def filter_stock_transactions(db: Session, account_id: int, filters: StockTransactionFilter, skip: int = 0, limit: int = 100) -> List[StockTransaction]:
    query = db.query(StockTransaction).filter(StockTransaction.account_id == account_id)
    
    if filters.start_date:
        query = query.filter(StockTransaction.date >= filters.start_date)
    if filters.end_date:
        query = query.filter(StockTransaction.date <= filters.end_date)
    if filters.stock_symbol:
        query = query.filter(StockTransaction.stock_symbol == filters.stock_symbol)
    if filters.transaction_type:
        query = query.filter(StockTransaction.transaction_type == filters.transaction_type)
    if filters.market:
        query = query.filter(StockTransaction.market == filters.market)
    
    return query.order_by(desc(StockTransaction.date)).offset(skip).limit(limit).all()

def get_all_stock_transactions(db: Session, filters: StockTransactionFilter, skip: int = 0, limit: int = 100) -> List[StockTransaction]:
    """모든 계좌의 주식 거래 목록 조회"""
    from sqlalchemy.orm import joinedload
    
    query = db.query(StockTransaction).options(joinedload(StockTransaction.stock))
    
    if filters.start_date:
        query = query.filter(StockTransaction.date >= filters.start_date)
    if filters.end_date:
        query = query.filter(StockTransaction.date <= filters.end_date)
    if filters.transaction_type:
        query = query.filter(StockTransaction.transaction_type == filters.transaction_type)
    
    return query.order_by(desc(StockTransaction.date)).offset(skip).limit(limit).all()

# Stock Holding CRUD operations
def get_stock_holdings(db: Session, account_id: int) -> List[StockHolding]:
    return db.query(StockHolding).filter(StockHolding.account_id == account_id).all()

def get_stock_holding(db: Session, account_id: int, stock_symbol: str) -> Optional[StockHolding]:
    """심볼로 주식 보유 현황 조회 (하위 호환성)"""
    return db.query(StockHolding).filter(
        StockHolding.account_id == account_id,
        StockHolding.stock_symbol == stock_symbol
    ).first()

def get_stock_holding_by_stock_id(db: Session, account_id: int, stock_id: int) -> Optional[StockHolding]:
    """stock_id로 주식 보유 현황 조회"""
    return db.query(StockHolding).filter(
        StockHolding.account_id == account_id,
        StockHolding.stock_id == stock_id
    ).first()

def update_stock_holding(db: Session, account_id: int, stock_symbol: str, holding_update: StockHoldingUpdate) -> Optional[StockHolding]:
    db_holding = get_stock_holding(db, account_id, stock_symbol)
    if db_holding:
        update_data = holding_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_holding, field, value)
        db.commit()
        db.refresh(db_holding)
    return db_holding

def delete_stock_holding(db: Session, account_id: int, stock_symbol: str) -> bool:
    db_holding = get_stock_holding(db, account_id, stock_symbol)
    if db_holding:
        db.delete(db_holding)
        db.commit()
        return True
    return False

# Helper functions for stock holdings
def _update_stock_holding(db: Session, stock_transaction: StockTransaction):
    """주식 거래 후 보유 현황 업데이트"""
    account_id = stock_transaction.account_id
    stock_id = stock_transaction.stock_id
    
    # 기존 보유 현황 조회 또는 생성
    holding = get_stock_holding_by_stock_id(db, account_id, stock_id)
    if not holding:
        holding = StockHolding(
            account_id=account_id,
            stock_id=stock_id,
            quantity=Decimal('0'),
            average_cost=Decimal('0'),
            total_cost=Decimal('0')
        )
        db.add(holding)
    
    if stock_transaction.transaction_type == StockTransactionType.BUY:
        # 매수: 수량과 총 매입가 증가
        new_quantity = holding.quantity + stock_transaction.quantity
        new_total_cost = holding.total_cost + (stock_transaction.quantity * stock_transaction.price_per_share)
        holding.quantity = new_quantity
        holding.total_cost = new_total_cost
        holding.average_cost = new_total_cost / new_quantity if new_quantity > 0 else Decimal('0')
        
    elif stock_transaction.transaction_type == StockTransactionType.SELL:
        # 매도: 수량과 총 매입가 감소 (평균 단가 유지)
        quantity_sold = stock_transaction.quantity
        if holding.quantity >= quantity_sold:
            cost_per_share = holding.average_cost
            cost_of_sold_shares = quantity_sold * cost_per_share
            
            holding.quantity -= quantity_sold
            holding.total_cost -= cost_of_sold_shares
            
            # 수량이 0이 되면 보유 현황 삭제
            if holding.quantity <= 0:
                db.delete(holding)
                return
    
    db.commit()
    db.refresh(holding)

def _recalculate_stock_holdings(db: Session, account_id: int):
    """계좌의 모든 주식 보유 현황 재계산"""
    # 기존 보유 현황 삭제
    db.query(StockHolding).filter(StockHolding.account_id == account_id).delete()
    
    # 해당 계좌의 모든 주식 거래를 시간순으로 조회
    stock_transactions = db.query(StockTransaction).filter(
        StockTransaction.account_id == account_id
    ).order_by(StockTransaction.date).all()
    
    # 주식별로 그룹화하여 처리
    holdings_by_stock_id = {}
    
    for transaction in stock_transactions:
        stock_id = transaction.stock_id
        if stock_id not in holdings_by_stock_id:
            holdings_by_stock_id[stock_id] = {
                'quantity': Decimal('0'),
                'total_cost': Decimal('0')
            }
        
        if transaction.transaction_type == StockTransactionType.BUY:
            holdings_by_stock_id[stock_id]['quantity'] += transaction.quantity
            holdings_by_stock_id[stock_id]['total_cost'] += transaction.quantity * transaction.price_per_share
        elif transaction.transaction_type == StockTransactionType.SELL:
            quantity_sold = transaction.quantity
            if holdings_by_stock_id[stock_id]['quantity'] > 0:
                avg_cost = holdings_by_stock_id[stock_id]['total_cost'] / holdings_by_stock_id[stock_id]['quantity']
                cost_of_sold_shares = quantity_sold * avg_cost
                holdings_by_stock_id[stock_id]['total_cost'] -= cost_of_sold_shares
            holdings_by_stock_id[stock_id]['quantity'] -= quantity_sold
    
    # 0보다 큰 수량만 보유 현황으로 저장
    for stock_id, data in holdings_by_stock_id.items():
        if data['quantity'] > 0:
            holding = StockHolding(
                account_id=account_id,
                stock_id=stock_id,
                quantity=data['quantity'],
                total_cost=data['total_cost'],
                average_cost=data['total_cost'] / data['quantity'] if data['quantity'] > 0 else Decimal('0')
            )
            db.add(holding)
    
    db.commit()

# Portfolio summary calculation
def get_portfolio_summary(db: Session) -> dict:
    from stock_service import stock_service

    # Get all accounts
    accounts = db.query(Account).all()
    
    total_cash = Decimal('0')
    
    for account in accounts:
        # Add cash balance
        if account.currency == 'KRW':
            total_cash += account.current_balance
        else:  # USD
            # TODO: Get real-time exchange rate
            total_cash += account.current_balance * Decimal('1300')  # Assume 1 USD = 1300 KRW
    
    # Get all stock holdings with stock information
    from sqlalchemy.orm import joinedload
    stock_holdings = db.query(StockHolding).options(joinedload(StockHolding.stock)).all()
    
    # Calculate current values
    total_stock_value = Decimal('0')
    portfolio_holdings = []
    
    for holding in stock_holdings:
        if holding.quantity > 0 and holding.stock:
            market = holding.stock.market
            # Determine market for API call
            api_market = 'kr' # default
            if market == 'KRX':
                api_market = 'kr'
            elif market in ['NYS', 'NAS', 'AMS']:
                api_market = 'us'

            current_price = stock_service.get_current_price(holding.stock.symbol, market=api_market)
            current_price = Decimal(str(current_price)) if current_price is not None else Decimal('0')

            current_value = holding.quantity * current_price
            profit_loss = current_value - holding.total_cost
            profit_loss_rate = (profit_loss / holding.total_cost * 100) if holding.total_cost > 0 else Decimal('0')
            
            portfolio_holdings.append({
                'symbol': holding.stock.symbol,
                'name': holding.stock.name,
                'quantity': holding.quantity,
                'average_cost': holding.average_cost,
                'current_price': current_price,
                'current_value': current_value,
                'profit_loss': profit_loss,
                'profit_loss_rate': profit_loss_rate
            })
            
            total_stock_value += current_value
    
    return {
        'total_cash': total_cash,
        'total_stock_value': total_stock_value,
        'total_portfolio_value': total_cash + total_stock_value,
        'holdings': portfolio_holdings
    }

# Stock CRUD operations
def create_stock(db: Session, stock: StockCreate) -> Stock:
    """새 주식 정보 생성"""
    db_stock = Stock(**stock.dict())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock

def get_stock(db: Session, stock_id: int) -> Optional[Stock]:
    """주식 정보 조회"""
    return db.query(Stock).filter(Stock.id == stock_id).first()

def get_stock_by_symbol(db: Session, symbol: str) -> Optional[Stock]:
    """심볼로 주식 정보 조회"""
    return db.query(Stock).filter(Stock.symbol == symbol).first()

def get_stocks(db: Session, skip: int = 0, limit: int = 100) -> List[Stock]:
    """모든 주식 정보 조회"""
    return db.query(Stock).offset(skip).limit(limit).all()

def update_stock(db: Session, stock_id: int, stock: StockUpdate) -> Optional[Stock]:
    """주식 정보 수정"""
    db_stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if db_stock:
        update_data = stock.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_stock, field, value)
        db.commit()
        db.refresh(db_stock)
    return db_stock

def delete_stock(db: Session, stock_id: int) -> bool:
    """주식 정보 삭제"""
    db_stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if db_stock:
        db.delete(db_stock)
        db.commit()
        return True
    return False

def get_or_create_stock(db: Session, symbol: str, name: str, market: str) -> Stock:
    """주식 정보 조회 또는 생성"""
    stock = get_stock_by_symbol(db, symbol)
    if not stock:
        stock_data = StockCreate(symbol=symbol, name=name, market=market)
        stock = create_stock(db, stock_data)
    return stock
