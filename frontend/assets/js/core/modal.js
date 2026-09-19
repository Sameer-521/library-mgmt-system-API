let titleCounter = 0;

/**
 * Show a confirmation dialog and resolve with the user's choice.
 * body accepts a Node so callers build content with DOM APIs (no HTML strings).
 * Resolves true on confirm, false on cancel / backdrop / Escape.
 */
export function confirmDialog({
  title,
  body,
  confirmLabel = "Confirm",
  danger = false,
}) {
  return new Promise((resolve) => {
    titleCounter += 1;
    const titleId = `confirm-dialog-title-${titleCounter}`;
    const previousFocus = document.activeElement;

    const scrim = document.createElement("div");
    scrim.className = "modal-scrim";

    const modal = document.createElement("div");
    modal.className = "modal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-labelledby", titleId);

    const header = document.createElement("div");
    header.className = "modal__header";
    const heading = document.createElement("h2");
    heading.className = "modal__title";
    heading.id = titleId;
    heading.textContent = title;
    header.appendChild(heading);

    const bodyEl = document.createElement("div");
    bodyEl.className = "modal__body";
    if (body) bodyEl.appendChild(body);

    const actions = document.createElement("div");
    actions.className = "modal__actions";
    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.className = "btn btn--secondary";
    cancelBtn.textContent = "Cancel";
    const confirmBtn = document.createElement("button");
    confirmBtn.type = "button";
    confirmBtn.className = `btn ${danger ? "btn--danger" : "btn--primary"}`;
    confirmBtn.textContent = confirmLabel;
    actions.append(cancelBtn, confirmBtn);

    modal.append(header, bodyEl, actions);
    scrim.appendChild(modal);
    document.body.appendChild(scrim);
    document.body.classList.add("no-scroll");
    cancelBtn.focus();

    let settled = false;

    function close(result) {
      if (settled) return;
      settled = true;
      document.removeEventListener("keydown", onKeydown, true);
      scrim.remove();
      document.body.classList.remove("no-scroll");
      if (previousFocus && previousFocus.isConnected) previousFocus.focus();
      resolve(result);
    }

    function onKeydown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        close(false);
      }
    }

    cancelBtn.addEventListener("click", () => close(false));
    confirmBtn.addEventListener("click", () => close(true));
    scrim.addEventListener("click", (event) => {
      if (event.target === scrim) close(false);
    });
    document.addEventListener("keydown", onKeydown, true);
  });
}

/**
 * Show an informational dialog with a single dismiss button.
 * Resolves when the user closes it (button, backdrop or Escape).
 */
export function infoDialog({ title, body, closeLabel = "OK" }) {
  return new Promise((resolve) => {
    titleCounter += 1;
    const titleId = `info-dialog-title-${titleCounter}`;
    const previousFocus = document.activeElement;

    const scrim = document.createElement("div");
    scrim.className = "modal-scrim";

    const modal = document.createElement("div");
    modal.className = "modal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-labelledby", titleId);

    const header = document.createElement("div");
    header.className = "modal__header";
    const heading = document.createElement("h2");
    heading.className = "modal__title";
    heading.id = titleId;
    heading.textContent = title;
    header.appendChild(heading);

    const bodyEl = document.createElement("div");
    bodyEl.className = "modal__body";
    if (body) {
      const line = document.createElement("p");
      line.textContent = body;
      bodyEl.appendChild(line);
    }

    const actions = document.createElement("div");
    actions.className = "modal__actions";
    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "btn btn--primary";
    closeBtn.textContent = closeLabel;
    actions.appendChild(closeBtn);

    modal.append(header, bodyEl, actions);
    scrim.appendChild(modal);
    document.body.appendChild(scrim);
    document.body.classList.add("no-scroll");
    closeBtn.focus();

    let settled = false;

    function close() {
      if (settled) return;
      settled = true;
      document.removeEventListener("keydown", onKeydown, true);
      scrim.remove();
      document.body.classList.remove("no-scroll");
      if (previousFocus && previousFocus.isConnected) previousFocus.focus();
      resolve();
    }

    function onKeydown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
      }
    }

    closeBtn.addEventListener("click", close);
    scrim.addEventListener("click", (event) => {
      if (event.target === scrim) close();
    });
    document.addEventListener("keydown", onKeydown, true);
  });
}

/** Build a minimal dialog body: one lead line plus muted detail lines. */
export function modalBody(lead, ...details) {
  const wrap = document.createElement("div");
  if (lead) {
    const leadEl = document.createElement("p");
    const strong = document.createElement("strong");
    strong.textContent = lead;
    leadEl.appendChild(strong);
    wrap.appendChild(leadEl);
  }
  for (const detail of details) {
    const line = document.createElement("p");
    line.className = "muted";
    line.textContent = detail;
    wrap.appendChild(line);
  }
  return wrap;
}
