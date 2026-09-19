import { AuthApi } from "../api/auth.js";
import {
  $,
  showAlert,
  hideAlert,
  setSubmitting,
  attachPasswordToggle,
} from "../utils/dom.js";

const form = $("#login-form");
const alertBox = $("#alert");
const submitBtn = $("#submit-btn");

attachPasswordToggle($("#password"), $("#toggle-password"));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert(alertBox);

  const email = $("#email").value.trim();
  const password = $("#password").value;

  if (!email || !password) {
    showAlert(alertBox, "Enter your email and password.");
    return;
  }

  setSubmitting(submitBtn, true);
  try {
    const data = await AuthApi.login(email, password);
    window.Session.setToken(data.access_token);
    window.location.replace(window.Session.landingPath());
  } catch (error) {
    showAlert(alertBox, error.detail || "Login failed.");
    setSubmitting(submitBtn, false);
  }
});
