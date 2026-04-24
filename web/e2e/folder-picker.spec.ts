import { test, expect } from "@playwright/test";

test.describe("Folder Picker", () => {
  test("opens browse modal and lists directories", async ({ page }) => {
    await page.goto("/");

    // Open the Add Project modal
    await page.getByText("+ Add Project").click();
    await expect(page.getByText("Add Project").first()).toBeVisible();

    // Click Browse to open the folder picker
    await page.getByRole("button", { name: "Browse" }).click();

    // The picker should show a current path and the "Select this folder" button
    await expect(page.getByText("Select this folder")).toBeVisible();
  });

  test("can navigate into a subdirectory", async ({ page }) => {
    await page.goto("/");
    await page.getByText("+ Add Project").click();
    await page.getByRole("button", { name: "Browse" }).click();

    // Wait for entries to load
    await expect(page.getByText("Select this folder")).toBeVisible();

    // Get the current path shown
    const currentPath = await page
      .locator(".font-mono.text-xs")
      .first()
      .textContent();
    expect(currentPath).toBeTruthy();

    // If there are directory entries, click the first one to navigate
    const entries = page.locator(
      ".max-h-64 button:not(:has-text('Up one level'))",
    );
    const count = await entries.count();
    if (count > 0) {
      const dirName = await entries.first().textContent();
      await entries.first().click();

      // Current path should update to include the clicked directory
      await expect(page.locator(".font-mono.text-xs").first()).not.toHaveText(
        currentPath!,
      );

      // Parent (..) should now be visible
      await expect(page.getByText("Up one level")).toBeVisible();
    }
  });

  test("can navigate up with parent (..) button", async ({ page }) => {
    await page.goto("/");
    await page.getByText("+ Add Project").click();
    await page.getByRole("button", { name: "Browse" }).click();
    await expect(page.getByText("Select this folder")).toBeVisible();

    // Navigate into a subdirectory first
    const entries = page.locator(
      ".max-h-64 button:not(:has-text('Up one level'))",
    );
    const count = await entries.count();
    if (count > 0) {
      await entries.first().click();
      await expect(page.getByText("Up one level")).toBeVisible();

      // Get the path after navigating down
      const deepPath = await page
        .locator(".font-mono.text-xs")
        .first()
        .textContent();

      // Navigate back up
      await page.getByText("Up one level").click();

      // Path should change back
      await expect(page.locator(".font-mono.text-xs").first()).not.toHaveText(
        deepPath!,
      );
    }
  });

  test("select folder populates the path input", async ({ page }) => {
    await page.goto("/");
    await page.getByText("+ Add Project").click();
    await page.getByRole("button", { name: "Browse" }).click();
    await expect(page.getByText("Select this folder")).toBeVisible();

    // Click "Select this folder"
    await page.getByText("Select this folder").click();

    // The browse modal should close and the input should have a value
    await expect(page.getByRole("button", { name: "Browse" })).toBeVisible();
    const pathInput = page.locator('input[placeholder*="projects"]');
    const value = await pathInput.inputValue();
    expect(value).toBeTruthy();
    expect(value.startsWith("/")).toBe(true);
  });

  test("cancel button closes the picker", async ({ page }) => {
    await page.goto("/");
    await page.getByText("+ Add Project").click();
    await page.getByRole("button", { name: "Browse" }).click();
    await expect(page.getByText("Select this folder")).toBeVisible();

    // Click the folder picker's Cancel (the small one, not the modal's)
    await page.getByRole("button", { name: "Cancel" }).first().click();

    // Should be back to the input + Browse button view
    await expect(page.getByRole("button", { name: "Browse" })).toBeVisible();
    await expect(page.getByText("Select this folder")).not.toBeVisible();
  });

  test("browse root prevents navigating above it", async ({ page }) => {
    await page.goto("/");
    await page.getByText("+ Add Project").click();
    await page.getByRole("button", { name: "Browse" }).click();
    await expect(page.getByText("Select this folder")).toBeVisible();

    // At the browse root, there should be no ".." button
    // (the root has no parent link)
    const parentButton = page.locator(".max-h-64 button:has-text('Up one level')");
    await expect(parentButton).not.toBeVisible();
  });
});
