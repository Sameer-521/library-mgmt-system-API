import { UsersApi } from "../api/users.js";
import { $, showAlert } from "../utils/dom.js";
import { formatDate } from "../utils/format.js";

const alertBox = $("#alert");
const loadingState = $("#loading-state");
const profileView = $("#profile-view");

async function loadProfile() {
  try {
    const profile = await UsersApi.me();
    loadingState.hidden = true;

    $("#profile-name").textContent = profile.full_name;
    $("#profile-email").textContent = profile.email;
    $("#profile-uid").textContent = profile.user_uid;
    $("#profile-card").textContent = profile.card_number;
    $("#profile-joined").textContent = formatDate(profile.created_at);

    const fines = $("#profile-fines");
    fines.textContent = profile.fine_balance > 0 ? String(profile.fine_balance) : "None";
    if (profile.fine_balance > 0) fines.style.color = "var(--danger)";

    profileView.hidden = false;
  } catch (error) {
    loadingState.hidden = true;
    showAlert(alertBox, error.detail || "Could not load your profile.");
  }
}

loadProfile();
