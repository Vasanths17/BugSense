import { useEffect, useState } from "react";
import { API_BASE } from "../config";

const LANGUAGE_SYNTAX_HINT = {
  "Python":           "python",
  "JavaScript":       "javascript",
  "JavaScript (JSX)": "jsx",
  "TypeScript":       "typescript",
  "TypeScript (TSX)": "tsx",
  "HTML":             "html",
  "CSS":              "css",
  "Java":             "java",
  "C":                "c",
  "C++":              "cpp",
};

export default function CodeViewer({ projectId, filePath, onClose }) {
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const [data,    setData]    = useState(null);  // { path, language, lines, total_lines }

  useEffect(() => {
    if (!projectId || !filePath) return;
    setLoading(true);
    setError(null);
    setData(null);

    fetch(`${API_BASE}/api/project/${projectId}/file?path=${encodeURIComponent(filePath)}`)
      .then(r => r.json().then(j => ({ ok: r.ok, body: j })))
      .then(({ ok, body }) => {
        if (!ok) throw new Error(body.detail ?? "Could not load file.");
        setData(body);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [projectId, filePath]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800
        border-b border-slate-700 flex-shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-slate-400 text-xs font-mono truncate">{filePath}</span>
          {data && (
            <span className="flex-shrink-0 text-xs bg-slate-700 text-slate-300
              px-2 py-0.5 rounded font-medium">
              {data.language}
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          className="ml-3 flex-shrink-0 text-slate-400 hover:text-white transition-colors"
          title="Close"
        >
          ✕
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto bg-slate-900">
        {loading && (
          <div className="flex items-center justify-center h-32 text-slate-400">
            <svg className="animate-spin w-6 h-6 mr-2" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10"
                stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
            Loading…
          </div>
        )}

        {error && (
          <div className="p-4 text-red-400 text-sm">⚠ {error}</div>
        )}

        {data && (
          <table className="w-full text-sm font-mono border-collapse">
            <tbody>
              {data.lines.map((line, idx) => (
                <tr key={idx} className="hover:bg-slate-800/60 group">
                  <td className="select-none text-right pr-4 pl-4 py-px
                    text-slate-600 group-hover:text-slate-500 w-12 border-r
                    border-slate-800 text-xs align-top">
                    {idx + 1}
                  </td>
                  <td className="pl-4 pr-4 py-px text-slate-200 whitespace-pre align-top
                    leading-5">
                    {line || " "}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer */}
      {data && (
        <div className="flex-shrink-0 px-4 py-1.5 bg-slate-800 border-t border-slate-700
          text-xs text-slate-500 flex gap-4">
          <span>{data.total_lines} lines</span>
          <span className="text-slate-600">|</span>
          <span>Read-only view</span>
        </div>
      )}
    </div>
  );
}
