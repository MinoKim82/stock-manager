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
import requests
from dotenv import load_dotenv
import yfinance as yf

load_dotenv() # .env 파일 로드

logger = logging.getLogger(__name__)

class StockService:
    def __init__(self):
        self.kr_stocks = None
        self.kr_etfs = None
        self.us_stocks = None
        self.us_etfs = None
        self.cache_dir = "stock_cache"
        self.cache_duration = timedelta(days=1)  # 1일 캐시

        self.KIS_APP_KEY = os.getenv("KIS_APP_KEY")
        self.KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")
        self.KIS_BASE_URL = "https://openapivts.koreainvestment.com:29443" # 모의투자 서버 URL
        self.KIS_ACCESS_TOKEN = None
        self.KIS_TOKEN_EXPIRED_AT = None
        
        # 캐시 디렉토리 생성
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # 초기화 시 토큰 캐시 로드
        self._load_token_cache()

    def _load_token_cache(self):
        """토큰 캐시 파일에서 토큰 정보 로드"""
        token_cache_file = os.path.join(self.cache_dir, "kis_token.pkl")
        try:
            if os.path.exists(token_cache_file):
                with open(token_cache_file, 'rb') as f:
                    token_data = pickle.load(f)
                    self.KIS_ACCESS_TOKEN = token_data.get('access_token')
                    self.KIS_TOKEN_EXPIRED_AT = token_data.get('expired_at')
                    logger.info("KIS Access Token loaded from cache.")
                    return True
        except Exception as e:
            logger.warning(f"Failed to load token cache: {e}")
        return False

    def _save_token_cache(self, access_token: str, expired_at: datetime):
        """토큰 정보를 캐시 파일에 저장"""
        token_cache_file = os.path.join(self.cache_dir, "kis_token.pkl")
        try:
            token_data = {
                'access_token': access_token,
                'expired_at': expired_at
            }
            with open(token_cache_file, 'wb') as f:
                pickle.dump(token_data, f)
            logger.info("KIS Access Token saved to cache.")
        except Exception as e:
            logger.error(f"Failed to save token cache: {e}")

    def _clear_token_cache(self):
        """토큰 캐시 파일 삭제"""
        token_cache_file = os.path.join(self.cache_dir, "kis_token.pkl")
        try:
            if os.path.exists(token_cache_file):
                os.remove(token_cache_file)
                logger.info("KIS Access Token cache cleared.")
        except Exception as e:
            logger.error(f"Failed to clear token cache: {e}")

    def get_token_status(self):
        """토큰 상태 정보 반환"""
        if not self.KIS_ACCESS_TOKEN or not self.KIS_TOKEN_EXPIRED_AT:
            return {
                "has_token": False,
                "expired_at": None,
                "is_valid": False,
                "time_remaining": None
            }
        
        now = datetime.now()
        is_valid = now < self.KIS_TOKEN_EXPIRED_AT
        time_remaining = (self.KIS_TOKEN_EXPIRED_AT - now).total_seconds() if is_valid else 0
        
        return {
            "has_token": True,
            "expired_at": self.KIS_TOKEN_EXPIRED_AT.isoformat(),
            "is_valid": is_valid,
            "time_remaining": time_remaining
        }

    def _get_kis_access_token(self):
        """한국투자증권 API 접근 토큰 발급 및 관리 (파일 캐싱)"""
        # 캐시에서 토큰 로드 시도
        if not self.KIS_ACCESS_TOKEN or not self.KIS_TOKEN_EXPIRED_AT:
            self._load_token_cache()
        
        # 유효한 토큰이 있으면 반환
        if self.KIS_ACCESS_TOKEN and self.KIS_TOKEN_EXPIRED_AT and datetime.now() < self.KIS_TOKEN_EXPIRED_AT:
            return self.KIS_ACCESS_TOKEN

        if not self.KIS_APP_KEY or not self.KIS_APP_SECRET:
            logger.error("KIS_APP_KEY or KIS_APP_SECRET is not set in .env")
            return None

        # 새 토큰 발급
        url = f"{self.KIS_BASE_URL}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.KIS_APP_KEY,
            "appsecret": self.KIS_APP_SECRET
        }
        try:
            res = requests.post(url, headers=headers, data=json.dumps(body))
            res.raise_for_status()
            response_data = res.json()
            access_token = response_data["access_token"]
            expires_in = response_data["expires_in"] # 초 단위
            expired_at = datetime.now() + timedelta(seconds=expires_in - 60) # 1분 여유
            
            # 토큰 정보 저장
            self.KIS_ACCESS_TOKEN = access_token
            self.KIS_TOKEN_EXPIRED_AT = expired_at
            self._save_token_cache(access_token, expired_at)
            
            logger.info("KIS Access Token issued and cached successfully.")
            return self.KIS_ACCESS_TOKEN
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting KIS access token: {e}")
            # 토큰 발급 실패 시 캐시 삭제
            self._clear_token_cache()
            return None

    def _get_kis_current_price(self, symbol: str) -> Optional[float]:
        """한국투자증권 API를 이용한 현재가 조회"""
        token = self._get_kis_access_token()
        if not token:
            return None

        url = f"{self.KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.KIS_APP_KEY,
            "appsecret": self.KIS_APP_SECRET,
            "tr_id": "FHKST01010100" # 주식 현재가 시세
        }
        params = {
            "fid_cond_mrkt_div_code": "J", # 주식 시장 구분 (J: 주식)
            "fid_input_iscd": symbol # 종목코드
        }

        try:
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            response_data = res.json()

            if response_data and response_data["rt_cd"] == "0": # 성공
                current_price = float(response_data["output"]["stck_prpr"])
                logger.info(f"KIS Current price for {symbol}: {current_price}")
                return current_price
            else:
                logger.error(f"KIS API error for {symbol}: {response_data.get('msg1')}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting KIS current price for {symbol}: {e}")
            return None
    
    def _get_kis_current_price_us(self, symbol: str, exchange: str) -> Optional[float]:
        """한국투자증권 API를 이용한 해외 주식 현재가 조회"""
        token = self._get_kis_access_token()
        if not token:
            return None

        # KIS API는 해외주식 현재가를 조회하기 위해 다른 URL과 tr_id를 사용합니다.
        url = f"{self.KIS_BASE_URL}/uapi/overseas-price/v1/quotations/price"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.KIS_APP_KEY,
            "appsecret": self.KIS_APP_SECRET,
            "tr_id": "HHDFS00000300"  # 해외주식 현재체결가
        }
        params = {
            "AUTH": "",  # URL 인코딩 문제 방지를 위해 빈 값으로 설정 (헤더에 토큰 사용)
            "EXCD": exchange,  # 거래소 코드 (NAS: 나스닥, NYS: 뉴욕, AMS: 아멕스)
            "SYMB": symbol  # 종목 코드
        }

        try:
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            response_data = res.json()

            if response_data and response_data.get("rt_cd") == "0":
                # 해외주식 API의 가격 필드는 'last' 입니다.
                current_price = float(response_data["output"]["last"])
                logger.info(f"KIS Current price for {symbol} ({exchange}): {current_price}")
                return current_price
            else:
                logger.error(f"KIS API error for {symbol}: {response_data.get('msg1')}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting KIS current price for {symbol}: {e}")
            return None
        except (KeyError, TypeError) as e:
            logger.error(f"Failed to parse KIS API response for {symbol}: {e}")
            return None

    def _get_us_stock_exchange(self, symbol: str) -> Optional[str]:
        """심볼로 미국 주식의 거래소 코드를 찾아 KIS API 형식으로 반환합니다."""
        self._load_us_stocks()
        if self.us_stocks is None:
            return None
        
        stock_info = self.us_stocks[self.us_stocks['Symbol'] == symbol]
        if not stock_info.empty:
            exchange = stock_info.iloc[0]['Market']
            if exchange == 'NYSE':
                return 'NYS'
            elif exchange == 'NASDAQ':
                return 'NAS'
            elif exchange == 'AMEX':
                return 'AMS'
            else:
                logger.warning(f"Unknown exchange '{exchange}' for symbol {symbol}")
                return None
        return None

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

    def _load_kr_etfs(self):
        """한국 etf 목록 로드 (캐싱 적용)"""
        if self.kr_etfs is not None:
            return
            
        cache_file = os.path.join(self.cache_dir, "kr_etfs.pkl")
        
        # 캐시가 유효한지 확인
        if self._is_cache_valid(cache_file):
            logger.info("Loading Korean etfs from cache")
            self.kr_etfs = self._load_from_cache(cache_file)
            if self.kr_etfs is not None:
                return
        
        # 캐시가 없거나 만료된 경우 API에서 로드
        try:
            logger.info("Loading Korean etfs from API")
            self.kr_etfs = fdr.StockListing('ETF/KR')

            # 컬럼명 정규화 (FinanceDataReader는 'Code'와 'Name' 사용)
            if 'Code' in self.kr_etfs.columns:
                self.kr_etfs = self.kr_etfs.rename(columns={'Code': 'Symbol'})
            
            logger.info(f"Loaded {len(self.kr_etfs)} Korean etf from API")
            
            # 캐시에 저장
            self._save_to_cache(self.kr_etfs, cache_file)
            
        except Exception as e:
            logger.error(f"Error loading Korean etfs: {e}")

    def _load_us_stocks(self):
        """미국 주식 목록 로드 (NYSE, NASDAQ, AMEX) (캐싱 적용)"""
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
            nyse = fdr.StockListing('NYSE')
            nyse['Market'] = 'NYS'
            nasdaq = fdr.StockListing('NASDAQ')
            nasdaq['Market'] = 'NAS'
            amex = fdr.StockListing('AMEX')
            amex['Market'] = 'AMS'
            
            self.us_stocks = pd.concat([nyse, nasdaq, amex], ignore_index=True)
            
            # 컬럼명 정규화 (FinanceDataReader는 'Code'와 'Name' 사용)
            if 'Code' in self.us_stocks.columns:
                self.us_stocks = self.us_stocks.rename(columns={'Code': 'Symbol'})
            
            logger.info(f"Loaded {len(self.us_stocks)} US stocks from API")
            
            # 캐시에 저장
            self._save_to_cache(self.us_stocks, cache_file)
            
        except Exception as e:
            logger.error(f"Error loading US stocks: {e}")

    def _load_us_etfs(self):
        """미국 etf 목록 로드 """
        if self.us_etfs is not None:
            return
            
        cache_file = os.path.join(self.cache_dir, "us_etfs.pkl")
        
        # 캐시가 유효한지 확인
        if self._is_cache_valid(cache_file):
            logger.info("Loading US etfs from cache")
            self.us_etfs = self._load_from_cache(cache_file)
            if self.us_etfs is not None:
                return
        
        # 캐시가 없거나 만료된 경우 API에서 로드
        try:
            logger.info("Loading US etfs from API")
            self.us_etfs = fdr.StockListing('ETF/US')

            # 컬럼명 정규화 (FinanceDataReader는 'Code'와 'Name' 사용)
            if 'Code' in self.us_etfs.columns:
                self.us_etfs = self.us_etfs.rename(columns={'Code': 'Symbol'})
            
            logger.info(f"Loaded {len(self.us_etfs)} US etfs from API")
            
            # 캐시에 저장
            self._save_to_cache(self.us_etfs, cache_file)
            
        except Exception as e:
            logger.error(f"Error loading US etfs: {e}")
    
    def search_kr_stocks(self, query: str, limit: int = 20) -> List[StockSearchResult]:
        """한국 주식 검색"""
        self._load_kr_stocks()
        
        if self.kr_stocks is None or self.kr_stocks.empty:
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

    def search_kr_etfs(self, query: str, limit: int = 20) -> List[StockSearchResult]:
        """한국 etf 검색"""
        self._load_kr_etfs()
        
        if self.kr_etfs is None or self.kr_etfs.empty:
            return []
        
        # 이름과 심볼로 검색
        query_lower = query.lower()
        mask = (
            self.kr_etfs['Name'].str.lower().str.contains(query_lower, na=False) |
            self.kr_etfs['Symbol'].str.lower().str.contains(query_lower, na=False)
        )
        
        results = self.kr_etfs[mask].head(limit)
        
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

        if self.us_stocks is None or self.us_stocks.empty:
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
                market=row['Market']
            )
            for _, row in results.iterrows()
        ]
    
    def search_us_etfs(self, query: str, limit: int = 20) -> List[StockSearchResult]:
        """미국 etf 검색"""
        self._load_us_etfs()

        if self.us_etfs is None or self.us_etfs.empty:
            return []
        
        # 이름과 심볼로 검색
        query_lower = query.lower()
        mask = (
            self.us_etfs['Name'].str.lower().str.contains(query_lower, na=False) |
            self.us_etfs['Symbol'].str.lower().str.contains(query_lower, na=False)
        )
        
        results = self.us_etfs[mask].head(limit)

        return [
            StockSearchResult(
                symbol=row['Symbol'],
                name=row['Name'],
                market='NYS'
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

        if market in ['all', 'kr']:
            kr_etf_results = self.search_kr_etfs(query, limit)
            results.extend(kr_etf_results)
        
        if market in ['all', 'us']:
            us_etf_results = self.search_us_etfs(query, limit)
            results.extend(us_etf_results)
        
        # 결과 제한
        return results[:limit]
    
    def get_current_price(self, symbol: str, market: str = 'kr') -> Optional[float]:
        """현재 주가 조회"""
        try:
            if market == 'kr':
                # 한국 주식 (KIS API 사용)
                return self._get_kis_current_price(symbol)
            elif market == 'us':
                # 미국 주식 (KIS API 사용)
                exchange = self._get_us_stock_exchange(symbol)
                if exchange:
                    price = self._get_kis_current_price_us(symbol, exchange)
                    if price is not None:
                        return price

                # KIS API 실패 시 yfinance로 대체
                logger.warning(f"Failed to get price for {symbol} via KIS API. Falling back to yfinance.")
                ticker = yf.Ticker(symbol)
                todays_data = ticker.history(period='1d')
                if not todays_data.empty:
                    return float(todays_data['Close'].iloc[-1])
                else:
                    logger.error(f"Could not get price from yfinance for {symbol}")
                    return None

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
