import { defineConfig } from "@hey-api/openapi-ts";

// The simulate routes are POST but have no side effects: generate query options
// (cached, cancellable) for them instead of mutations.
const POST_QUERIES = new Set(["/api/simulate", "/api/simulate/state", "/api/compare"]);

export default defineConfig({
  input: "./openapi.json",
  output: "./src/api",
  plugins: ["@hey-api/client-fetch", "@tanstack/react-query"],
  parser: {
    hooks: {
      operations: {
        isQuery: (op) => (op.method === "post" && POST_QUERIES.has(op.path) ? true : undefined),
      },
    },
  },
});
