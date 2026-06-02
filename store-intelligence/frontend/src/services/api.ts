import axios from 'axios';
import type {
  AnomalyResponse,
  FunnelResponse,
  HealthResponse,
  HeatmapResponse,
  MetricsResponse,
} from '@/types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 12000,
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    if (!config || config.__retryCount >= 2) {
      return Promise.reject(error);
    }
    config.__retryCount = config.__retryCount ? config.__retryCount + 1 : 1;
    await new Promise((resolve) => setTimeout(resolve, 300 * config.__retryCount));
    return api(config);
  },
);

export const getMetrics = async (storeId = 'ST1008', date?: string): Promise<MetricsResponse> => {
  const response = await api.get<MetricsResponse>(`/stores/${storeId}/metrics`, {
    params: date ? { date } : undefined,
  });
  try {
    console.debug('[api] getMetrics', { storeId, date, data: response.data });
  } catch (e) {
    // ignore logging failures in older browsers
  }
  return response.data;
};

export const getFunnel = async (storeId = 'ST1008', date?: string): Promise<FunnelResponse> => {
  const response = await api.get<FunnelResponse>(`/stores/${storeId}/funnel`, {
    params: date ? { date } : undefined,
  });
  try {
    console.debug('[api] getFunnel', { storeId, date, data: response.data });
  } catch (e) {}
  return response.data;
};

export const getHeatmap = async (storeId = 'ST1008', date?: string): Promise<HeatmapResponse> => {
  const response = await api.get<HeatmapResponse>(`/stores/${storeId}/heatmap`, {
    params: date ? { date } : undefined,
  });
  try {
    console.debug('[api] getHeatmap', { storeId, date, data: response.data });
  } catch (e) {}
  return response.data;
};

export const getAnomalies = async (storeId = 'ST1008', date?: string): Promise<AnomalyResponse> => {
  const response = await api.get<AnomalyResponse>(`/stores/${storeId}/anomalies`, {
    params: date ? { date } : undefined,
  });
  try {
    console.debug('[api] getAnomalies', { storeId, date, data: response.data });
  } catch (e) {}
  return response.data;
};

export const getHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/health');
  return response.data;
};
