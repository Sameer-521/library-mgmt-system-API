(function () {
  const Session = window.Session;
  const MOBILE_QUERY = window.matchMedia("(max-width: 760px)");

  function navItems() {
    const p = Session.prefix();
    if (Session.isStaffLike()) {
      return {
        sections: [
          {
            label: "Staff",
            items: [
              { label: "Dashboard", href: p + "staff/dashboard.html" },
              { label: "Loans", href: p + "staff/loans.html" },
              { label: "Inventory", href: p + "staff/inventory.html" },
              { label: "Members", href: p + "staff/members.html" },
            ],
          },
          {
            label: "Library",
            items: [
              { label: "Catalog", href: p + "catalog.html" },
              { label: "My Reservations", href: p + "reservations.html" },
            ],
          },
        ],
      };
    }
    return {
      sections: [
        {
          label: "Library",
          items: [
            { label: "Catalog", href: p + "catalog.html" },
            { label: "My Reservations", href: p + "reservations.html" },
            { label: "My Loans", href: p + "loans.html" },
            { label: "Fines", href: p + "fines.html" },
            { label: "Profile", href: p + "profile.html" },
          ],
        },
      ],
    };
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function buildNavToggle() {
    const button = el("button", "nav-toggle");
    button.type = "button";
    button.setAttribute("aria-controls", "sidebar-nav");
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-label", "Open navigation");
    button.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true">
        <path fill-rule="evenodd" d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5m0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5m0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5"/>
      </svg>
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true" hidden>
        <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708"/>
      </svg>`;
    return button;
  }

  function buildSidebar() {
    const sidebar = el("aside", "sidebar");
    sidebar.id = "sidebar-nav";

    const brand = el("div", "sidebar__brand");
    const brandText = el("div");
    brandText.appendChild(el("div", "sidebar__brand-name", "Library"));
    brandText.appendChild(el("div", "sidebar__brand-sub", "Management System"));
    brand.appendChild(brandText);
    sidebar.appendChild(brand);

    const nav = el("nav", "sidebar__nav");
    const current =
      document.body.dataset.nav || window.location.pathname.split("/").pop();
    let activeSet = false;
    for (const section of navItems().sections) {
      nav.appendChild(el("div", "sidebar__section", section.label));
      for (const item of section.items) {
        const link = el("a", "sidebar__link", item.label);
        link.href = item.href;
        if (!activeSet && item.href.endsWith(current)) {
          link.classList.add("active");
          activeSet = true;
        }
        nav.appendChild(link);
      }
    }
    sidebar.appendChild(nav);

    const footer = el("div", "sidebar__footer");
    const logout = el("button", "btn btn--block logout-btn", "Logout");
    logout.type = "button";
    logout.addEventListener("click", () => {
      Session.clear();
      window.location.replace(Session.loginPath());
    });
    footer.appendChild(logout);
    sidebar.appendChild(footer);

    return sidebar;
  }

  function buildTopbar() {
    const topbar = el("header", "topbar");
    topbar.appendChild(buildNavToggle());
    const title = document.body.dataset.title || "";
    topbar.appendChild(el("div", "topbar__title", title));

    const user = el("div", "topbar__user");
    user.appendChild(el("span", "topbar__email", Session.email() || ""));
    user.appendChild(
      el(
        "span",
        `badge badge--${Session.isStaffLike() ? "blue" : "gray"}`,
        Session.getRole()
      )
    );
    topbar.appendChild(user);
    return topbar;
  }

  function buildShell(pageNodes) {
    const shell = el("div", "shell");
    shell.appendChild(buildSidebar());

    const main = el("div", "main");
    main.appendChild(buildTopbar());

    const content = el("main", "content");
    pageNodes.forEach((node) => content.appendChild(node));
    main.appendChild(content);

    shell.appendChild(main);
    return shell;
  }

  function setupDrawer(topbar, sidebar, scrim) {
    const toggle = topbar.querySelector(".nav-toggle");
    const [iconMenu, iconClose] = toggle.querySelectorAll("svg");
    let open = false;

    function setOpen(shouldOpen, { returnFocus = false } = {}) {
      open = shouldOpen;
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute(
        "aria-label",
        open ? "Close navigation" : "Open navigation"
      );
      iconMenu.toggleAttribute("hidden", open);
      iconClose.toggleAttribute("hidden", !open);
      sidebar.classList.toggle("open", open);
      scrim.classList.toggle("visible", open);
      document.body.classList.toggle("no-scroll", open);
      if (open) {
        const firstLink = sidebar.querySelector("a");
        if (firstLink) firstLink.focus();
      } else if (returnFocus) {
        toggle.focus();
      }
    }

    toggle.addEventListener("click", () => setOpen(!open));
    scrim.addEventListener("click", () =>
      setOpen(false, { returnFocus: true })
    );
    document.addEventListener("keydown", (event) => {
      if (open && event.key === "Escape") setOpen(false, { returnFocus: true });
    });
    sidebar.addEventListener("click", (event) => {
      if (open && event.target.closest("a")) setOpen(false);
    });
    MOBILE_QUERY.addEventListener("change", () => {
      if (open && !MOBILE_QUERY.matches) setOpen(false);
    });
  }

  async function showFineBanner(content) {
    // Members only: warn about outstanding fines on every page.
    if (Session.isStaffLike()) return;
    try {
      const response = await fetch(`${window.CONFIG.API_BASE_URL}/users/me`, {
        headers: { Authorization: `Bearer ${Session.getToken()}` },
      });
      if (!response.ok) return;
      const profile = await response.json();
      if (!(profile.fine_balance > 0)) return;
      const banner = el(
        "div",
        "banner banner--warning",
        `You have an outstanding fine of ₦${Number(profile.fine_balance).toLocaleString()}. Online payment is coming soon - please pay at the library desk to restore reservation privileges.`
      );
      banner.setAttribute("role", "status");
      content.prepend(banner);
    } catch {
      // The banner is a nicety; never break a page over it.
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (document.body.dataset.layout === "auth") return;

    const pageNodes = Array.from(document.body.children).filter(
      (node) => node.tagName !== "SCRIPT" && node.tagName !== "LINK"
    );
    document.body.textContent = "";

    const shell = buildShell(pageNodes);
    const scrim = el("div", "scrim");
    shell.appendChild(scrim);
    document.body.appendChild(shell);

    setupDrawer(
      shell.querySelector(".topbar"),
      shell.querySelector(".sidebar"),
      scrim
    );
    showFineBanner(shell.querySelector(".content"));
  });
})();
