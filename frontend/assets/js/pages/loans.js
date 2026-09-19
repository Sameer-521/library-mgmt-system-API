import { BooksApi } from "../api/books.js";
import { $, showAlert } from "../utils/dom.js";
import { formatDateTime } from "../utils/format.js";

const PAGE_SIZE = 20;
const LATE_FEE_PER_DAY = 100; // client-side estimate, matches backend fine rule

const params = new URLSearchParams(window.location.search);
const state = {
  offset: Math.max(0, parseInt(params.get("offset"), 10) || 0),
};

const alertBox = $("#alert");
const rowsBody = $("#loan-rows");
const emptyState = $("#empty-state");
const loadingState = $("#loading-state");
const pagination = $("#pagination");
const pageInfo = $("#page-info");
const prevBtn = $("#prev-btn");
const nextBtn = $("#next-btn");

function dateOnly(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function daysLate(dueAt) {
  const diff = dateOnly(new Date()).getTime() - dateOnly(new Date(dueAt)).getTime();
  return Math.max(0, Math.round(diff / 86400000));
}

function buildUrl(offset) {
  const query = new URLSearchParams();
  query.set("offset", String(offset));
  return `loans.html?${query.toString()}`;
}

function statusCellContent(loan) {
  const cell = document.createElement("td");
  const badge = document.createElement("span");

  if (loan.status === "active") {
    const late = daysLate(loan.due_at);
    if (late > 0) {
      badge.className = "badge badge--red";
      badge.textContent = `${late} ${late === 1 ? "day" : "days"} overdue`;
      const fine = document.createElement("div");
      fine.className = "muted";
      fine.style.fontSize = "12.5px";
      fine.style.marginTop = "2px";
      fine.textContent = `est. fine on return ${late * LATE_FEE_PER_DAY}`;
      cell.append(badge, fine);
      return cell;
    }
    badge.className = "badge badge--green";
    badge.textContent = "active";
  } else if (loan.status === "returned_late") {
    badge.className = "badge badge--amber";
    badge.textContent = "returned late";
  } else {
    badge.className = "badge badge--gray";
    badge.textContent = "returned";
  }

  cell.appendChild(badge);
  return cell;
}

function renderRows(items) {
  rowsBody.textContent = "";
  for (const loan of items) {
    const row = document.createElement("tr");

    const bookCell = document.createElement("td");
    bookCell.className = "col-book";
    const title = document.createElement("div");
    title.textContent = loan.book_title;
    const isbn = document.createElement("div");
    isbn.className = "muted mono";
    isbn.style.fontSize = "12.5px";
    isbn.textContent = loan.book_isbn;
    bookCell.append(title, isbn);

    const copyCell = document.createElement("td");
    copyCell.className = "mono";
    copyCell.textContent = loan.bk_copy_barcode;

    const checkedOutCell = document.createElement("td");
    checkedOutCell.textContent = formatDateTime(loan.checked_out_at);

    const dueCell = document.createElement("td");
    dueCell.textContent = formatDateTime(loan.due_at);

    const returnedCell = document.createElement("td");
    returnedCell.textContent = loan.returned_at ? formatDateTime(loan.returned_at) : "-";

    row.append(bookCell, copyCell, checkedOutCell, dueCell, returnedCell, statusCellContent(loan));
    rowsBody.appendChild(row);
  }
}

function renderPagination(total) {
  const from = total === 0 ? 0 : state.offset + 1;
  const to = Math.min(state.offset + PAGE_SIZE, total);
  pageInfo.textContent = `Showing ${from}-${to} of ${total}`;

  if (state.offset > 0) {
    prevBtn.href = buildUrl(Math.max(0, state.offset - PAGE_SIZE));
    prevBtn.removeAttribute("aria-disabled");
  } else {
    prevBtn.removeAttribute("href");
    prevBtn.setAttribute("aria-disabled", "true");
  }

  if (state.offset + PAGE_SIZE < total) {
    nextBtn.href = buildUrl(state.offset + PAGE_SIZE);
    nextBtn.removeAttribute("aria-disabled");
  } else {
    nextBtn.removeAttribute("href");
    nextBtn.setAttribute("aria-disabled", "true");
  }
}

async function loadLoans() {
  loadingState.hidden = false;
  emptyState.hidden = true;
  rowsBody.textContent = "";
  pagination.hidden = true;

  try {
    const data = await BooksApi.myLoans({ limit: PAGE_SIZE, offset: state.offset });
    loadingState.hidden = true;

    if (data.items.length === 0) {
      if (state.offset > 0) {
        window.location.replace(buildUrl(0));
        return;
      }
      emptyState.hidden = false;
      return;
    }

    renderRows(data.items);
    pagination.hidden = false;
    renderPagination(data.total);
  } catch (error) {
    loadingState.hidden = true;
    showAlert(alertBox, error.detail || "Could not load your loans.");
  }
}

loadLoans();
