import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Col
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  ArrowLeftOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { transactionApi, accountApi, stockApi } from '../services/api';
import { Transaction, TransactionFormData, Account, StockSearchResult } from '../types';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Option } = Select;

const TransactionList: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
  const [stockSearchVisible, setStockSearchVisible] = useState(false);
  const [stockSearchResults, setStockSearchResults] = useState<StockSearchResult[]>([]);
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

  const cashTransactionTypes = [
    { value: '입금', label: '입금' },
    { value: '출금', label: '출금' },
    { value: '배당금', label: '배당금' },
    { value: '이자', label: '이자' },
  ];

  const stockTransactionTypes = [
    { value: '매수', label: '매수' },
    { value: '매도', label: '매도' },
    { value: '배당금', label: '배당금' },
  ];

  const currencies = [
    { value: 'KRW', label: 'KRW (원)' },
    { value: 'USD', label: 'USD (달러)' },
  ];


  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [accountData, transactionsData] = await Promise.all([
        accountApi.getAccount(Number(id)),
        transactionApi.getTransactions(Number(id), {})
      ]);
      setAccount(accountData);
      setTransactions(transactionsData);
    } catch (error) {
      message.error('데이터를 불러오는데 실패했습니다.');
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      fetchData();
    }
  }, [id, fetchData]);

  const handleCreate = () => {
    setEditingTransaction(null);
    form.resetFields();
    form.setFieldsValue({ account_id: Number(id), transaction_currency: account?.currency || 'KRW' });
    setModalVisible(true);
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
    setStockSearchVisible(true);
    try {
      const results = await stockApi.searchStocks(query);
      setStockSearchResults(results);
    } catch (error) {
      message.error('주식 검색에 실패했습니다.');
      console.error('Error searching stocks:', error);
    }
  };

  const handleStockSelect = (stock: StockSearchResult) => {
    form.setFieldsValue({
      stock_name: stock.name,
      stock_symbol: stock.symbol,
    });
    setStockSearchVisible(false);
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
        return '#52c41a';
      case '매도':
        return '#ff4d4f';
      case '입금':
        return '#1890ff';
      case '출금':
        return '#fa8c16';
      default:
        return '#666';
    }
  };

  const columns = [
    {
      title: '날짜',
      dataIndex: 'date',
      key: 'date',
      render: (value: string) => formatDate(value),
      sorter: (a: Transaction, b: Transaction) => new Date(a.date).getTime() - new Date(b.date).getTime(),
    },
    {
      title: '유형',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      render: (value: string) => (
        <span style={{ color: getTransactionTypeColor(value) }}>
          {value}
        </span>
      ),
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
    },
    {
      title: '수량',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (value: number) => value ? value.toLocaleString() : '-',
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
    },
    {
      title: '설명',
      dataIndex: 'description',
      key: 'description',
      render: (value: string) => value || '-',
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
    },
  ];

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '50px' }}>Loading...</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/accounts/${id}`)}>
          계좌 상세로 돌아가기
        </Button>
      </div>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={2} style={{ margin: 0 }}>
            거래 내역 - {account?.owner_name} ({account?.account_type})
          </Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            거래 추가
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={transactions}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
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
          <Form.Item name="account_id" hidden>
            <Input />
          </Form.Item>
          <Row gutter={16}>
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
            <Col span={12}>
              <Form.Item
                name="date"
                label="날짜"
                rules={[{ required: true, message: '날짜를 선택해주세요.' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
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

          {['입금', '출금', '이자', '배당금'].includes(transactionType) && (
            <Form.Item name="amount" label="금액">
              <InputNumber
                style={{ width: '100%' }}
                formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
              />
            </Form.Item>
          )}

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="transaction_currency"
                label="거래 통화"
                rules={[{ required: true, message: '거래 통화를 선택해주세요.' }]}
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
            <Col span={12}>
              <Form.Item name="exchange_rate" label="환율 (해당시)">
                <InputNumber
                  style={{ width: '100%' }}
                  formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                />
              </Form.Item>
            </Col>
          </Row>

          {/* 수수료 필드 - 거래 유형에 따라 동적 표시 */}
          <Form.Item shouldUpdate={(prevValues, currentValues) => 
            prevValues.transaction_type !== currentValues.transaction_type ||
            prevValues.account_id !== currentValues.account_id
          }>
            {({ getFieldValue }) => {
              const transactionType = getFieldValue('transaction_type');
              const accountId = getFieldValue('account_id');
              const selectedAccount = account;
              
              // 매수/매도: 수수료 표시
              if (transactionType === '매수' || transactionType === '매도') {
                return (
                  <Form.Item name="fee" label="수수료" initialValue={0}>
                    <InputNumber
                      style={{ width: '100%' }}
                      formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                );
              }
              // 해외 계좌 입금/출금: 환전수수료 표시
              else if ((transactionType === '입금' || transactionType === '출금') && selectedAccount?.currency === 'USD') {
                return (
                  <Form.Item name="exchange_fee" label="수수료 (환전수수료 - 원화)" initialValue={0}>
                    <InputNumber
                      style={{ width: '100%' }}
                      formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                );
              }
              // 배당금, 이자, 국내 계좌 입출금: 수수료 없음
              return null;
            }}
          </Form.Item>

          <Form.Item name="description" label="설명">
            <Input.TextArea rows={2} placeholder="거래에 대한 설명을 입력하세요" />
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
          {stockSearchResults.map((stock) => (
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
                  {stock.symbol}
                </div>
            </div>
          ))}
        </div>
      </Modal>
    </div>
  );
};

export default TransactionList;
