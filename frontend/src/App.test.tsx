import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import App from "./App";
import { client } from "./api/client.gen";
import "./i18n/setup";

describe("App", () => {
  it("shows server status from /api/health", async () => {
    client.setConfig({
      baseUrl: "http://localhost",
      fetch: async () =>
        new Response(JSON.stringify({ status: "ok" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    });
    render(
      <QueryClientProvider client={new QueryClient()}>
        <App />
      </QueryClientProvider>,
    );
    expect(await screen.findByText("Server is running")).toBeTruthy();
  });
});
