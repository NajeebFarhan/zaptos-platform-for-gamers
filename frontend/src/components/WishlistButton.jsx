import { Heart } from "lucide-react";
import { findSaved, toggleItem, useWishlist } from "../lib/wishlist";

/**
 * Save / unsave a product group.
 * variant "icon"    — square ghost button (card actions)
 * variant "overlay" — round button floating over a product image
 * variant "full"    — labelled button (drawer)
 */
export default function WishlistButton({ group, query, variant = "icon", className = "" }) {
  const snap = useWishlist();
  const saved = !!findSaved(snap, group);
  const label = saved ? "Remove from wishlist" : "Add to wishlist";

  const onClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    toggleItem(group, query);
  };

  const heart = <Heart className={`h-4 w-4 transition ${saved ? "fill-bad text-bad" : ""}`} />;

  if (variant === "overlay") {
    return (
      <button
        onClick={onClick}
        aria-pressed={saved}
        aria-label={label}
        title={label}
        className={`grid h-9 w-9 place-items-center rounded-full border border-line bg-ink/85 text-text shadow backdrop-blur transition hover:scale-110 hover:border-bad/60 ${className}`}
      >
        {heart}
      </button>
    );
  }
  if (variant === "full") {
    return (
      <button onClick={onClick} aria-pressed={saved} className={`btn-ghost ${saved ? "border-bad/50" : ""} ${className}`}>
        {heart}
        {saved ? "Saved" : "Save"}
      </button>
    );
  }
  return (
    <button onClick={onClick} aria-pressed={saved} aria-label={label} title={label} className={`btn-ghost px-3 ${saved ? "border-bad/50" : ""} ${className}`}>
      {heart}
    </button>
  );
}
