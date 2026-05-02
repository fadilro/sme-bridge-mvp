import React from 'react';
import './ImpactOverview.css';

interface Props {
  total: number;
  electricity: number;
  water: number;
  loading?: boolean;
}

const ImpactOverview: React.FC<Props> = ({ total, electricity, water, loading }) => {
  if (loading) {
    return <div className="overview-skeleton">Loading Impact Data...</div>;
  }

  return (
    <div className="impact-overview">
      <div className="impact-card total">
        <span className="card-label">Total Carbon Footprint</span>
        <div className="card-value">
          <span className="number">{total.toLocaleString()}</span>
          <span className="unit">kg CO2e</span>
        </div>
        <div className="card-trend text-dim">YTD Overview</div>
      </div>
      
      <div className="impact-card">
        <span className="card-label">Electricity Impact</span>
        <div className="card-value">
          <span className="number">{electricity.toLocaleString()}</span>
          <span className="unit">kg CO2e</span>
        </div>
        <div className="progress-mini">
          <div className="progress-bar" style={{ width: `${(electricity/total || 0) * 100}%` }}></div>
        </div>
      </div>
      
      <div className="impact-card">
        <span className="card-label">Water Impact</span>
        <div className="card-value">
          <span className="number">{water.toLocaleString()}</span>
          <span className="unit">kg CO2e</span>
        </div>
        <div className="progress-mini">
          <div className="progress-bar water" style={{ width: `${(water/total || 0) * 100}%` }}></div>
        </div>
      </div>
    </div>
  );
};

export default ImpactOverview;
