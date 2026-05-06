import { useEffect, useState } from 'react';
import { useChatsStore } from '@/entities/chat/model/store';
import { DEFAULT_SETTINGS } from '@/entities/chat/model/types';
import { fetchModels } from '@/shared/api/gigachat';
import { IconClose } from '@/shared/ui/Icon';
import { IconButton } from '@/shared/ui/IconButton';

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
}

/**
 * Панель настроек модели. Позволяет менять:
 *  - модель (подтягивается из /models, fallback — список по умолчанию);
 *  - system prompt;
 *  - temperature, top_p, max_tokens, repetition_penalty;
 *  - режим стриминга (SSE on/off).
 */
export function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const settings = useChatsStore((s) => s.settings);
  const update = useChatsStore((s) => s.updateSettings);
  const [availableModels, setAvailableModels] = useState<string[]>([]);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    fetchModels(controller.signal)
      .then((res) => setAvailableModels(res.data.map((m) => m.id)))
      .catch(() => setAvailableModels(['GigaChat', 'GigaChat-Pro', 'GigaChat-Max', 'GigaChat-2']));
    return () => controller.abort();
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className="flex max-h-[90vh] w-full max-w-lg flex-col rounded-xl border border-border-subtle bg-bg-elevated shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
          <h2 className="text-base font-semibold">Настройки модели</h2>
          <IconButton label="Закрыть" onClick={onClose}>
            <IconClose />
          </IconButton>
        </header>

        <div className="flex-1 space-y-5 overflow-y-auto px-5 py-4">
          <Field label="Модель">
            <select
              value={settings.model}
              onChange={(e) => update({ model: e.target.value })}
              className="w-full rounded-md border border-border-subtle bg-bg-primary px-3 py-2 text-sm focus:border-border-strong focus:outline-none"
            >
              {availableModels.length === 0 && <option value={settings.model}>{settings.model}</option>}
              {availableModels.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Системный промпт">
            <textarea
              value={settings.systemPrompt}
              onChange={(e) => update({ systemPrompt: e.target.value })}
              rows={4}
              className="w-full resize-y rounded-md border border-border-subtle bg-bg-primary px-3 py-2 text-sm focus:border-border-strong focus:outline-none"
            />
          </Field>

          <SliderField
            label="Temperature"
            hint="Креативность ответа. 0 — детерминированно, 2 — хаотично."
            value={settings.temperature}
            onChange={(v) => update({ temperature: v })}
            min={0}
            max={2}
            step={0.05}
          />

          <SliderField
            label="Top-P"
            hint="Порог кумулятивной вероятности токенов."
            value={settings.top_p}
            onChange={(v) => update({ top_p: v })}
            min={0}
            max={1}
            step={0.05}
          />

          <SliderField
            label="Max tokens"
            hint="Максимальный размер ответа в токенах."
            value={settings.max_tokens}
            onChange={(v) => update({ max_tokens: Math.round(v) })}
            min={128}
            max={8192}
            step={64}
            integer
          />

          <SliderField
            label="Repetition penalty"
            hint="Штраф за повторения (>1 — сильнее)."
            value={settings.repetition_penalty}
            onChange={(v) => update({ repetition_penalty: v })}
            min={1}
            max={2}
            step={0.05}
          />

          <label className="flex items-center justify-between rounded-md border border-border-subtle bg-bg-primary px-3 py-2 text-sm">
            <span>
              <span className="font-medium">Streaming (SSE)</span>
              <br />
              <span className="text-xs text-text-muted">Постепенное отображение ответа</span>
            </span>
            <input
              type="checkbox"
              checked={settings.streaming}
              onChange={(e) => update({ streaming: e.target.checked })}
              className="h-4 w-4 accent-accent"
            />
          </label>
        </div>

        <footer className="flex items-center justify-between border-t border-border-subtle px-5 py-3">
          <button
            type="button"
            onClick={() => update(DEFAULT_SETTINGS)}
            className="text-sm text-text-secondary hover:text-text-primary"
          >
            Сбросить к значениям по умолчанию
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md bg-accent px-4 py-1.5 text-sm font-medium text-white hover:bg-accent-hover"
          >
            Готово
          </button>
        </footer>
      </div>
    </div>
  );
}

interface FieldProps {
  label: string;
  children: React.ReactNode;
}

function Field({ label, children }: FieldProps) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium">{label}</span>
      {children}
    </label>
  );
}

interface SliderProps {
  label: string;
  hint: string;
  value: number;
  onChange: (next: number) => void;
  min: number;
  max: number;
  step: number;
  integer?: boolean;
}

function SliderField({ label, hint, value, onChange, min, max, step, integer }: SliderProps) {
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <span className="text-sm font-medium">{label}</span>
        <span className="font-mono text-xs text-text-secondary">
          {integer ? Math.round(value) : value.toFixed(2)}
        </span>
      </div>
      <input
        type="range"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-accent"
      />
      <p className="mt-1 text-xs text-text-muted">{hint}</p>
    </div>
  );
}
