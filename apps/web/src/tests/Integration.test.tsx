import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';
import * as apiClient from '../api/client';

// Mock the API client
vi.mock('../api/client', async () => {
  const actual = await vi.importActual('../api/client');
  return {
    ...actual,
    getDashboardOverview: vi.fn(),
    getDashboardAlerts: vi.fn(),
    getBillDetail: vi.fn(),
    approveBill: vi.fn(),
    apiClient: {
      get: vi.fn(),
    },
  };
});

describe('App Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('navigates to and renders Dashboard with live data', async () => {
    vi.mocked(apiClient.getDashboardOverview).mockResolvedValue({
      total_co2e_ytd: 1250.5,
      electricity_co2e: 800,
      water_co2e: 450.5,
    });
    vi.mocked(apiClient.getDashboardAlerts).mockResolvedValue({
      total_requiring_review: 3,
      flagged_low_confidence_count: 2,
      flagged_unreadable_count: 1,
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    expect(await screen.findByText('1,250.5')).toBeInTheDocument(); // Exact Total
    expect(screen.getByText(/3 bills require your attention/)).toBeInTheDocument(); // Alert count
  });

  it('completes a bill review workflow', async () => {
    const mockBill: apiClient.UtilityBillRecord = {
      id: 'bill123',
      sme_id: 'test_sme',
      status: 'flagged_low_confidence' as unknown as apiClient.UtilityBillStatus,
      original_filename: 'invoice.pdf',
      created_at: '2024-01-01T00:00:00Z',
      extracted_provider: 'Old Provider',
      extracted_period: 'Jan 2024',
      extracted_usage: 100,
      extracted_usage_unit: 'kWh',
    } as unknown as apiClient.UtilityBillRecord;

    vi.mocked(apiClient.getBillDetail).mockResolvedValue(mockBill);
    vi.mocked(apiClient.approveBill).mockResolvedValue();

    render(
      <MemoryRouter initialEntries={['/review/bill123']}>
        <App />
      </MemoryRouter>
    );

    // Wait for data to load
    await waitFor(() => expect(screen.getByDisplayValue('Old Provider')).toBeInTheDocument());

    // Modify usage
    const usageInput = screen.getByLabelText(/Usage Value/i);
    fireEvent.change(usageInput, { target: { value: '150' } });

    // Submit
    const submitBtn = screen.getByText(/Approve & Save/i);
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.approveBill).toHaveBeenCalledWith('bill123', expect.objectContaining({
        usage_value: 150
      }));
    });
  });
});
