import { useState } from 'react';
import { ArticleInput } from './components/ArticleInput';
import { OptionsPanel } from './components/OptionsPanel';
import { ResultsDisplay } from './components/ResultsDisplay';
import { HowTo } from './components/HowTo';
import { LoadingOverlay } from './components/LoadingOverlay';
import { fetchArticle, processArticle, reportBadOutput } from './api/client';
import type { ArticleFetchResponse, ProcessResponse, KnowledgeLevel, ReportBadOutputRequest } from './types';

function App() {
  const [article, setArticle] = useState<ArticleFetchResponse | null>(null);
  const [processedResult, setProcessedResult] = useState<ProcessResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<'main' | 'howto'>('main');

  const handleFetch = async (identifier: string) => {
    setIsLoading(true);
    setError(null);
    setProcessedResult(null);

    try {
      const result = await fetchArticle(identifier);
      setArticle(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch article');
      setArticle(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProcess = async (options: {
    translate?: { target_language: string };
    summarize?: { knowledge_level: KnowledgeLevel };
  }) => {
    if (!article) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await processArticle({
        identifier: article.article_id,
        ...options,
      });
      setProcessedResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process article');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReport = async (request: ReportBadOutputRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await reportBadOutput(request);
      setProcessedResult(result.new_result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate output');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      {isLoading && <LoadingOverlay />}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-5 flex items-center justify-between">
          <div>
            <h1
              className="text-xl font-semibold text-slate-800 tracking-tight cursor-pointer hover:text-slate-600 transition-colors"
              onClick={() => setPage('main')}
            >
              Article Translator & Summarizer
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Understand scientific articles and preprints in your language and at your level
            </p>
          </div>
          <button
            onClick={() => setPage(page === 'howto' ? 'main' : 'howto')}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            How to use
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6">
        {page === 'howto' ? (
          <HowTo onBack={() => setPage('main')} />
        ) : (
          <>
            {error && (
              <div className="mb-5 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              {/* Left Column - Input and Options */}
              <div className="lg:col-span-1 space-y-4">
                <ArticleInput onFetch={handleFetch} isLoading={isLoading} />
                <OptionsPanel
                  onProcess={handleProcess}
                  isLoading={isLoading}
                  hasArticle={article !== null}
                />
              </div>

              {/* Right Column - Results */}
              <div className="lg:col-span-2">
                <ResultsDisplay
                  article={article}
                  processedResult={processedResult}
                  onReport={handleReport}
                  isLoading={isLoading}
                />
              </div>
            </div>
          </>
        )}
      </main>

      <footer className="border-t border-gray-200 bg-white mt-auto">
        <div className="max-w-6xl mx-auto px-4 py-4 text-center text-xs text-gray-400">
          Powered by PubMed, arxiv, biorxiv, medrxiv, and Claude AI
        </div>
      </footer>
    </div>
  );
}

export default App;
