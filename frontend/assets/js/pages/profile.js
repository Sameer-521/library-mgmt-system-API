import { UsersApi } from "../api/users.js";
import { infoDialog } from "../core/modal.js";
import { $, showAlert, hideAlert, setSubmitting } from "../utils/dom.js";
import { formatDate, formatMoney } from "../utils/format.js";

const MAX_PHOTO_BYTES = 2 * 1024 * 1024; // 2 MB
const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/webp"];
const DEFAULT_AVATAR = "assets/icons/avatar-default.svg";

const alertBox = $("#alert");
const loadingState = $("#loading-state");
const profileView = $("#profile-view");
const avatarImg = $("#avatar-img");
const photoInput = $("#photo-input");
const photoUpload = $("#photo-upload");
const payFineBtn = $("#pay-fine-btn");

let avatarObjectUrl = null; // object URL currently shown (preview or served pic)

function clearAvatarObjectUrl() {
  if (avatarObjectUrl) {
    URL.revokeObjectURL(avatarObjectUrl);
    avatarObjectUrl = null;
  }
}

function showDefaultAvatar() {
  clearAvatarObjectUrl();
  avatarImg.onerror = null;
  avatarImg.src = DEFAULT_AVATAR;
}

async function showAvatarFromApi() {
  const blob = await UsersApi.fetchProfilePicture();
  clearAvatarObjectUrl();
  avatarImg.onerror = null;
  avatarObjectUrl = URL.createObjectURL(blob);
  avatarImg.src = avatarObjectUrl;
}

// Fallback chain: authed API endpoint -> default avatar (404, network error,
// expired session, missing picture).
async function renderAvatar(urlPath) {
  if (!urlPath) {
    showDefaultAvatar();
    return;
  }
  try {
    await showAvatarFromApi();
  } catch {
    showDefaultAvatar();
  }
}

function setPreview(file) {
  clearAvatarObjectUrl();
  avatarImg.onerror = null;
  avatarObjectUrl = URL.createObjectURL(file);
  avatarImg.src = avatarObjectUrl;
}

photoInput.addEventListener("change", () => {
  hideAlert(alertBox);
  photoUpload.hidden = true;
  const file = photoInput.files[0];
  if (!file) return;

  if (!ALLOWED_TYPES.includes(file.type)) {
    showAlert(alertBox, "Choose a PNG, JPEG or WebP image.");
    photoInput.value = "";
    return;
  }
  if (file.size > MAX_PHOTO_BYTES) {
    showAlert(alertBox, "Image must be 2 MB or smaller.");
    photoInput.value = "";
    return;
  }

  setPreview(file);
  photoUpload.hidden = false;
});

photoUpload.addEventListener("click", async () => {
  const file = photoInput.files[0];
  if (!file) return;
  hideAlert(alertBox);

  setSubmitting(photoUpload, true);
  try {
    const data = await UsersApi.uploadProfilePicture(file);
    photoUpload.hidden = true;
    photoInput.value = "";
    await renderAvatar(data && data.profile_picture_url);
    // The topbar avatar chip (layout.js) re-fetches its own blob on this.
    document.dispatchEvent(new CustomEvent("avatar:updated"));
    showAlert(alertBox, "Profile picture updated.", "success");
  } catch (error) {
    let message;
    if (error.status === 413) {
      message = "Image must be 2 MB or smaller.";
    } else if (error.status === 422) {
      message = "That file doesn't look like a valid PNG, JPEG or WebP image.";
    } else if (error.status === 404) {
      message = "Profile picture uploads are not available yet.";
    } else {
      message = error.detail || "Could not upload the photo.";
    }
    showAlert(alertBox, message);
  } finally {
    setSubmitting(photoUpload, false);
  }
});

payFineBtn.addEventListener("click", () => {
  infoDialog({
    title: "Pay fine",
    body: "Online payment is coming soon. Please pay at the library desk.",
  });
});

async function loadProfile() {
  try {
    const profile = await UsersApi.me();
    loadingState.hidden = true;

    renderAvatar(profile.profile_picture_url);

    $("#profile-name").textContent = profile.full_name;
    $("#profile-email").textContent = profile.email;
    $("#profile-uid").textContent = profile.user_uid;
    $("#profile-card").textContent = profile.card_number;
    $("#profile-joined").textContent = formatDate(profile.created_at);

    // Staff/admin accounts are never fined (backend skips accrual) — the
    // fine row + pay button leave the profile entirely for staff.
    if (Session.isStaffLike()) {
      const finesDd = $("#profile-fines").closest("dd");
      finesDd.previousElementSibling?.remove(); // "Fine balance" dt
      finesDd.remove(); // dd carrying the Pay fine button
    } else {
      const fines = $("#profile-fines");
      fines.textContent =
        profile.fine_balance > 0 ? formatMoney(profile.fine_balance) : "None";
      if (profile.fine_balance > 0) {
        fines.classList.add("text-danger");
        payFineBtn.disabled = false;
      }
    }

    profileView.hidden = false;
  } catch (error) {
    loadingState.hidden = true;
    showAlert(alertBox, error.detail || "Could not load your profile.");
  }
}

loadProfile();
