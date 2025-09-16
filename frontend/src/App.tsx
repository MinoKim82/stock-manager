import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import koKR from 'antd/locale/ko_KR';
import Layout from './components/Layout';
import AccountList from './pages/AccountList';
import AccountDetail from './pages/AccountDetail';
import TransactionList from './pages/TransactionList';
import TransactionManagement from './pages/TransactionManagement';
import PortfolioSummary from './pages/PortfolioSummary';
import './App.css';

function App() {
  return (
    <ConfigProvider locale={koKR}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<PortfolioSummary />} />
            <Route path="/accounts" element={<AccountList />} />
            <Route path="/accounts/:id" element={<AccountDetail />} />
            <Route path="/accounts/:id/transactions" element={<TransactionList />} />
            <Route path="/transactions" element={<TransactionManagement />} />
          </Routes>
        </Layout>
      </Router>
    </ConfigProvider>
  );
}

export default App;
