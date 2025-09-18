import axios from 'axios';
import { Account, Transaction, CashTransaction, StockTransaction, StockSearchResult, PortfolioSummary, TransactionFilter, AccountFormData, TransactionFormData } from '../types';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Account API
export const accountApi = {
  // 계좌 목록 조회
  getAccounts: async (): Promise<Account[]> => {
    const response = await api.get('/accounts/');
    return response.data;
  },

  // 계좌 상세 조회
  getAccount: async (id: number): Promise<Account> => {
    const response = await api.get(`/accounts/${id}`);
    return response.data;
  },

  // 계좌 생성
  createAccount: async (account: AccountFormData): Promise<Account> => {
    const response = await api.post('/accounts/', account);
    return response.data;
  },

  // 계좌 수정
  updateAccount: async (id: number, account: Partial<AccountFormData>): Promise<Account> => {
    const response = await api.put(`/accounts/${id}`, account);
    return response.data;
  },

  // 계좌 삭제
  deleteAccount: async (id: number): Promise<void> => {
    await api.delete(`/accounts/${id}`);
  },
};

// Cash Transaction API (현금 거래)
export const cashTransactionApi = {
  // 모든 현금 거래 목록 조회
  getAllTransactions: async (filters?: TransactionFilter): Promise<CashTransaction[]> => {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.transaction_type) params.append('transaction_type', filters.transaction_type);
    
    const response = await api.get(`/transactions/?${params.toString()}`);
    return response.data;
  },

  // 현금 거래 목록 조회
  getTransactions: async (accountId: number, filters?: TransactionFilter): Promise<CashTransaction[]> => {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.transaction_type) params.append('transaction_type', filters.transaction_type);
    
    const response = await api.get(`/accounts/${accountId}/transactions/?${params.toString()}`);
    return response.data;
  },

  // 현금 거래 상세 조회
  getTransaction: async (id: number): Promise<CashTransaction> => {
    const response = await api.get(`/transactions/${id}`);
    return response.data;
  },

  // 현금 거래 생성
  createTransaction: async (transaction: TransactionFormData): Promise<CashTransaction> => {
    const response = await api.post('/transactions/', transaction);
    return response.data;
  },

  // 현금 거래 수정
  updateTransaction: async (id: number, transaction: Partial<TransactionFormData>): Promise<CashTransaction> => {
    const response = await api.put(`/transactions/${id}`, transaction);
    return response.data;
  },

  // 현금 거래 삭제
  deleteTransaction: async (id: number): Promise<void> => {
    await api.delete(`/transactions/${id}`);
  },
};

// Stock Transaction API (주식 거래)
export const stockTransactionApi = {
  // 모든 주식 거래 목록 조회
  getAllTransactions: async (filters?: any): Promise<StockTransaction[]> => {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.stock_symbol) params.append('stock_symbol', filters.stock_symbol);
    if (filters?.transaction_type) params.append('transaction_type', filters.transaction_type);
    if (filters?.market) params.append('market', filters.market);
    
    const response = await api.get(`/stock-transactions/?${params.toString()}`);
    return response.data;
  },

  // 주식 거래 목록 조회
  getTransactions: async (accountId: number, filters?: any): Promise<StockTransaction[]> => {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.stock_symbol) params.append('stock_symbol', filters.stock_symbol);
    if (filters?.transaction_type) params.append('transaction_type', filters.transaction_type);
    if (filters?.market) params.append('market', filters.market);
    
    const response = await api.get(`/accounts/${accountId}/stock-transactions/?${params.toString()}`);
    return response.data;
  },

  // 주식 거래 상세 조회
  getTransaction: async (id: number): Promise<StockTransaction> => {
    const response = await api.get(`/stock-transactions/${id}`);
    return response.data;
  },

  // 주식 거래 생성
  createTransaction: async (transaction: any): Promise<StockTransaction> => {
    const response = await api.post('/stock-transactions/', transaction);
    return response.data;
  },

  // 주식 거래 수정
  updateTransaction: async (id: number, transaction: any): Promise<StockTransaction> => {
    const response = await api.put(`/stock-transactions/${id}`, transaction);
    return response.data;
  },

  // 주식 거래 삭제
  deleteTransaction: async (id: number): Promise<void> => {
    await api.delete(`/stock-transactions/${id}`);
  },
};

// 통합 거래 API (하위 호환성)
export const transactionApi = {
  // 모든 거래 목록 조회 (현금 + 주식)
  getAllTransactions: async (filters?: TransactionFilter): Promise<Transaction[]> => {
    const [cashTransactions, stockTransactions] = await Promise.all([
      cashTransactionApi.getAllTransactions(filters),
      stockTransactionApi.getAllTransactions(filters)
    ]);
    
    // 디버깅: 주식 거래 데이터 확인
    console.log('Stock transactions:', stockTransactions[0]);
    console.log('Stock transactions length:', stockTransactions.length);
    if (stockTransactions[0]) {
      console.log('First stock transaction stock:', stockTransactions[0].stock);
    }
    
    // 통합하여 정렬
    const allTransactions: Transaction[] = [
      ...cashTransactions.map(t => ({
        ...t,
        stock_name: undefined,
        stock_symbol: undefined,
        quantity: undefined,
        price_per_share: undefined,
        total_amount: undefined,
        net_amount: undefined,
        fee: undefined // 현금 거래에는 fee가 없음
      })),
      ...stockTransactions.map(t => {
        console.log('Processing stock transaction:', t.id, 'stock:', t.stock);
        return {
          ...t,
          amount: undefined,
          exchange_fee: undefined,
          description: undefined,
          // stock 객체에서 정보 추출
          stock_name: t.stock?.name || undefined,
          stock_symbol: t.stock?.symbol || undefined,
        };
      })
    ];
    
    // 중복 제거 (거래 유형 + id 기준으로 고유하게 처리)
    const uniqueTransactions = allTransactions.filter((transaction, index, self) => 
      index === self.findIndex(t => 
        t.id === transaction.id && 
        t.transaction_type === transaction.transaction_type
      )
    );
    
    console.log('Final transactions count:', uniqueTransactions.length);
    console.log('2021-04-18 transaction in final list:', uniqueTransactions.find(t => t.id === 13 && t.transaction_type === '매수'));
    
    return uniqueTransactions.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  },

  // 거래 목록 조회 (현금 + 주식)
  getTransactions: async (accountId: number, filters?: TransactionFilter): Promise<Transaction[]> => {
    const [cashTransactions, stockTransactions] = await Promise.all([
      cashTransactionApi.getTransactions(accountId, filters),
      stockTransactionApi.getTransactions(accountId, filters)
    ]);
    
    // 통합하여 정렬
    const allTransactions: Transaction[] = [
      ...cashTransactions.map(t => ({
        ...t,
        stock_name: undefined,
        stock_symbol: undefined,
        quantity: undefined,
        price_per_share: undefined,
        total_amount: undefined,
        net_amount: undefined,
        fee: undefined // 현금 거래에는 fee가 없음
      })),
      ...stockTransactions.map(t => ({
        ...t,
        amount: undefined,
        exchange_fee: undefined,
        description: undefined,
        // stock 객체에서 정보 추출
        stock_name: t.stock?.name,
        stock_symbol: t.stock?.symbol,
      }))
    ];
    
    // 중복 제거 (id 기준)
    const uniqueTransactions = allTransactions.filter((transaction, index, self) => 
      index === self.findIndex(t => t.id === transaction.id)
    );
    
    return uniqueTransactions.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  },

  // 거래 상세 조회
  getTransaction: async (id: number): Promise<Transaction> => {
    try {
      const cashTransaction = await cashTransactionApi.getTransaction(id);
      return {
        ...cashTransaction,
        stock_name: undefined,
        stock_symbol: undefined,
        quantity: undefined,
        price_per_share: undefined,
        total_amount: undefined,
        net_amount: undefined,
        fee: undefined
      };
    } catch {
      const stockTransaction = await stockTransactionApi.getTransaction(id);
      return {
        ...stockTransaction,
        amount: undefined,
        exchange_fee: undefined,
        description: undefined,
        // stock 객체에서 정보 추출
        stock_name: stockTransaction.stock?.name,
        stock_symbol: stockTransaction.stock?.symbol,
      };
    }
  },

  // 거래 생성
  createTransaction: async (transaction: TransactionFormData): Promise<Transaction> => {
    if (transaction.transaction_type === '매수' || transaction.transaction_type === '매도') {
      const stockTransaction = await stockTransactionApi.createTransaction(transaction);
      return {
        ...stockTransaction,
        amount: undefined,
        exchange_fee: undefined,
        description: undefined,
        // stock 객체에서 정보 추출
        stock_name: stockTransaction.stock?.name,
        stock_symbol: stockTransaction.stock?.symbol,
      };
    } else {
      const cashTransaction = await cashTransactionApi.createTransaction(transaction);
      return {
        ...cashTransaction,
        stock_name: undefined,
        stock_symbol: undefined,
        quantity: undefined,
        price_per_share: undefined,
        total_amount: undefined,
        net_amount: undefined,
        fee: undefined
      };
    }
  },

  // 거래 수정
  updateTransaction: async (id: number, transaction: Partial<TransactionFormData>): Promise<Transaction> => {
    try {
      const cashTransaction = await cashTransactionApi.updateTransaction(id, transaction);
      return {
        ...cashTransaction,
        stock_name: undefined,
        stock_symbol: undefined,
        quantity: undefined,
        price_per_share: undefined,
        total_amount: undefined,
        net_amount: undefined,
        fee: undefined
      };
    } catch {
      const stockTransaction = await stockTransactionApi.updateTransaction(id, transaction);
      return {
        ...stockTransaction,
        amount: undefined,
        exchange_fee: undefined,
        description: undefined,
        // stock 객체에서 정보 추출
        stock_name: stockTransaction.stock?.name,
        stock_symbol: stockTransaction.stock?.symbol,
      };
    }
  },

  // 거래 삭제
  deleteTransaction: async (id: number): Promise<void> => {
    try {
      await cashTransactionApi.deleteTransaction(id);
    } catch {
      await stockTransactionApi.deleteTransaction(id);
    }
  },
};

// Stock API
export const stockApi = {
  // 주식 검색
  searchStocks: async (query: string, market: string = 'all'): Promise<StockSearchResult[]> => {
    const response = await api.get(`/stocks/search?q=${encodeURIComponent(query)}&market=${market}`);
    return response.data;
  },

  // 주가 조회
  getStockPrice: async (symbol: string, market: string = 'kr'): Promise<{ symbol: string; price: number; market: string }> => {
    const response = await api.get(`/stocks/price/${symbol}?market=${market}`);
    return response.data;
  },

  // 주식 캐시 새로고침
  refreshCache: async (): Promise<void> => {
    await api.post('/stocks/cache/refresh');
  },

  // 주식 캐시 초기화
  clearCache: async (): Promise<void> => {
    await api.delete('/stocks/cache');
  },
};

// Portfolio API
export const portfolioApi = {
  // 포트폴리오 요약 조회
  getPortfolioSummary: async (): Promise<PortfolioSummary> => {
    const response = await api.get('/portfolio/summary');
    return response.data;
  },
};

export default api;
