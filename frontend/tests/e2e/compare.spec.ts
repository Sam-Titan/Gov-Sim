import { expect, test } from "@playwright/test";
import { choose } from "./helpers";

async function openCompare(page: import("@playwright/test").Page) {
  await page.goto("/compare");
  await choose(page, "State", "Bihar");
  await choose(page, "District", "Araria");
  await expect(page).toHaveURL(/district=/); // the link is updated before the next click
}

test("Compare: same scheme, B with a harder application, shows B minus A as a range", async ({
  page,
}) => {
  await openCompare(page);
  const b = page.getByRole("region", { name: "Setting B" });
  const burden = b.getByRole("slider", { name: /Application burden/ });
  await burden.focus();
  await burden.press("ArrowRight");
  await expect(page.getByRole("region", { name: /Difference/ })).toContainText(/pp/);
  await expect(page.getByTestId("difference")).toContainText(/to/);
  await expect(page.getByTestId("difference")).toContainText("−");
});

test("Compare: two different schemes show no difference", async ({ page }) => {
  await openCompare(page);
  const b = page.getByRole("region", { name: "Setting B" });
  await b
    .getByRole("combobox", { name: "Scheme" })
    .selectOption({ label: "PMUY (cooking gas)" });
  await expect(page.getByText(/No difference is shown: A and B are different schemes/)).toBeVisible();
});
