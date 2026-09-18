(function () {
  const Session = window.Session;

  function navItems() {
    const p = Session.prefix();
    if (Session.isStaffLike()) {
      return {
        sections: [
          {
            label: "Staff",
            items: [
              { label: "Dashboard", href: p + "staff/dashboard.html" },
              { label: "Loans", href: p + "placeholder.html" },
              { label: "Inventory", href: p + "placeholder.html" },
              { label: "Members", href: p + "placeholder.html" },
            ],
          },
          {
            label: "Library",
            items: [
              { label: "Catalog", href: p + "catalog.html" },
              { label: "My Reservations", href: p + "placeholder.html" },
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
            { label: "My Reservations", href: p + "placeholder.html" },
            { label: "My Loans", href: p + "placeholder.html" },
            { label: "Fines", href: p + "placeholder.html" },
            { label: "Profile", href: p + "placeholder.html" },
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

  function buildSidebar() {
    const sidebar = el("aside", "sidebar");

    const brand = el("div", "sidebar__brand");
    const brandText = el("div");
    brandText.appendChild(el("div", "sidebar__brand-name", "Library"));
    brandText.appendChild(el("div", "sidebar__brand-sub", "Management System"));
    brand.appendChild(brandText);
    sidebar.appendChild(brand);

    const nav = el("nav", "sidebar__nav");
    const current = window.location.pathname.split("/").pop();
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
    const logout = el("button", "btn btn--secondary btn--block", "Logout");
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
    const title = document.body.dataset.title || "";
    topbar.appendChild(el("div", "topbar__title", title));

    const user = el("div", "topbar__user");
    user.appendChild(el("span", "topbar__email", Session.email() || ""));
    user.appendChild(el("span", `badge badge--${Session.isStaffLike() ? "blue" : "gray"}`, Session.getRole()));
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

  document.addEventListener("DOMContentLoaded", () => {
    if (document.body.dataset.layout === "auth") return;

    const pageNodes = Array.from(document.body.children).filter(
      (node) => node.tagName !== "SCRIPT" && node.tagName !== "LINK"
    );
    document.body.textContent = "";
    document.body.appendChild(buildShell(pageNodes));
  });
})();
