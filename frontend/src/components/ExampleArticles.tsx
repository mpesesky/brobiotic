import { useState, useEffect } from 'react';
import { getExampleArticles } from '../api/client';
import type { ExampleArticle } from '../types';

interface ExampleArticlesProps {
  onFetch: (identifier: string) => void;
}

const SOURCE_COLORS: Record<string, string> = {
  pubmed: 'bg-blue-100 text-blue-800',
  arxiv: 'bg-orange-100 text-orange-800',
  biorxiv: 'bg-red-100 text-red-800',
  medrxiv: 'bg-teal-100 text-teal-800',
};

export function ExampleArticles({ onFetch }: ExampleArticlesProps) {
  const [articles, setArticles] = useState<ExampleArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCopied, setShowCopied] = useState<string | null>(null);

  const fetchExamples = async () => {
    setLoading(true);
    try {
      const res = await getExampleArticles();
      setArticles(res.articles);
    } catch {
      setArticles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExamples();
  }, []);

  const copyId = (id: string) => {
    navigator.clipboard.writeText(id).then(() => {
      setShowCopied(id);
      setTimeout(() => setShowCopied(null), 2000);
    });
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <p className="text-gray-400 text-center italic">Loading examples...</p>
      </div>
    );
  }

  if (articles.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <p className="text-gray-400 text-center italic">
          Enter an article identifier above to get started
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="bg-gradient-to-r from-slate-50 to-gray-50 border-b border-gray-200 px-5 py-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Try an example article</h3>
        <button
          onClick={fetchExamples}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Shuffle
        </button>
      </div>
      <div className="divide-y divide-gray-100">
        {articles.map((article) => (
          <div
            key={article.article_id}
            className="px-5 py-3 hover:bg-slate-50 transition-colors cursor-pointer group"
            onClick={() => onFetch(article.article_id)}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm text-gray-800 font-medium leading-snug line-clamp-2 group-hover:text-blue-700 transition-colors">
                  {article.title}
                </p>
                <div className="mt-1.5 flex items-center gap-2">
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${SOURCE_COLORS[article.source] || 'bg-gray-100 text-gray-800'}`}>
                    {article.source}
                  </span>
                  <code className="text-xs text-gray-400">{article.article_id}</code>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  copyId(article.article_id);
                }}
                className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 rounded"
                title="Copy article ID"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
      {showCopied && (
        <div className="fixed bottom-6 right-6 z-50 bg-gray-800 text-white text-sm px-4 py-2 rounded-lg shadow-lg animate-fade-in">
          Copied!
        </div>
      )}
    </div>
  );
}
