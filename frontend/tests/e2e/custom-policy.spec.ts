import { expect, test } from "@playwright/test";
import { choose, pick } from "./helpers";

test("Custom policy: age 60+ rural group on PMUY shows badge, group uptake and reach", async ({
  page,
}) => {
  await pick(page, "Bihar", "Araria", "PMUY");
  await page.getByRole("switch", { name: "Custom policy" }).click();
  await page.getByRole("textbox", { name: "Policy name" }).fill("Elders first");
  await choose(page, "Age", "60 or older");
  await choose(page, "Area", "Rural");
  await expect(page.getByText("New policy", { exact: true }).first()).toBeVisible();
  await expect(page.getByText(/This is a new policy, far from any real scheme/)).toBeVisible();
  await expect(page.getByText(/Start scheme, all eligible \(NFHS-5\)/)).toBeVisible();
  await expect(page.getByText("Estimated number reached")).toBeVisible();
  await expect(page.getByText(/Estimated, Census 2011 base/)).toBeVisible();
  await expect(page).toHaveURL(/custom=1/);
  await expect(page).toHaveURL(/age60=1/);
  await expect(page).toHaveURL(/rural=1/);
});

test("Custom policy: a group that is too small is refused with a reason", async ({ page }) => {
  await pick(page, "Bihar", "Araria", "PMUY");
  await page.getByRole("switch", { name: "Custom policy" }).click();
  await choose(page, "Age", "60 or older");
  await choose(page, "Disability", "With a disability");
  await choose(page, "Bank account", "Without a bank account");
  await expect(page.getByText(/target group is too small in this district/i)).toBeVisible();
});
