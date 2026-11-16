import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { client } from "./api/client.gen";
import "./i18n/setup";

vi.mock("./features/map/DistrictMap", () => ({ DistrictMap: () => <div>map</div> }));

function mockApi(health: boolean) {
  client.setConfig({
    baseUrl: "http://localhost",
    fetch: async (input: RequestInfo | URL) => {
      const url = input instanceof Request ? input.url : String(input);
      const path = new URL(url).pathname;
      if (path === "/api/health" && !health) return new Response("down", { status: 503 });
      const body = path === "/api/health" ? { status: "ok" } : [];
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    },
  });
}

function renderApp() {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("App", () => {
  it("shows the wake-up screen while the server is down", async () => {
    mockApi(false);
    renderApp();
    expect(await screen.findByRole("status")).toHaveProperty(
      "textContent",
      "Waking up the server…",
    );
  });

  it("opens the simulator when the server is up", async () => {
    mockApi(true);
    renderApp();
    expect(await screen.findByText("Expected result")).toBeTruthy();
  });
});
