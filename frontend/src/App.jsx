import { useState, useEffect } from "react";
import UploadZone from "./components/UploadZone";
import FileTree from "./components/FileTree";
import CodeViewer from "./components/CodeViewer";
import DashboardView from "./components/DashboardView";
import IssuesExplorerView from "./components/IssuesExplorerView";
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
const FileIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14,2 14,8 20,8" />
  </svg>
);

// ── Health Badge ──────────────────────────────────────────────────────────────
function HealthBadge() {
  const [status, setStatus] = useState("checking");
  useEffect(() => {
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
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${styles[status]}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dots[status]}`} />
      {labels[status]}
    </span>
  );
}

// ── Reports Placeholder View ─────────────────────────────────────────────────
function ReportsView({ report }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Reports</h2>
        <p className="text-gray-500 mt-1">Generate and export audit and compliance reports</p>
      </div>
      <div className="bg-white border border-gray-200 rounded-xl p-8 flex flex-col items-center gap-5">
        <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center text-blue-500 text-2xl">
          📄
        </div>
        <div className="text-center">
          <p className="font-semibold text-gray-700">
            {report ? `Report ready for ${report.project_name}` : "No reports generated yet"}
          </p>
          <p className="text-sm text-gray-400 mt-1">
            {report ? `Total issues: ${report.total_issues} · Health Score: ${report.health_score?.score ?? 100}/100` : "Run an analysis first to generate a structured report"}
          </p>
        </div>
        <button
          onClick={() => {
            if (!report) return;
            const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${report.project_name}_analysis_report.json`;
            a.click();
          }}
          disabled={!report}
          className={`px-6 py-2.5 rounded-lg font-medium transition-colors shadow-sm ${
            report ? "bg-blue-600 hover:bg-blue-700 text-white cursor-pointer" : "bg-blue-600 text-white opacity-40 cursor-not-allowed"
          }`}
        >
          Export JSON Report
        </button>
      </div>
    </div>
  );
}

// ── Root App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [activeId, setActiveId]         = useState("upload");
  const [project, setProject]           = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [report, setReport]             = useState(null);
  const [analyzing, setAnalyzing]       = useState(false);
  const [analysisStep, setAnalysisStep] = useState("");

  const handleRunAnalysis = async () => {
    if (!project) return;
    setAnalyzing(true);
    setAnalysisStep("Initializing Static Analysis...");

    try {
      setAnalysisStep("Running AST, Ruff, Bandit & Radon Scanners...");
      const res = await fetch(`${API_BASE}/api/analyze/${project.project_id}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed.");

      setAnalysisStep("Building Explainable Issue Cards...");
      setTimeout(() => {
        setReport(data);
        setAnalyzing(false);
        setAnalysisStep("");
        setActiveId("dashboard");
      }, 500);
    } catch (err) {
      alert(`Error during analysis: ${err.message}`);
      setAnalyzing(false);
      setAnalysisStep("");
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Top Nav */}
      <header className="bg-slate-900 border-b border-slate-700 flex items-center justify-between px-6 py-3 flex-shrink-0 z-10 shadow-lg">
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
            {[
              { id: "upload",    label: "Upload Project",     emoji: "📂" },
              { id: "dashboard", label: "Analysis Dashboard", emoji: "📊" },
              { id: "issues",    label: "Issues Explorer",    emoji: "🔍", badge: report ? report.total_issues : null },
              { id: "reports",   label: "Reports",            emoji: "📄" },
            ].map(item => {
              const active = activeId === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveId(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-left ${
                    active ? "bg-blue-600 text-white shadow-md" : "text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-base leading-none">{item.emoji}</span>
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== null && item.badge !== undefined && (
                    <span className={`text-[11px] px-1.5 py-0.5 rounded-full font-bold ${
                      active ? "bg-blue-800 text-white" : "bg-slate-700 text-slate-300"
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
          <div className="px-4 py-4 border-t border-slate-700 text-xs text-slate-500 text-center">
            BugSense v0.4.0
          </div>
        </aside>

        {/* Main View Area */}
        <main className={`flex-1 overflow-y-auto ${activeId === "upload" ? "p-0" : "p-8"}`}>
          {activeId === "upload" && (
            !project ? (
              <div className="p-8">
                <UploadZone onUploadSuccess={(data) => {
                  setProject(data);
                  setReport(null);
                }} />
              </div>
            ) : (
              <div className="flex gap-0 h-full">
                {/* File Tree Left Sub-Panel */}
                <div className="w-72 flex-shrink-0 bg-slate-900 border-r border-slate-700 flex flex-col h-full overflow-hidden">
                  <div className="px-4 py-3 border-b border-slate-700 flex-shrink-0">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-white font-semibold text-sm truncate" title={project.project_name}>
                        📂 {project.project_name}
                      </h3>
                      <button
                        onClick={() => { setProject(null); setSelectedFile(null); setReport(null); }}
                        className="text-xs text-slate-500 hover:text-slate-300 transition-colors flex-shrink-0"
                        title="Upload another project"
                      >
                        ✕
                      </button>
                    </div>
                    <div className="mt-2 flex gap-3 text-xs text-slate-400">
                      <span>{project.total_files} files</span>
                      <span>·</span>
                      <span>{project.supported_files_count} analysable</span>
                    </div>
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

                  <div className="flex-1 overflow-y-auto text-sm">
                    <FileTree
                      nodes={project.file_tree}
                      selectedPath={selectedFile?.path}
                      onFileClick={(node) => setSelectedFile({ path: node.path, name: node.name })}
                    />
                  </div>

                  {/* Run Analysis CTA */}
                  <div className="p-3 border-t border-slate-700 flex-shrink-0">
                    <button
                      onClick={handleRunAnalysis}
                      disabled={analyzing}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors shadow-md text-sm"
                    >
                      {analyzing ? (
                        <>
                          <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                          </svg>
                          Analyzing…
                        </>
                      ) : (
                        <>⚡ Run Analysis</>
                      )}
                    </button>
                    {analysisStep && (
                      <p className="mt-2 text-xs text-center text-blue-400 animate-pulse font-medium">
                        {analysisStep}
                      </p>
                    )}
                  </div>
                </div>

                {/* Code Viewer Right Sub-Panel */}
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
            )
          )}

          {activeId === "dashboard" && (
            <DashboardView
              report={report}
              onNavigateToIssues={() => setActiveId("issues")}
            />
          )}

          {activeId === "issues" && (
            <IssuesExplorerView report={report} />
          )}

          {activeId === "reports" && (
            <ReportsView report={report} />
          )}
        </main>
      </div>
    </div>
  );
}
