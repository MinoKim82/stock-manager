import FinanceDataReader as fdr
import pandas as pd
from typing import List, Optional
from schemas import StockSearchResult
import logging
import os
import pickle
import json
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StockService:
    def __init__(self):
        self.kr_stocks = None
        self.us_stocks = None
        self.cache_dir = "stock_cache"
        self.cache_duration = timedelta(days=1)  # 1일 캐시
        
        # 캐시 디렉토리 생성
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """캐시 파일이 유효한지 확인"""
        if not os.path.exists(cache_file):
            return False
        
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        return datetime.now() - cache_time < self.cache_duration
    
    def _load_from_cache(self, cache_file: str) -> Optional[pd.DataFrame]:
        """캐시에서 데이터 로드"""
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading cache {cache_file}: {e}")
            return None
    
    def _save_to_cache(self, data: pd.DataFrame, cache_file: str):
        """데이터를 캐시에 저장"""
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving cache {cache_file}: {e}")
    
    def _load_kr_stocks(self):
        """한국 주식 목록 로드 (캐싱 적용)"""
        if self.kr_stocks is not None:
            return
            
        cache_file = os.path.join(self.cache_dir, "kr_stocks.pkl")
        
        # 캐시가 유효한지 확인
        if self._is_cache_valid(cache_file):
            logger.info("Loading Korean stocks from cache")
            self.kr_stocks = self._load_from_cache(cache_file)
            if self.kr_stocks is not None:
                return
        
        # 캐시가 없거나 만료된 경우 API에서 로드
        try:
            logger.info("Loading Korean stocks from API")
            self.kr_stocks = fdr.StockListing('KRX')

            # 컬럼명 정규화 (FinanceDataReader는 'Code'와 'Name' 사용)
            if 'Code' in self.kr_stocks.columns:
                self.kr_stocks = self.kr_stocks.rename(columns={'Code': 'Symbol'})
            
            logger.info(f"Loaded {len(self.kr_stocks)} Korean stocks from API")
            
            # 캐시에 저장
            self._save_to_cache(self.kr_stocks, cache_file)
            
        except Exception as e:
            logger.error(f"Error loading Korean stocks: {e}")
    
    def _load_us_stocks(self):
        """미국 주식 목록 로드 (S&P 500) (캐싱 적용)"""
        if self.us_stocks is not None:
            return
            
        cache_file = os.path.join(self.cache_dir, "us_stocks.pkl")
        
        # 캐시가 유효한지 확인
        if self._is_cache_valid(cache_file):
            logger.info("Loading US stocks from cache")
            self.us_stocks = self._load_from_cache(cache_file)
            if self.us_stocks is not None:
                return
        
        # 캐시가 없거나 만료된 경우 API에서 로드
        try:
            logger.info("Loading US stocks from API")
            self.us_stocks = fdr.StockListing('NYSE')
            print(self.us_stocks.head())
            
            # 컬럼명 정규화 (FinanceDataReader는 'Code'와 'Name' 사용)
            if 'Code' in self.us_stocks.columns:
                self.us_stocks = self.us_stocks.rename(columns={'Code': 'Symbol'})
            
            logger.info(f"Loaded {len(self.us_stocks)} US stocks from API")
            
            # 캐시에 저장
            self._save_to_cache(self.us_stocks, cache_file)
            
        except Exception as e:
            logger.error(f"Error loading US stocks: {e}")
    
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
    
    def clear_cache(self):
        """캐시 초기화"""
        try:
            kr_cache = os.path.join(self.cache_dir, "kr_stocks.pkl")
            us_cache = os.path.join(self.cache_dir, "us_stocks.pkl")
            
            if os.path.exists(kr_cache):
                os.remove(kr_cache)
            if os.path.exists(us_cache):
                os.remove(us_cache)
                
            self.kr_stocks = None
            self.us_stocks = None
            
            logger.info("Stock cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def refresh_cache(self):
        """캐시 강제 새로고침"""
        self.clear_cache()
        self._load_kr_stocks()
        self._load_us_stocks()

# 전역 인스턴스
stock_service = StockService()
