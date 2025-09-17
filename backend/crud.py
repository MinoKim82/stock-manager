from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional
from models import Account, Transaction, TransactionType
from schemas import AccountCreate, AccountUpdate, TransactionCreate, TransactionUpdate, TransactionFilter
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

    # Apply all transactions to recalculate current balance
    transactions = db.query(Transaction).filter(Transaction.account_id == account_id).order_by(Transaction.date).all()

    for transaction in transactions:
        if transaction.transaction_type == TransactionType.DEPOSIT:
            db_account.current_balance += transaction.amount
        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            db_account.current_balance -= transaction.amount
        elif transaction.transaction_type == TransactionType.BUY:
            total_cost = (transaction.quantity * transaction.price_per_share) + transaction.fee
            db_account.current_balance -= total_cost
        elif transaction.transaction_type == TransactionType.SELL:
            total_revenue = (transaction.quantity * transaction.price_per_share) - transaction.fee
            db_account.current_balance += total_revenue
        elif transaction.transaction_type == TransactionType.DIVIDEND:
            db_account.current_balance += transaction.amount
        elif transaction.transaction_type == TransactionType.INTEREST:
            db_account.current_balance += transaction.amount
    
    db.commit()
    db.refresh(db_account)

# Transaction CRUD operations
def create_transaction(db: Session, transaction: TransactionCreate) -> Transaction:
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    # Update account balance
    db_account = db.query(Account).filter(Account.id == db_transaction.account_id).first()
    if db_account:
        if db_transaction.transaction_type == TransactionType.DEPOSIT:
            db_account.current_balance += db_transaction.amount
        elif db_transaction.transaction_type == TransactionType.WITHDRAWAL:
            db_account.current_balance -= db_transaction.amount
        elif db_transaction.transaction_type == TransactionType.BUY:
            total_cost = (db_transaction.quantity * db_transaction.price_per_share) + db_transaction.fee
            db_account.current_balance -= total_cost
        elif db_transaction.transaction_type == TransactionType.SELL:
            total_revenue = (db_transaction.quantity * db_transaction.price_per_share) - db_transaction.fee
            db_account.current_balance += total_revenue
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
    if filters.stock_symbol:
        query = query.filter(Transaction.stock_symbol == filters.stock_symbol)
    if filters.transaction_type:
        query = query.filter(Transaction.transaction_type == filters.transaction_type)
    
    return query.order_by(desc(Transaction.date)).offset(skip).limit(limit).all()

def get_all_transactions(db: Session, filters: TransactionFilter, skip: int = 0, limit: int = 100) -> List[Transaction]:
    """모든 계좌의 거래 목록 조회"""
    query = db.query(Transaction)
    
    if filters.start_date:
        query = query.filter(Transaction.date >= filters.start_date)
    if filters.end_date:
        query = query.filter(Transaction.date <= filters.end_date)
    if filters.stock_symbol:
        query = query.filter(Transaction.stock_symbol == filters.stock_symbol)
    if filters.transaction_type:
        query = query.filter(Transaction.transaction_type == filters.transaction_type)
    
    return query.order_by(desc(Transaction.date)).offset(skip).limit(limit).all()

# Portfolio summary calculation
def get_portfolio_summary(db: Session) -> dict:
    from stock_service import stock_service

    # Get all accounts
    accounts = db.query(Account).all()
    
    total_cash = Decimal('0')
    holdings = {}
    
    for account in accounts:
        # Add cash balance
        if account.currency == 'KRW':
            total_cash += account.current_balance
        else:  # USD
            # TODO: Get real-time exchange rate
            total_cash += account.current_balance * Decimal('1300')  # Assume 1 USD = 1300 KRW
    
    # Calculate stock holdings
    transactions = db.query(Transaction).filter(
        Transaction.transaction_type.in_([TransactionType.BUY, TransactionType.SELL])
    ).order_by(Transaction.date).all()
    
    for transaction in transactions:
        if not transaction.stock_symbol:
            continue
            
        symbol = transaction.stock_symbol
        if symbol not in holdings:
            holdings[symbol] = {
                'symbol': symbol,
                'name': transaction.stock_name or '',
                'quantity': Decimal('0'),
                'total_cost': Decimal('0'),
                'market': transaction.market.value if transaction.market else ''
            }
        
        if transaction.transaction_type == TransactionType.BUY:
            holdings[symbol]['quantity'] += transaction.quantity or Decimal('0')
            holdings[symbol]['total_cost'] += (transaction.quantity or Decimal('0')) * (transaction.price_per_share or Decimal('0'))
        elif transaction.transaction_type == TransactionType.SELL:
            quantity_sold = transaction.quantity or Decimal('0')
            if holdings[symbol]['quantity'] > 0:
                avg_cost_before_sale = holdings[symbol]['total_cost'] / holdings[symbol]['quantity']
                cost_of_sold_shares = quantity_sold * avg_cost_before_sale
                holdings[symbol]['total_cost'] -= cost_of_sold_shares
            holdings[symbol]['quantity'] -= quantity_sold

    # Calculate current values
    total_stock_value = Decimal('0')
    portfolio_holdings = []
    
    for symbol, holding in holdings.items():
        if holding['quantity'] > 0:
            market = holding['market']
            # Determine market for API call
            api_market = 'kr' # default
            if market == 'KRX':
                api_market = 'kr'
            elif market in ['NYS', 'NAS', 'AMS']:
                api_market = 'us'

            current_price = stock_service.get_current_price(symbol, market=api_market)
            current_price = Decimal(str(current_price)) if current_price is not None else Decimal('0')

            current_value = holding['quantity'] * current_price
            average_cost = holding['total_cost'] / holding['quantity'] if holding['quantity'] > 0 else Decimal('0')
            profit_loss = current_value - holding['total_cost']
            profit_loss_rate = (profit_loss / holding['total_cost'] * 100) if holding['total_cost'] > 0 else Decimal('0')
            
            portfolio_holdings.append({
                'symbol': symbol,
                'name': holding['name'],
                'quantity': holding['quantity'],
                'average_cost': average_cost,
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
