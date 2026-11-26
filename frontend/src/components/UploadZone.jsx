import { useState, useRef } from "react";
import { API_BASE } from "../config";

const ZIP_MAX_MB = 25;
const ZIP_MAX_BYTES = ZIP_MAX_MB * 1024 * 1024;

// ── icons ────────────────────────────────────────────────────────────────────
const UploadCloudIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-16 h-16" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16,16 12,12 8,16" />
    <line x1="12" y1="12" x2="12" y2="21" />
    <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
  </svg>
);

const BugIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M8 2l1.5 1.5" /><path d="M14.5 3.5L16 2" />
    <path d="M9 9a3 3 0 0 1 6 0v5a3 3 0 0 1-6 0V9z" />
    <path d="M6.5 8.5A3.5 3.5 0 0 0 3 12v1a9 9 0 0 0 18 0v-1a3.5 3.5 0 0 0-3.5-3.5" />
    <path d="M3 13h3" /><path d="M18 13h3" /><path d="M12 20v2" />
  </svg>
);

export default function UploadZone({ onUploadSuccess }) {
  const [dragging, setDragging]   = useState(false);
  const [loading,  setLoading]    = useState(false);
  const [error,    setError]      = useState(null);
  const inputRef = useRef(null);

  const validate = (file) => {
    if (!file.name.toLowerCase().endsWith(".zip"))
      return "Only .zip files are accepted.";
    if (file.size > ZIP_MAX_BYTES)
      return `File is too large. Max size is ${ZIP_MAX_MB} MB.`;
    if (file.size === 0)
      return "File is empty.";
    return null;
  };

  const handleFile = async (file) => {
    setError(null);
    const err = validate(file);
    if (err) { setError(err); return; }

    setLoading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/api/upload`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Upload failed.");
      onUploadSuccess(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const onInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Upload Project</h2>
        <p className="text-gray-500 mt-1">Upload your project ZIP file for AI-powered bug analysis</p>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !loading && inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl transition-colors cursor-pointer p-12
          flex flex-col items-center gap-4 select-none
          ${dragging ? "border-blue-500 bg-blue-100" : "border-blue-300 bg-blue-50 hover:bg-blue-100 hover:border-blue-400"}
          ${loading  ? "opacity-60 cursor-not-allowed" : ""}
        `}
      >
        <input ref={inputRef} type="file" accept=".zip" className="hidden" onChange={onInputChange} />

        {loading ? (
          <>
            <div className="w-16 h-16 flex items-center justify-center">
              <svg className="animate-spin w-12 h-12 text-blue-500" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
            </div>
            <p className="text-blue-600 font-medium">Uploading & scanning project…</p>
          </>
        ) : (
          <>
            <div className="text-blue-400"><UploadCloudIcon /></div>
            <div className="text-center">
              <p className="text-gray-700 font-medium text-lg">
                Drop your project ZIP here or click to browse
              </p>
              <p className="text-gray-400 text-sm mt-1">Supports .zip files up to {ZIP_MAX_MB} MB</p>
            </div>
            <button className="mt-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium
              rounded-lg transition-colors shadow-sm pointer-events-none">
              Browse Files
            </button>
          </>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700
          rounded-lg px-4 py-3 text-sm">
          <span className="font-bold mt-0.5">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {/* Info box */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 text-white">
        <div className="flex items-start gap-3">
          <div className="text-blue-400 mt-0.5 flex-shrink-0"><BugIcon /></div>
          <div>
            <h3 className="font-semibold text-lg mb-2">What BugSense Does</h3>
            <ul className="space-y-2 text-slate-300 text-sm">
              {[
                ["AI-Powered Bug Detection",  "Scans your codebase using advanced static analysis to identify bugs, vulnerabilities, and code smells."],
                ["Explainable Analysis",       "Every issue comes with a plain-English explanation of why it's a problem and how to fix it."],
                ["Severity Ranking",           "Issues are ranked Critical → Low so you tackle the most important problems first."],
                ["Detailed Reports",           "Export structured reports for your team, CI pipeline, or audit trail."],
              ].map(([title, body]) => (
                <li key={title} className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span><strong className="text-white">{title}</strong> — {body}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
