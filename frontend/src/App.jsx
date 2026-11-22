import { useState, useEffect } from 'react'

// ── Inline SVG icons ────────────────────────────────────────────────────────

const BugIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M8 2l1.5 1.5"/>
    <path d="M14.5 3.5L16 2"/>
    <path d="M9 9a3 3 0 0 1 6 0v5a3 3 0 0 1-6 0V9z"/>
    <path d="M6.5 8.5A3.5 3.5 0 0 0 3 12v1a9 9 0 0 0 18 0v-1a3.5 3.5 0 0 0-3.5-3.5"/>
    <path d="M3 13h3"/>
    <path d="M18 13h3"/>
    <path d="M12 20v2"/>
  </svg>
)

const FolderIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
  </svg>
)

const ChartIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10"/>
    <line x1="12" y1="20" x2="12" y2="4"/>
    <line x1="6" y1="20" x2="6" y2="14"/>
  </svg>
)

const SearchIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
)

const FileIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14,2 14,8 20,8"/>
  </svg>
)

const UploadCloudIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-16 h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16,16 12,12 8,16"/>
    <line x1="12" y1="12" x2="12" y2="21"/>
    <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
  </svg>
)

// ── Views ────────────────────────────────────────────────────────────────────

function UploadProjectView() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Upload Project</h2>
        <p className="text-gray-500 mt-1">Upload your project ZIP file for AI-powered bug analysis</p>
      </div>

      {/* Drop Zone */}
      <div className="border-2 border-dashed border-blue-300 rounded-xl bg-blue-50 hover:bg-blue-100 hover:border-blue-400 transition-colors cursor-pointer p-12 flex flex-col items-center gap-4">
        <div className="text-blue-400">
          <UploadCloudIcon />
        </div>
        <div className="text-center">
          <p className="text-gray-700 font-medium text-lg">Drop your project ZIP here or click to browse</p>
          <p className="text-gray-400 text-sm mt-1">Supports .zip files up to 50MB</p>
        </div>
        <button className="mt-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors shadow-sm">
          Browse Files
        </button>
      </div>

      {/* Info Box */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 text-white">
        <div className="flex items-start gap-3">
          <div className="text-blue-400 mt-0.5 flex-shrink-0">
            <BugIcon />
          </div>
          <div>
            <h3 className="font-semibold text-lg mb-2">What BugSense Does</h3>
            <ul className="space-y-2 text-slate-300 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5">✓</span>
                <span><strong className="text-white">AI-Powered Bug Detection</strong> — Scans your codebase using advanced static analysis and language models to identify bugs, vulnerabilities, and code smells</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5">✓</span>
                <span><strong className="text-white">Explainable Analysis</strong> — Every issue comes with a plain-English explanation of why it's a problem and how to fix it</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5">✓</span>
                <span><strong className="text-white">Severity Ranking</strong> — Issues are ranked by severity (Critical, High, Medium, Low) so you tackle the most important problems first</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5">✓</span>
                <span><strong className="text-white">Detailed Reports</strong> — Export structured reports for your team, CI pipeline, or audit trail</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

function AnalysisDashboardView() {
  const statCards = [
    { label: 'Bugs Found', value: '0', color: 'text-red-500', bg: 'bg-red-50', border: 'border-red-100' },
    { label: 'Files Analyzed', value: '0', color: 'text-blue-500', bg: 'bg-blue-50', border: 'border-blue-100' },
    { label: 'Analysis Time', value: '0s', color: 'text-purple-500', bg: 'bg-purple-50', border: 'border-purple-100' },
    { label: 'Severity', value: 'N/A', color: 'text-orange-500', bg: 'bg-orange-50', border: 'border-orange-100' },
  ]
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Analysis Dashboard</h2>
        <p className="text-gray-500 mt-1">Overview of your latest analysis run</p>
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {statCards.map(card => (
          <div key={card.label} className={`${card.bg} ${card.border} border rounded-xl p-5 flex flex-col gap-1`}>
            <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">{card.label}</span>
            <span className={`text-4xl font-bold ${card.color}`}>{card.value}</span>
          </div>
        ))}
      </div>
      <div className="flex flex-col items-center justify-center h-56 bg-white border border-gray-200 rounded-xl">
        <div className="text-gray-300 mb-3">
          <ChartIcon />
        </div>
        <p className="text-gray-400 font-medium">No analysis run yet</p>
        <p className="text-gray-300 text-sm mt-1">Upload a project to begin</p>
      </div>
    </div>
  )
}

function IssuesExplorerView() {
  const headers = ['ID', 'File', 'Line', 'Severity', 'Type', 'Description']
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
  )
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
        <button
          disabled
          className="px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg opacity-40 cursor-not-allowed"
        >
          Generate Report
        </button>
      </div>
    </div>
  )
}

// ── Navigation config ─────────────────────────────────────────────────────

const NAV_ITEMS = [
  { id: 'upload', label: 'Upload Project', emoji: '📂', Icon: FolderIcon, View: UploadProjectView },
  { id: 'dashboard', label: 'Analysis Dashboard', emoji: '📊', Icon: ChartIcon, View: AnalysisDashboardView },
  { id: 'issues', label: 'Issues Explorer', emoji: '🔍', Icon: SearchIcon, View: IssuesExplorerView },
  { id: 'reports', label: 'Reports', emoji: '📄', Icon: FileIcon, View: ReportsView },
]

// ── Health Status Badge ───────────────────────────────────────────────────

function HealthBadge() {
  const [status, setStatus] = useState('checking') // 'checking' | 'connected' | 'disconnected'

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/health', { signal: AbortSignal.timeout(3000) })
        if (res.ok) {
          setStatus('connected')
        } else {
          setStatus('disconnected')
        }
      } catch {
        setStatus('disconnected')
      }
    }
    check()
  }, [])

  if (status === 'checking') {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-300 border border-yellow-500/30">
        <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
        Checking…
      </span>
    )
  }
  if (status === 'connected') {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-300 border border-green-500/30">
        <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
        Connected
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-300 border border-red-500/30">
      <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
      Disconnected
    </span>
  )
}

// ── Root App ──────────────────────────────────────────────────────────────

export default function App() {
  const [activeView, setActiveView] = useState('upload')
  const ActiveView = NAV_ITEMS.find(n => n.id === activeView)?.View ?? UploadProjectView

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Top Nav */}
      <header className="bg-slate-900 border-b border-slate-700 flex items-center justify-between px-6 py-3 flex-shrink-0 z-10 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="text-blue-400">
            <BugIcon />
          </div>
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

      {/* Body: Sidebar + Main */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-60 bg-slate-800 flex-shrink-0 flex flex-col border-r border-slate-700">
          <nav className="flex-1 py-4 space-y-1 px-3">
            {NAV_ITEMS.map(item => {
              const isActive = activeView === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveView(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-left group
                    ${isActive
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                    }`}
                >
                  <span className="text-base leading-none">{item.emoji}</span>
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>

          {/* Sidebar Footer */}
          <div className="px-4 py-4 border-t border-slate-700">
            <div className="text-xs text-slate-500 text-center">
              BugSense v0.1.0
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-8">
          <ActiveView />
        </main>
      </div>
    </div>
  )
}
