import { render, screen } from "@testing-library/react";
import type { CompareResponse, SimulateResponse } from "@/api/types.gen";
import i18n from "@/i18n/setup";
import mock from "../../../../shared/mocks/simulate.sample.json";
import { DifferencePanel } from "./Compare";

const one = mock as unknown as SimulateResponse;

function data(diff: CompareResponse["difference"], bScheme = one.scheme): CompareResponse {
  return { a: one, b: { ...one, scheme: bScheme }, difference: diff };
}

describe("DifferencePanel", () => {
  beforeEach(() => i18n.changeLanguage("en"));

  it("shows B minus A as a range with signs", () => {
    render(<DifferencePanel data={data({ comparable: true, point: 2.5, low: 1, high: 4.2 })} />);
    expect(screen.getByTestId("difference").textContent).toBe("+1.0 to +4.2 pp");
    expect(screen.getByText("Middle value: +2.5 pp")).toBeTruthy();
  });

  it("shows a negative difference with a minus sign", () => {
    render(<DifferencePanel data={data({ comparable: true, point: -2, low: -3, high: -0.5 })} />);
    expect(screen.getByTestId("difference").textContent).toBe("−3.0 to −0.5 pp");
  });

  it("shows no number when the bases differ", () => {
    render(
      <DifferencePanel data={data({ comparable: false, point: null, low: null, high: null })} />,
    );
    expect(screen.queryByTestId("difference")).toBeNull();
    expect(screen.getByRole("status").textContent).toContain("cannot be compared");
  });

  it("says so when A and B are different schemes", () => {
    render(
      <DifferencePanel
        data={data({ comparable: false, point: null, low: null, high: null }, "pmuy")}
      />,
    );
    expect(screen.getByRole("status").textContent).toContain("different schemes");
  });
});
