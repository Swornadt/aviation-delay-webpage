"use client";

import { useState } from "react";
import { askCopilot } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
  sql?: string;
};

export default function CopilotDrawer() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const prompt = input.trim();
    if (!prompt || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: prompt }]);
    setInput("");
    setLoading(true);

    try {
      const res = await askCopilot(prompt);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, sql: res.generated_sql },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Something went wrong: ${(err as Error).message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed bottom-4 right-4">
      {open ? (
        <div className="w-96 h-[28rem] rounded-xl bg-slate-900 border border-slate-800 flex flex-col">
          <div className="flex items-center justify-between p-3 border-b border-slate-800">
            <span className="text-sm font-medium">Copilot</span>
            <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-100">
              ✕
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm">
            {messages.length === 0 && (
              <div className="text-slate-500 text-center mt-8">
                Ask about today&apos;s flights, delays, or cancellations.
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                <div
                  className={`inline-block rounded-lg px-3 py-2 max-w-[85%] ${
                    m.role === "user" ? "bg-sky-600 text-white" : "bg-slate-800 text-slate-100"
                  }`}
                >
                  {m.content}
                </div>
                {m.sql && (
                  <details className="mt-1 text-xs text-slate-500">
                    <summary className="cursor-pointer">Show SQL</summary>
                    <pre className="whitespace-pre-wrap text-left mt-1">{m.sql}</pre>
                  </details>
                )}
              </div>
            ))}
            {loading && <div className="text-slate-500 text-xs">Thinking…</div>}
          </div>

          <form onSubmit={handleSubmit} className="p-3 border-t border-slate-800 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. which carrier had the most delays today?"
              className="flex-1 rounded-md bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-600"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-md bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-sm px-3"
            >
              Ask
            </button>
          </form>
        </div>
      ) : (
        <button
          onClick={() => setOpen(true)}
          className="rounded-full bg-sky-600 hover:bg-sky-500 text-white px-4 py-3 shadow-lg text-sm font-medium"
        >
          Ask Copilot
        </button>
      )}
    </div>
  );
}