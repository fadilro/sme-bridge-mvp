import React from 'react';
import './BreakdownChart.css';

interface Props {
  electricity: number;
  water: number;
}

const BreakdownChart: React.FC<Props> = ({ electricity, water }) => {
  const total = electricity + water;
  const ePercent = total > 0 ? (electricity / total) * 100 : 0;
  const wPercent = total > 0 ? (water / total) * 100 : 0;

  return (
    <div className="breakdown-chart-container">
      <h3>Consumption Breakdown</h3>
      <div className="chart-wrapper">
        <div className="stacked-bar">
          <div 
            className="bar-segment electricity" 
            style={{ width: `${ePercent}%` }}
            title={`Electricity: ${ePercent.toFixed(1)}%`}
          ></div>
          <div 
            className="bar-segment water" 
            style={{ width: `${wPercent}%` }}
            title={`Water: ${wPercent.toFixed(1)}%`}
          ></div>
        </div>
        
        <div className="chart-legend">
          <div className="legend-item">
            <span className="dot electricity"></span>
            <span className="label">Electricity ({ePercent.toFixed(1)}%)</span>
          </div>
          <div className="legend-item">
            <span className="dot water"></span>
            <span className="label">Water ({wPercent.toFixed(1)}%)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BreakdownChart;
