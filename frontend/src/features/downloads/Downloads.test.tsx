import { render, screen } from "@testing-library/react";
import type { SimulateResponse } from "@/api/types.gen";
import i18n from "@/i18n/setup";
import mock from "../../../../shared/mocks/simulate.sample.json";
import { DownloadBar, PrintSummary } from "./Downloads";

const sim = mock as unknown as SimulateResponse;
const meta = { link: "http://x/?state=UP", date: "2026-11-16", version: "2026-11-15" };

describe("print layout", () => {
  beforeEach(() => i18n.changeLanguage("en"));

  it("summary is only for paper and shows settings, link, date, version, sources", () => {
    render(<PrintSummary items={[sim]} meta={meta} />);
    const box = screen.getByTestId("print-summary");
    expect(box.className).toContain("hidden");
    expect(box.className).toContain("print:block");
    const text = box.textContent ?? "";
    expect(text).toContain("http://x/?state=UP");
    expect(text).toContain("2026-11-16");
    expect(text).toContain("2026-11-15");
    expect(text).toContain("Sources: NFHS-5");
    expect(text).toContain("A planning aid, not a guarantee.");
  });

  it("buttons are hidden on paper and the CSV button is off with no data", () => {
    const { container } = render(
      <DownloadBar fileKey="download.simulateFile" build={() => null} />,
    );
    expect((container.firstChild as HTMLElement).className).toContain("print:hidden");
    expect((screen.getByText("Download CSV").closest("button") as HTMLButtonElement).disabled).toBe(
      true,
    );
    expect(screen.getByText("Print / Save as PDF")).toBeTruthy();
  });
});
