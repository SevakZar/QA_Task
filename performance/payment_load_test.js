import http from "k6/http";
import { check, sleep } from "k6";
import { handleHtmlSummary } from "./summary.js";

export const handleSummary = handleHtmlSummary("load");

const BASE_URL = (__ENV.BASE_URL || "http://127.0.0.1:8080").replace(/\/$/, "");
const CELL_NUMBER = __ENV.CELL_NUMBER || "09121111111";

export const options = {
  vus: 10,
  duration: "30s",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<1000"],
    checks: ["rate>0.99"],
  },
};

export default function () {
  const response = http.get(`${BASE_URL}/payment/?CellNumber=${CELL_NUMBER}`);
  const body = response.json();

  check(response, {
    "HTTP status is 200": (r) => r.status === 200,
    "body.status is 200": () => body && body.status === 200,
    "payment_methods is an array": () => Array.isArray(body && body.payment_methods),
  });

  sleep(1);
}