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
};
