import en from "./en.json";
import hi from "./hi.json";

function keys(o: Record<string, unknown>, prefix = ""): string[] {
  return Object.entries(o).flatMap(([k, v]) =>
    k.startsWith("_")
      ? []
      : typeof v === "object" && v !== null
        ? keys(v as Record<string, unknown>, `${prefix}${k}.`)
        : [`${prefix}${k}`],
  );
}

describe("translations", () => {
  it("Hindi has every English key and nothing else", () => {
    expect(keys(hi).sort()).toEqual(keys(en).sort());
  });
});

describe("language choice", () => {
  it("is saved in localStorage", async () => {
    const { default: i18n } = await import("./setup");
    await i18n.changeLanguage("hi");
    expect(localStorage.getItem("govsim.lang")).toBe("hi");
    await i18n.changeLanguage("en");
    expect(localStorage.getItem("govsim.lang")).toBe("en");
  });
});
