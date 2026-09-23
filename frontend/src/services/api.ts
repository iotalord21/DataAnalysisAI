import axios from 'axios';
import { DatasetSummary, AnalysisResult, VisualizationSpec, InsightItem, VerificationResult, FinalReport, PlanStep } from '../types';

const API_BASE = '/api';

export const api = {
  async getSystemInfo() {
    const res = await axios.get(`${API_BASE}/info`);
    return res.data;
  },

  async getSamples() {
    const res = await axios.get(`${API_BASE}/datasets/samples`);
    return res.data;
  },

  async loadSample(sampleId: string): Promise<DatasetSummary> {
    const res = await axios.post(`${API_BASE}/datasets/load-sample/${sampleId}`);
    return res.data;
  },

  async uploadDataset(file: File): Promise<DatasetSummary> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await axios.post(`${API_BASE}/datasets/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async runAnalysis(datasetId: string, query: string) {
    const res = await axios.post(`${API_BASE}/analysis/run`, {
      dataset_id: datasetId,
      query,
    });
    return res.data;
  },

  streamAnalysis(
    datasetId: string,
    query: string,
    onUpdate: (data: {
      node?: string;
      events?: any[];
      plan?: PlanStep[];
      visualizations?: VisualizationSpec[];
      insights?: InsightItem[];
      verification?: VerificationResult;
      final_report?: FinalReport;
    }) => void,
    onComplete: (data: any) => void,
    onError: (err: any) => void
  ): () => void {
    const queryParam = encodeURIComponent(query);
    const eventSource = new EventSource(`${API_BASE}/analysis/stream?dataset_id=${datasetId}&query=${queryParam}`);

    eventSource.addEventListener('update', (event) => {
      try {
        const payload = JSON.parse(event.data);
        onUpdate(payload);
      } catch (e) {
        console.error('Error parsing SSE update:', e);
      }
    });

    eventSource.addEventListener('complete', (event) => {
      try {
        const payload = JSON.parse(event.data);
        onComplete(payload);
      } catch (e) {
        console.error('Error parsing SSE complete:', e);
      } finally {
        eventSource.close();
      }
    });

    eventSource.addEventListener('error', (event) => {
      console.error('SSE Error:', event);
      onError(event);
      eventSource.close();
    });

    // Return cleanup abort function
    return () => {
      eventSource.close();
    };
  },
};
