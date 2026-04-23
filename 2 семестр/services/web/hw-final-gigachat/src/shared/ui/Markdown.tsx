import { memo, useMemo } from 'react';
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
 * Markdown-рендерер для ответов ассистента.
 *
 * Поддерживает:
 *   - GitHub Flavored Markdown (remark-gfm): таблицы, чекбоксы, автоссылки;
 *   - подсветку синтаксиса в блоках кода (rehype-highlight + highlight.js);
 *   - кастомный CodeBlock с кнопкой «скопировать».
 */
export const Markdown = memo(function Markdown({ content, streaming }: MarkdownProps) {
  const display = useMemo(() => {
    if (!streaming) return content;
    // При стриминге добавим невидимый маркер, чтобы каретка висела в конце.
    return content;
  }, [content, streaming]);

  return (
    <div className={`markdown ${streaming ? 'caret' : ''}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeHighlight, { detect: true, ignoreMissing: true }]]}
        components={{
          code(props) {
            const { node, className, children, ...rest } = props as {
              node?: unknown;
              className?: string;
              children?: React.ReactNode;
              inline?: boolean;
            };
            const inline = (props as { inline?: boolean }).inline;
            if (inline) {
              return (
                <code className={className} {...rest}>
                  {children}
                </code>
              );
            }
            const language = /language-([\w-]+)/.exec(className || '')?.[1] ?? '';
            const raw = String(children).replace(/\n$/, '');
            return (
              <CodeBlock language={language} code={raw}>
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
        {display}
      </ReactMarkdown>
    </div>
  );
});
