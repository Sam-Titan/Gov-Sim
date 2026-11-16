import { act, fireEvent, render, screen } from "@testing-library/react";
import i18n from "@/i18n/setup";
import { CustomPolicy } from "./CustomPolicy";

describe("CustomPolicy form", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    return i18n.changeLanguage("en");
  });
  afterEach(() => vi.useRealTimers());

  it("turns the choices into a target group and leaves 'Anyone' out", () => {
    const onChange = vi.fn();
    render(<CustomPolicy name="" group={{}} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText("Gender"), { target: { value: "yes" } });
    fireEvent.change(screen.getByLabelText("Area"), { target: { value: "no" } });
    fireEvent.change(screen.getByLabelText("Policy name"), { target: { value: "  Women urban " } });
    act(() => vi.advanceTimersByTime(400));
    expect(onChange).toHaveBeenLastCalledWith({
      name: "Women urban",
      group: { female: true, rural: false },
    });
  });

  it("starts from the group in the link", () => {
    render(
      <CustomPolicy name="X" group={{ age_60_plus: true, unbanked: false }} onChange={vi.fn()} />,
    );
    expect((screen.getByLabelText("Age") as HTMLSelectElement).value).toBe("yes");
    expect((screen.getByLabelText("Bank account") as HTMLSelectElement).value).toBe("no");
    expect((screen.getByLabelText("Gender") as HTMLSelectElement).value).toBe("any");
  });

  it("says that the bank account value is a state value", () => {
    render(<CustomPolicy name="" group={{}} onChange={vi.fn()} />);
    expect(screen.getByText(/state value/)).toBeTruthy();
  });
});
