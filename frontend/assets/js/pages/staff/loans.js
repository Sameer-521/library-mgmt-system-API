import { BooksApi } from "../../api/books.js";
import { UsersApi } from "../../api/users.js";
import { confirmDialog, modalBody } from "../../core/modal.js";
import { $, showAlert, hideAlert, setSubmitting } from "../../utils/dom.js";
import { formatDateTime } from "../../utils/format.js";

const PAGE_SIZE = 20;
const LATE_FEE_PER_DAY = 100; // client-side estimate, matches backend fine rule

const params = new URLSearchParams(window.location.search);
const state = {
  offset: Math.max(0, parseInt(params.get("offset"), 10) || 0),
};

const alertBox = $("#alert");
const summary = $("#summary");
const rowsBody = $("#loan-rows");
const emptyState = $("#empty-state");
const loadingState = $("#loading-state");
const pagination = $("#pagination");
const pageInfo = $("#page-info");
const prevBtn = $("#prev-btn");
const nextBtn = $("#next-btn");

const members = new Map(); // user_uid -> user
const inViewLoans = new Map(); // loan_id -> row data from the active loans table

const checkoutForm = $("#checkout-form");
const checkoutMember = $("#checkout-member");
const checkoutIsbn = $("#checkout-isbn");
const checkoutSubmit = $("#checkout-submit");
const checkoutResult = $("#checkout-result");

const returnForm = $("#return-form");
const returnLoanId = $("#return-loan-id");
const returnBarcode = $("#return-barcode");
const returnSubmit = $("#return-submit");
const returnResult = $("#return-result");

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
  const late = daysLate(loan.due_at);
  const cell = document.createElement("td");
  if (late > 0) {
    const badge = document.createElement("span");
    badge.className = "badge badge--red";
    badge.textContent = `${late} ${late === 1 ? "day" : "days"} overdue`;
    const fine = document.createElement("div");
    fine.className = "muted";
    fine.style.fontSize = "12.5px";
    fine.style.marginTop = "2px";
    fine.textContent = `est. fine ${late * LATE_FEE_PER_DAY}`;
    cell.append(badge, fine);
  } else {
    const badge = document.createElement("span");
    badge.className = "badge badge--green";
    badge.textContent = "active";
    cell.appendChild(badge);
  }
  return cell;
}

function renderRows(items) {
  rowsBody.textContent = "";
  inViewLoans.clear();
  for (const loan of items) {
    inViewLoans.set(loan.loan_id, loan);
    const row = document.createElement("tr");

    const idCell = document.createElement("td");
    idCell.className = "mono";
    idCell.textContent = loan.loan_id;

    const memberCell = document.createElement("td");
    const name = document.createElement("div");
    name.textContent = loan.user_full_name;
    const email = document.createElement("div");
    email.className = "muted";
    email.style.fontSize = "12.5px";
    email.textContent = loan.user_email;
    memberCell.append(name, email);

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

    const actionCell = document.createElement("td");
    const returnBtn = document.createElement("button");
    returnBtn.type = "button";
    returnBtn.className = "btn btn--secondary";
    returnBtn.textContent = "Return";
    returnBtn.addEventListener("click", () => {
      fillReturnForm(loan);
    });
    actionCell.appendChild(returnBtn);

    row.append(
      idCell,
      memberCell,
      bookCell,
      copyCell,
      checkedOutCell,
      dueCell,
      statusCellContent(loan),
      actionCell
    );
    rowsBody.appendChild(row);
  }
}

function renderSummary(items, total) {
  const overdueCount = items.filter((loan) => daysLate(loan.due_at) > 0).length;
  summary.textContent = `${total} active · ${overdueCount} overdue on this page`;
  summary.hidden = false;
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
  summary.hidden = true;

  try {
    const data = await BooksApi.activeLoans({ limit: PAGE_SIZE, offset: state.offset });
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
    renderSummary(data.items, data.total);
    pagination.hidden = false;
    renderPagination(data.total);
  } catch (error) {
    loadingState.hidden = true;
    showAlert(alertBox, error.detail || "Could not load active loans.");
  }
}

async function loadMembers() {
  try {
    const data = await UsersApi.list({ limit: 100, offset: 0 });
    const options = $("#member-options");
    options.textContent = "";
    for (const user of data.items) {
      members.set(user.user_uid, user);
      const option = document.createElement("option");
      option.value = user.user_uid;
      option.label = `${user.full_name} · ${user.email} · ${user.card_number}`;
      options.appendChild(option);
    }
  } catch {
    // Member suggestions are a convenience; checkout still works with a typed ID.
  }
}

function resolveMemberUid(raw) {
  const trimmed = raw.trim();
  if (members.has(trimmed)) return trimmed;
  for (const [uid, user] of members) {
    if (user.email.toLowerCase() === trimmed.toLowerCase()) return uid;
  }
  return null;
}

function fillReturnForm(loan) {
  returnLoanId.value = loan.loan_id;
  returnBarcode.value = loan.bk_copy_barcode;
  returnForm.scrollIntoView({ block: "center" });
  returnLoanId.focus();
}

checkoutForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert(alertBox);
  checkoutResult.hidden = true;

  const uid = resolveMemberUid(checkoutMember.value);
  const isbn = checkoutIsbn.value.trim();
  if (!uid) {
    showAlert(alertBox, "Select a member from the list.");
    checkoutMember.focus();
    return;
  }
  if (!isbn) {
    showAlert(alertBox, "Enter an ISBN.");
    checkoutIsbn.focus();
    return;
  }

  const member = members.get(uid);
  const who = member ? `${member.email}` : uid;
  const confirmed = await confirmDialog({
    title: "Check out this book?",
    body: modalBody(
      `ISBN ${isbn} to ${who}`,
      `User ID ${uid}`,
      "If the member has an active reservation for this book, it is fulfilled automatically."
    ),
    confirmLabel: "Check out",
  });
  if (!confirmed) return;

  setSubmitting(checkoutSubmit, true);
  try {
    const data = await BooksApi.loanBook({ user_uid: uid, isbn });
    let text = `Loan ${data.loan.loan_id} - copy ${data.loan.bk_copy_barcode} checked out to ${who}, due ${formatDateTime(data.loan.due_at)}.`;
    if (data.was_scheduled) {
      text += " Fulfilled the member's active reservation.";
    }
    checkoutResult.textContent = text;
    checkoutResult.hidden = false;
    checkoutForm.reset();
    await loadLoans();
  } catch (error) {
    showAlert(alertBox, error.detail || "Checkout failed.");
  } finally {
    setSubmitting(checkoutSubmit, false);
  }
});

returnForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert(alertBox);
  returnResult.hidden = true;

  const loan_id = returnLoanId.value.trim();
  const bk_copy_barcode = returnBarcode.value.trim();
  if (!loan_id || !bk_copy_barcode) {
    showAlert(alertBox, "Enter both the loan ID and the copy barcode.");
    return;
  }

  const known = inViewLoans.get(loan_id);
  const late = known ? daysLate(known.due_at) : 0;
  const confirmed = await confirmDialog({
    title: "Return this copy?",
    body: modalBody(
      `Loan ${loan_id}`,
      `Copy ${bk_copy_barcode}`,
      ...(late > 0
        ? [`Overdue by ${late} ${late === 1 ? "day" : "days"} - est. fine ${late * LATE_FEE_PER_DAY}.`]
        : ["Returned copies move to IN_CHECK for staff inspection."])
    ),
    confirmLabel: "Return",
  });
  if (!confirmed) return;

  setSubmitting(returnSubmit, true);
  try {
    const data = await BooksApi.returnLoan({ bk_copy_barcode, loan_id });
    if ("fine" in data) {
      showAlert(
        alertBox,
        `Late return - fine applied: ${data.fine} (${data["delay time"]}). ${data.message}`,
        "warning"
      );
    } else {
      showAlert(alertBox, data.message, "success");
    }
    returnForm.reset();
    await loadLoans();
  } catch (error) {
    showAlert(alertBox, error.detail || "Return failed.");
  } finally {
    setSubmitting(returnSubmit, false);
  }
});

loadMembers();
loadLoans();
