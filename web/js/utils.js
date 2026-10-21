// Pure helpers (tested with `node --test`).
export const MAX_TEXT_CHARS = 5000;
export const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
export const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"];

export function validateText(text) {
  const t = (text ?? "").trim();
  if (!t) return { ok: false, error: "Please enter some text to analyze." };
  if (t.length > MAX_TEXT_CHARS) return { ok: false, error: `Text is too long (max ${MAX_TEXT_CHARS} characters).` };
  return { ok: true, value: t };
}

export function validateImage(file) {
  if (!file) return { ok: false, error: "Please choose an image." };
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) return { ok: false, error: `Unsupported file type: ${file.type || "unknown"}.` };
  if (file.size > MAX_IMAGE_BYTES) return { ok: false, error: "Image is larger than 10 MB." };
  return { ok: true };
}

export function isValidSpaceId(id) {
  return typeof id === "string" && /^[A-Za-z0-9][\w.-]*\/[A-Za-z0-9][\w.-]*$/.test(id.trim());
}

export function pct(score) {
  return `${(Number(score) * 100).toFixed(1)}%`;
}

const EMOJI = { positive: "😊", neutral: "😐", negative: "😞" };
export function sentimentEmoji(label) {
  return EMOJI[label] ?? "❔";
}
