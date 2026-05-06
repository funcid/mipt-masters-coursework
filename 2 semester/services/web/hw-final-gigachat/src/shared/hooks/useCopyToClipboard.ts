import { useCallback, useRef, useState } from 'react';

/**
 * Копирование в буфер обмена с индикацией «успешно».
 * Флаг copied держится 1.6 секунды, чтобы UI успел показать галочку.
 */
export function useCopyToClipboard(timeout = 1600) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<number | null>(null);

  const copy = useCallback(
    async (text: string) => {
      try {
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(text);
        } else {
          // Fallback для старых браузеров / http
          const ta = document.createElement('textarea');
          ta.value = text;
          ta.setAttribute('readonly', '');
          ta.style.position = 'absolute';
          ta.style.left = '-9999px';
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
        }
        setCopied(true);
        if (timer.current) window.clearTimeout(timer.current);
        timer.current = window.setTimeout(() => setCopied(false), timeout);
        return true;
      } catch (error) {
        console.error('Clipboard error', error);
        return false;
      }
    },
    [timeout],
  );

  return { copied, copy };
}
