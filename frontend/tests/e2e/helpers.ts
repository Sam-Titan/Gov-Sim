import { expect, type Page } from "@playwright/test";

/** Select the option of a native select whose text starts with `text`. */
export async function choose(page: Page, name: string, text: string | RegExp) {
  const select = page.getByRole("combobox", { name, exact: true });
  const pattern = typeof text === "string" ? new RegExp(`^${text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`) : text;
  const option = select.locator("option", { hasText: pattern }).first();
  await option.waitFor({ state: "attached" });
  const value = (await option.getAttribute("value")) ?? "";
  await select.selectOption(value);
  // wait until the page has taken the choice (the next click must not run before it)
  await expect(select).toHaveValue(value);
}

/** Open the Simulator and pick state, district and scheme with the real lists. */
export async function pick(page: Page, state: string, district: string, scheme?: string) {
  await page.goto("/");
  await choose(page, "State", state);
  await choose(page, "District", district);
  if (scheme) await choose(page, "Scheme", scheme);
}

/** The middle value and the range of the result panel, as numbers. */
export async function readRange(page: Page) {
  const panel = page.getByRole("region", { name: /Expected result/ });
  await expect(panel).toContainText("%");
  const text = (await panel.innerText()).replace(/\s+/g, " ");
  const m = text.match(/(-?\d+(?:\.\d+)?)\s*[–-]\s*(-?\d+(?:\.\d+)?)\s*%/);
  if (!m) throw new Error(`no range in: ${text.slice(0, 200)}`);
  return { low: Number(m[1]), high: Number(m[2]) };
}
