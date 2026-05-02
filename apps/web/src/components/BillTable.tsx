import React from 'react';
import { Link } from 'react-router-dom';
import type { UtilityBillRecord } from '../api/client';
import './BillTable.css';

interface Props {
  bills: UtilityBillRecord[];
}

const BillTable: React.FC<Props> = ({ bills }) => {
  if (bills.length === 0) {
    return <div className="empty-table">No bills found requiring review.</div>;
  }

  return (
    <div className="table-container">
      <table className="bill-table">
        <thead>
          <tr>
            <th>Submitted</th>
            <th>Filename</th>
            <th>Status</th>
            <th>Reason</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {bills.map((bill) => (
            <tr key={bill.id}>
              <td>{new Date(bill.created_at).toLocaleDateString()}</td>
              <td className="filename">{bill.original_filename || 'Unknown'}</td>
              <td>
                <span className={`status-badge ${bill.status}`}>
                  {bill.status.replace(/_/g, ' ')}
                </span>
              </td>
              <td className="reason text-dim">
                {bill.status === 'flagged_low_confidence' ? 'Low Extraction Confidence' : 'Unreadable File'}
              </td>
              <td>
                <Link to={`/review/${bill.id}`} className="btn-inspect">
                  Inspect
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default BillTable;
