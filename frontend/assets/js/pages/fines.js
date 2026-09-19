import { UsersApi } from "../api/users.js";
import { $, showAlert } from "../utils/dom.js";
import { formatMoney } from "../utils/format.js";

const alertBox = $("#alert");
const loadingState = $("#loading-state");
const balanceView = $("#balance-view");
const balanceAmount = $("#balance-amount");
const balanceNote = $("#balance-note");

async function loadBalance() {
  try {
    const profile = await UsersApi.me();
    loadingState.hidden = true;

    if (profile.fine_balance > 0) {
      balanceAmount.textContent = formatMoney(profile.fine_balance);
      balanceAmount.style.color = "var(--danger)";
      balanceNote.textContent =
        "Please settle this balance at the front desk. A balance of 10 or more blocks borrowing and reserving. Online payment is coming soon - please pay at the library desk.";
    } else {
      balanceAmount.textContent = "No outstanding fines";
      balanceAmount.style.color = "var(--success)";
      balanceNote.textContent = "Your account is in good standing.";
    }
    balanceView.hidden = false;
  } catch (error) {
    loadingState.hidden = true;
    showAlert(alertBox, error.detail || "Could not load your fine balance.");
  }
}

loadBalance();
