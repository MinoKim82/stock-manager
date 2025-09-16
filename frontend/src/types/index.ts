export interface Account {
  id: number;
  owner_name: string;
  broker: string;
  account_number: string;
  account_type: '연금계좌' | 'IRP계좌' | 'ISA계좌' | 'CMA계좌' | '종합매매계좌' | '미국주식계좌';
  balance: number;
  currency: 'KRW' | 'USD';
  created_at: string;
  updated_at: string;
}

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
  fee: number;
  transaction_currency: 'KRW' | 'USD';
  exchange_rate?: number;
  created_at: string;
  updated_at: string;
  total_amount?: number;
}

export interface StockSearchResult {
  symbol: string;
  name: string;
  market: string;
}

export interface StockHolding {
  symbol: string;
  name: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  current_value: number;
  profit_loss: number;
  profit_loss_rate: number;
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
  balance: number;
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
  fee: number;
  transaction_currency: string;
  exchange_rate?: number;
}
