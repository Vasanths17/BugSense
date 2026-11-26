import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from "recharts";

const SEVERITY_COLORS = {
  Critical: "#ef4444", // red-500
  High:     "#f97316", // orange-500
  Medium:   "#eab308", // yellow-500
  Low:      "#3b82f6", // blue-500
};

const CATEGORY_COLORS = {
  "Bug":          "#3b82f6", // blue-500
  "Security":     "#ef4444", // red-500
  "Code Quality": "#10b981", // emerald-500
};

export default function DashboardView({ report, onNavigateToIssues, onDownloadPdf, downloadingPdf, onResetProject }) {
  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center h-96 bg-white border border-gray-200 rounded-xl p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center text-blue-500 text-2xl mb-4">
          📊
        </div>
        <h3 className="text-xl font-bold text-gray-800">No Analysis Run Yet</h3>
        <p className="text-gray-500 text-sm mt-1 max-w-md">
          Upload your project ZIP and click <strong>"Run Analysis"</strong> to generate a complete health score, defect breakdown, and quality metrics.
        </p>
      </div>
    );
  }

  const {
    total_issues,
    severity_breakdown: sev,
    category_breakdown: cat,
    health_score: health,
    file_metrics = [],
  } = report;

  // Data for charts
  const severityData = [
    { name: "Critical", count: sev.critical, color: SEVERITY_COLORS.Critical },
    { name: "High",     count: sev.high,     color: SEVERITY_COLORS.High },
    { name: "Medium",   count: sev.medium,   color: SEVERITY_COLORS.Medium },
    { name: "Low",      count: sev.low,      color: SEVERITY_COLORS.Low },
  ];

  const categoryData = [
    { name: "Bugs",         value: cat.bugs,     color: CATEGORY_COLORS["Bug"] },
    { name: "Security",     value: cat.security, color: CATEGORY_COLORS["Security"] },
    { name: "Code Quality", value: cat.quality,  color: CATEGORY_COLORS["Code Quality"] },
  ].filter(d => d.value > 0);

  // Grade color
  const gradeColors = {
    A: "text-emerald-500 bg-emerald-50 border-emerald-200",
    B: "text-blue-500 bg-blue-50 border-blue-200",
    C: "text-yellow-600 bg-yellow-50 border-yellow-200",
    D: "text-orange-500 bg-orange-50 border-orange-200",
    F: "text-red-500 bg-red-50 border-red-200",
  };

  const gradeStyle = health ? (gradeColors[health.grade] || gradeColors.C) : gradeColors.A;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Analysis Dashboard</h2>
          <p className="text-gray-500 text-sm mt-0.5">
            Static debugging results for <span className="font-semibold text-gray-700">{report.project_name}</span>
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={onDownloadPdf}
            disabled={downloadingPdf}
            className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white font-medium text-sm rounded-lg shadow-sm transition-colors flex items-center gap-2"
          >
            {downloadingPdf ? (
              <>
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                Generating PDF...
              </>
            ) : (
              <>📥 Download PDF Report</>
            )}
          </button>
          <button
            onClick={onNavigateToIssues}
            className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm rounded-lg shadow-sm transition-colors flex items-center gap-2"
          >
            🔍 View All Issues ({total_issues})
          </button>
          <button
            onClick={onResetProject}
            className="px-3 py-2 bg-slate-100 hover:bg-red-50 hover:text-red-600 text-slate-600 font-medium text-sm rounded-lg border border-slate-200 transition-colors"
            title="Clear current scan and upload a new project"
          >
            🔄 New Scan
          </button>
        </div>
      </div>

      {/* Health Score & High Level Overview Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Health Score Card */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Project Health Score</span>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${gradeStyle}`}>
              Grade {health?.grade || "N/A"}
            </span>
          </div>

          <div className="my-4 flex items-baseline gap-3">
            <span className="text-6xl font-black text-gray-900 tracking-tight">
              {health?.score ?? 100}
            </span>
            <span className="text-gray-400 text-lg font-medium">/ 100</span>
            <span className="ml-auto text-sm font-semibold text-gray-600">
              {health?.status || "Healthy"}
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-gray-100 rounded-full h-2.5 mb-4 overflow-hidden">
            <div
              className={`h-2.5 rounded-full ${
                (health?.score ?? 100) >= 80 ? "bg-emerald-500" :
                (health?.score ?? 100) >= 60 ? "bg-yellow-500" : "bg-red-500"
              }`}
              style={{ width: `${health?.score ?? 100}%` }}
            />
          </div>

          <div className="text-xs text-gray-500 border-t border-gray-100 pt-3">
            <p className="leading-relaxed">{health?.explanation}</p>
          </div>
        </div>

        {/* Severity Metrics Cards */}
        <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-red-50/70 border border-red-200/80 rounded-xl p-4 flex flex-col justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-red-600">Critical</span>
            <span className="text-3xl font-extrabold text-red-700 my-1">{sev.critical}</span>
            <span className="text-[11px] text-red-500">Security & syntax breaks</span>
          </div>

          <div className="bg-orange-50/70 border border-orange-200/80 rounded-xl p-4 flex flex-col justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-orange-600">High</span>
            <span className="text-3xl font-extrabold text-orange-700 my-1">{sev.high}</span>
            <span className="text-[11px] text-orange-500">Undefined vars & flaws</span>
          </div>

          <div className="bg-yellow-50/70 border border-yellow-200/80 rounded-xl p-4 flex flex-col justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-yellow-700">Medium</span>
            <span className="text-3xl font-extrabold text-yellow-800 my-1">{sev.medium}</span>
            <span className="text-[11px] text-yellow-600">Logical & quality bugs</span>
          </div>

          <div className="bg-blue-50/70 border border-blue-200/80 rounded-xl p-4 flex flex-col justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-600">Low</span>
            <span className="text-3xl font-extrabold text-blue-700 my-1">{sev.low}</span>
            <span className="text-[11px] text-blue-500">Unused vars & styles</span>
          </div>

          {/* Quick Metrics row */}
          <div className="col-span-2 sm:col-span-2 bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between">
            <div>
              <span className="text-xs uppercase font-bold text-gray-400">Total Issues</span>
              <p className="text-2xl font-bold text-gray-800">{total_issues}</p>
            </div>
            <div className="text-right text-xs text-gray-500">
              <p><strong className="text-gray-700">{report.detected_count}</strong> Confirmed</p>
              <p><strong className="text-gray-700">{report.potential_count}</strong> Potential</p>
            </div>
          </div>

          <div className="col-span-2 sm:col-span-2 bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between">
            <div>
              <span className="text-xs uppercase font-bold text-gray-400">Files Scanned</span>
              <p className="text-2xl font-bold text-gray-800">{file_metrics.length}</p>
            </div>
            <div className="text-right text-xs text-gray-500">
              <p><strong className="text-gray-700">{health?.total_loc?.toLocaleString() ?? 0}</strong> Lines of Code</p>
              <p className="text-emerald-600 font-medium">100% Offline Scanned</p>
            </div>
          </div>
        </div>
      </div>

      {/* Visual Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Bar Chart */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-4">Issues by Severity</h3>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(val) => [val, "Issues"]}
                  contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#fff", borderRadius: "8px" }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Donut / Pie Chart */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-4">Issues by Category</h3>
          <div className="h-60 w-full flex items-center justify-center">
            {categoryData.length === 0 ? (
              <p className="text-gray-400 text-sm">No issues detected in any category!</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cat-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#fff", borderRadius: "8px" }}
                  />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* File Quality & Complexity Table */}
      {file_metrics.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">File Metrics & Maintainability</h3>
              <p className="text-xs text-gray-500">Per-file cyclomatic complexity, lines of code, and maintainability index</p>
            </div>
            <span className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md font-medium">
              {file_metrics.length} Files
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">File</th>
                  <th className="px-4 py-3">Language</th>
                  <th className="px-4 py-3">Lines (LOC)</th>
                  <th className="px-4 py-3">Avg Complexity</th>
                  <th className="px-4 py-3">Maintainability</th>
                  <th className="px-4 py-3">Rank</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {file_metrics.map((fm) => {
                  const rankBadge = {
                    A: "bg-emerald-100 text-emerald-800",
                    B: "bg-blue-100 text-blue-800",
                    C: "bg-yellow-100 text-yellow-800",
                    D: "bg-orange-100 text-orange-800",
                    F: "bg-red-100 text-red-800",
                  }[fm.maintainability_rank || "A"] || "bg-gray-100 text-gray-800";

                  return (
                    <tr key={fm.file_path} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-6 py-3 font-mono text-xs text-gray-800 truncate max-w-xs" title={fm.file_path}>
                        {fm.file_path}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600">
                        {fm.language}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-700 font-medium">
                        {fm.loc}
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {fm.cyclomatic_complexity !== null ? (
                          <span className={fm.cyclomatic_complexity > 10 ? "text-red-600 font-bold" : "text-gray-700"}>
                            {fm.cyclomatic_complexity}
                          </span>
                        ) : "—"}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-700">
                        {fm.maintainability_index !== null ? `${fm.maintainability_index}/100` : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold ${rankBadge}`}>
                          {fm.maintainability_rank || "A"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
