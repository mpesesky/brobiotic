interface HowToProps {
  onBack: () => void;
}

export function HowTo({ onBack }: HowToProps) {
  return (
    <div className="max-w-3xl mx-auto">
      <button
        onClick={onBack}
        className="mb-4 text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back
      </button>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">How It Works</h2>
          <p className="text-sm text-gray-600 leading-relaxed">
            This tool helps you understand scientific articles by translating them into your language
            and summarizing them at your knowledge level. It supports published journal articles from
            PubMed as well as preprints from arXiv, bioRxiv, and medRxiv.
          </p>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-800 mb-3">1. Find an article</h3>
          <p className="text-sm text-gray-600 leading-relaxed mb-3">
            Paste any of the following into the search box, then click away or press Enter:
          </p>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
              <span><span className="font-medium text-gray-700">PMID</span> &mdash; a numeric PubMed identifier, e.g. <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">41514338</code></span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
              <span><span className="font-medium text-gray-700">DOI</span> &mdash; e.g. <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">10.1038/s41586-024-07386-0</code></span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
              <span><span className="font-medium text-gray-700">PubMed URL</span> &mdash; e.g. <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">https://pubmed.ncbi.nlm.nih.gov/41514338/</code></span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
              <span><span className="font-medium text-gray-700">arXiv URL or ID</span> &mdash; e.g. <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">https://arxiv.org/abs/2401.12345</code> or <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">arxiv:2401.12345</code></span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
              <span><span className="font-medium text-gray-700">bioRxiv / medRxiv URL</span> &mdash; e.g. <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">https://www.biorxiv.org/content/10.1101/2024.01.01.123456v1</code></span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
              <span><span className="font-medium text-gray-700">Article title</span> &mdash; a text search against PubMed (best for published articles)</span>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-800 mb-3">2. Choose what to do with it</h3>
          <p className="text-sm text-gray-600 leading-relaxed mb-3">
            Once the article loads, you can:
          </p>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-purple-500 mt-1.5" />
              <span><span className="font-medium text-gray-700">Summarize</span> &mdash; get a concise summary tailored to your background. Choose from <em>Expert</em> (field specialist), <em>Adjacent</em> (scientist from another field), or <em>Lay person</em> (general public).</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5" />
              <span><span className="font-medium text-gray-700">Translate</span> &mdash; translate the title and content into another language while preserving scientific accuracy.</span>
            </li>
          </ul>
          <p className="text-sm text-gray-600 leading-relaxed mt-3">
            You can do both at the same time. Results are cached so repeat requests are instant.
          </p>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-800 mb-3">3. Review the results</h3>
          <p className="text-sm text-gray-600 leading-relaxed">
            Switch between the Original, Summary, and Translation tabs to compare.
            If the AI output isn't accurate, click the <span className="text-red-500 font-medium">Report</span> button
            to flag it and get a fresh result.
          </p>
        </div>

        <div className="pt-4 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">Supported Sources</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <a
              href="https://pubmed.ncbi.nlm.nih.gov/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
            >
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">PubMed</span>
              <span className="text-sm text-gray-600">Peer-reviewed biomedical literature</span>
            </a>
            <a
              href="https://arxiv.org/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-orange-300 hover:bg-orange-50 transition-colors"
            >
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">arXiv</span>
              <span className="text-sm text-gray-600">Physics, math, CS, and more</span>
            </a>
            <a
              href="https://www.biorxiv.org/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-red-300 hover:bg-red-50 transition-colors"
            >
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">bioRxiv</span>
              <span className="text-sm text-gray-600">Biology preprints</span>
            </a>
            <a
              href="https://www.medrxiv.org/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
            >
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">medRxiv</span>
              <span className="text-sm text-gray-600">Health sciences preprints</span>
            </a>
          </div>
        </div>

        <div className="pt-4 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-800 mb-2">Good to know</h3>
          <ul className="space-y-1.5 text-sm text-gray-600">
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5" />
              <span>For PubMed articles, citation metrics from iCite are shown when available. Preprints do not have citation metrics.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5" />
              <span>When full text is available (open-access PubMed articles or any preprint), summaries are richer and reference specific figures and tables.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5" />
              <span>Preprints have <em>not</em> been peer reviewed. The preprint notice in the results is a reminder of this.</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
