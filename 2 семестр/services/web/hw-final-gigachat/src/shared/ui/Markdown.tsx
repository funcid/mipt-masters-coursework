import { isValidElement, memo, type ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { CodeBlock } from './CodeBlock';

interface MarkdownProps {
  content: string;
  /** Когда true, добавляем мигающий курсор в конец (streaming индикация) */
  streaming?: boolean;
}

/**
 * Рекурсивно собирает «чистый» текст из React-нод.
 * Нужен, потому что после rehype-highlight children для code превращается
 * в дерево <span class="hljs-*">...</span>, и String(children) даёт "[object Object]".
 */
function extractText(node: ReactNode): string {
  if (node == null || typeof node === 'boolean') return '';
  if (typeof node === 'string' || typeof node === 'number') return String(node);
  if (Array.isArray(node)) return node.map(extractText).join('');
  if (isValidElement(node)) {
    const children = (node.props as { children?: ReactNode }).children;
    return extractText(children);
  }
  return '';
}

/**
 * Markdown-рендерер для ответов ассистента.
 *
 * Поддерживает:
 *   - GitHub Flavored Markdown (remark-gfm): таблицы, чекбоксы, автоссылки;
 *   - подсветку синтаксиса в блоках кода (rehype-highlight + highlight.js);
 *   - кастомный CodeBlock с кнопкой «скопировать».
 */
export const Markdown = memo(function Markdown({ content, streaming }: MarkdownProps) {
  return (
    <div className={`markdown ${streaming ? 'caret' : ''}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeHighlight, { detect: true, ignoreMissing: true }]]}
        components={{
          code({ className, children, ...rest }) {
            // В react-markdown v9 проп `inline` больше не пробрасывается,
            // поэтому блоки кода опознаём по наличию language-* класса.
            const match = /language-([\w-]+)/.exec(className ?? '');
            if (!match) {
              return (
                <code className={className} {...rest}>
                  {children}
                </code>
              );
            }
            const code = extractText(children).replace(/\n$/, '');
            return (
              <CodeBlock language={match[1]} code={code}>
                <code className={className}>{children}</code>
              </CodeBlock>
            );
          },
          a({ href, children, ...rest }) {
            return (
              <a href={href} target="_blank" rel="noreferrer noopener" {...rest}>
                {children}
              </a>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});
