import { useState } from 'react';
import type { ArticleFetchResponse, ProcessResponse, ReportBadOutputRequest } from '../types';

interface ResultsDisplayProps {
  article: ArticleFetchResponse | null;
  processedResult: ProcessResponse | null;
  onReport: (request: ReportBadOutputRequest) => void;
  isLoading: boolean;
}

type TabType = 'original' | 'summary' | 'translation';

function CacheBadge({ cachedAt }: { cachedAt: string }) {
  const date = new Date(cachedAt);
  const formatted = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
      </svg>
      Cached {formatted}
    </span>
  );
}

export function ResultsDisplay({ article, processedResult, onReport, isLoading }: ResultsDisplayProps) {
  const [activeTab, setActiveTab] = useState<TabType>('original');

  // Auto-switch to summary tab when results come in
  const hasProcessedContent = processedResult?.summary || processedResult?.translated_abstract;

  if (!article) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <p className="text-gray-400 text-center italic">
          Enter an article identifier above to get started
        </p>
      </div>
    );
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const handleReportClick = (resultType: 'summary' | 'translation') => {
    if (!processedResult) return;
    const comment = window.prompt('Optional: describe what was wrong with this output');
    const request: ReportBadOutputRequest = {
      pmid: processedResult.pmid,
      result_type: resultType,
      target_language: processedResult.target_language,
      knowledge_level: processedResult.knowledge_level,
      comment: comment || undefined,
    };
    onReport(request);
  };

  // Determine available tabs
  const tabs: { id: TabType; label: string; available: boolean }[] = [
    { id: 'original', label: 'Original', available: true },
    { id: 'summary', label: 'Summary', available: !!processedResult?.summary },
    { id: 'translation', label: 'Translation', available: !!processedResult?.translated_abstract },
  ];

  const availableTabs = tabs.filter((t) => t.available);

  // If we just got processed results and we're on original tab, switch to the new content
  const effectiveTab =
    activeTab === 'original' && hasProcessedContent
      ? processedResult?.summary
        ? 'summary'
        : 'translation'
      : activeTab;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Article Header */}
      <div className="bg-gradient-to-r from-slate-50 to-gray-50 border-b border-gray-200 p-5">
        <h3 className="text-lg font-semibold text-gray-900 leading-snug">{article.title}</h3>
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
          <span>{article.authors.slice(0, 3).join(', ')}{article.authors.length > 3 && ' et al.'}</span>
          <span className="text-gray-400">|</span>
          <span className="italic">{article.journal}</span>
          <span className="text-gray-400">|</span>
          <span>{article.pub_date}</span>
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
            PMID: {article.pmid}
          </span>
          {article.pmcid && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
              {article.pmcid}
            </span>
          )}
          {article.has_full_text && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800">
              Full Text Available
            </span>
          )}
          {article.from_cache && article.cached_at && (
            <CacheBadge cachedAt={article.cached_at} />
          )}
        </div>

        {/* Citation Metrics */}
        {article.citation_metrics && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-gray-600">
              <span>
                <span className="font-medium text-gray-700">{article.citation_metrics.citation_count}</span> citations
              </span>
              {article.citation_metrics.citations_per_year != null && (
                <span>
                  <span className="font-medium text-gray-700">{article.citation_metrics.citations_per_year.toFixed(1)}</span>/year
                </span>
              )}
              {article.citation_metrics.relative_citation_ratio != null && (
                <span title="Relative Citation Ratio: 1.0 = field average">
                  RCR: <span className="font-medium text-gray-700">{article.citation_metrics.relative_citation_ratio.toFixed(2)}</span>
                </span>
              )}
              {article.citation_metrics.nih_percentile != null && (
                <span title="Percentile among NIH-funded papers">
                  NIH Percentile: <span className="font-medium text-gray-700">{article.citation_metrics.nih_percentile.toFixed(0)}</span>
                </span>
              )}
            </div>
            {(() => {
              // Check if paper is within last 2 years
              const yearMatch = article.pub_date.match(/\b(20\d{2})\b/);
              if (yearMatch) {
                const pubYear = parseInt(yearMatch[1], 10);
                const currentYear = new Date().getFullYear();
                if (currentYear - pubYear < 2) {
                  return (
                    <p className="mt-2 text-xs text-amber-600 italic">
                      Recently published papers may not have had sufficient time to accumulate citations.
                    </p>
                  );
                }
              }
              return null;
            })()}
          </div>
        )}
      </div>

      {/* Tabs */}
      {availableTabs.length > 1 && (
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {availableTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                  effectiveTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
                {tab.id !== 'original' && (
                  <span className="ml-1.5 inline-flex items-center justify-center w-2 h-2 rounded-full bg-blue-600" />
                )}
              </button>
            ))}
          </nav>
        </div>
      )}

      {/* Tab Content */}
      <div className="p-5">
        {/* Original Tab */}
        {effectiveTab === 'original' && (
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Abstract</h4>
            {article.abstract ? (
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">{article.abstract}</p>
            ) : (
              <p className="text-gray-400 italic">No abstract available for this article.</p>
            )}
          </div>
        )}

        {/* Summary Tab */}
        {effectiveTab === 'summary' && processedResult?.summary && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 capitalize">
                  {processedResult.knowledge_level?.replace('_', ' ')} level
                </span>
                {processedResult.from_cache && processedResult.cached_at && (
                  <CacheBadge cachedAt={processedResult.cached_at} />
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleReportClick('summary')}
                  disabled={isLoading}
                  className="text-xs text-red-400 hover:text-red-600 flex items-center gap-1 disabled:opacity-50"
                  title="Report bad output and regenerate"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  Report
                </button>
                <button
                  onClick={() => {
                    let text = `Summary:\n${processedResult.summary}\n\nKey Findings:\n${processedResult.key_findings?.map((f) => `- ${f}`).join('\n')}\n\nContext:\n${processedResult.context}`;
                    if (processedResult.acronyms && processedResult.acronyms.length > 0) {
                      text += `\n\nAcronyms:\n${processedResult.acronyms.map((a) => `- ${a}`).join('\n')}`;
                    }
                    copyToClipboard(text);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy
                </button>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Summary</h4>
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">{processedResult.summary}</p>
            </div>

            {processedResult.key_findings && processedResult.key_findings.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Key Findings</h4>
                <ul className="space-y-2">
                  {processedResult.key_findings.map((finding, index) => (
                    <li key={index} className="flex items-start gap-2 text-gray-700">
                      <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-blue-500 mt-2" />
                      <span>{finding}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {processedResult.context && (
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Context</h4>
                <p className="text-gray-700 leading-relaxed whitespace-pre-line">{processedResult.context}</p>
              </div>
            )}

            {processedResult.acronyms && processedResult.acronyms.length > 0 && (
              <div className="pt-4 border-t border-gray-100">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Acronyms</h4>
                <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 text-sm">
                  {processedResult.acronyms.map((acronym, index) => {
                    const [abbr, ...rest] = acronym.split(':');
                    const meaning = rest.join(':').trim();
                    return (
                      <div key={index} className="flex gap-2">
                        <dt className="font-medium text-gray-700">{abbr.trim()}</dt>
                        <dd className="text-gray-600">{meaning}</dd>
                      </div>
                    );
                  })}
                </dl>
              </div>
            )}
          </div>
        )}

        {/* Translation Tab */}
        {effectiveTab === 'translation' && processedResult?.translated_abstract && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                  {processedResult.target_language}
                </span>
                {processedResult.from_cache && processedResult.cached_at && (
                  <CacheBadge cachedAt={processedResult.cached_at} />
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleReportClick('translation')}
                  disabled={isLoading}
                  className="text-xs text-red-400 hover:text-red-600 flex items-center gap-1 disabled:opacity-50"
                  title="Report bad output and regenerate"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  Report
                </button>
                <button
                  onClick={() =>
                    copyToClipboard(
                      `${processedResult.translated_title}\n\n${processedResult.translated_abstract}`
                    )
                  }
                  className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy
                </button>
              </div>
            </div>

            {processedResult.translated_title && (
              <h3 className="text-lg font-semibold text-gray-900">{processedResult.translated_title}</h3>
            )}
            <p className="text-gray-700 leading-relaxed whitespace-pre-line">
              {processedResult.translated_abstract}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
