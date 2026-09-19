export function $(selector, root = document) {
  return root.querySelector(selector);
}

export function setText(el, text) {
  el.textContent = text;
}

export function showAlert(el, message, variant = "error") {
  el.className = `alert alert--${variant}`;
  el.textContent = message;
  el.hidden = false;
}

export function hideAlert(el) {
  el.hidden = true;
  el.textContent = "";
}

export function setSubmitting(button, isSubmitting) {
  button.disabled = isSubmitting;
}

export function attachPasswordToggle(input, button) {
  const [iconEye, iconSlash] = button.querySelectorAll("svg");

  function sync() {
    const visible = input.type === "text";
    iconEye.toggleAttribute("hidden", !visible);
    iconSlash.toggleAttribute("hidden", visible);
    button.setAttribute("aria-pressed", String(visible));
    button.setAttribute(
      "aria-label",
      visible ? "Hide password" : "Show password"
    );
  }

  button.addEventListener("click", () => {
    input.type = input.type === "password" ? "text" : "password";
    sync();
  });

  sync();
}
