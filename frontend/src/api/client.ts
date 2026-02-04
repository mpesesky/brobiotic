import type {
  ArticleFetchRequest,
  ArticleFetchResponse,
  ProcessRequest,
  ProcessResponse,
  ReportBadOutputRequest,
  ReportBadOutputResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }
  return response.json();
}

export async function fetchArticle(identifier: string): Promise<ArticleFetchResponse> {
  const response = await fetch(`${API_BASE}/articles/fetch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ identifier } as ArticleFetchRequest),
  });
  return handleResponse<ArticleFetchResponse>(response);
}

export async function processArticle(request: ProcessRequest): Promise<ProcessResponse> {
  const response = await fetch(`${API_BASE}/articles/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<ProcessResponse>(response);
}

export async function reportBadOutput(request: ReportBadOutputRequest): Promise<ReportBadOutputResponse> {
  const response = await fetch(`${API_BASE}/articles/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<ReportBadOutputResponse>(response);
}
