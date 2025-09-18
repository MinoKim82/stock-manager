import React, { useState, useEffect, useCallback } from 'react';
import { 
  Table, 
  Button, 
  Space, 
  Typography, 
  Card, 
  Modal, 
  Form, 
  Input, 
  Select, 
  InputNumber, 
  DatePicker,
  message, 
  Popconfirm,
  Row,
  Col,
  Tag
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined,
  SearchOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { transactionApi, accountApi, stockApi } from '../services/api';
import { Transaction, TransactionFormData, Account, StockSearchResult } from '../types';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Option } = Select;

const TransactionManagement: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
  const [stockSearchVisible, setStockSearchVisible] = useState(false);
  const [stockSearchResults, setStockSearchResults] = useState<StockSearchResult[]>([]);
  const [stockSearchLoading, setStockSearchLoading] = useState(false);
  const [filterVisible, setFilterVisible] = useState(false);
  const [form] = Form.useForm();
  const transactionType = Form.useWatch('transaction_type', form);

  const transactionTypes = [
    { value: '입금', label: '입금' },
    { value: '출금', label: '출금' },
    { value: '매수', label: '매수' },
    { value: '매도', label: '매도' },
    { value: '배당금', label: '배당금' },
    { value: '이자', label: '이자' },
  ];

  const currencies = [
    { value: 'KRW', label: 'KRW (원)' },
    { value: 'USD', label: 'USD (달러)' },
  ];

  const marketTypes = [
    { value: 'KRX', label: 'KRX (한국)' },
    { value: 'HKS', label: 'HKS (홍콩)' },
    { value: 'NYS', label: 'NYS (뉴욕)' },
    { value: 'NAS', label: 'NAS (나스닥)' },
    { value: 'AMS', label: 'AMS (아멕스)' },
    { value: 'TSE', label: 'TSE (도쿄)' },
    { value: 'SHS', label: 'SHS (상해)' },
    { value: 'SZS', label: 'SZS (심천)' },
    { value: 'SHI', label: 'SHI (상해지수)' },
    { value: 'SZI', label: 'SZI (심천지수)' },
    { value: 'HSX', label: 'HSX (호치민)' },
    { value: 'HNX', label: 'HNX (하노이)' },
    { value: 'BAY', label: 'BAY (뉴욕주간)' },
    { value: 'BAQ', label: 'BAQ (나스닥주간)' },
    { value: 'BAA', label: 'BAA (아멕스주간)' },
  ];

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [accountsData, transactionsData] = await Promise.all([
        accountApi.getAccounts(),
        transactionApi.getAllTransactions()
      ]);
      setAccounts(accountsData);
      setTransactions(transactionsData);
    } catch (error) {
      message.error('데이터를 불러오는데 실패했습니다.');
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreate = () => {
    setEditingTransaction(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleAccountChange = (accountId: number) => {
    const selectedAccount = accounts.find(acc => acc.id === accountId);
    if (selectedAccount) {
      form.setFieldsValue({
        transaction_currency: selectedAccount.currency
      });
    }
  };

  const handleEdit = (transaction: Transaction) => {
    setEditingTransaction(transaction);
    form.setFieldsValue({
      ...transaction,
      date: dayjs(transaction.date),
    });
    setModalVisible(true);
  };

  const handleDelete = async (transactionId: number) => {
    try {
      await transactionApi.deleteTransaction(transactionId);
      message.success('거래가 삭제되었습니다.');
      fetchData();
    } catch (error) {
      message.error('거래 삭제에 실패했습니다.');
      console.error('Error deleting transaction:', error);
    }
  };

  const handleSubmit = async (values: TransactionFormData) => {
    try {
      const payload: any = { ...values };

      if (values.transaction_type === '매수' || values.transaction_type === '매도') {
        delete payload.amount;
      } else if (values.transaction_type === '배당금') {
        delete payload.quantity;
        delete payload.price_per_share;
      } else {
        delete payload.stock_name;
        delete payload.stock_symbol;
        delete payload.market;
        delete payload.quantity;
        delete payload.price_per_share;
      }

      const submitData = {
        ...payload,
        date: values.date ? dayjs(values.date).toISOString() : new Date().toISOString(),
      };

      if (editingTransaction) {
        await transactionApi.updateTransaction(editingTransaction.id, submitData);
        message.success('거래가 수정되었습니다.');
      } else {
        await transactionApi.createTransaction(submitData);
        message.success('거래가 생성되었습니다.');
      }
      setModalVisible(false);
      fetchData();
    } catch (error) {
      message.error('거래 저장에 실패했습니다.');
      console.error('Error saving transaction:', error);
    }
  };

  const handleStockSearch = async (query: string) => {
    if (!query.trim()) return;
    
    try {
      setStockSearchLoading(true);
      setStockSearchVisible(true);
      const results = await stockApi.searchStocks(query);
      setStockSearchResults(results);
    } catch (error) {
      message.error('주식 검색에 실패했습니다.');
      console.error('Error searching stocks:', error);
    } finally {
      setStockSearchLoading(false);
    }
  };

  const handleStockSelect = (stock: StockSearchResult) => {
    form.setFieldsValue({
      stock_name: stock.name,
      stock_symbol: stock.symbol,
      market: stock.market,
    });
    setStockSearchVisible(false);
  };

  const handleRefreshCache = async () => {
    try {
      await stockApi.refreshCache();
      message.success('주식 캐시가 새로고침되었습니다.');
    } catch (error) {
      message.error('캐시 새로고침에 실패했습니다.');
      console.error('Error refreshing cache:', error);
    }
  };

  const formatCurrency = (amount: number | undefined | null, currency: string) => {
    if (amount === undefined || amount === null || isNaN(amount)) {
      return '-';
    }
    
    try {
      return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: currency,
      }).format(amount);
    } catch (error) {
      console.error('Currency formatting error:', error, { amount, currency });
      return amount.toString();
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  const getTransactionTypeColor = (type: string) => {
    switch (type) {
      case '매수':
        return 'green';
      case '매도':
        return 'red';
      case '입금':
        return 'blue';
      case '출금':
        return 'orange';
      case '배당금':
        return 'purple';
      case '이자':
        return 'cyan';
      default:
        return 'default';
    }
  };

  const getAccountName = (accountId: number) => {
    const account = accounts.find(acc => acc.id === accountId);
    return account ? `${account.owner_name} (${account.broker})` : '알 수 없음';
  };

  const columns = [
    {
      title: '날짜',
      dataIndex: 'date',
      key: 'date',
      render: (value: string) => formatDate(value),
      sorter: (a: Transaction, b: Transaction) => new Date(a.date).getTime() - new Date(b.date).getTime(),
      width: 100,
    },
    {
      title: '계좌',
      dataIndex: 'account_id',
      key: 'account_id',
      render: (accountId: number) => getAccountName(accountId),
      width: 150,
    },
    {
      title: '유형',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      render: (value: string) => (
        <Tag color={getTransactionTypeColor(value)}>
          {value}
        </Tag>
      ),
      width: 80,
    },
    {
      title: '종목명',
      dataIndex: 'stock_name',
      key: 'stock_name',
      render: (value: string, record: Transaction) => (
        <div>
          <div>{value || '-'}</div>
          {record.stock_symbol && (
            <div style={{ fontSize: '12px', color: '#666' }}>
              {record.stock_symbol}
            </div>
          )}
        </div>
      ),
      width: 120,
    },
    {
      title: '금액/가격',
      key: 'amount',
      render: (_: any, record: Transaction) => {
        if (record.total_amount) {
          return formatCurrency(record.total_amount, record.transaction_currency);
        }
        return record.amount ? formatCurrency(record.amount, record.transaction_currency) : '-';
      },
      width: 120,
    },
    {
      title: '수량',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (value: number) => value ? value.toLocaleString() : '-',
      width: 80,
    },
    {
      title: '수수료',
      key: 'fee',
      render: (value: any, record: Transaction) => {
        // 현금 거래의 경우 환전수수료 표시
        if (record.transaction_type === '입금' || record.transaction_type === '출금' || 
            record.transaction_type === '배당금' || record.transaction_type === '이자') {
          if (record.exchange_fee && record.exchange_fee > 0) {
            return formatCurrency(record.exchange_fee, 'KRW');
          }
          return '-';
        }
        // 주식 거래의 경우 수수료 표시
        else if (record.transaction_type === '매수' || record.transaction_type === '매도') {
          if (record.fee && record.fee > 0) {
            return formatCurrency(record.fee, record.transaction_currency);
          }
          return '-';
        }
        return '-';
      },
      width: 100,
    },
    {
      title: '작업',
      key: 'actions',
      render: (_: any, record: Transaction) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            수정
          </Button>
          <Popconfirm
            title="거래를 삭제하시겠습니까?"
            onConfirm={() => handleDelete(record.id)}
            okText="예"
            cancelText="아니오"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              삭제
            </Button>
          </Popconfirm>
        </Space>
      ),
      width: 120,
    },
  ];

  return (
    <div>
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={2} style={{ margin: 0 }}>거래 관리</Title>
          <Space>
            <Button 
              icon={<FilterOutlined />} 
              onClick={() => setFilterVisible(!filterVisible)}
            >
              필터
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              거래 추가
            </Button>
            <Button onClick={handleRefreshCache} title="주식 데이터 캐시 새로고침">
              캐시 새로고침
            </Button>
          </Space>
        </div>

        {filterVisible && (
          <Card size="small" style={{ marginBottom: 16, background: '#f5f5f5' }}>
            <Row gutter={16}>
              <Col span={6}>
                <Select placeholder="거래 유형" style={{ width: '100%' }} allowClear>
                  {transactionTypes.map(type => (
                    <Option key={type.value} value={type.value}>
                      {type.label}
                    </Option>
                  ))}
                </Select>
              </Col>
              <Col span={6}>
                <Select placeholder="계좌" style={{ width: '100%' }} allowClear>
                  {accounts.map(account => (
                    <Option key={account.id} value={account.id}>
                      {account.owner_name} ({account.broker})
                    </Option>
                  ))}
                </Select>
              </Col>
              <Col span={6}>
                <DatePicker.RangePicker style={{ width: '100%' }} placeholder={['시작일', '종료일']} />
              </Col>
              <Col span={6}>
                <Button type="primary" icon={<SearchOutlined />} style={{ width: '100%' }}>
                  검색
                </Button>
              </Col>
            </Row>
          </Card>
        )}

        <Table
          columns={columns}
          dataSource={transactions}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20, showSizeChanger: true }}
          scroll={{ x: 1000 }}
        />
      </Card>

      <Modal
        title={editingTransaction ? '거래 수정' : '거래 추가'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="account_id"
                label="계좌"
                rules={[{ required: true, message: '계좌를 선택해주세요.' }]}
              >
                <Select onChange={handleAccountChange}>
                  {accounts.map(account => (
                    <Option key={account.id} value={account.id}>
                      {account.owner_name} ({account.broker}) - {account.account_type} [{account.currency}]
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="transaction_type"
                label="거래 유형"
                rules={[{ required: true, message: '거래 유형을 선택해주세요.' }]}
              >
                <Select>
                  {transactionTypes.map(type => (
                    <Option key={type.value} value={type.value}>
                      {type.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="date"
                label="날짜"
                rules={[{ required: true, message: '날짜를 선택해주세요.' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              {['입금', '출금', '이자', '배당금'].includes(transactionType) && (
                <Form.Item
                  name="amount"
                  label="금액"
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                    parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                  />
                </Form.Item>
              )}
            </Col>
          </Row>

          {['매수', '매도', '배당금'].includes(transactionType) && (
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="stock_name" label="주식명">
                  <Input.Search
                    placeholder="주식명을 입력하세요"
                    enterButton={<SearchOutlined />}
                    onSearch={handleStockSearch}
                  />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name="stock_symbol" label="주식 심볼">
                  <Input disabled />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name="market" label="거래소">
                  <Select>
                    {marketTypes.map(market => (
                      <Option key={market.value} value={market.value}>
                        {market.label}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          )}

          {['매수', '매도'].includes(transactionType) && (
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="quantity" label="수량">
                  <InputNumber
                    style={{ width: '100%' }}
                    formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                    parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="price_per_share" label="주당 가격">
                  <InputNumber
                    style={{ width: '100%' }}
                    formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                    parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                  />
                </Form.Item>
              </Col>
            </Row>
          )}

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="fee"
                label="수수료"
                initialValue={0}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="transaction_currency"
                label="거래 통화"
                rules={[{ required: true, message: '거래 통화를 선택해주세요.' }]}
                help="계좌 선택 시 자동으로 설정됩니다"
              >
                <Select>
                  {currencies.map(currency => (
                    <Option key={currency.value} value={currency.value}>
                      {currency.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="exchange_rate"
            label="환율 (해당시)"
          >
            <InputNumber
              style={{ width: '100%' }}
              formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="주식 검색"
        open={stockSearchVisible}
        onCancel={() => setStockSearchVisible(false)}
        footer={null}
        width={600}
      >
        <div>
          {stockSearchLoading ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              검색 중...
            </div>
          ) : stockSearchResults.length > 0 ? (
            stockSearchResults.map((stock) => (
              <div
                key={stock.symbol}
                style={{
                  padding: '8px',
                  border: '1px solid #d9d9d9',
                  marginBottom: '8px',
                  cursor: 'pointer',
                  borderRadius: '4px',
                }}
                onClick={() => handleStockSelect(stock)}
              >
                <div><strong>{stock.name}</strong></div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  {stock.symbol} - {stock.market}
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
              검색 결과가 없습니다.
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default TransactionManagement;
