import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Typography, Button, Descriptions, Spin, Alert, Row, Col, Statistic } from 'antd';
import { ArrowLeftOutlined, TransactionOutlined } from '@ant-design/icons';
import { accountApi, transactionApi } from '../services/api';
import { Account, Transaction } from '../types';

const { Title } = Typography;

const AccountDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [account, setAccount] = useState<Account | null>(null);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAccountDetail = useCallback(async () => {
    try {
      setLoading(true);
      const [accountData, transactionsData] = await Promise.all([
        accountApi.getAccount(Number(id)),
        transactionApi.getTransactions(Number(id), {})
      ]);
      setAccount(accountData);
      setRecentTransactions(transactionsData.slice(0, 5)); // 최근 5개 거래만 표시
    } catch (err) {
      setError('계좌 정보를 불러오는데 실패했습니다.');
      console.error('Error fetching account detail:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      fetchAccountDetail();
    }
  }, [id, fetchAccountDetail]);

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !account) {
    return <Alert message="오류" description={error || '계좌를 찾을 수 없습니다.'} type="error" showIcon />;
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/accounts')}>
          계좌 목록으로 돌아가기
        </Button>
      </div>

      <Title level={2}>계좌 상세 정보</Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="현재 잔액"
              value={account.current_balance}
              formatter={(value) => formatCurrency(Number(value), account.currency)}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="계좌 유형"
              value={account.account_type}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="통화"
              value={account.currency}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="계좌 정보">
            <Descriptions column={1}>
              <Descriptions.Item label="소유자">{account.owner_name}</Descriptions.Item>
              <Descriptions.Item label="증권사">{account.broker}</Descriptions.Item>
              <Descriptions.Item label="계좌번호">{account.account_number}</Descriptions.Item>
              <Descriptions.Item label="계좌유형">{account.account_type}</Descriptions.Item>
              <Descriptions.Item label="잔액">
                {formatCurrency(account.current_balance, account.currency)}
              </Descriptions.Item>
              <Descriptions.Item label="통화">{account.currency}</Descriptions.Item>
              <Descriptions.Item label="생성일">
                {formatDate(account.created_at)}
              </Descriptions.Item>
              <Descriptions.Item label="수정일">
                {formatDate(account.updated_at)}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col span={12}>
          <Card 
            title="최근 거래 내역"
            extra={
              <Button 
                type="primary" 
                icon={<TransactionOutlined />}
                onClick={() => navigate(`/accounts/${id}/transactions`)}
              >
                전체 거래 보기
              </Button>
            }
          >
            {recentTransactions.length > 0 ? (
              <div>
                {recentTransactions.map((transaction) => (
                  <div key={transaction.id} style={{ marginBottom: 8, padding: 8, background: '#f5f5f5', borderRadius: 4 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>{transaction.transaction_type}</span>
                      <span>{formatDate(transaction.date)}</span>
                    </div>
                    {transaction.stock_name && (
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        {transaction.stock_name} ({transaction.stock_symbol})
                      </div>
                    )}
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      {transaction.total_amount && formatCurrency(transaction.total_amount, transaction.transaction_currency)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', color: '#999' }}>
                거래 내역이 없습니다.
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AccountDetail;
