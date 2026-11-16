import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { client } from "@/api/client.gen";
import i18n from "@/i18n/setup";
import { About } from "./About";

function renderAbout() {
  client.setConfig({
    baseUrl: "http://localhost",
    fetch: async () =>
      new Response(
        JSON.stringify([
          { id: "1", pc11_s_id: "1", name: "A", state: "S", has_data: true },
          { id: "2", pc11_s_id: "1", name: "B", state: "S", has_data: false, reason: "unmapped" },
        ]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
  });
  render(
    <QueryClientProvider client={new QueryClient()}>
      <About />
    </QueryClientProvider>,
  );
}

describe("About page", () => {
  beforeEach(() => i18n.changeLanguage("en"));

  it("has the disclaimer and the three missing districts (D-034)", async () => {
    renderAbout();
    expect(screen.getByTestId("disclaimer").textContent).toBe("A planning aid, not a guarantee.");
    expect(screen.getByText(/Chandigarh/)).toBeTruthy();
    expect(screen.getByText(/Vidisha/)).toBeTruthy();
    expect(screen.getByText(/Lakshadweep/)).toBeTruthy();
    expect(
      await screen.findByText(/1 of 2 listed districts have no result; 1 of them/),
    ).toBeTruthy();
  });

  it("credits DHS and IIPS, the map, and says the Census licence is not stated", () => {
    renderAbout();
    expect(screen.getByText(/The DHS Program/)).toBeTruthy();
    expect(
      screen.getByText(/International Institute for Population Sciences \(IIPS\)/),
    ).toBeTruthy();
    expect(screen.getByText("Licence: Not stated.")).toBeTruthy();
    expect(screen.getAllByText(/CC BY-NC-SA 4\.0/).length).toBeGreaterThan(0);
  });
});
