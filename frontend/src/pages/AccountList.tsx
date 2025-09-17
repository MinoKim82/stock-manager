import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Typography, Card, Modal, Form, Input, Select, InputNumber, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { accountApi } from '../services/api';
import { Account, AccountFormData } from '../types';

const { Title } = Typography;
const { Option } = Select;

const AccountList: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [form] = Form.useForm();

  const accountTypes = [
    { value: '연금계좌', label: '연금계좌' },
    { value: 'IRP계좌', label: 'IRP계좌' },
    { value: 'ISA계좌', label: 'ISA계좌' },
    { value: 'CMA계좌', label: 'CMA계좌' },
    { value: '종합매매계좌', label: '종합매매계좌' },
    { value: '해외주식계좌', label: '해외주식계좌' },
  ];

  const currencies = [
    { value: 'KRW', label: 'KRW (원)' },
    { value: 'USD', label: 'USD (달러)' },
  ];

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const data = await accountApi.getAccounts();
      setAccounts(data);
    } catch (error) {
      message.error('계좌 목록을 불러오는데 실패했습니다.');
      console.error('Error fetching accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingAccount(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (account: Account) => {
    setEditingAccount(account);
    form.setFieldsValue(account);
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await accountApi.deleteAccount(id);
      message.success('계좌가 삭제되었습니다.');
      fetchAccounts();
    } catch (error) {
      message.error('계좌 삭제에 실패했습니다.');
      console.error('Error deleting account:', error);
    }
  };

  const handleSubmit = async (values: AccountFormData) => {
    try {
      if (editingAccount) {
        await accountApi.updateAccount(editingAccount.id, values);
        message.success('계좌가 수정되었습니다.');
      } else {
        await accountApi.createAccount(values);
        message.success('계좌가 생성되었습니다.');
      }
      setModalVisible(false);
      fetchAccounts();
    } catch (error) {
      message.error('계좌 저장에 실패했습니다.');
      console.error('Error saving account:', error);
    }
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const columns = [
    {
      title: '소유자',
      dataIndex: 'owner_name',
      key: 'owner_name',
    },
    {
      title: '증권사',
      dataIndex: 'broker',
      key: 'broker',
    },
    {
      title: '계좌번호',
      dataIndex: 'account_number',
      key: 'account_number',
    },
    {
      title: '계좌유형',
      dataIndex: 'account_type',
      key: 'account_type',
    },
    {
      title: '잔액',
      dataIndex: 'current_balance',
      key: 'current_balance',
      render: (value: number, record: Account) => formatCurrency(value, record.currency),
    },
    {
      title: '통화',
      dataIndex: 'currency',
      key: 'currency',
    },
    {
      title: '작업',
      key: 'actions',
      render: (_: any, record: Account) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => window.open(`/accounts/${record.id}`, '_blank')}
          >
            상세
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            수정
          </Button>
          <Popconfirm
            title="계좌를 삭제하시겠습니까?"
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

  return (
    <div>
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={2} style={{ margin: 0 }}>계좌 관리</Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            계좌 추가
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={accounts}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingAccount ? '계좌 수정' : '계좌 추가'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="owner_name"
            label="소유자 이름"
            rules={[{ required: true, message: '소유자 이름을 입력해주세요.' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="broker"
            label="증권사"
            rules={[{ required: true, message: '증권사를 입력해주세요.' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="account_number"
            label="계좌번호"
            rules={[{ required: true, message: '계좌번호를 입력해주세요.' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="account_type"
            label="계좌유형"
            rules={[{ required: true, message: '계좌유형을 선택해주세요.' }]}
          >
            <Select>
              {accountTypes.map(type => (
                <Option key={type.value} value={type.value}>
                  {type.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="initial_balance"
            label="초기 금액"
            rules={[{ required: true, message: '잔액을 입력해주세요.' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
            />
          </Form.Item>

          <Form.Item
            name="currency"
            label="통화"
            rules={[{ required: true, message: '통화를 선택해주세요.' }]}
          >
            <Select>
              {currencies.map(currency => (
                <Option key={currency.value} value={currency.value}>
                  {currency.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AccountList;
