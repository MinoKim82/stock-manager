import axios from 'axios';
import { Account, Transaction, StockSearchResult, PortfolioSummary, TransactionFilter, AccountFormData, TransactionFormData } from '../types';

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

// Transaction API
export const transactionApi = {
  // 거래 목록 조회
  getTransactions: async (accountId: number, filters?: TransactionFilter): Promise<Transaction[]> => {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.stock_symbol) params.append('stock_symbol', filters.stock_symbol);
    if (filters?.transaction_type) params.append('transaction_type', filters.transaction_type);
    
    const response = await api.get(`/accounts/${accountId}/transactions/?${params.toString()}`);
    return response.data;
  },

  // 거래 상세 조회
  getTransaction: async (id: number): Promise<Transaction> => {
    const response = await api.get(`/transactions/${id}`);
    return response.data;
  },

  // 거래 생성
  createTransaction: async (transaction: TransactionFormData): Promise<Transaction> => {
    const response = await api.post('/transactions/', transaction);
    return response.data;
  },

  // 거래 수정
  updateTransaction: async (id: number, transaction: Partial<TransactionFormData>): Promise<Transaction> => {
    const response = await api.put(`/transactions/${id}`, transaction);
    return response.data;
  },

  // 거래 삭제
  deleteTransaction: async (id: number): Promise<void> => {
    await api.delete(`/transactions/${id}`);
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
