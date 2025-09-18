# 주식 관리 시스템

나와 가족의 증권 계좌 및 주식을 관리하는 백엔드와 프론트엔드 서비스입니다.

## 기능

### 계좌 관리
- 여러 증권사의 계좌 관리
- 계좌 유형: 연금계좌, IRP계좌, ISA계좌, CMA계좌, 종합매매계좌, 미국주식계좌
- 계좌별 잔액 및 통화 관리

### 거래 관리
- **현금 거래**: 입금, 출금, 배당금, 이자 거래 기록
- **주식 거래**: 매수, 매도 거래 전용 관리
- **주식 보유 현황**: 실시간 보유 주식 수량 및 평균 단가 관리
- 다중 통화 지원 (KRW, USD)
- 거래 내역 필터링 및 검색

### 주식 검색
- 한국 주식 및 미국 주식 검색
- FinanceDataReader를 통한 실시간 주가 조회
- 주식 선택 시 자동 입력

### 포트폴리오 요약
- 전체 계좌 현금 잔액
- 보유 주식 평가금액
- 손익 및 수익률 계산

## 기술 스택

### Backend
- FastAPI
- PostgreSQL
- SQLAlchemy
- FinanceDataReader
- Pydantic

### Frontend
- React 18
- TypeScript
- Ant Design
- Axios
- React Router

## 설치 및 실행

### 1. 데이터베이스 설정
PostgreSQL 데이터베이스가 실행 중이어야 합니다.
- Host: 192.168.0.100:5432
- Database: stock-db
- Username: postgres
- Password: H1svy8e4CV1XiP3NigV4

### 1-1. 데이터베이스 마이그레이션 (기존 사용자)
기존 데이터베이스에서 주식 관련 데이터를 분리하는 마이그레이션이 필요합니다.

**⚠️ 중요: 마이그레이션 전에 데이터베이스 백업을 권장합니다.**

```bash
cd backend
python migrate_database.py [데이터베이스_경로]
```

마이그레이션 스크립트는 다음 작업을 수행합니다:
1. 기존 `transactions` 테이블에서 주식 거래 데이터 추출
2. 새로운 `stock_transactions` 테이블 생성 및 데이터 이동
3. 새로운 `stock_holdings` 테이블 생성 및 보유 현황 계산
4. 기존 `transactions` 테이블에서 주식 관련 컬럼 제거
5. 모든 계좌의 잔액 재계산

### 2. Backend 실행
```bash
cd backend
pip install -r requirements.txt
python run.py
```

Backend 서비스는 http://localhost:8000에서 실행됩니다.

### 3. Frontend 실행
```bash
cd frontend
npm install
npm start
```

Frontend 서비스는 http://localhost:3000에서 실행됩니다.

## API 문서

Backend 서비스 실행 후 http://localhost:8000/docs에서 Swagger UI를 통해 API 문서를 확인할 수 있습니다.

## 주요 엔드포인트

### 계좌 관리
- `GET /accounts/` - 계좌 목록 조회
- `POST /accounts/` - 계좌 생성
- `GET /accounts/{id}` - 계좌 상세 조회
- `PUT /accounts/{id}` - 계좌 수정
- `DELETE /accounts/{id}` - 계좌 삭제

### 현금 거래 관리
- `GET /accounts/{id}/transactions/` - 현금 거래 목록 조회
- `POST /transactions/` - 현금 거래 생성
- `PUT /transactions/{id}` - 현금 거래 수정
- `DELETE /transactions/{id}` - 현금 거래 삭제

### 주식 거래 관리
- `GET /accounts/{id}/stock-transactions/` - 주식 거래 목록 조회
- `POST /stock-transactions/` - 주식 거래 생성
- `PUT /stock-transactions/{id}` - 주식 거래 수정
- `DELETE /stock-transactions/{id}` - 주식 거래 삭제

### 주식 보유 현황
- `GET /accounts/{id}/stock-holdings/` - 주식 보유 현황 조회
- `GET /accounts/{id}/stock-holdings/{symbol}` - 특정 주식 보유 현황 조회
- `PUT /accounts/{id}/stock-holdings/{symbol}` - 주식 보유 현황 수정
- `DELETE /accounts/{id}/stock-holdings/{symbol}` - 주식 보유 현황 삭제

### 주식 검색
- `GET /stocks/search` - 주식 검색
- `GET /stocks/price/{symbol}` - 주가 조회

### 포트폴리오
- `GET /portfolio/summary` - 포트폴리오 요약

## 데이터베이스 구조

### 테이블 구성
- **accounts**: 계좌 정보 (기존과 동일)
- **transactions**: 현금 거래만 (입금, 출금, 배당금, 이자)
- **stock_transactions**: 주식 거래 전용 (매수, 매도)
- **stock_holdings**: 주식 보유 현황 (수량, 평균 단가, 총 매입가)

### 주요 변경사항
1. **데이터 분리**: 주식 거래와 현금 거래를 별도 테이블로 분리
2. **보유 현황 관리**: 실시간 주식 보유 수량 및 평균 단가 자동 계산
3. **성능 최적화**: 주식 관련 쿼리 성능 향상을 위한 인덱스 추가
4. **데이터 무결성**: 주식 거래 시 자동으로 보유 현황 업데이트

## 프로젝트 구조

```
stock_manager/
├── backend/
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── models.py            # 데이터베이스 모델
│   ├── schemas.py           # Pydantic 스키마
│   ├── crud.py              # 데이터베이스 CRUD 작업
│   ├── stock_service.py     # 주식 검색 서비스
│   ├── database.py          # 데이터베이스 연결
│   ├── config.py            # 설정
│   ├── migrate_database.py  # 데이터베이스 마이그레이션 스크립트
│   ├── requirements.txt     # Python 의존성
│   └── run.py               # 실행 스크립트
├── frontend/
│   ├── src/
│   │   ├── components/      # React 컴포넌트
│   │   ├── pages/           # 페이지 컴포넌트
│   │   ├── services/        # API 서비스
│   │   ├── types/           # TypeScript 타입 정의
│   │   └── App.tsx          # 메인 앱 컴포넌트
│   └── package.json         # Node.js 의존성
└── README.md
```