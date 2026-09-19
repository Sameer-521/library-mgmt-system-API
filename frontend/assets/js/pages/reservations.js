import { BooksApi } from "../api/books.js";
import { $, showAlert } from "../utils/dom.js";
import { formatDateTime } from "../utils/format.js";

const alertBox = $("#alert");
const summary = $("#summary");
const rowsBody = $("#reservation-rows");
const emptyState = $("#empty-state");
const loadingState = $("#loading-state");

const STATUS_BADGES = {
  active: "badge--green",
  consumed: "badge--blue",
  expired: "badge--gray",
};

function statusBadge(status) {
  const badge = document.createElement("span");
  badge.className = `badge ${STATUS_BADGES[status] || "badge--gray"}`;
  badge.textContent = status;
  return badge;
}

function renderSummary(schedules) {
  const counts = { active: 0, consumed: 0, expired: 0 };
  for (const s of schedules) {
    counts[s.status] = (counts[s.status] || 0) + 1;
  }
  summary.textContent = `${counts.active} active · ${counts.consumed} consumed · ${counts.expired} expired`;
  summary.hidden = false;
}

function renderRows(schedules) {
  rowsBody.textContent = "";
  for (const s of schedules) {
    const row = document.createElement("tr");

    const idCell = document.createElement("td");
    idCell.className = "mono";
    idCell.textContent = s.schedule_id;

    const bookCell = document.createElement("td");
    bookCell.className = "col-book";
    const title = document.createElement("p");
    title.textContent = s.book_title;
    const author = document.createElement("p");
    author.className = "muted cell-sub";
    author.textContent = s.book_author;
    bookCell.append(title, author);

    const copyCell = document.createElement("td");
    copyCell.className = "mono";
    copyCell.textContent = s.bk_copy_barcode;

    const dateCell = document.createElement("td");
    dateCell.textContent = formatDateTime(s.created_at);

    const statusCell = document.createElement("td");
    statusCell.appendChild(statusBadge(s.status));

    row.append(idCell, bookCell, copyCell, dateCell, statusCell);
    rowsBody.appendChild(row);
  }
}

async function init() {
  try {
    const schedules = await BooksApi.mySchedules();
    loadingState.hidden = true;

    if (schedules.length === 0) {
      emptyState.hidden = false;
      return;
    }

    renderSummary(schedules);
    renderRows(schedules);
  } catch (error) {
    loadingState.hidden = true;
    showAlert(alertBox, error.detail || "Could not load your reservations.");
  }
}

init();
