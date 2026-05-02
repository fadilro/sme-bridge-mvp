import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getBillDetail, approveBill } from '../api/client';
import type { UtilityBillRecord, BillApprovePayload } from '../api/client';
import './ReviewDetailPage.css';

const ReviewDetailPage: React.FC = () => {
  const { billId } = useParams<{ billId: string }>();
  const navigate = useNavigate();
  
  const [bill, setBill] = useState<UtilityBillRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [provider, setProvider] = useState('');
  const [period, setPeriod] = useState('');
  const [usage, setUsage] = useState<number>(0);
  const [unit, setUnit] = useState('kWh');

  useEffect(() => {
    if (!billId) return;
    
    const fetchBill = async () => {
      try {
        const data = await getBillDetail(billId);
        setBill(data);
        // Pre-fill form if data was partially extracted
        setProvider(data.extracted_provider || '');
        setPeriod(data.extracted_period || '');
        setUsage(data.extracted_usage || 0);
        setUnit(data.extracted_usage_unit || 'kWh');
      } catch {
        setError('Failed to load bill details.');
      } finally {
        setLoading(false);
      }
    };

    fetchBill();
  }, [billId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!billId) return;

    try {
      setSubmitting(true);
      const payload: BillApprovePayload = {
        provider,
        billing_period: period,
        usage_value: usage,
        usage_unit: unit,
      };
      await approveBill(billId, payload);
      navigate('/review');
    } catch {
      setError('Failed to approve bill. Please check your inputs.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="loading-state">Loading bill details...</div>;
  if (!bill) return <div className="error-state">Bill not found.</div>;

  return (
    <div className="review-detail-page">
      <div className="page-header-actions">
        <button className="btn-back" onClick={() => navigate('/review')}>
          ← Back to List
        </button>
      </div>
      
      <h1>Review Bill</h1>
      <p className="text-dim">Verify the data extracted from <strong>{bill.original_filename}</strong></p>

      <div className="review-container">
        <div className="bill-preview-section">
          <h3>Bill Preview</h3>
          <div className="preview-placeholder">
             <p>File: {bill.original_filename}</p>
             <a href="#" className="btn-secondary">Download Raw File</a>
             {/* In a real app, embed PDF/Image viewer here */}
          </div>
          
          <div className="extraction-log">
             <h4>Extraction Context</h4>
             <p>Status: <span className={`status-text ${bill.status}`}>{bill.status.replace(/_/g, ' ')}</span></p>
             <p>Confidence: {bill.status === 'flagged_low_confidence' ? 'Low' : 'Failed'}</p>
          </div>
        </div>

        <div className="approval-form-section">
          <h3>Correction Form</h3>
          <form onSubmit={handleSubmit} className="approval-form">
            <div className="form-group">
              <label htmlFor="provider">Service Provider</label>
              <input 
                id="provider"
                type="text" 
                value={provider} 
                onChange={(e) => setProvider(e.target.value)} 
                placeholder="e.g. Tenaga Nasional"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="period">Billing Period</label>
              <input 
                id="period"
                type="text" 
                value={period} 
                onChange={(e) => setPeriod(e.target.value)} 
                placeholder="e.g. Jan 2024"
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="usage">Usage Value</label>
                <input 
                  id="usage"
                  type="number" 
                  step="0.01"
                  value={usage} 
                  onChange={(e) => setUsage(parseFloat(e.target.value))} 
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="unit">Unit</label>
                <select id="unit" value={unit} onChange={(e) => setUnit(e.target.value)}>
                  <option value="kWh">kWh (Electricity)</option>
                  <option value="m3">m³ (Water)</option>
                  <option value="liters">Liters</option>
                </select>
              </div>
            </div>

            {error && <p className="form-error">{error}</p>}

            <button type="submit" className="btn-approve" disabled={submitting}>
              {submitting ? 'Processing...' : 'Approve & Save'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ReviewDetailPage;
