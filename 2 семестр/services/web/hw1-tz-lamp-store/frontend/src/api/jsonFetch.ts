type ErrorBody = {
  error?: {
    code?: string;
    message?: string;
  };
};

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let response: Response;
  try {
    response = await fetch(url, { ...init, headers });
  } catch (cause) {
    throw new ApiError(0, cause instanceof Error ? cause.message : 'Сеть недоступна');
  }

  const text = await response.text();
  const body = text ? (JSON.parse(text) as unknown) : null;

  if (!response.ok) {
    const err = body as ErrorBody | null;
    const message = err?.error?.message ?? response.statusText ?? `HTTP ${response.status}`;
    const code = err?.error?.code;
    throw new ApiError(response.status, message, code);
  }

  if (response.status === 204 || body === null) {
    return undefined as T;
  }

  return body as T;
}
