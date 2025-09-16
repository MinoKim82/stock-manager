import React, { useState, useEffect } from 'react';
import { Card, Table, Typography, Statistic, Row, Col, Spin, Alert } from 'antd';
import { portfolioApi } from '../services/api';
import { PortfolioSummary as PortfolioSummaryType } from '../types';

const { Title } = Typography;

const PortfolioSummary: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioSummaryType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPortfolioSummary();
  }, []);

  const fetchPortfolioSummary = async () => {
    try {
      setLoading(true);
      const data = await portfolioApi.getPortfolioSummary();
      setPortfolio(data);
    } catch (err) {
      setError('포트폴리오 정보를 불러오는데 실패했습니다.');
      console.error('Error fetching portfolio summary:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number, currency: string = 'KRW') => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const columns = [
    {
      title: '종목명',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '심볼',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '보유수량',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (value: number) => value.toLocaleString(),
    },
    {
      title: '평균단가',
      dataIndex: 'average_cost',
      key: 'average_cost',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '현재가',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '평가금액',
      dataIndex: 'current_value',
      key: 'current_value',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '손익',
      dataIndex: 'profit_loss',
      key: 'profit_loss',
      render: (value: number) => (
        <span style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {formatCurrency(value)}
        </span>
      ),
    },
    {
      title: '수익률',
      dataIndex: 'profit_loss_rate',
      key: 'profit_loss_rate',
      render: (value: number) => (
        <span style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {formatPercentage(value)}
        </span>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return <Alert message="오류" description={error} type="error" showIcon />;
  }

  if (!portfolio) {
    return <Alert message="포트폴리오 정보가 없습니다." type="info" showIcon />;
  }

  return (
    <div>
      <Title level={2}>포트폴리오 요약</Title>
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="총 현금"
              value={portfolio.total_cash}
              formatter={(value) => formatCurrency(Number(value))}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="총 주식 가치"
              value={portfolio.total_stock_value}
              formatter={(value) => formatCurrency(Number(value))}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="총 포트폴리오 가치"
              value={portfolio.total_portfolio_value}
              formatter={(value) => formatCurrency(Number(value))}
            />
          </Card>
        </Col>
      </Row>

      <Card title="보유 주식">
        <Table
          columns={columns}
          dataSource={portfolio.holdings}
          rowKey="symbol"
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default PortfolioSummary;
