import { useState } from 'react';
import { ArticleInput } from './components/ArticleInput';
import { OptionsPanel } from './components/OptionsPanel';
import { ResultsDisplay } from './components/ResultsDisplay';
import { fetchArticle, processArticle, reportBadOutput } from './api/client';
import type { ArticleFetchResponse, ProcessResponse, KnowledgeLevel, ReportBadOutputRequest } from './types';

function App() {
  const [article, setArticle] = useState<ArticleFetchResponse | null>(null);
  const [processedResult, setProcessedResult] = useState<ProcessResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-5">
          <h1 className="text-xl font-semibold text-slate-800 tracking-tight">
            Article Translator & Summarizer
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Understand scientific articles and preprints in your language and at your level
          </p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6">
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
