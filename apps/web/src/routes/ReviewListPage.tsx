import React, { useEffect, useState } from 'react';
import BillTable from '../components/BillTable';
import { apiClient, UtilityBillStatus } from '../api/client';
import type { UtilityBillRecord } from '../api/client';

const ReviewListPage: React.FC = () => {
  const [bills, setBills] = useState<UtilityBillRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const SME_ID = 'test_sme'; // MVP Hardcoded

  useEffect(() => {
    const fetchBills = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get<UtilityBillRecord[]>(`/bills?sme_id=${SME_ID}`);
        setBills(response.data);
      } catch {
        setError('Failed to load bills.');
      } finally {
        setLoading(false);
      }
    };

    fetchBills();
  }, []);

  return (
    <div className="review-list-page">
      <h1>Bill Verification</h1>
      <p className="text-dim" style={{ marginBottom: '2rem' }}>
        Review and approve utility bills that require manual verification.
      </p>
      
      {loading ? (
        <p>Loading bills...</p>
      ) : error ? (
        <p className="text-danger">{error}</p>
      ) : (
        <BillTable bills={bills.filter(b => 
          b.status === UtilityBillStatus.FLAGGED_LOW_CONFIDENCE || 
          b.status === UtilityBillStatus.FLAGGED_UNREADABLE
        )} />
      )}
    </div>
  );
};

export default ReviewListPage;
