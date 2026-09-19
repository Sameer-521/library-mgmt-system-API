import { UsersApi } from "../api/users.js";
import { infoDialog } from "../core/modal.js";
import { $, showAlert, hideAlert, setSubmitting } from "../utils/dom.js";
import { formatDate, formatMoney } from "../utils/format.js";

const MAX_PHOTO_BYTES = 2 * 1024 * 1024; // 2 MB
const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/webp"];

const alertBox = $("#alert");
const loadingState = $("#loading-state");
const profileView = $("#profile-view");
const avatarImg = $("#avatar-img");
const photoInput = $("#photo-input");
const photoUpload = $("#photo-upload");
const payFineBtn = $("#pay-fine-btn");

let previewUrl = null;

function setPreview(file) {
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  avatarImg.src = previewUrl;
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
    if (data && data.profile_picture_url) {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      previewUrl = null;
      avatarImg.src = window.CONFIG.API_BASE_URL + data.profile_picture_url;
    }
    photoUpload.hidden = true;
    photoInput.value = "";
    showAlert(alertBox, "Profile picture updated.", "success");
  } catch (error) {
    const message =
      error.status === 404
        ? "Profile picture uploads are not available yet."
        : error.detail || "Could not upload the photo.";
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

    if (profile.profile_picture_url) {
      avatarImg.src = window.CONFIG.API_BASE_URL + profile.profile_picture_url;
    }

    $("#profile-name").textContent = profile.full_name;
    $("#profile-email").textContent = profile.email;
    $("#profile-uid").textContent = profile.user_uid;
    $("#profile-card").textContent = profile.card_number;
    $("#profile-joined").textContent = formatDate(profile.created_at);

    const fines = $("#profile-fines");
    fines.textContent =
      profile.fine_balance > 0 ? formatMoney(profile.fine_balance) : "None";
    if (profile.fine_balance > 0) {
      fines.classList.add("text-danger");
      payFineBtn.disabled = false;
    }

    profileView.hidden = false;
  } catch (error) {
    loadingState.hidden = true;
    showAlert(alertBox, error.detail || "Could not load your profile.");
  }
}

loadProfile();
