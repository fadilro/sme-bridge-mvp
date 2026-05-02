import React from 'react';
import { Link } from 'react-router-dom';
import './AlertsBar.css';

interface Props {
  lowConfidence: number;
  unreadable: number;
}

const AlertsBar: React.FC<Props> = ({ lowConfidence, unreadable }) => {
  const total = lowConfidence + unreadable;
  
  if (total === 0) return null;

  return (
    <div className="alerts-bar fade-in">
      <div className="alerts-content">
        <span className="alert-icon">⚠️</span>
        <div className="alert-text">
          <strong>{total} bills require your attention.</strong>
          <span className="alert-details">
            {lowConfidence > 0 && `${lowConfidence} low confidence extraction`}
            {lowConfidence > 0 && unreadable > 0 && ' and '}
            {unreadable > 0 && `${unreadable} unreadable/corrupted files`}
          </span>
        </div>
      </div>
      <Link to="/review" className="alert-action">
        Review Now
      </Link>
    </div>
  );
};

export default AlertsBar;
