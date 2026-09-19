import { BooksApi } from "../api/books.js";
import { confirmDialog, modalBody } from "../core/modal.js";
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
  if (window.Session.isStaffLike()) {
    const editLink = $("#edit-book-link");
    editLink.href = `staff/inventory.html?edit=${encodeURIComponent(book.isbn)}`;
    editLink.hidden = false;
  }
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

reserveBtn.addEventListener("click", async () => {
  hideAlert(alertBox);
  const confirmed = await confirmDialog({
    title: "Reserve this book?",
    body: modalBody(
      currentBook.title,
      `${currentBook.author} · ISBN ${currentBook.isbn}`,
      "The copy will be held for you until 6pm."
    ),
    confirmLabel: "Reserve",
  });
  if (!confirmed) return;

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
