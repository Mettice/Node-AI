/**
 * Language Selector Component
 * Displays programming languages with icons in a dropdown
 */

import { SelectWithIcons } from '@/components/common/SelectWithIcons';

interface LanguageSelectorProps {
  currentLanguage: string;
  onChange: (language: string) => void;
}

// Programming language options with icons
const LANGUAGE_OPTIONS = [
  { value: 'python', label: 'Python', icon: 'python' },
  { value: 'javascript', label: 'JavaScript', icon: 'javascript' },
];

export function LanguageSelector({
  currentLanguage,
  onChange,
}: LanguageSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
        Language <span className="text-red-400">*</span>
      </label>
      <p className="text-xs text-slate-400 -mt-1">
        Select the programming language for code execution
      </p>
      <SelectWithIcons
        value={currentLanguage || 'python'}
        onChange={onChange}
        options={LANGUAGE_OPTIONS}
        placeholder="Select a language..."
      />
    </div>
  );
}

