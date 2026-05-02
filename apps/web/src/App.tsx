import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './routes/DashboardPage';
import ReviewListPage from './routes/ReviewListPage';
import ReviewDetailPage from './routes/ReviewDetailPage';
import ExportsPage from './routes/ExportsPage';

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="review" element={<ReviewListPage />} />
        <Route path="review/:billId" element={<ReviewDetailPage />} />
        <Route path="exports" element={<ExportsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
};

export default App;
