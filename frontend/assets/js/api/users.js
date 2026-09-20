import { request } from "./client.js";

export const UsersApi = {
  list(params = {}) {
    return request("GET", "/users", { query: params });
  },
  me() {
    return request("GET", "/users/me");
  },
  uploadProfilePicture(file) {
    return request("POST", "/users/me/profile-picture", {
      multipart: { file },
    });
  },
  // Raw fetch (not client.js): the response is image bytes, not JSON.
  // Falls back silently — the caller renders the default avatar on failure.
  async fetchProfilePicture() {
    const token = window.Session.getToken();
    const response = await fetch(
      `${window.CONFIG.API_BASE_URL}/users/me/profile-picture`,
      token ? { headers: { Authorization: `Bearer ${token}` } } : undefined
    );
    if (!response.ok) throw new Error(`Profile picture fetch failed: ${response.status}`);
    return response.blob();
  },
};
