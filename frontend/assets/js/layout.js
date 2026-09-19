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

  function populateNav(nav) {
    const current =
      document.body.dataset.nav || window.location.pathname.split("/").pop();
    let activeSet = false;
    const list = el("ul", "sidebar__list");
    for (const section of navItems().sections) {
      const sectionItem = el("li");
      sectionItem.appendChild(el("span", "sidebar__section", section.label));
      const group = el("ul", "sidebar__group");
      for (const item of section.items) {
        const entry = el("li");
        const link = el("a", "sidebar__link", item.label);
        link.href = item.href;
        if (!activeSet && item.href.endsWith(current)) {
          link.classList.add("active");
          activeSet = true;
        }
        entry.appendChild(link);
        group.appendChild(entry);
      }
      sectionItem.appendChild(group);
      list.appendChild(sectionItem);
    }
    nav.appendChild(list);
  }

  function enhanceTopbar(topbar) {
    topbar.querySelector(".topbar__title").textContent =
      document.body.dataset.title || "";
    topbar.querySelector(".topbar__email").textContent = Session.email() || "";
    const badge = topbar.querySelector(".badge");
    badge.classList.add(`badge--${Session.isStaffLike() ? "blue" : "gray"}`);
    badge.textContent = Session.getRole();
  }

  function wireLogout(sidebar) {
    const logout = sidebar.querySelector(".logout-btn");
    logout.addEventListener("click", () => {
      Session.clear();
      window.location.replace(Session.loginPath());
    });
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
      const banner = el("div", "banner banner--warning");
      banner.setAttribute("role", "status");
      const icon = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "svg"
      );
      icon.setAttribute("width", "16");
      icon.setAttribute("height", "16");
      icon.setAttribute("fill", "currentColor");
      icon.setAttribute("viewBox", "0 0 16 16");
      icon.setAttribute("aria-hidden", "true");
      const iconPath = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "path"
      );
      iconPath.setAttribute(
        "d",
        "M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"
      );
      icon.appendChild(iconPath);
      const text = document.createElement("span");
      text.textContent = `You have an outstanding fine of ₦${Number(profile.fine_balance).toLocaleString()}. Please pay at the library desk to restore reservation privileges.`;
      banner.append(icon, text);
      content.prepend(banner);
    } catch {
      // The banner is a nicety; never break a page over it.
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (document.body.dataset.layout === "auth") return;

    const sidebar = document.querySelector(".sidebar");
    const topbar = document.querySelector(".topbar");
    const content = document.querySelector(".content");
    const scrim = document.querySelector(".scrim");

    sidebar.querySelector(".sidebar__brand").href = Session.landingPath();
    populateNav(sidebar.querySelector(".sidebar__nav"));
    enhanceTopbar(topbar);
    wireLogout(sidebar);
    setupDrawer(topbar, sidebar, scrim);
    showFineBanner(content);
  });
})();
