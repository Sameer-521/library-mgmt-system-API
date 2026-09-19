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
  create({ title, author, isbn, location, available }) {
    return request("POST", "/books", {
      form: { title, author, isbn, location, available },
    });
  },
  update(isbn, fields) {
    return request("PUT", `/books/${encodeURIComponent(isbn)}`, { form: fields });
  },
  generateCopies({ isbn, quantity }) {
    return request("POST", "/books/generate-copies", {
      form: { isbn, quantity: String(quantity) },
    });
  },
  bkCopies(params = {}) {
    return request("GET", "/books/bk-copies", { query: params });
  },
  updateBkCopies(bookCopies) {
    return request("PATCH", "/books/bk-copies", {
      json: { book_copies: bookCopies },
    });
  },
};
