import { readFileSync } from "node:fs";
import { expect, type Page, test } from "@playwright/test";
import { choose, pick } from "./helpers";

async function saved(page: Page, buttonName: string | RegExp) {
  const button = page.getByRole("button", { name: buttonName });
  await expect(button).toBeEnabled(); // disabled while a result is updating
  const wait = page.waitForEvent("download");
  await button.click();
  const download = await wait;
  const bytes = readFileSync(await download.path());
  return { name: download.suggestedFilename(), bytes, text: bytes.toString("utf8") };
}

test("CSV: result file has a BOM, CRLF, the scenario link, and a guarded policy name", async ({
  page,
}) => {
  await pick(page, "Bihar", "Araria", "PMUY");
  await page.getByRole("switch", { name: "Custom policy" }).click();
  await page.getByRole("textbox", { name: "Policy name" }).fill("=SUM(A1)");
  await choose(page, "Age", "60 or older");
  // the form commits to the link after a short delay; download only once it has
  await expect(page).toHaveURL(/name=.*age60=1|age60=1.*name=/);
  await expect(page.getByText("Estimated number reached")).toBeVisible();

  const csv = await saved(page, "Download CSV");
  expect(csv.name).toMatch(/^govsim-result-\d{4}-\d{2}-\d{2}\.csv$/);
  expect([...csv.bytes.subarray(0, 3)]).toEqual([0xef, 0xbb, 0xbf]);
  expect(csv.text).toContain("\r\n");
  expect(csv.text).toContain("'=SUM(A1)");
  expect(csv.text).not.toMatch(/(^|,)=SUM\(A1\)/m);
  expect(csv.text).toContain("Policy name");
  expect(csv.text).toContain("Araria");
  expect(csv.text).toContain("custom=1"); // the scenario link
  expect(csv.text).toContain("Model and data version");
});

test("CSV: state table has one row per district of the state, with slider columns", async ({
  page,
}) => {
  await pick(page, "Bihar", "Araria", "PM-JAY");
  const burden = page.getByRole("slider", { name: /Application burden/ });
  await burden.focus();
  await burden.press("ArrowRight");
  await expect(page).toHaveURL(/burden=/);
  await expect(page.getByText(/Making the application harder/)).toBeVisible();
  const csv = await saved(page, "Download state table (CSV)");
  expect(csv.name).toMatch(/^govsim-state-/);
  expect(csv.text).toContain("Application burden (1 easy, 5 hard) (used)");
  expect(csv.text).toContain("Application burden (1 easy, 5 hard) (real)");
  expect(csv.text.split("\r\n").filter(Boolean).length).toBeGreaterThan(30);
});

test("CSV: Compare file has A, B and B minus A", async ({ page }) => {
  await page.goto("/compare");
  await choose(page, "State", "Bihar");
  await choose(page, "District", "Araria");
  await expect(page).toHaveURL(/district=/);
  const b = page.getByRole("region", { name: "Setting B" });
  const burden = b.getByRole("slider", { name: /Application burden/ });
  await burden.focus();
  await burden.press("ArrowRight");
  await expect(page).toHaveURL(/b_burden=/);
  await expect(page.getByTestId("difference")).toContainText("−"); // the new result is in
  const csv = await saved(page, "Download CSV");
  expect(csv.name).toMatch(/^govsim-compare-/);
  expect([...csv.bytes.subarray(0, 3)]).toEqual([0xef, 0xbb, 0xbf]);
  const lines = csv.text.split("\r\n");
  expect(lines.some((l) => l.startsWith("Policy A,"))).toBe(true);
  expect(lines.some((l) => l.startsWith("Policy B,"))).toBe(true);
  expect(lines.some((l) => l.startsWith("B minus A,"))).toBe(true);
});

test("Print view: summary shows, menu, map and buttons are hidden", async ({ page }) => {
  await pick(page, "Bihar", "Araria", "PM-JAY");
  await expect(page.getByText("Expected result")).toBeVisible();
  await page.emulateMedia({ media: "print" });
  await expect(page.getByTestId("print-summary")).toBeVisible();
  await expect(page.getByRole("banner")).toBeHidden();
  await expect(page.getByRole("button", { name: "Download CSV" })).toBeHidden();
  await expect(page.getByRole("button", { name: /Print/ })).toBeHidden();
  await expect(page.getByRole("combobox", { name: "State" })).toBeHidden();
});
