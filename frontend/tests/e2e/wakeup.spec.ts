import { expect, test } from "@playwright/test";

// A cold Render backend answers 502/503/504, hangs, or drops the connection. All of these
// mean "still waking": the wake-up screen stays, no error screen, polling goes on.
const STEPS = [
  { name: "502", act: (r: import("@playwright/test").Route) => r.fulfill({ status: 502 }) },
  { name: "503", act: (r: import("@playwright/test").Route) => r.fulfill({ status: 503 }) },
  { name: "504", act: (r: import("@playwright/test").Route) => r.fulfill({ status: 504 }) },
  { name: "dropped", act: (r: import("@playwright/test").Route) => r.abort("connectionrefused") },
  { name: "timeout", act: () => new Promise<void>(() => {}) }, // never answers
] as const;

test("Wake-up: 502, 503, 504, dropped and hung health calls keep the wake-up screen, then the app opens", async ({
  page,
}) => {
  test.setTimeout(120_000);
  const seen: string[] = [];
  await page.route("**/api/health", async (route) => {
    const step = STEPS[seen.length];
    if (step) {
      seen.push(step.name);
      await step.act(route);
    } else {
      seen.push("ok");
      await route.continue(); // the real backend answers
    }
  });
  await page.goto("/");

  const wake = page.getByRole("status").filter({ hasText: "Waking up the server…" });
  await expect(wake).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);

  // every failing answer is followed by another poll; the screen never turns into an error
  await expect.poll(() => seen.length, { timeout: 90_000 }).toBeGreaterThan(STEPS.length);
  await expect(page.getByRole("heading", { name: "Expected result" })).toBeVisible({
    timeout: 30_000,
  });
  await expect(wake).toHaveCount(0);
  expect(seen.slice(0, STEPS.length)).toEqual(STEPS.map((s) => s.name));
});

test("Wake-up screen is shown in Hindi too", async ({ page }) => {
  await page.route("**/api/health", (route) => route.fulfill({ status: 503 }));
  await page.goto("/");
  await page.getByRole("button", { name: "हिन्दी" }).click();
  await expect(page.getByRole("status").filter({ hasText: "सर्वर चालू हो रहा है…" })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("Wake-up: reloading a deep link (/compare) after the server wakes opens that page", async ({
  page,
}) => {
  let calls = 0;
  await page.route("**/api/health", (route) =>
    ++calls < 3 ? route.fulfill({ status: 503 }) : route.continue(),
  );
  await page.goto("/compare");
  await expect(page.getByRole("heading", { name: "Compare two settings" })).toBeVisible({
    timeout: 30_000,
  });
});
