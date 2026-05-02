import React, { useEffect, useState } from 'react';
import ImpactOverview from '../components/ImpactOverview';
import AlertsBar from '../components/AlertsBar';
import BreakdownChart from '../components/BreakdownChart';
import { getDashboardOverview, getDashboardAlerts } from '../api/client';
import type { DashboardOverview, DashboardAlerts } from '../api/client';

const DashboardPage: React.FC = () => {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [alerts, setAlerts] = useState<DashboardAlerts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // MVP: Hardcoded SME ID
  const SME_ID = 'test_sme';

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [overviewData, alertsData] = await Promise.all([
          getDashboardOverview(SME_ID),
          getDashboardAlerts(SME_ID)
        ]);
        setOverview(overviewData);
        setAlerts(alertsData);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
        setError('Unable to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (error) {
    return (
      <div className="error-state fade-in">
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <h1>Sustainability Dashboard</h1>
      <p className="text-dim" style={{ marginBottom: '2.5rem' }}>
        Real-time tracking of your Scope 3 utility emissions.
      </p>

      {alerts && (
        <AlertsBar 
          lowConfidence={alerts.flagged_low_confidence_count} 
          unreadable={alerts.flagged_unreadable_count} 
        />
      )}

      {overview && (
        <>
          <ImpactOverview 
            total={overview.total_co2e_ytd} 
            electricity={overview.electricity_co2e} 
            water={overview.water_co2e} 
            loading={loading}
          />
          
          <BreakdownChart 
            electricity={overview.electricity_co2e} 
            water={overview.water_co2e} 
          />
        </>
      )}
      
      {!loading && !overview && (
        <div className="empty-state">
          <h3>No data available yet</h3>
          <p>Start by submitting your first utility bill via email.</p>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
