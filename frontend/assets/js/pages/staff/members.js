import { UsersApi } from "../../api/users.js";
import { $, showAlert } from "../../utils/dom.js";
import { formatDate } from "../../utils/format.js";

const PAGE_SIZE = 20;
const isAdmin = window.Session.getRole() === "admin";

const params = new URLSearchParams(window.location.search);
const state = {
  role: params.get("role") === "staff" && isAdmin ? "staff" : "members",
  offset: Math.max(0, parseInt(params.get("offset"), 10) || 0),
};

const alertBox = $("#alert");
const tabs = $("#role-tabs");
const tabMembers = $("#tab-members");
const tabStaff = $("#tab-staff");
const rowsBody = $("#member-rows");
const emptyState = $("#empty-state");
const loadingState = $("#loading-state");
const pagination = $("#pagination");
const pageInfo = $("#page-info");
const prevBtn = $("#prev-btn");
const nextBtn = $("#next-btn");

function buildUrl(role, offset) {
  const query = new URLSearchParams();
  if (role === "staff") query.set("role", "staff");
  query.set("offset", String(offset));
  return `members.html?${query.toString()}`;
}

function renderTabs() {
  if (!isAdmin) return;
  tabs.hidden = false;
  tabMembers.setAttribute("aria-pressed", String(state.role === "members"));
  tabStaff.setAttribute("aria-pressed", String(state.role === "staff"));
}

function renderRows(items) {
  rowsBody.textContent = "";
  for (const user of items) {
    const row = document.createElement("tr");

    const nameCell = document.createElement("td");
    nameCell.className = "col-book";
    const name = document.createElement("p");
    name.textContent = user.full_name;
    const email = document.createElement("p");
    email.className = "muted cell-sub";
    email.textContent = user.email;
    nameCell.append(name, email);

    const uidCell = document.createElement("td");
    uidCell.className = "mono";
    uidCell.textContent = user.user_uid;

    const cardCell = document.createElement("td");
    cardCell.className = "mono";
    cardCell.textContent = user.card_number;

    const joinedCell = document.createElement("td");
    joinedCell.textContent = formatDate(user.created_at);

    const statusCell = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = `badge ${user.is_active ? "badge--green" : "badge--gray"}`;
    badge.textContent = user.is_active ? "active" : "inactive";
    statusCell.appendChild(badge);

    row.append(nameCell, uidCell, cardCell, joinedCell, statusCell);
    rowsBody.appendChild(row);
  }
}

function renderPagination(total) {
  const from = total === 0 ? 0 : state.offset + 1;
  const to = Math.min(state.offset + PAGE_SIZE, total);
  pageInfo.textContent = `Showing ${from}-${to} of ${total}`;

  prevBtn.disabled = state.offset <= 0;
  nextBtn.disabled = state.offset + PAGE_SIZE >= total;
}

prevBtn.addEventListener("click", () => {
  window.location.href = buildUrl(
    state.role,
    Math.max(0, state.offset - PAGE_SIZE)
  );
});

nextBtn.addEventListener("click", () => {
  window.location.href = buildUrl(state.role, state.offset + PAGE_SIZE);
});

async function loadUsers() {
  loadingState.hidden = false;
  emptyState.hidden = true;
  rowsBody.textContent = "";
  pagination.hidden = true;

  try {
    const query = { limit: PAGE_SIZE, offset: state.offset };
    if (state.role === "staff") query.role = "staff";
    const data = await UsersApi.list(query);
    loadingState.hidden = true;

    if (data.items.length === 0) {
      if (state.offset > 0) {
        window.location.replace(buildUrl(state.role, 0));
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
    showAlert(alertBox, error.detail || "Could not load users.");
  }
}

tabMembers.addEventListener("click", () => {
  if (state.role !== "members") window.location.href = buildUrl("members", 0);
});

tabStaff.addEventListener("click", () => {
  if (state.role !== "staff") window.location.href = buildUrl("staff", 0);
});

renderTabs();
loadUsers();
