import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";
import { choose } from "./helpers";

const hi = JSON.parse(readFileSync("src/i18n/hi.json", "utf8"));

test("EN/HI: switching language changes the page, shows the draft note, and is remembered", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("note")).toHaveCount(0);
  await page.getByRole("button", { name: "हिन्दी" }).click();
  await expect(page.getByRole("note")).toHaveText(hi.app.hindiDraft);
  await expect(page.getByRole("heading", { name: hi.result.title })).toBeVisible();
  await expect(page.getByRole("link", { name: hi.nav.compare })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("lang", "hi");

  await page.reload();
  await expect(page.getByRole("heading", { name: hi.result.title })).toBeVisible();

  await page.getByRole("button", { name: "English" }).click();
  await expect(page.getByRole("note")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Expected result" })).toBeVisible();
});

test("EN/HI: a Hindi result shows Hindi labels with Latin digits", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "हिन्दी" }).click();
  await choose(page, hi.picker.state, "Bihar");
  await choose(page, hi.picker.district, "Araria");
  await choose(page, hi.picker.scheme, hi.scheme.pmjay);
  await expect(page.getByText(/^\d+(\.\d+)?–\d+(\.\d+)?%$/).first()).toBeVisible();
  await expect(page.getByText(hi.sliders.title)).toBeVisible();
  await expect(page.getByText("Expected result")).toHaveCount(0);
});

for (const path of ["/", "/compare", "/report", "/about"]) {
  for (const lng of ["English", "हिन्दी"]) {
    test(`Mobile 390 px, ${lng}: ${path} has no sideways page scroll`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(path);
      await page.getByRole("button", { name: lng }).click();
      await expect(page.getByRole("banner")).toBeVisible();
      await page.waitForLoadState("networkidle");
      const over = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(over).toBeLessThanOrEqual(0);
    });
  }
}
