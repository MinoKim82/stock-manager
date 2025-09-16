from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional
from models import Account, Transaction
from schemas import AccountCreate, AccountUpdate, TransactionCreate, TransactionUpdate, TransactionFilter
from decimal import Decimal

# Account CRUD operations
def create_account(db: Session, account: AccountCreate) -> Account:
    db_account = Account(**account.dict())
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
        for field, value in update_data.items():
            setattr(db_account, field, value)
        db.commit()
        db.refresh(db_account)
    return db_account

def delete_account(db: Session, account_id: int) -> bool:
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if db_account:
        db.delete(db_account)
        db.commit()
        return True
    return False

# Transaction CRUD operations
def create_transaction(db: Session, transaction: TransactionCreate) -> Transaction:
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transactions(db: Session, account_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
    return db.query(Transaction).filter(Transaction.account_id == account_id).order_by(desc(Transaction.date)).offset(skip).limit(limit).all()

def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def update_transaction(db: Session, transaction_id: int, transaction_update: TransactionUpdate) -> Optional[Transaction]:
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if db_transaction:
        update_data = transaction_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_transaction, field, value)
        db.commit()
        db.refresh(db_transaction)
    return db_transaction

def delete_transaction(db: Session, transaction_id: int) -> bool:
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
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

# Portfolio summary calculation
def get_portfolio_summary(db: Session) -> dict:
    # Get all accounts
    accounts = db.query(Account).all()
    
    total_cash = Decimal('0')
    holdings = {}
    
    for account in accounts:
        # Add cash balance
        if account.currency == 'KRW':
            total_cash += account.balance
        else:  # USD
            # Convert USD to KRW using exchange rate (simplified)
            total_cash += account.balance * Decimal('1300')  # Assume 1 USD = 1300 KRW
    
    # Calculate stock holdings
    transactions = db.query(Transaction).filter(
        Transaction.transaction_type.in_(['BUY', 'SELL'])
    ).all()
    
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
                'total_fee': Decimal('0')
            }
        
        if transaction.transaction_type == 'BUY':
            holdings[symbol]['quantity'] += transaction.quantity or Decimal('0')
            holdings[symbol]['total_cost'] += (transaction.quantity or Decimal('0')) * (transaction.price_per_share or Decimal('0'))
            holdings[symbol]['total_fee'] += transaction.fee or Decimal('0')
        elif transaction.transaction_type == 'SELL':
            holdings[symbol]['quantity'] -= transaction.quantity or Decimal('0')
            holdings[symbol]['total_cost'] -= (transaction.quantity or Decimal('0')) * (transaction.price_per_share or Decimal('0'))
            holdings[symbol]['total_fee'] += transaction.fee or Decimal('0')
    
    # Calculate current values (simplified - would need real-time price data)
    total_stock_value = Decimal('0')
    portfolio_holdings = []
    
    for symbol, holding in holdings.items():
        if holding['quantity'] > 0:
            # Simplified current price (would need real-time data)
            current_price = Decimal('50000')  # Placeholder
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
