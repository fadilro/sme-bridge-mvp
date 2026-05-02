import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';
import { describe, it, expect, vi } from 'vitest';

// Mock API client
vi.mock('../api/client', () => ({
  getDashboardOverview: vi.fn().mockResolvedValue({ total_co2e_ytd: 100, electricity_co2e: 60, water_co2e: 40 }),
  getDashboardAlerts: vi.fn().mockResolvedValue({ flagged_low_confidence_count: 1, flagged_unreadable_count: 0, total_requiring_review: 1 }),
}));

describe('App', () => {
  it('renders correctly', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByText(/SME Bridge/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Dashboard/i).length).toBeGreaterThan(0);
  });
});
