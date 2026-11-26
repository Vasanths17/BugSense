import React, { useState, useMemo } from "react";

const SEVERITY_BADGES = {
  Critical: "bg-red-100 text-red-700 border-red-300",
  High:     "bg-orange-100 text-orange-800 border-orange-300",
  Medium:   "bg-yellow-100 text-yellow-800 border-yellow-300",
  Low:      "bg-blue-100 text-blue-800 border-blue-300",
};

const CATEGORY_BADGES = {
  "Bug":          "bg-blue-50 text-blue-700 border-blue-200",
  "Security":     "bg-red-50 text-red-700 border-red-200",
  "Code Quality": "bg-emerald-50 text-emerald-700 border-emerald-200",
};

export default function IssuesExplorerView({ report }) {
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [searchTerm, setSearchTerm]       = useState("");
  const [severityFilter, setSeverityFilter] = useState("All");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [typeFilter, setTypeFilter]         = useState("All");

  const issues = report?.issues || [];

  // Filter logic
  const filteredIssues = useMemo(() => {
    return issues.filter((issue) => {
      // Search term
      if (searchTerm) {
        const query = searchTerm.toLowerCase();
        const matchTitle = issue.title.toLowerCase().includes(query);
        const matchFile = issue.file_name.toLowerCase().includes(query);
        const matchRule = issue.rule_id.toLowerCase().includes(query);
        const matchExplanation = issue.explanation.toLowerCase().includes(query);
        if (!matchTitle && !matchFile && !matchRule && !matchExplanation) {
          return false;
        }
      }

      // Severity
      if (severityFilter !== "All" && issue.severity !== severityFilter) {
        return false;
      }

      // Category
      if (categoryFilter !== "All" && issue.category !== categoryFilter) {
        return false;
      }

      // Detection Type
      if (typeFilter !== "All" && issue.detection_type !== typeFilter) {
        return false;
      }

      return true;
    });
  }, [issues, searchTerm, severityFilter, categoryFilter, typeFilter]);

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center h-96 bg-white border border-gray-200 rounded-xl p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center text-blue-500 text-2xl mb-4">
          🔍
        </div>
        <h3 className="text-xl font-bold text-gray-800">No Issues to Explore</h3>
        <p className="text-gray-500 text-sm mt-1 max-w-md">
          Run an analysis on your project first to view and filter detected issues, security flaws, and code smells.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Issues Explorer</h2>
        <p className="text-gray-500 text-sm mt-0.5">
          Showing {filteredIssues.length} of {issues.length} total findings for {report.project_name}
        </p>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        {/* Search */}
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Search by issue title, file name, or keyword..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <span className="absolute left-3 top-2.5 text-gray-400 text-sm">🔍</span>
          {searchTerm && (
            <button
              onClick={() => setSearchTerm("")}
              className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600 text-xs"
            >
              ✕
            </button>
          )}
        </div>

        {/* Dropdowns */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Severity */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="All">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>

          {/* Category */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="All">All Categories</option>
            <option value="Bug">Bugs</option>
            <option value="Security">Security</option>
            <option value="Code Quality">Code Quality</option>
          </select>

          {/* Detection Type */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="All">All Confidence</option>
            <option value="Detected">Detected (Confirmed)</option>
            <option value="Potential">Potential (Heuristic)</option>
          </select>
        </div>
      </div>

      {/* Issues Table */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">ID & Title</th>
                <th className="px-4 py-3.5">Category</th>
                <th className="px-4 py-3.5">Severity</th>
                <th className="px-4 py-3.5">Location</th>
                <th className="px-4 py-3.5">Confidence</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredIssues.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-400">
                    <p className="text-base font-semibold text-gray-600">No issues matching your filters</p>
                    <p className="text-xs text-gray-400 mt-1">Try resetting search or filters</p>
                  </td>
                </tr>
              ) : (
                filteredIssues.map((issue) => (
                  <tr
                    key={issue.id}
                    onClick={() => setSelectedIssue(issue)}
                    className="hover:bg-blue-50/50 cursor-pointer transition-colors group"
                  >
                    <td className="px-6 py-3.5">
                      <div className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                        {issue.title}
                      </div>
                      <div className="text-xs text-gray-400 font-mono mt-0.5">
                        {issue.id} · <span className="text-gray-500">{issue.rule_id}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium border ${CATEGORY_BADGES[issue.category]}`}>
                        {issue.category}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold border ${SEVERITY_BADGES[issue.severity]}`}>
                        {issue.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 font-mono text-xs text-gray-600 max-w-xs truncate" title={issue.file_name}>
                      {issue.file_name}:{issue.line_number ?? "—"}
                    </td>
                    <td className="px-4 py-3.5">
                      <span className={`inline-block text-xs font-medium ${
                        issue.detection_type === "Detected" ? "text-emerald-600" : "text-amber-600"
                      }`}>
                        {issue.detection_type === "Detected" ? "● Confirmed" : "○ Potential"}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedIssue(issue);
                        }}
                        className="text-xs bg-slate-100 hover:bg-blue-600 hover:text-white px-3 py-1 rounded-md font-medium text-slate-700 transition-colors"
                      >
                        Explain ➔
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Modal / Explainable Issue Card ── */}
      {selectedIssue && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden border border-gray-200">
            {/* Modal Header */}
            <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${SEVERITY_BADGES[selectedIssue.severity]}`}>
                  {selectedIssue.severity}
                </span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${CATEGORY_BADGES[selectedIssue.category]}`}>
                  {selectedIssue.category}
                </span>
                <span className="text-xs text-slate-400 font-mono">{selectedIssue.id}</span>
              </div>
              <button
                onClick={() => setSelectedIssue(null)}
                className="text-slate-400 hover:text-white text-lg font-bold transition-colors w-8 h-8 rounded-full flex items-center justify-center hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            {/* Modal Body - Scrollable */}
            <div className="p-6 overflow-y-auto space-y-6">
              {/* Title & File Path */}
              <div>
                <h3 className="text-xl font-bold text-gray-900">{selectedIssue.title}</h3>
                <div className="mt-1 flex items-center gap-2 text-xs font-mono text-gray-500 bg-gray-50 px-3 py-1.5 rounded-md border border-gray-200">
                  <span>📄 {selectedIssue.file_name}</span>
                  {selectedIssue.line_number && (
                    <span className="text-blue-600 font-bold">Line {selectedIssue.line_number}</span>
                  )}
                  <span className="ml-auto text-gray-400">Tool: {selectedIssue.tool}</span>
                </div>
              </div>

              {/* Read-Only Code Context Snippet */}
              {selectedIssue.code_snippet && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">Code Context</h4>
                  <div className="bg-slate-900 text-slate-100 rounded-xl p-4 font-mono text-xs overflow-x-auto shadow-inner border border-slate-800">
                    <pre className="whitespace-pre leading-relaxed">{selectedIssue.code_snippet}</pre>
                  </div>
                </div>
              )}

              {/* Structured 4-Part Explanation Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 1. What was found */}
                <div className="bg-blue-50/60 border border-blue-200 rounded-xl p-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-blue-700 flex items-center gap-1.5 mb-1.5">
                    <span>💡</span> Simple Explanation
                  </h4>
                  <p className="text-xs text-gray-700 leading-relaxed">{selectedIssue.explanation}</p>
                </div>

                {/* 2. Why it matters */}
                <div className="bg-amber-50/60 border border-amber-200 rounded-xl p-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-amber-700 flex items-center gap-1.5 mb-1.5">
                    <span>❓</span> Why It Matters
                  </h4>
                  <p className="text-xs text-gray-700 leading-relaxed">{selectedIssue.why_it_matters}</p>
                </div>

                {/* 3. Possible Impact */}
                <div className="bg-red-50/60 border border-red-200 rounded-xl p-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-red-700 flex items-center gap-1.5 mb-1.5">
                    <span>⚠️</span> Possible Impact
                  </h4>
                  <p className="text-xs text-gray-700 leading-relaxed">{selectedIssue.possible_impact}</p>
                </div>

                {/* 4. Recommendation */}
                <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1.5 mb-1.5">
                    <span>🛠️</span> How to Fix
                  </h4>
                  <p className="text-xs text-gray-700 leading-relaxed">{selectedIssue.recommendation}</p>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
              <span>Rule Code: <strong>{selectedIssue.rule_id}</strong></span>
              <button
                onClick={() => setSelectedIssue(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
