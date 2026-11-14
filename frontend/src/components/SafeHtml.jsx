import { useMemo } from "react";
import { useNavigate } from "react-router";
import DOMPurify from "dompurify";

// Second sanitisation layer (the backend already allow-lists tags/attributes).
DOMPurify.addHook("afterSanitizeAttributes", (node) => {
  if (node.tagName === "A") {
    const href = node.getAttribute("href") || "";
    if (/^https?:\/\//i.test(href)) {
      node.setAttribute("target", "_blank");
      node.setAttribute("rel", "noopener noreferrer nofollow");
    }
  }
  if (node.tagName === "IMG") {
    node.setAttribute("loading", "lazy");
    node.setAttribute("referrerpolicy", "no-referrer");
  }
});

/** Renders scraped HTML safely; internal wiki links navigate inside the SPA. */
export default function SafeHtml({ html, className = "prose-guide" }) {
  const navigate = useNavigate();
  const clean = useMemo(
    () => DOMPurify.sanitize(html || "", { ADD_ATTR: ["target", "loading", "referrerpolicy"], FORBID_TAGS: ["style", "form"] }),
    [html],
  );

  const onClick = (e) => {
    const a = e.target.closest?.("a");
    const href = a?.getAttribute("href");
    if (href && href.startsWith("/guides/") && !e.metaKey && !e.ctrlKey) {
      e.preventDefault();
      navigate(href);
    }
  };

  return <div className={className} onClick={onClick} dangerouslySetInnerHTML={{ __html: clean }} />;
}
