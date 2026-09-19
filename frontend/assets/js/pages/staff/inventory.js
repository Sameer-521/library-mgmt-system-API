import { BooksApi } from "../../api/books.js";
import { confirmDialog, modalBody } from "../../core/modal.js";
import { $, showAlert, hideAlert, setSubmitting } from "../../utils/dom.js";

const PAGE_SIZE = 20;
const COPY_STATUSES = [
  "IN_CHECK",
  "AVAILABLE",
  "BORROWED",
  "RESERVED",
  "LOST",
  "DAMAGED",
];
const INSPECTION_TARGETS = ["AVAILABLE", "LOST", "DAMAGED"];

const STATUS_BADGES = {
  AVAILABLE: "badge--green",
  IN_CHECK: "badge--amber",
  BORROWED: "badge--blue",
  RESERVED: "badge--gray",
  LOST: "badge--red",
  DAMAGED: "badge--red",
};

const params = new URLSearchParams(window.location.search);
const state = {
  status: params.get("status") || "IN_CHECK",
  isbn: params.get("isbn") || "",
  offset: Math.max(0, parseInt(params.get("offset"), 10) || 0),
};

const alertBox = $("#alert");

const createForm = $("#create-form");
const createSubmit = $("#create-submit");
const createResult = $("#create-result");

const editLoadForm = $("#edit-load-form");
const editIsbnInput = $("#edit-isbn");
const editLoadBtn = $("#edit-load-btn");
const editForm = $("#edit-form");
const editSubmit = $("#edit-submit");
const editResult = $("#edit-result");
let loadedBook = null;

const copiesForm = $("#copies-form");
const copiesSubmit = $("#copies-submit");
const copiesResult = $("#copies-result");

const inspectionFilterForm = $("#inspection-filter-form");
const inspectionStatus = $("#inspection-status");
const inspectionIsbn = $("#inspection-isbn");
const inspectionAlert = $("#inspection-alert");
const inspectionRows = $("#inspection-rows");
const inspectionEmpty = $("#inspection-empty");
const inspectionLoading = $("#inspection-loading");
const inspectionActions = $("#inspection-actions");
const inspectionApply = $("#inspection-apply");
const inspectionPending = $("#inspection-pending");
const inspectionPagination = $("#inspection-pagination");
const inspectionPageInfo = $("#inspection-page-info");
const inspectionPrev = $("#inspection-prev");
const inspectionNext = $("#inspection-next");

function buildUrl(offset) {
  const query = new URLSearchParams();
  query.set("status", state.status);
  if (state.isbn) query.set("isbn", state.isbn);
  query.set("offset", String(offset));
  return `inventory.html?${query.toString()}`;
}

function statusBadge(value) {
  const badge = document.createElement("span");
  badge.className = `badge ${STATUS_BADGES[value] || "badge--gray"}`;
  badge.textContent = value;
  return badge;
}

function applyConfirmLabel(writeOffs, total) {
  return writeOffs > 0 && writeOffs === total ? "Write off" : "Apply updates";
}

// --- Create book ---

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert(alertBox);
  createResult.hidden = true;

  const title = $("#create-title").value.trim();
  const author = $("#create-author").value.trim();
  const isbn = $("#create-isbn").value.trim();
  const location = $("#create-location").value.trim();
  const available = $("#create-available").checked ? "true" : "false";
  if (!title || !author || !isbn || !location) {
    showAlert(alertBox, "Fill in title, author, ISBN and location.");
    return;
  }

  const confirmed = await confirmDialog({
    title: "Add this book?",
    body: modalBody(
      `"${title}" by ${author}`,
      `ISBN ${isbn} · shelf ${location}`,
      `Available for loans: ${available === "true" ? "yes" : "no"}`
    ),
    confirmLabel: "Add book",
  });
  if (!confirmed) return;

  setSubmitting(createSubmit, true);
  try {
    const data = await BooksApi.create({
      title,
      author,
      isbn,
      location,
      available,
    });
    createResult.textContent = `${data.message} (ISBN ${isbn}).`;
    createResult.hidden = false;
    createForm.reset();
    $("#create-available").checked = true;
  } catch (error) {
    showAlert(alertBox, error.detail || "Could not add the book.");
  } finally {
    setSubmitting(createSubmit, false);
  }
});

// --- Edit book ---

async function loadBookForEdit(isbn) {
  hideAlert(alertBox);
  editResult.hidden = true;
  setSubmitting(editLoadBtn, true);
  try {
    const book = await BooksApi.fetchByIsbn(isbn);
    loadedBook = book;
    $("#edit-title").value = book.title;
    $("#edit-author").value = book.author;
    $("#edit-location").value = book.location;
    $("#edit-available").checked = Boolean(book.available);
    editForm.hidden = false;
  } catch (error) {
    loadedBook = null;
    editForm.hidden = true;
    showAlert(alertBox, error.detail || "Book not found.");
  } finally {
    setSubmitting(editLoadBtn, false);
  }
}

editLoadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const isbn = editIsbnInput.value.trim();
  if (!isbn) {
    showAlert(alertBox, "Enter an ISBN to load.");
    return;
  }
  await loadBookForEdit(isbn);
});

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert(alertBox);
  editResult.hidden = true;
  if (!loadedBook) return;

  const current = {
    title: $("#edit-title").value.trim(),
    author: $("#edit-author").value.trim(),
    location: $("#edit-location").value.trim(),
    available: $("#edit-available").checked,
  };
  const fields = {};
  if (current.title !== loadedBook.title) fields.title = current.title;
  if (current.author !== loadedBook.author) fields.author = current.author;
  if (current.location !== loadedBook.location)
    fields.location = current.location;
  if (current.available !== Boolean(loadedBook.available)) {
    fields.available = current.available ? "true" : "false";
  }

  if (Object.keys(fields).length === 0) {
    showAlert(alertBox, "No changes to save.", "info");
    return;
  }

  const confirmed = await confirmDialog({
    title: "Save these changes?",
    body: modalBody(
      `Update "${loadedBook.title}"`,
      `ISBN ${loadedBook.isbn}`,
      `Fields changed: ${Object.keys(fields).join(", ")}`
    ),
    confirmLabel: "Save changes",
  });
  if (!confirmed) return;

  setSubmitting(editSubmit, true);
  try {
    await BooksApi.update(loadedBook.isbn, fields);
    const names = Object.keys(fields).join(", ");
    editResult.textContent = `Updated ${names} on ISBN ${loadedBook.isbn}.`;
    editResult.hidden = false;
    await loadBookForEdit(loadedBook.isbn);
  } catch (error) {
    showAlert(alertBox, error.detail || "Could not save the changes.");
  } finally {
    setSubmitting(editSubmit, false);
  }
});

// --- Generate copies ---

copiesForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert(alertBox);
  copiesResult.hidden = true;

  const isbn = $("#copies-isbn").value.trim();
  const quantity = parseInt($("#copies-quantity").value, 10);
  if (!isbn) {
    showAlert(alertBox, "Enter an ISBN.");
    return;
  }
  if (!Number.isInteger(quantity) || quantity < 1) {
    showAlert(alertBox, "Quantity must be a whole number of at least 1.");
    return;
  }

  const confirmed = await confirmDialog({
    title: "Generate book copies?",
    body: modalBody(
      `${quantity} new ${quantity === 1 ? "copy" : "copies"} of ISBN ${isbn}`,
      "New copies cannot be removed through the staff UI."
    ),
    confirmLabel: "Generate",
  });
  if (!confirmed) return;

  setSubmitting(copiesSubmit, true);
  try {
    const data = await BooksApi.generateCopies({ isbn, quantity });
    copiesResult.textContent = data.message;
    copiesResult.hidden = false;
    copiesForm.reset();
  } catch (error) {
    showAlert(alertBox, error.detail || "Could not generate copies.");
  } finally {
    setSubmitting(copiesSubmit, false);
  }
});

// --- Inspection ---

function renderInspectionRows(items) {
  inspectionRows.textContent = "";
  for (const copy of items) {
    const row = document.createElement("tr");

    const barcodeCell = document.createElement("td");
    barcodeCell.className = "mono";
    barcodeCell.textContent = copy.copy_barcode;

    const bookCell = document.createElement("td");
    bookCell.className = "col-book";
    const title = document.createElement("p");
    title.textContent = copy.book_title;
    const isbn = document.createElement("p");
    isbn.className = "muted mono";
    isbn.textContent = copy.book_isbn;
    bookCell.append(title, isbn);

    const statusCell = document.createElement("td");
    statusCell.appendChild(statusBadge(copy.status));

    const targetCell = document.createElement("td");
    const select = document.createElement("select");
    select.className = "select";
    select.dataset.barcode = copy.copy_barcode;
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "No change";
    select.appendChild(placeholder);
    for (const target of INSPECTION_TARGETS) {
      const option = document.createElement("option");
      option.value = target;
      option.textContent = target;
      select.appendChild(option);
    }
    targetCell.appendChild(select);

    row.append(barcodeCell, bookCell, statusCell, targetCell);
    inspectionRows.appendChild(row);
  }
}

function syncPending() {
  const pending = Array.from(
    inspectionRows.querySelectorAll("select[data-barcode]")
  ).filter((select) => select.value !== "");
  inspectionPending.textContent =
    pending.length === 0
      ? ""
      : `${pending.length} update${pending.length === 1 ? "" : "s"} staged`;
  inspectionActions.hidden = inspectionRows.childElementCount === 0;
}

inspectionRows.addEventListener("change", (event) => {
  if (event.target.matches("select[data-barcode]")) syncPending();
});

function renderInspectionPagination(total) {
  const from = total === 0 ? 0 : state.offset + 1;
  const to = Math.min(state.offset + PAGE_SIZE, total);
  inspectionPageInfo.textContent = `Showing ${from}-${to} of ${total}`;

  inspectionPrev.disabled = state.offset <= 0;
  inspectionNext.disabled = state.offset + PAGE_SIZE >= total;
}

inspectionPrev.addEventListener("click", () => {
  window.location.href = buildUrl(Math.max(0, state.offset - PAGE_SIZE));
});

inspectionNext.addEventListener("click", () => {
  window.location.href = buildUrl(state.offset + PAGE_SIZE);
});

async function loadInspection() {
  inspectionLoading.hidden = false;
  inspectionEmpty.hidden = true;
  inspectionRows.textContent = "";
  inspectionActions.hidden = true;
  inspectionPagination.hidden = true;
  hideAlert(inspectionAlert);

  try {
    const data = await BooksApi.bkCopies({
      limit: PAGE_SIZE,
      offset: state.offset,
      status: state.status,
      ...(state.isbn ? { isbn: state.isbn } : {}),
    });
    inspectionLoading.hidden = true;

    if (data.items.length === 0) {
      if (state.offset > 0) {
        window.location.replace(buildUrl(0));
        return;
      }
      inspectionEmpty.hidden = false;
      return;
    }

    renderInspectionRows(data.items);
    syncPending();
    inspectionPagination.hidden = false;
    renderInspectionPagination(data.total);
  } catch (error) {
    inspectionLoading.hidden = true;
    showAlert(inspectionAlert, error.detail || "Could not load book copies.");
  }
}

inspectionFilterForm.addEventListener("submit", (event) => {
  event.preventDefault();
  window.location.href = buildUrl(0);
});

inspectionApply.addEventListener("click", async () => {
  hideAlert(inspectionAlert);
  const updates = Array.from(
    inspectionRows.querySelectorAll("select[data-barcode]")
  )
    .filter((select) => select.value !== "")
    .map((select) => ({
      copy_barcode: select.dataset.barcode,
      status: select.value,
    }));

  if (updates.length === 0) {
    showAlert(inspectionAlert, "No status changes staged.", "info");
    return;
  }

  const byTarget = {};
  for (const update of updates) {
    byTarget[update.status] = (byTarget[update.status] || 0) + 1;
  }
  const lines = Object.entries(byTarget).map(
    ([target, count]) =>
      `${count} ${count === 1 ? "copy" : "copies"} -> ${target}`
  );
  const writeOff = (byTarget.LOST || 0) + (byTarget.DAMAGED || 0);
  const confirmed = await confirmDialog({
    title: "Apply status updates?",
    body: modalBody(
      `Updating ${updates.length} ${updates.length === 1 ? "copy" : "copies"}`,
      ...lines,
      ...(writeOff > 0
        ? [
            `${writeOff} ${writeOff === 1 ? "copy is" : "copies are"} being written off as lost or damaged.`,
          ]
        : [])
    ),
    confirmLabel: applyConfirmLabel(writeOff, updates.length),
    danger: writeOff > 0,
  });
  if (!confirmed) return;

  setSubmitting(inspectionApply, true);
  try {
    const data = await BooksApi.updateBkCopies(updates);
    showAlert(inspectionAlert, data.message, "success");
    if (data.num_not_found > 0) {
      showAlert(
        inspectionAlert,
        `${data.message} - not found: ${data.not_found_barcodes.join(", ")}`,
        "warning"
      );
    }
    await loadInspection();
  } catch (error) {
    showAlert(inspectionAlert, error.detail || "Could not apply updates.");
  } finally {
    setSubmitting(inspectionApply, false);
  }
});

async function init() {
  inspectionStatus.value = COPY_STATUSES.includes(state.status)
    ? state.status
    : "IN_CHECK";
  state.status = inspectionStatus.value;
  inspectionIsbn.value = state.isbn;

  loadInspection();

  // Deep link from catalog/book pages: inventory.html?edit=<isbn>
  const editIsbn = params.get("edit");
  if (editIsbn) {
    editIsbnInput.value = editIsbn;
    await loadBookForEdit(editIsbn);
  }
}

init();
