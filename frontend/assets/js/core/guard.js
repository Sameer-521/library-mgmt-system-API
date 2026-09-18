(function () {
  const options = document.currentScript ? document.currentScript.dataset : {};
  const Session = window.Session;

  if (options.auth === "required") {
    if (!Session.isLoggedIn()) {
      window.location.replace(Session.loginPath());
      return;
    }
    if (options.role === "staff" && !Session.isStaffLike()) {
      window.location.replace(Session.prefix() + "catalog.html");
    }
  } else if (options.auth === "guest") {
    if (Session.isLoggedIn()) {
      window.location.replace(Session.landingPath());
    }
  }
})();
