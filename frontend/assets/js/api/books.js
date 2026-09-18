import { request } from "./client.js";

export const BooksApi = {
  list(params = {}) {
    return request("GET", "/books", { query: params });
  },
  fetchByIsbn(isbn) {
    return request("GET", "/books/fetch", { query: { isbn } });
  },
  schedule(isbn) {
    return request("POST", "/books/schedule-book", { query: { isbn } });
  },
  mySchedules() {
    return request("GET", "/books/schedules/me");
  },
};
