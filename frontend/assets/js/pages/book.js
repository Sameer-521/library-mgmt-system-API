import { BooksApi } from "../api/books.js";
import { $, showAlert, hideAlert } from "../utils/dom.js";
import { formatDateTime } from "../utils/format.js";

const isbn = new URLSearchParams(window.location.search).get("isbn");

const alertBox = $("#alert");
const loadingState = $("#loading-state");
const bookCard = $("#book-card");
const reserveBtn = $("#reserve-btn");
const reserveNote = $("#reserve-note");
const reserveResult = $("#reserve-result");
const reserveAlert = $("#reserve-alert");
const reserveDetails = $("#reserve-details");
const modal = $("#reserve-modal");
const modalConfirm = $("#modal-confirm");
const modalCancel = $("#modal-cancel");
let currentBook = null;

function availabilityBadge(copies) {
  const badge = $("#book-badge");
  if (copies > 0) {
    badge.className = "badge badge-available";
    badge.textContent = `${copies} available`;
  } else {
    badge.className = "badge badge-unavailable";
    badge.textContent = "Out of stock";
  }
}

function renderBook(book) {
  currentBook = book;
  document.title = `${book.title} - Library`;
  $("#book-title").textContent = book.title;
  $("#book-author").textContent = book.author;
  $("#book-isbn").textContent = book.isbn;
  $("#book-barcode").textContent = book.library_barcode;
  $("#book-location").textContent = book.location;
  $("#book-added").textContent = formatDateTime(book.created_at);
  $("#book-updated").textContent = formatDateTime(book.updated_at);
  availabilityBadge(book.available_copies);

  if (book.available_copies === 0) {
    reserveBtn.disabled = true;
    reserveNote.hidden = false;
    reserveNote.textContent = "No available copies.";
  }
}

function detailRow(label, value) {
  const dt = document.createElement("dt");
  dt.textContent = label;
  const dd = document.createElement("dd");
  dd.textContent = value;
  return [dt, dd];
}

function renderReserveSuccess(data) {
  const parts = [data.message];
  if (data.note) parts.push(data.note);
  showAlert(reserveAlert, parts.join(" "), "success");

  const info = data.schedule_info || {};
  reserveDetails.append(
    ...detailRow("Schedule ID", info.schedule_id || "-"),
    ...detailRow("Reserved copy", info.bk_copy_barcode || "-"),
    ...detailRow("Status", info.status || "-"),
    ...detailRow("Created", formatDateTime(info.created_at))
  );

  reserveResult.hidden = false;
  reserveBtn.disabled = true;
  reserveBtn.textContent = "Reserved";
}

function openModal() {
  $("#modal-book-title").textContent = currentBook.title;
  $("#modal-book-meta").textContent = `${currentBook.author} · ISBN ${currentBook.isbn}`;
  modal.hidden = false;
  document.body.classList.add("no-scroll");
  modalCancel.focus();
}

function closeModal({ returnFocus = false } = {}) {
  modal.hidden = true;
  document.body.classList.remove("no-scroll");
  if (returnFocus) reserveBtn.focus();
}

reserveBtn.addEventListener("click", () => {
  hideAlert(alertBox);
  openModal();
});

modalCancel.addEventListener("click", () => closeModal({ returnFocus: true }));

modal.addEventListener("click", (event) => {
  if (event.target === modal) closeModal({ returnFocus: true });
});

document.addEventListener("keydown", (event) => {
  if (!modal.hidden && event.key === "Escape") {
    closeModal({ returnFocus: true });
  }
});

modalConfirm.addEventListener("click", async () => {
  hideAlert(alertBox);
  closeModal();
  reserveBtn.disabled = true;
  try {
    const data = await BooksApi.schedule(isbn);
    renderReserveSuccess(data);
  } catch (error) {
    if (error.code === "NO_COPIES_AVAILABLE") {
      reserveNote.hidden = false;
      reserveNote.textContent = "No available copies.";
    } else {
      reserveBtn.disabled = false;
    }
    showAlert(alertBox, error.detail || "Could not reserve this book.");
  }
});

async function init() {
  if (!isbn) {
    loadingState.hidden = true;
    showAlert(alertBox, "No book selected.");
    return;
  }

  try {
    const book = await BooksApi.fetchByIsbn(isbn);
    loadingState.hidden = true;
    bookCard.hidden = false;
    renderBook(book);
  } catch (error) {
    loadingState.hidden = true;
    showAlert(alertBox, error.detail || "Book not found.");
  }
}

init();
