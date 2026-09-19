import { request } from "./client.js";

export const UsersApi = {
  list(params = {}) {
    return request("GET", "/users", { query: params });
  },
};
