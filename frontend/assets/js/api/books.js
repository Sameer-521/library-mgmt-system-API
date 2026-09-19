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
  activeLoans(params = {}) {
    return request("GET", "/books/loans/active", { query: params });
  },
  loanBook({ user_uid, isbn }) {
    return request("POST", "/books/loan-book", { form: { user_uid, isbn } });
  },
  returnLoan({ bk_copy_barcode, loan_id }) {
    return request("POST", "/books/loan-return", {
      form: { bk_copy_barcode, loan_id },
    });
  },
};
