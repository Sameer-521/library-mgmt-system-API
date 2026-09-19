const DATE_OPTS = { year: "numeric", month: "short", day: "numeric" };
const TIME_OPTS = { hour: "2-digit", minute: "2-digit" };

export function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString(undefined, DATE_OPTS);
}

export function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return `${date.toLocaleDateString(undefined, DATE_OPTS)}, ${date.toLocaleTimeString(undefined, TIME_OPTS)}`;
}

export function daysBetween(from, to) {
  return Math.floor((to.getTime() - from.getTime()) / 86400000);
}

const CURRENCY_SYMBOL = "₦";

export function formatMoney(amount) {
  return `${CURRENCY_SYMBOL}${Number(amount).toLocaleString()}`;
}
