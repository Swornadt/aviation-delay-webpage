"use client";

import { useState } from "react";

// TODO (Phase 3): wire this up to POST /api/v1/copilot/chat once the
// backend RAG engine is implemented. See PRD Req 4.4.

export default function CopilotDrawer() {
  const [open, setOpen] = useState(false);

  return (
    <div className="fixed bottom-4 right-4">
      {open ? (
        <div className="w-80 h-96 rounded-xl bg-slate-900 border border-slate-800 flex flex-col">
          <div className="flex items-center justify-between p-3 border-b border-slate-800">
            <span className="text-sm font-medium">Copilot</span>
            <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-100">
              ✕
            </button>
          </div>
          <div className="flex-1 flex items-center justify-center text-slate-500 text-sm px-4 text-center">
            Chat isn&apos;t wired up yet — backend copilot endpoint is a placeholder.
          </div>
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
