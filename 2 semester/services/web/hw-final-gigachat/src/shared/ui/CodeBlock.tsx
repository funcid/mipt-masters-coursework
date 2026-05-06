import { type ReactNode } from 'react';
import { IconCheck, IconCopy } from './Icon';
import { useCopyToClipboard } from '@/shared/hooks/useCopyToClipboard';

interface CodeBlockProps {
  language: string;
  code: string;
  children: ReactNode;
}

/**
 * Обёртка над pre/code, визуально похожая на ChatGPT:
 * заголовок с языком + кнопка «скопировать».
 */
export function CodeBlock({ language, code, children }: CodeBlockProps) {
  const { copied, copy } = useCopyToClipboard();
  const displayLang = language || 'code';

  return (
    <div className="my-4 overflow-hidden rounded-lg border border-border-subtle bg-[#0d1117]">
      <div className="flex items-center justify-between bg-white/[0.04] px-3 py-1.5 text-xs text-text-secondary">
        <span className="font-mono uppercase tracking-wide">{displayLang}</span>
        <button
          type="button"
          onClick={() => copy(code)}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-text-secondary transition-colors hover:bg-white/[0.06] hover:text-text-primary"
        >
          {copied ? <IconCheck width={14} height={14} /> : <IconCopy width={14} height={14} />}
          <span>{copied ? 'Скопировано' : 'Копировать'}</span>
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-[0.9rem] leading-relaxed">{children}</pre>
    </div>
  );
}
