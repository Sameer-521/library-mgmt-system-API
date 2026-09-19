const BASE_URL = window.CONFIG.API_BASE_URL;

export class ApiError extends Error {
  constructor(status, detail, code = null) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.code = code;
  }
}

function extractDetail(data) {
  if (!data) return "Request failed";
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item) => {
        const loc = (item.loc || []).filter((part) => part !== "body").join(".");
        return loc ? `${loc}: ${item.msg}` : item.msg;
      })
      .join("; ");
  }
  if (typeof data.detail === "object" && data.detail !== null) {
    return data.detail.message || data.detail.code || JSON.stringify(data.detail);
  }
  return typeof data === "string" ? data : JSON.stringify(data);
}

function extractErrorCode(data) {
  if (data && typeof data.detail === "object" && data.detail !== null) {
    return data.detail.code || null;
  }
  return null;
}

async function parseBody(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function request(method, path, { query, form, json, multipart } = {}) {
  let url = BASE_URL + path;
  if (query) {
    const params = new URLSearchParams(query);
    const qs = params.toString();
    if (qs) url += `?${qs}`;
  }

  const options = { method, headers: {} };
  const token = window.Session.getToken();
  const hadToken = Boolean(token);
  if (hadToken) options.headers.Authorization = `Bearer ${token}`;

  if (form) {
    options.headers["Content-Type"] = "application/x-www-form-urlencoded";
    options.body = new URLSearchParams(form).toString();
  } else if (json !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(json);
  } else if (multipart) {
    // No Content-Type header: the browser sets the multipart boundary.
    const body = new FormData();
    for (const [key, value] of Object.entries(multipart)) body.append(key, value);
    options.body = body;
  }

  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new ApiError(0, "Network error. Is the API running at " + BASE_URL + "?");
  }

  if (response.status === 401 && hadToken) {
    window.Session.clear();
    window.location.replace(window.Session.loginPath());
    throw new ApiError(401, "Session expired. Please login again.");
  }

  const data = await parseBody(response);

  if (!response.ok) {
    throw new ApiError(response.status, extractDetail(data), extractErrorCode(data));
  }

  return data;
}
