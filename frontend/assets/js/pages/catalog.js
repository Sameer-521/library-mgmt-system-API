import { BooksApi } from "../api/books.js";
import { $, showAlert, hideAlert } from "../utils/dom.js";

const PAGE_SIZE = 20;

const params = new URLSearchParams(window.location.search);
const state = {
  field: params.get("field") || "title",
  q: params.get("q") || "",
  offset: Math.max(0, parseInt(params.get("offset"), 10) || 0),
};

const form = $("#filter-form");
const fieldSelect = $("#filter-field");
const qInput = $("#filter-q");
const clearBtn = $("#clear-btn");
const alertBox = $("#alert");
const rowsBody = $("#book-rows");
const emptyState = $("#empty-state");
const loadingState = $("#loading-state");
const pagination = $("#pagination");
const pageInfo = $("#page-info");
const prevBtn = $("#prev-btn");
const nextBtn = $("#next-btn");

function buildQuery() {
  const query = { limit: PAGE_SIZE, offset: state.offset };
  const trimmed = state.q.trim();
  if (trimmed) query[state.field] = trimmed;
  return query;
}

function buildUrl(offset, field, q) {
  const query = new URLSearchParams();
  query.set("field", field);
  query.set("q", q);
  query.set("offset", String(offset));
  return `catalog.html?${query.toString()}`;
}

function availabilityBadge(copies) {
  const badge = document.createElement("span");
  if (copies > 0) {
    badge.className = "badge badge-available";
    badge.textContent = `${copies} available`;
  } else {
    badge.className = "badge badge-unavailable";
    badge.textContent = "Out of stock";
  }
  return badge;
}

function renderRows(items) {
  rowsBody.textContent = "";
  for (const book of items) {
    const row = document.createElement("tr");

    const titleCell = document.createElement("td");
    titleCell.className = "col-book";
    const link = document.createElement("a");
    link.href = `book.html?isbn=${encodeURIComponent(book.isbn)}`;
    link.textContent = book.title;
    titleCell.appendChild(link);

    const authorCell = document.createElement("td");
    authorCell.textContent = book.author;

    const isbnCell = document.createElement("td");
    isbnCell.className = "mono";
    isbnCell.textContent = book.isbn;

    const locationCell = document.createElement("td");
    locationCell.textContent = book.location;

    const availabilityCell = document.createElement("td");
    availabilityCell.appendChild(availabilityBadge(book.available_copies));

    row.append(titleCell, authorCell, isbnCell, locationCell, availabilityCell);
    rowsBody.appendChild(row);
  }
}

function renderPagination(total) {
  const from = total === 0 ? 0 : state.offset + 1;
  const to = Math.min(state.offset + PAGE_SIZE, total);
  pageInfo.textContent = `Showing ${from}-${to} of ${total}`;

  if (state.offset > 0) {
    prevBtn.href = buildUrl(Math.max(0, state.offset - PAGE_SIZE), state.field, state.q);
    prevBtn.removeAttribute("aria-disabled");
  } else {
    prevBtn.removeAttribute("href");
    prevBtn.setAttribute("aria-disabled", "true");
  }

  if (state.offset + PAGE_SIZE < total) {
    nextBtn.href = buildUrl(state.offset + PAGE_SIZE, state.field, state.q);
    nextBtn.removeAttribute("aria-disabled");
  } else {
    nextBtn.removeAttribute("href");
    nextBtn.setAttribute("aria-disabled", "true");
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  window.location.href = buildUrl(0, fieldSelect.value, qInput.value);
});

clearBtn.addEventListener("click", () => {
  window.location.href = "catalog.html";
});

async function init() {
  fieldSelect.value = state.field;
  qInput.value = state.q;

  try {
    const data = await BooksApi.list(buildQuery());
    loadingState.hidden = true;

    if (data.items.length === 0) {
      emptyState.hidden = false;
      return;
    }

    renderRows(data.items);
    pagination.hidden = false;
    renderPagination(data.total);
  } catch (error) {
    loadingState.hidden = true;
    showAlert(alertBox, error.detail || "Failed to load the catalog.");
  }
}

init();
