// Language → Tailwind colour pill
const LANG_COLORS = {
  "Python":               "bg-blue-100 text-blue-700",
  "JavaScript":           "bg-yellow-100 text-yellow-700",
  "JavaScript (JSX)":     "bg-yellow-100 text-yellow-800",
  "TypeScript":           "bg-sky-100 text-sky-700",
  "TypeScript (TSX)":     "bg-sky-100 text-sky-800",
  "HTML":                 "bg-orange-100 text-orange-700",
  "CSS":                  "bg-pink-100 text-pink-700",
  "Java":                 "bg-red-100 text-red-700",
  "C":                    "bg-purple-100 text-purple-700",
  "C++":                  "bg-purple-100 text-purple-800",
};

export function LangPill({ lang }) {
  const cls = LANG_COLORS[lang] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${cls}`}>
      {lang}
    </span>
  );
}

export default LANG_COLORS;
