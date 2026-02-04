import { useState } from 'react';
import type { KnowledgeLevel } from '../types';

interface OptionsPanelProps {
  onProcess: (options: {
    translate?: { target_language: string };
    summarize?: { knowledge_level: KnowledgeLevel };
  }) => void;
  isLoading: boolean;
  hasArticle: boolean;
}

const LANGUAGES = [
  { code: 'English', label: 'English' },
  { code: 'Spanish', label: 'Spanish' },
  { code: 'French', label: 'French' },
  { code: 'German', label: 'German' },
  { code: 'Chinese', label: 'Chinese' },
  { code: 'Japanese', label: 'Japanese' },
  { code: 'Portuguese', label: 'Portuguese' },
  { code: 'Italian', label: 'Italian' },
  { code: 'Korean', label: 'Korean' },
  { code: 'Russian', label: 'Russian' },
  { code: 'Arabic', label: 'Arabic' },
];

const KNOWLEDGE_LEVELS: { value: KnowledgeLevel; label: string; description: string }[] = [
  {
    value: 'expert',
    label: 'Expert',
    description: 'For domain specialists - technical terminology, methodology focus',
  },
  {
    value: 'adjacent',
    label: 'Adjacent Field',
    description: 'For researchers from related fields - explains key terms',
  },
  {
    value: 'lay_person',
    label: 'General Public',
    description: 'Plain language with analogies and real-world significance',
  },
];

export function OptionsPanel({ onProcess, isLoading, hasArticle }: OptionsPanelProps) {
  const [translateEnabled, setTranslateEnabled] = useState(false);
  const [targetLanguage, setTargetLanguage] = useState('English');
  const [summarizeEnabled, setSummarizeEnabled] = useState(true);
  const [knowledgeLevel, setKnowledgeLevel] = useState<KnowledgeLevel>('adjacent');

  const handleProcess = () => {
    const options: {
      translate?: { target_language: string };
      summarize?: { knowledge_level: KnowledgeLevel };
    } = {};

    if (translateEnabled) {
      options.translate = { target_language: targetLanguage };
    }
    if (summarizeEnabled) {
      options.summarize = { knowledge_level: knowledgeLevel };
    }

    onProcess(options);
  };

  const canProcess = hasArticle && (translateEnabled || summarizeEnabled);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Options</h2>

      {/* Translation Options */}
      <div className="mb-5">
        <label className="flex items-center cursor-pointer group">
          <input
            type="checkbox"
            checked={translateEnabled}
            onChange={(e) => setTranslateEnabled(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
          />
          <span className="ml-2 text-sm font-medium text-gray-700 group-hover:text-gray-900">
            Translate
          </span>
        </label>
        {translateEnabled && (
          <select
            value={targetLanguage}
            onChange={(e) => setTargetLanguage(e.target.value)}
            className="mt-2 w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.label}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Summarization Options */}
      <div className="mb-5">
        <label className="flex items-center cursor-pointer group">
          <input
            type="checkbox"
            checked={summarizeEnabled}
            onChange={(e) => setSummarizeEnabled(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
          />
          <span className="ml-2 text-sm font-medium text-gray-700 group-hover:text-gray-900">
            Summarize
          </span>
        </label>
        {summarizeEnabled && (
          <div className="mt-2 space-y-1.5">
            {KNOWLEDGE_LEVELS.map((level) => (
              <label
                key={level.value}
                className={`flex items-center p-2.5 border rounded cursor-pointer transition-all ${
                  knowledgeLevel === level.value
                    ? 'border-blue-500 bg-blue-50 shadow-sm'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <input
                  type="radio"
                  name="knowledgeLevel"
                  value={level.value}
                  checked={knowledgeLevel === level.value}
                  onChange={() => setKnowledgeLevel(level.value)}
                  className="w-3.5 h-3.5 text-blue-600"
                />
                <div className="ml-2.5">
                  <div className="text-sm font-medium text-gray-800">{level.label}</div>
                  <div className="text-xs text-gray-500 leading-snug">{level.description}</div>
                </div>
              </label>
            ))}
          </div>
        )}
      </div>

      <button
        onClick={handleProcess}
        disabled={isLoading || !canProcess}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? 'Processing...' : 'Process Article'}
      </button>
    </div>
  );
}
