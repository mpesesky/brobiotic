import { useState, useRef } from 'react';

interface ArticleInputProps {
  onFetch: (identifier: string) => void;
  isLoading: boolean;
}

export function ArticleInput({ onFetch, isLoading }: ArticleInputProps) {
  const [identifier, setIdentifier] = useState('');
  const lastFetched = useRef('');

  const triggerFetch = () => {
    const trimmed = identifier.trim();
    if (trimmed && trimmed !== lastFetched.current && !isLoading) {
      lastFetched.current = trimmed;
      onFetch(trimmed);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      triggerFetch();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Find Article</h2>
      <label htmlFor="identifier" className="block text-sm text-gray-600 mb-1.5">
        PMID, DOI, URL, arxiv/biorxiv URL, or title
      </label>
      <input
        type="text"
        id="identifier"
        value={identifier}
        onChange={(e) => setIdentifier(e.target.value)}
        onBlur={triggerFetch}
        onKeyDown={handleKeyDown}
        placeholder="e.g., 41514338 or https://arxiv.org/abs/2401.12345"
        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        disabled={isLoading}
      />
      {isLoading && (
        <p className="mt-2 text-xs text-gray-500 italic">Fetching...</p>
      )}
    </div>
  );
}
