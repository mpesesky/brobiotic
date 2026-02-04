import { useState } from 'react';

interface ArticleInputProps {
  onFetch: (identifier: string) => void;
  isLoading: boolean;
}

export function ArticleInput({ onFetch, isLoading }: ArticleInputProps) {
  const [identifier, setIdentifier] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (identifier.trim()) {
      onFetch(identifier.trim());
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Find Article</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="identifier" className="block text-sm text-gray-600 mb-1.5">
            PMID, DOI, URL, or title
          </label>
          <input
            type="text"
            id="identifier"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="e.g., 41514338"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            disabled={isLoading}
          />
        </div>
        <button
          type="submit"
          disabled={isLoading || !identifier.trim()}
          className="w-full bg-slate-800 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-slate-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Fetching...' : 'Fetch Article'}
        </button>
      </form>
    </div>
  );
}
