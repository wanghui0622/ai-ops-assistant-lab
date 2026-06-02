import { useCallback, useEffect, useRef, useState } from "react";
import type { HookEvent, MetricItem, SessionState } from "../types/session";

const API = "";

export function useSession() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [events, setEvents] = useState<HookEvent[]>([]);
  const [metrics, setMetrics] = useState<MetricItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const refresh = useCallback(async (id: string) => {
    const res = await fetch(`${API}/api/sessions/${id}`);
    if (!res.ok) throw new Error(await res.text());
    setSession(await res.json());
  }, []);

  const init = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch(`${API}/api/sessions`, { method: "POST" });
      const { session_id } = await res.json();
      const mres = await fetch(`${API}/api/metrics`);
      const md = await mres.json();
      setMetrics(md.metrics || []);
      await refresh(session_id);
      if (esRef.current) esRef.current.close();
      const es = new EventSource(`${API}/api/sessions/${session_id}/stream`);
      esRef.current = es;
      es.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data) as HookEvent;
          if (data.type) setEvents((prev) => [...prev, data]);
        } catch { /* ping */ }
      };
      es.addEventListener("skill_start", (ev) => { try { setEvents((p) => [...p, JSON.parse((ev as MessageEvent).data)]); } catch {} });
      ["skill_complete","skill_step","hitl_pause","report_ready","model_call","user_action","session_message"].forEach((t) => {
        es.addEventListener(t, (ev) => { try { setEvents((p) => [...p, JSON.parse((ev as MessageEvent).data)]); } catch {} });
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally { setLoading(false); }
  }, [refresh]);

  useEffect(() => { init(); return () => esRef.current?.close(); }, [init]);

  const sendMessage = async (content: string) => {
    if (!session) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/sessions/${session.session_id}/messages`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSession(await res.json());
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setLoading(false); }
  };

  const sendAction = async (action: string, payload: Record<string, unknown> = {}) => {
    if (!session) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/sessions/${session.session_id}/actions`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action, payload }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSession(await res.json());
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setLoading(false); }
  };

  return { session, events, metrics, loading, error, sendMessage, sendAction, refresh };
}
