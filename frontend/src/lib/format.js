const inrFmt = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
const numFmt = new Intl.NumberFormat("en-IN");

export const inr = (n) => (n == null ? "—" : inrFmt.format(Math.round(n)));
export const num = (n) => (n == null ? "—" : numFmt.format(n));

export function ratingWord(r) {
  if (r == null) return null;
  if (r >= 4.5) return "Excellent";
  if (r >= 4.0) return "Very good";
  if (r >= 3.5) return "Good";
  if (r >= 3.0) return "Fair";
  return "Poor";
}

export function timeAgo(tsSeconds) {
  if (!tsSeconds) return null;
  const s = Math.max(0, Date.now() / 1000 - tsSeconds);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  if (s < 86400) return `${Math.round(s / 3600)} h ago`;
  return `${Math.round(s / 86400)} d ago`;
}

export function formatDate(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export const KIND_LABELS = {
  gpu: "Graphics card", cpu: "Processor", console: "Console", controller: "Controller", headset: "Headset",
  keyboard: "Keyboard", mouse: "Mouse", mousepad: "Mouse pad", monitor: "Monitor", laptop: "Laptop",
  prebuilt: "Gaming PC", motherboard: "Motherboard", ram: "RAM", ssd: "SSD", hdd: "Hard drive", psu: "Power supply",
  case: "Cabinet", cooler: "Cooler", chair: "Chair", wheel: "Racing wheel", accessory: "Accessory", game: "Video game",
};
