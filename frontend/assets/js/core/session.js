(function () {
  const TOKEN_KEY = "lib_token";

  function decodePayload(token) {
    try {
      const part = token.split(".")[1];
      const pad = part.length % 4 ? "=".repeat(4 - (part.length % 4)) : "";
      const json = atob(part.replace(/-/g, "+").replace(/_/g, "/") + pad);
      return JSON.parse(json);
    } catch {
      return null;
    }
  }

  function inStaffSection() {
    return window.location.pathname.includes("/staff/");
  }

  window.Session = {
    getToken() {
      return localStorage.getItem(TOKEN_KEY);
    },
    setToken(token) {
      localStorage.setItem(TOKEN_KEY, token);
    },
    clear() {
      localStorage.removeItem(TOKEN_KEY);
    },
    claims() {
      const token = this.getToken();
      return token ? decodePayload(token) : null;
    },
    isLoggedIn() {
      const claims = this.claims();
      return Boolean(claims && claims.exp * 1000 > Date.now());
    },
    getRole() {
      const claims = this.claims();
      return claims ? claims.role : null;
    },
    isStaffLike() {
      const role = this.getRole();
      return role === "staff" || role === "admin";
    },
    email() {
      const claims = this.claims();
      return claims ? claims.sub : null;
    },
    userUid() {
      const claims = this.claims();
      return claims ? claims.user_uid : null;
    },
    prefix() {
      return inStaffSection() ? "../" : "";
    },
    loginPath() {
      return this.prefix() + "index.html";
    },
    landingPath() {
      return this.isStaffLike() ? this.prefix() + "staff/dashboard.html" : this.prefix() + "catalog.html";
    },
  };
})();
