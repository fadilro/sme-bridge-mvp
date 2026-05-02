import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getDashboardOverview = async (smeId: string): Promise<DashboardOverview> => {
  const response = await apiClient.get<DashboardOverview>(`/dashboard/overview?sme_id=${smeId}`);
  return response.data;
};

export const getDashboardAlerts = async (smeId: string): Promise<DashboardAlerts> => {
  const response = await apiClient.get<DashboardAlerts>(`/dashboard/alerts?sme_id=${smeId}`);
  return response.data;
};

export const getBillDetail = async (billId: string): Promise<UtilityBillRecord> => {
  const response = await apiClient.get<UtilityBillRecord>(`/bills/${billId}`);
  return response.data;
};

export const approveBill = async (billId: string, payload: BillApprovePayload): Promise<void> => {
  await apiClient.post(`/bills/${billId}/approve`, payload);
};

export const downloadExport = async (kind: 'csv' | 'pdf' | 'xlsx', smeId?: string) => {
  const url = `/exports/${kind}?sme_id=${smeId || ''}`;
  try {
    const response = await apiClient.get(url, { responseType: 'blob' });
    
    // Extract filename from Content-Disposition header if available
    let filename = '';
    const disposition = response.headers['content-disposition'];
    if (disposition && disposition.indexOf('filename=') !== -1) {
      const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
      const matches = filenameRegex.exec(disposition);
      if (matches != null && matches[1]) { 
        filename = matches[1].replace(/['"]/g, '');
      }
    }
    
    // Fallback filenames
    if (!filename) {
      if (kind === 'csv') filename = `csi_export_${smeId || 'all'}.csv`;
      else if (kind === 'xlsx') filename = `audit_archive_${smeId || 'all'}.xlsx`;
      else if (kind === 'pdf') filename = `sustainability_summary_${smeId || 'all'}.pdf`;
    }

    const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  } catch (error) {
    console.error(`Failed to download ${kind} export:`, error);
    throw error;
  }
};

export interface DashboardOverview {
  total_co2e_ytd: number;
  electricity_co2e: number;
  water_co2e: number;
}

export interface DashboardAlerts {
  flagged_low_confidence_count: number;
  flagged_unreadable_count: number;
  total_requiring_review: number;
}

export const UtilityBillStatus = {
  PENDING: 'pending',
  SUCCESS: 'success',
  FLAGGED_LOW_CONFIDENCE: 'flagged_low_confidence',
  FLAGGED_UNREADABLE: 'flagged_unreadable',
  RESOLVED_BY_CLIENT: 'resolved_by_client',
} as const;

export type UtilityBillStatus = typeof UtilityBillStatus[keyof typeof UtilityBillStatus];

export interface UtilityBillRecord {
  id: string;
  sme_id: string;
  status: UtilityBillStatus;
  original_filename?: string;
  extracted_provider?: string;
  extracted_period?: string;
  extracted_usage?: number;
  extracted_usage_unit?: string;
  calculated_co2e?: number;
  reviewer_id?: string;
  created_at: string;
}

export interface BillApprovePayload {
  provider: string;
  billing_period: string;
  usage_value: number;
  usage_unit: string;
}
