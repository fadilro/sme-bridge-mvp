import React from 'react';
import { downloadExport } from '../api/client';
import { useSme } from '../context/SmeContext';
import './ExportsPage.css';

const ExportsPage: React.FC = () => {
  const { selectedSmeId: SME_ID } = useSme(); // Set via SME selector in sidebar

  return (
    <div className="exports-page">
      <h1>Data Exports</h1>
      <p className="text-dim" style={{ marginBottom: '2.5rem' }}>
        Download your sustainability metrics and raw data for reporting and audit purposes.
      </p>

      <div className="exports-grid">
        <div className="export-card">
          <div className="export-icon">📄</div>
          <div className="export-info">
            <h3>Sustainability Summary (PDF)</h3>
            <p>A professional report summarizing your YTD carbon footprint, category breakdown, and data integrity metrics.</p>
            <ul className="export-features">
              <li>✓ Total CO2e Impact</li>
              <li>✓ Category Breakdown</li>
              <li>✓ Data Quality Audit</li>
            </ul>
          </div>
          <button 
            className="btn-export" 
            onClick={() => downloadExport('pdf', SME_ID)}
          >
            Download PDF
          </button>
        </div>

        <div className="export-card">
          <div className="export-icon">📊</div>
          <div className="export-info">
            <h3>Raw Data Export (CSV)</h3>
            <p>Complete historical data of all processed and validated utility bills in a machine-readable format.</p>
            <ul className="export-features">
              <li>✓ Row-level granularity</li>
              <li>✓ Validated usage values</li>
              <li>✓ Audit IDs & Filenames</li>
            </ul>
          </div>
          <button 
            className="btn-export btn-secondary" 
            onClick={() => downloadExport('csv', SME_ID)}
          >
            Download CSV
          </button>
        </div>

        <div className="export-card">
          <div className="export-icon">💾</div>
          <div className="export-info">
            <h3>Audit Archive (XLSX)</h3>
            <p>Comprehensive Excel workbook containing full audit trails, including reviewer IDs and emission factor snapshots.</p>
            <ul className="export-features">
              <li>✓ Full Audit Metadata</li>
              <li>✓ Multi-tab ready</li>
              <li>✓ Original filenames</li>
            </ul>
          </div>
          <button 
            className="btn-export btn-secondary" 
            onClick={() => downloadExport('xlsx', SME_ID)}
          >
            Download XLSX
          </button>
        </div>
      </div>

      <div className="export-notice">
        <p><strong>Note:</strong> Exports only include bills with "Success" or "Resolved" status. Pending or flagged bills will not appear in these reports until they are verified.</p>
      </div>
    </div>
  );
};

export default ExportsPage;
