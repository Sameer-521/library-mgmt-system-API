import { AuthApi } from "../api/auth.js";
import { $, showAlert, hideAlert, setSubmitting, attachPasswordToggle } from "../utils/dom.js";

const form = $("#signup-form");
const body = $("#signup-body");
const alertBox = $("#alert");
const submitBtn = $("#submit-btn");

attachPasswordToggle($("#password"), $("#toggle-password"));

const NAME_MIN = 3;
const NAME_MAX = 30;
const PASS_MIN = 8;
const PASS_MAX = 30;
const PASS_PATTERN = /^[A-Za-z0-9_@!]+$/;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validate(fullName, email, password) {
  if (fullName.length < NAME_MIN || fullName.length > NAME_MAX) {
    return `Full name must be ${NAME_MIN}–${NAME_MAX} characters.`;
  }
  if (!EMAIL_PATTERN.test(email)) {
    return "Enter a valid email address.";
  }
  if (password.length < PASS_MIN || password.length > PASS_MAX) {
    return `Password must be ${PASS_MIN}–${PASS_MAX} characters.`;
  }
  if (!PASS_PATTERN.test(password)) {
    return "Password can only contain letters, numbers and _ @ !.";
  }
  return null;
}

function showSuccess(userUid) {
  body.textContent = "";
  const alert = document.createElement("div");
  alert.className = "alert alert--success";
  alert.textContent = "Account created successfully.";
  const info = document.createElement("p");
  info.className = "muted";
  info.style.marginBottom = "14px";
  info.append("Your member ID: ");
  const code = document.createElement("span");
  code.className = "mono";
  code.textContent = userUid || "-";
  info.appendChild(code);
  const link = document.createElement("a");
  link.className = "btn btn--primary btn--block";
  link.href = "index.html";
  link.textContent = "Go to login";
  link.style.textDecoration = "none";
  body.append(alert, info, link);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert(alertBox);

  const fullName = $("#full-name").value.trim();
  const email = $("#email").value.trim();
  const password = $("#password").value;

  const problem = validate(fullName, email, password);
  if (problem) {
    showAlert(alertBox, problem);
    return;
  }

  setSubmitting(submitBtn, true);
  try {
    const data = await AuthApi.signUp(fullName, email, password);
    showSuccess(data.user_uid);
  } catch (error) {
    showAlert(alertBox, error.detail || "Sign-up failed.");
    setSubmitting(submitBtn, false);
  }
});
