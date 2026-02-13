export type KnowledgeLevel = 'expert' | 'adjacent' | 'lay_person';

export interface ArticleFetchRequest {
  identifier: string;
}

export interface CitationMetrics {
  citation_count: number;
  citations_per_year?: number;
  relative_citation_ratio?: number;  // 1.0 = field average
  nih_percentile?: number;
  expected_citations?: number;
  field_citation_rate?: number;
}

export interface ArticleFetchResponse {
  article_id: string;
  source: string;
  pmcid: string | null;
  doi: string | null;
  title: string;
  abstract: string;
  authors: string[];
  journal: string;
  pub_date: string;
  has_full_text: boolean;
  citation_metrics?: CitationMetrics;
  from_cache: boolean;
  cached_at: string | null;
}

export interface TranslationOptions {
  target_language: string;
}

export interface SummarizationOptions {
  knowledge_level: KnowledgeLevel;
}

export interface ProcessRequest {
  identifier: string;
  translate?: TranslationOptions;
  summarize?: SummarizationOptions;
}

export interface ProcessResponse {
  article_id: string;
  title: string;
  original_abstract: string;
  translated_abstract?: string;
  translated_title?: string;
  summary?: string;
  key_findings?: string[];
  context?: string;
  acronyms?: string[];
  target_language?: string;
  knowledge_level?: string;
  from_cache: boolean;
  cached_at: string | null;
  result_id: string | null;
}

export interface ExampleArticle {
  article_id: string;
  title: string;
  source: string;
}

export interface ExampleArticlesResponse {
  articles: ExampleArticle[];
}

export interface ErrorResponse {
  detail: string;
}

export interface ReportBadOutputRequest {
  article_id: string;
  result_type: 'translation' | 'summary';
  target_language?: string;
  knowledge_level?: string;
  comment?: string;
}

export interface ReportBadOutputResponse {
  success: boolean;
  new_result: ProcessResponse;
}
