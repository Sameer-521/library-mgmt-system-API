import { request } from "./client.js";

export const AuthApi = {
  login(email, password) {
    return request("POST", "/auth/login", { form: { email, password } });
  },
  signUp(fullName, email, password) {
    return request("POST", "/users/sign-up", {
      form: { full_name: fullName, email, password },
    });
  },
};
