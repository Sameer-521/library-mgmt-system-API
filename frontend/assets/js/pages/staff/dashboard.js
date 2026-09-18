if (window.Session.getRole() === "admin") {
  const banner = document.createElement("div");
  banner.className = "banner";
  banner.textContent =
    "You are logged in as admin. The dedicated admin panel is planned separately. The staff tools work the same for you.";
  document.getElementById("admin-note-slot").appendChild(banner);
}
