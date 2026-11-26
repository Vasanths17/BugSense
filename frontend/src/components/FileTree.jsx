import { useState } from "react";

// ── icons ────────────────────────────────────────────────────────────────────
const FolderIcon = ({ open }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24"
    fill={open ? "#60a5fa" : "none"} stroke={open ? "#60a5fa" : "currentColor"}
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
  </svg>
);

const FileIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 flex-shrink-0 text-slate-400"
    viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14,2 14,8 20,8" />
  </svg>
);

const ChevronIcon = ({ open }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={`w-3 h-3 flex-shrink-0 transition-transform ${open ? "rotate-90" : ""}`}
    viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
    strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9,18 15,12 9,6" />
  </svg>
);

// Extension → colour dot
const EXT_COLOR = {
  ".py":   "bg-blue-400",
  ".js":   "bg-yellow-400",
  ".jsx":  "bg-yellow-500",
  ".ts":   "bg-sky-400",
  ".tsx":  "bg-sky-500",
  ".html": "bg-orange-400",
  ".css":  "bg-pink-400",
  ".java": "bg-red-400",
  ".c":    "bg-purple-400",
  ".cpp":  "bg-purple-500",
};

function ExtDot({ ext }) {
  const cls = EXT_COLOR[ext] ?? "bg-slate-400";
  return <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cls}`} />;
}

// ── Single tree node ─────────────────────────────────────────────────────────
function TreeNode({ node, depth, selectedPath, onFileClick }) {
  const [open, setOpen] = useState(depth < 2);  // auto-open 2 levels deep

  if (node.type === "directory") {
    return (
      <div>
        <button
          onClick={() => setOpen(o => !o)}
          className="w-full flex items-center gap-1.5 py-0.5 px-1 rounded
            hover:bg-slate-700 text-slate-300 text-sm text-left group transition-colors"
          style={{ paddingLeft: `${depth * 14 + 4}px` }}
        >
          <span className="text-slate-500"><ChevronIcon open={open} /></span>
          <FolderIcon open={open} />
          <span className="truncate">{node.name}</span>
        </button>

        {open && node.children?.map(child => (
          <TreeNode
            key={child.path}
            node={child}
            depth={depth + 1}
            selectedPath={selectedPath}
            onFileClick={onFileClick}
          />
        ))}
      </div>
    );
  }

  // File node
  const isSelected = node.path === selectedPath;
  const isSupported = node.supported;

  return (
    <button
      onClick={() => isSupported && onFileClick(node)}
      disabled={!isSupported}
      title={isSupported ? node.path : `${node.path} (not analysable)`}
      className={`w-full flex items-center gap-1.5 py-0.5 px-1 rounded text-sm text-left
        transition-colors truncate
        ${isSelected
          ? "bg-blue-600 text-white"
          : isSupported
            ? "text-slate-300 hover:bg-slate-700 cursor-pointer"
            : "text-slate-500 cursor-default opacity-60"
        }`}
      style={{ paddingLeft: `${depth * 14 + 4}px` }}
    >
      {node.extension
        ? <ExtDot ext={node.extension} />
        : <FileIcon />}
      <span className="truncate">{node.name}</span>
    </button>
  );
}

// ── Public component ─────────────────────────────────────────────────────────
export default function FileTree({ nodes, selectedPath, onFileClick }) {
  if (!nodes || nodes.length === 0) {
    return <p className="text-slate-500 text-sm px-3 py-4">No files found.</p>;
  }

  return (
    <div className="select-none py-2">
      {nodes.map(node => (
        <TreeNode
          key={node.path}
          node={node}
          depth={0}
          selectedPath={selectedPath}
          onFileClick={onFileClick}
        />
      ))}
    </div>
  );
}
