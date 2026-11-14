import { expect, test } from "@playwright/test";
const screens = [
  ["Ask", "/ask", "Ask with evidence"],
  ["Sources", "/sources", "Sources"],
  ["Knowledge", "/knowledge", "Knowledge"],
  ["Quality", "/quality", "Quality"],
  ["Operations", "/operations", "Operations"],
  ["Settings", "/settings", "Settings"],
] as const;

test("workspace navigation and honest availability", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  const navigation = page.getByRole("navigation", { name: "Main navigation" });
  for (const [name, path, title] of screens) {
    await navigation.getByRole("link", { name, exact: true }).click();
    await expect(page).toHaveURL(path);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
    await expect(
      navigation.getByRole("link", { name, exact: true }),
    ).toHaveAttribute("aria-current", "page");
    await expect(
      page.getByText("Not available yet", { exact: true }),
    ).toBeVisible();
    await expect(page.getByRole("textbox")).toHaveCount(0);
    await expect(page.getByRole("button")).toHaveCount(0);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
  }
  await page.screenshot({
    path: testInfo.outputPath("settings.png"),
    fullPage: true,
  });
  await page.goto("/unknown-workspace-page");
  await expect(
    page.getByRole("heading", { name: "Page not found" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Return to overview" }).click();
  await expect(page).toHaveURL("/");
});

test("keyboard navigation and skip link", async ({ page }) => {
  await page.goto("/sources");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to content" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();
  await page.goto("/");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  await expect(
    page
      .getByRole("navigation")
      .getByRole("link", { name: "Ask", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("heading", { name: "Ask with evidence" }),
  ).toBeVisible();
});
