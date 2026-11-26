import { useState } from "react";
import UploadZone from "./components/UploadZone";
import FileTree from "./components/FileTree";
import CodeViewer from "./components/CodeViewer";
import { LangPill } from "./components/LangPill";
import { API_BASE } from "./config";

// ── Icons ─────────────────────────────────────────────────────────────────────
const BugIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M8 2l1.5 1.5" /><path d="M14.5 3.5L16 2" />
    <path d="M9 9a3 3 0 0 1 6 0v5a3 3 0 0 1-6 0V9z" />
    <path d="M6.5 8.5A3.5 3.5 0 0 0 3 12v1a9 9 0 0 0 18 0v-1a3.5 3.5 0 0 0-3.5-3.5" />
    <path d="M3 13h3" /><path d="M18 13h3" /><path d="M12 20v2" />
  </svg>
);
const FolderIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
  </svg>
);
const ChartIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </svg>
);
const SearchIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);
const FileIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14,2 14,8 20,8" />
  </svg>
);

// ── Health Badge ──────────────────────────────────────────────────────────────
import { useState as uState, useEffect as uEffect } from "react";
function HealthBadge() {
  const [status, setStatus] = uState("checking");
  uEffect(() => {
    fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(3000) })
      .then(r => r.ok ? setStatus("connected") : setStatus("disconnected"))
      .catch(() => setStatus("disconnected"));
  }, []);

  const styles = {
    checking:     "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
    connected:    "bg-green-500/20  text-green-300  border-green-500/30",
    disconnected: "bg-red-500/20    text-red-300    border-red-500/30",
  };
  const dots = {
    checking:     "bg-yellow-400 animate-pulse",
    connected:    "bg-green-400",
    disconnected: "bg-red-400",
  };
  const labels = { checking: "Checking…", connected: "Connected", disconnected: "Disconnected" };

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs
      font-medium border ${styles[status]}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dots[status]}`} />
      {labels[status]}
    </span>
  );
}

// ── Placeholder views ─────────────────────────────────────────────────────────
function AnalysisDashboardView() {
  const cards = [
    { label: "Bugs Found",     value: "0",   color: "text-red-500",    bg: "bg-red-50",    border: "border-red-100" },
    { label: "Files Analyzed", value: "0",   color: "text-blue-500",   bg: "bg-blue-50",   border: "border-blue-100" },
    { label: "Analysis Time",  value: "0s",  color: "text-purple-500", bg: "bg-purple-50", border: "border-purple-100" },
    { label: "Severity",       value: "N/A", color: "text-orange-500", bg: "bg-orange-50", border: "border-orange-100" },
  ];
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Analysis Dashboard</h2>
        <p className="text-gray-500 mt-1">Overview of your latest analysis run</p>
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {cards.map(c => (
          <div key={c.label} className={`${c.bg} ${c.border} border rounded-xl p-5 flex flex-col gap-1`}>
            <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">{c.label}</span>
            <span className={`text-4xl font-bold ${c.color}`}>{c.value}</span>
          </div>
        ))}
      </div>
      <div className="flex flex-col items-center justify-center h-56 bg-white border border-gray-200 rounded-xl">
        <div className="text-gray-300 mb-3"><ChartIcon /></div>
        <p className="text-gray-400 font-medium">No analysis run yet</p>
        <p className="text-gray-300 text-sm mt-1">Upload a project to begin</p>
      </div>
    </div>
  );
}

function IssuesExplorerView() {
  const headers = ["ID", "File", "Line", "Severity", "Type", "Description"];
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Issues Explorer</h2>
        <p className="text-gray-500 mt-1">Browse and filter detected issues</p>
      </div>
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-gray-200">
                {headers.map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={headers.length} className="text-center py-16">
                  <div className="flex flex-col items-center gap-2 text-gray-400">
                    <SearchIcon />
                    <p className="font-medium text-gray-500">No issues found yet</p>
                    <p className="text-xs text-gray-300">Upload and analyze a project to see issues here</p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ReportsView() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Reports</h2>
        <p className="text-gray-500 mt-1">Generate and export analysis reports</p>
      </div>
      <div className="bg-white border border-gray-200 rounded-xl p-8 flex flex-col items-center gap-5">
        <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center text-gray-400">
          <FileIcon />
        </div>
        <div className="text-center">
          <p className="font-medium text-gray-600">No reports available</p>
          <p className="text-sm text-gray-400 mt-1">Run an analysis first to generate a report</p>
        </div>
        <button disabled className="px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg opacity-40 cursor-not-allowed">
          Generate Report
        </button>
      </div>
    </div>
  );
}

// ── Upload + File Explorer View ───────────────────────────────────────────────
function UploadProjectView() {
  const [project,      setProject]      = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);  // { path, name }
  const [analyzing,    setAnalyzing]    = useState(false);
  const [analyzeMsg,   setAnalyzeMsg]   = useState(null);

  const handleAnalyze = async () => {
    if (!project) return;
    setAnalyzing(true);
    setAnalyzeMsg(null);
    try {
      // Placeholder – real endpoint wired in a future step
      const res = await fetch(`${API_BASE}/api/analyze/${project.project_id}`, { method: "POST" });
      if (res.status === 404) {
        setAnalyzeMsg("Analysis engine coming soon! (Step 3)");
      } else {
        const d = await res.json().catch(() => ({}));
        setAnalyzeMsg(d.detail ?? "Analysis started.");
      }
    } catch {
      setAnalyzeMsg("Analysis engine coming soon! (Step 3)");
    } finally {
      setAnalyzing(false);
    }
  };

  if (!project) {
    return <UploadZone onUploadSuccess={setProject} />;
  }

  // ── Project loaded layout ────────────────────────────────────────────────
  return (
    <div className="flex gap-0 h-full -m-8">
      {/* ── Left panel: tree ─────────────────────────────────────── */}
      <div className="w-72 flex-shrink-0 bg-slate-900 border-r border-slate-700
        flex flex-col h-full overflow-hidden">
        {/* Project header */}
        <div className="px-4 py-3 border-b border-slate-700 flex-shrink-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-white font-semibold text-sm truncate" title={project.project_name}>
              📂 {project.project_name}
            </h3>
            <button
              onClick={() => { setProject(null); setSelectedFile(null); }}
              className="text-xs text-slate-500 hover:text-slate-300 transition-colors flex-shrink-0"
              title="Upload another project"
            >
              ✕
            </button>
          </div>
          {/* Stats */}
          <div className="mt-2 flex gap-3 text-xs text-slate-400">
            <span>{project.total_files} files</span>
            <span>·</span>
            <span>{project.supported_files_count} analysable</span>
          </div>
          {/* Language breakdown */}
          {Object.keys(project.language_breakdown).length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {Object.entries(project.language_breakdown)
                .sort((a, b) => b[1] - a[1])
                .map(([lang, count]) => (
                  <span key={lang} className="text-xs bg-slate-700 text-slate-300 rounded px-1.5 py-0.5">
                    {lang} <span className="text-slate-500">{count}</span>
                  </span>
                ))}
            </div>
          )}
        </div>

        {/* File Tree */}
        <div className="flex-1 overflow-y-auto text-sm">
          <FileTree
            nodes={project.file_tree}
            selectedPath={selectedFile?.path}
            onFileClick={(node) => setSelectedFile({ path: node.path, name: node.name })}
          />
        </div>

        {/* Run Analysis button */}
        <div className="p-3 border-t border-slate-700 flex-shrink-0">
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5
              bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed
              text-white font-semibold rounded-lg transition-colors shadow-md text-sm"
          >
            {analyzing ? (
              <>
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10"
                    stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor"
                    d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                Running…
              </>
            ) : (
              <>🔍 Run Analysis</>
            )}
          </button>
          {analyzeMsg && (
            <p className="mt-2 text-xs text-center text-slate-400">{analyzeMsg}</p>
          )}
        </div>
      </div>

      {/* ── Right panel: code viewer ──────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden bg-slate-900">
        {selectedFile ? (
          <CodeViewer
            projectId={project.project_id}
            filePath={selectedFile.path}
            onClose={() => setSelectedFile(null)}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 text-slate-500">
            <FileIcon />
            <p className="text-sm">Select a file from the tree to view its contents</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Nav config ────────────────────────────────────────────────────────────────
const NAV = [
  { id: "upload",    label: "Upload Project",     emoji: "📂", View: UploadProjectView },
  { id: "dashboard", label: "Analysis Dashboard", emoji: "📊", View: AnalysisDashboardView },
  { id: "issues",    label: "Issues Explorer",    emoji: "🔍", View: IssuesExplorerView },
  { id: "reports",   label: "Reports",            emoji: "📄", View: ReportsView },
];

// ── Root App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [activeId, setActiveId] = useState("upload");
  const ActiveView = NAV.find(n => n.id === activeId)?.View ?? UploadProjectView;

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Top Nav */}
      <header className="bg-slate-900 border-b border-slate-700 flex items-center
        justify-between px-6 py-3 flex-shrink-0 z-10 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="text-blue-400"><BugIcon /></div>
          <div>
            <h1 className="text-white font-bold text-xl leading-none tracking-tight">BugSense</h1>
            <p className="text-slate-400 text-xs mt-0.5 leading-none">Explainable AI Debugging</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-slate-500 text-xs hidden sm:block">Backend status:</span>
          <HealthBadge />
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-60 bg-slate-800 flex-shrink-0 flex flex-col border-r border-slate-700">
          <nav className="flex-1 py-4 space-y-1 px-3">
            {NAV.map(item => {
              const active = activeId === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveId(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm
                    font-medium transition-all text-left
                    ${active
                      ? "bg-blue-600 text-white shadow-md"
                      : "text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                    }`}
                >
                  <span className="text-base leading-none">{item.emoji}</span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
          <div className="px-4 py-4 border-t border-slate-700">
            <div className="text-xs text-slate-500 text-center">BugSense v0.2.0</div>
          </div>
        </aside>

        {/* Main */}
        <main className={`flex-1 overflow-y-auto ${activeId === "upload" ? "p-0" : "p-8"}`}>
          <ActiveView />
        </main>
      </div>
    </div>
  );
}
