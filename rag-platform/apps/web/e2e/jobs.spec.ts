import { expect, test } from "@playwright/test";

test("job view shows returned progress and removes it after access expires", async ({
  page,
}) => {
  // Synthetic HTTP fixture tests UI transitions; real broker recovery is tested separately.
  let signedIn = true;
  await page.route("**/api/jobs", (route) =>
    route.fulfill(
      signedIn
        ? {
            status: 200,
            contentType: "application/json",
            body: JSON.stringify([
              {
                id: "synthetic-job",
                kind: "worker_check",
                state: "running",
                attempts: 2,
                progress: 40,
              },
            ]),
          }
        : { status: 401, contentType: "application/json", body: "{}" },
    ),
  );
  await page.goto("/operations");
  await expect(
    page.getByRole("heading", { name: "Background jobs" }),
  ).toBeVisible();
  await expect(page.getByText("Attempt 2 · 40% complete")).toBeVisible();
  await expect(page.getByRole("progressbar")).toHaveAttribute("value", "40");
  signedIn = false;
  await expect(
    page.getByRole("heading", { name: "Sign in to view your jobs" }),
  ).toBeVisible({ timeout: 10000 });
  await expect(page.getByText("Job synthetic-job")).toHaveCount(0);
});

test("job service failure has a working refresh and honest empty state", async ({
  page,
}) => {
  let available = false;
  await page.route("**/api/jobs", (route) =>
    route.fulfill({
      status: available ? 200 : 503,
      contentType: "application/json",
      body: available ? "[]" : "{}",
    }),
  );
  await page.goto("/operations");
  await expect(
    page.getByRole("alert", { name: "Jobs could not be refreshed" }),
  ).toContainText("Jobs could not be refreshed");
  available = true;
  await page.getByRole("button", { name: "Refresh jobs" }).click();
  await expect(page.getByText("No background jobs yet.")).toBeVisible();
});
