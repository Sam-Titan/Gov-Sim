import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import { client } from "../api/client.gen";
import "../i18n/setup";
import { HEALTH_POLL_MS, healthQuery } from "./health";

vi.mock("../features/map/DistrictMap", () => ({ DistrictMap: () => <div>map</div> }));

type Step = number | "network" | "hang";

function mockSequence(steps: Step[]) {
  const calls: string[] = [];
  client.setConfig({
    baseUrl: "http://localhost",
    fetch: async (input: RequestInfo | URL, init?: RequestInit) => {
      const req = input instanceof Request ? input : new Request(String(input), init);
      const path = new URL(req.url).pathname;
      if (path !== "/api/health") {
        return new Response("[]", { status: 200, headers: { "Content-Type": "application/json" } });
      }
      const step = steps[calls.length] ?? 200;
      calls.push(String(step));
      if (step === "network") throw new TypeError("Failed to fetch");
      if (step === "hang") {
        return new Promise<Response>((_, reject) =>
          req.signal.addEventListener("abort", () => reject(req.signal.reason)),
        );
      }
      return step === 200
        ? new Response(JSON.stringify({ status: "ok" }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          })
        : new Response("upstream", { status: step });
    },
  });
  return calls;
}

describe("health polling (cold backend)", () => {
  it("polls every 3 seconds", () => {
    expect(HEALTH_POLL_MS).toBe(3000);
  });

  it.each([502, 503, 504, "network"] as const)("treats %s as still waking", async (step) => {
    mockSequence([step]);
    const qc = new QueryClient();
    await expect(qc.fetchQuery({ ...healthQuery(), staleTime: 0 })).rejects.toBeDefined();
    // a failed poll leaves no data, so refetchInterval keeps polling
    expect(healthQuery().refetchInterval({ state: { data: undefined } })).toBe(HEALTH_POLL_MS);
    expect(healthQuery().refetchInterval({ state: { data: { status: "ok" } } })).toBe(false);
  });

  it("a hung request is aborted by the timeout and counted as still waking", async () => {
    mockSequence(["hang"]);
    await expect(new QueryClient().fetchQuery(healthQuery(50))).rejects.toBeDefined();
  });

  it("shows the wake-up screen, never an error, until health answers 200", async () => {
    const calls = mockSequence([502, 503, 504, "network", 200]);
    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect((await screen.findByRole("status")).textContent).toBe("Waking up the server…");
    expect(screen.queryByText(/error/i)).toBeNull();
    await waitFor(() => expect(calls.length).toBeGreaterThanOrEqual(5), { timeout: 20000 });
    expect(await screen.findByText("Expected result", {}, { timeout: 5000 })).toBeTruthy();
  }, 30000);
});
