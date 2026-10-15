import { useCallback, useEffect, useRef, useState } from 'react';

const BASE = '/api';

export async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(body.detail || `HTTP ${res.status}`);
    err.status = res.status;
    err.fields = body;
    throw err;
  }
  return body;
}

/** Fetch helper with loading/error state; `deps` re-runs the request (e.g. on filter change). */
export function useApi(path, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const key = JSON.stringify(deps);

  useEffect(() => {
    if (path === null) return;
    let alive = true;
    setLoading(true);
    request(path)
      .then((d) => alive && (setData(d), setError(null)))
      .catch((e) => alive && (setError(e), setData(null)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, key]);

  return { data, error, loading };
}

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const abort = useRef(null);

  const send = useCallback(async (text) => {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    const next = [...messages, { role: 'user', content: trimmed }];
    setMessages(next);
    setBusy(true);
    setError(null);
    abort.current = new AbortController();
    try {
      const data = await request('/chat/', {
        method: 'POST',
        body: JSON.stringify({ messages: next }),
        signal: abort.current.signal,
      });
      setMessages([
        ...next,
        {
          role: 'assistant',
          content: data.reply,
          mode: data.mode,
          provider: data.provider,
          model: data.model,
          note: data.note,
          sources: data.sources,
        },
      ]);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }, [messages, busy]);

  const reset = useCallback(() => {
    abort.current?.abort();
    setMessages([]);
    setError(null);
    setBusy(false);
  }, []);

  return { messages, send, busy, error, reset };
}
