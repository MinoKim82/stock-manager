import FinanceDataReader as fdr
import pandas as pd
from typing import List, Optional
from schemas import StockSearchResult
import logging

logger = logging.getLogger(__name__)

class StockService:
    def __init__(self):
        self.kr_stocks = None
        self.us_stocks = None
    
    def _load_kr_stocks(self):
        """한국 주식 목록 로드"""
        try:
            if self.kr_stocks is None:
                # KRX 상장사 목록 가져오기
                self.kr_stocks = fdr.StockListing('KRX')
                logger.info(f"Loaded {len(self.kr_stocks)} Korean stocks")
        except Exception as e:
            logger.error(f"Error loading Korean stocks: {e}")
            self.kr_stocks = pd.DataFrame()
    
    def _load_us_stocks(self):
        """미국 주식 목록 로드 (S&P 500)"""
        try:
            if self.us_stocks is None:
                # S&P 500 목록 가져오기
                self.us_stocks = fdr.StockListing('S&P500')
                logger.info(f"Loaded {len(self.us_stocks)} US stocks")
        except Exception as e:
            logger.error(f"Error loading US stocks: {e}")
            self.us_stocks = pd.DataFrame()
    
    def search_kr_stocks(self, query: str, limit: int = 20) -> List[StockSearchResult]:
        """한국 주식 검색"""
        self._load_kr_stocks()
        
        if self.kr_stocks.empty:
            return []
        
        # 이름과 심볼로 검색
        query_lower = query.lower()
        mask = (
            self.kr_stocks['Name'].str.lower().str.contains(query_lower, na=False) |
            self.kr_stocks['Symbol'].str.lower().str.contains(query_lower, na=False)
        )
        
        results = self.kr_stocks[mask].head(limit)
        
        return [
            StockSearchResult(
                symbol=row['Symbol'],
                name=row['Name'],
                market='KRX'
            )
            for _, row in results.iterrows()
        ]
    
    def search_us_stocks(self, query: str, limit: int = 20) -> List[StockSearchResult]:
        """미국 주식 검색"""
        self._load_us_stocks()
        
        if self.us_stocks.empty:
            return []
        
        # 이름과 심볼로 검색
        query_lower = query.lower()
        mask = (
            self.us_stocks['Name'].str.lower().str.contains(query_lower, na=False) |
            self.us_stocks['Symbol'].str.lower().str.contains(query_lower, na=False)
        )
        
        results = self.us_stocks[mask].head(limit)
        
        return [
            StockSearchResult(
                symbol=row['Symbol'],
                name=row['Name'],
                market='NYSE/NASDAQ'
            )
            for _, row in results.iterrows()
        ]
    
    def search_stocks(self, query: str, market: str = 'all', limit: int = 20) -> List[StockSearchResult]:
        """주식 검색 (한국 + 미국)"""
        results = []
        
        if market in ['all', 'kr']:
            kr_results = self.search_kr_stocks(query, limit)
            results.extend(kr_results)
        
        if market in ['all', 'us']:
            us_results = self.search_us_stocks(query, limit)
            results.extend(us_results)
        
        # 결과 제한
        return results[:limit]
    
    def get_current_price(self, symbol: str, market: str = 'kr') -> Optional[float]:
        """현재 주가 조회"""
        try:
            if market == 'kr':
                # 한국 주식
                data = fdr.DataReader(symbol, '2024-01-01', '2024-12-31')
                if not data.empty:
                    return float(data['Close'].iloc[-1])
            elif market == 'us':
                # 미국 주식
                data = fdr.DataReader(symbol, '2024-01-01', '2024-12-31')
                if not data.empty:
                    return float(data['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
        
        return None

# 전역 인스턴스
stock_service = StockService()
