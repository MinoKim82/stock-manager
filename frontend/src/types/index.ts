export interface Account {
  id: number;
  owner_name: string;
  broker: string;
  account_number: string;
  account_type: '연금계좌' | 'IRP계좌' | 'ISA계좌' | 'CMA계좌' | '종합매매계좌' | '해외주식계좌';
  current_balance: number;
  currency: 'KRW' | 'USD';
  created_at: string;
  updated_at: string;
}

// 현금 거래 (입금, 출금, 배당금, 이자)
export interface CashTransaction {
  id: number;
  account_id: number;
  transaction_type: '입금' | '출금' | '배당금' | '이자';
  date: string;
  amount: number;
  transaction_currency: 'KRW' | 'USD';
  exchange_rate?: number;
  exchange_fee: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

// 주식 정보
export interface Stock {
  id: number;
  symbol: string;
  name: string;
  market: string;
  created_at: string;
  updated_at: string;
}

// 주식 거래 (매수, 매도)
export interface StockTransaction {
  id: number;
  account_id: number;
  transaction_type: '매수' | '매도';
  date: string;
  stock_id: number;
  stock?: Stock; // 정규화된 주식 정보
  quantity: number;
  price_per_share: number;
  fee: number;
  transaction_currency: 'KRW' | 'USD';
  exchange_rate?: number;
  created_at: string;
  updated_at: string;
  total_amount: number;
  net_amount: number;
}

// 통합 거래 타입 (표시용)
export interface Transaction {
  id: number;
  account_id: number;
  transaction_type: '입금' | '출금' | '매수' | '매도' | '배당금' | '이자';
  date: string;
  amount?: number;
  stock_name?: string;
  stock_symbol?: string;
  quantity?: number;
  price_per_share?: number;
  fee?: number; // 주식 거래에만 있음
  transaction_currency: 'KRW' | 'USD';
  exchange_rate?: number;
  exchange_fee?: number; // 현금 거래에만 있음
  description?: string;
  created_at: string;
  updated_at: string;
  total_amount?: number;
  net_amount?: number;
}

export interface StockSearchResult {
  symbol: string;
  name: string;
  market: string;
}

export interface StockHolding {
  id: number;
  account_id: number;
  stock_id: number;
  stock?: Stock; // 정규화된 주식 정보
  quantity: number;
  average_cost: number;
  total_cost: number;
  created_at: string;
  updated_at: string;
  // 계산된 필드들 (프론트엔드에서 사용)
  symbol?: string;
  name?: string;
  current_price?: number;
  current_value?: number;
  profit_loss?: number;
  profit_loss_rate?: number;
}

export interface PortfolioSummary {
  total_cash: number;
  total_stock_value: number;
  total_portfolio_value: number;
  holdings: StockHolding[];
}

export interface TransactionFilter {
  start_date?: string;
  end_date?: string;
  stock_symbol?: string;
  transaction_type?: string;
}

export interface AccountFormData {
  owner_name: string;
  broker: string;
  account_number: string;
  account_type: string;
  initial_balance: number;
  currency: string;
}

export interface TransactionFormData {
  account_id: number;
  transaction_type: string;
  date: string;
  amount?: number;
  stock_name?: string;
  stock_symbol?: string;
  quantity?: number;
  price_per_share?: number;
  fee?: number; // 주식 거래에만 필요
  transaction_currency: string;
  exchange_rate?: number;
  exchange_fee?: number; // 현금 거래에만 필요
  description?: string;
}
