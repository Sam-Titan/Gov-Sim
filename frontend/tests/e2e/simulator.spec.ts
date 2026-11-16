import { expect, test } from "@playwright/test";
import { choose, pick } from "./helpers";

test("Simulator: pick a district, move a slider, result and link follow", async ({ page }) => {
  await pick(page, "Bihar", "Araria", "PM-JAY (health cover)");
  await expect(page.getByText("From data (NFHS-5)")).toBeVisible();
  await expect(page.getByText("Plan with the range, not the middle value.")).toBeVisible();
  await expect(page.getByText("No setting differs from the real scheme.")).toBeVisible();

  // application burden up with the keyboard
  const burden = page.getByRole("slider", { name: /Application burden/ });
  await burden.focus();
  await burden.press("ArrowRight");
  await expect(page.getByText("What moves the result most")).toBeVisible();
  await expect(page.getByText(/Making the application harder lowers uptake by/)).toBeVisible();
  await expect(page).toHaveURL(/burden=/);

  // the link restores the same scenario
  const url = page.url();
  await page.goto(url);
  await expect(page.getByRole("combobox", { name: "District" })).toContainText("Araria");
  await expect(page.getByText(/Making the application harder lowers uptake by/)).toBeVisible();

  // back to real settings
  await page.getByRole("button", { name: "Back to real settings" }).click();
  await expect(page.getByText("No setting differs from the real scheme.")).toBeVisible();
});

test("Simulator: a setting beyond real schemes shows the warning", async ({ page }) => {
  await pick(page, "Bihar", "Araria", "PM-JAY (health cover)");
  const docs = page.getByRole("slider", { name: /Documents needed/ });
  await docs.focus();
  await docs.press("End");
  await expect(page.getByText(/Beyond what real schemes do/)).toBeVisible();
});

test("Simulator: a district without data says why, no result", async ({ page }) => {
  await page.goto("/");
  await choose(page, "State", "Telangana");
  await choose(page, "District", /no data/);
  await expect(page.getByText(/No result for this district/)).toBeVisible();
});
