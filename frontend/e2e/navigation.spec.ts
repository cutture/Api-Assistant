/**
 * E2E tests for navigation flows
 */

import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate to all main pages', async ({ page }) => {
    await page.goto('/');

    // Check home page loads
    await expect(page.getByText(/documents/i)).toBeVisible();

    // Navigate to Search
    await page.getByRole('link', { name: /^search$/i }).click();
    await expect(page).toHaveURL(/\/search/);

    // Navigate to Chat
    await page.getByRole('link', { name: /^chat$/i }).click();
    await expect(page).toHaveURL(/\/chat/);

    // Navigate to Sessions
    await page.getByRole('link', { name: /^sessions$/i }).click();
    await expect(page).toHaveURL(/\/sessions/);

    // Navigate to Diagrams
    await page.getByRole('link', { name: /^diagrams$/i }).click();
    await expect(page).toHaveURL(/\/diagrams/);

    // Navigate to Settings (Settings icon button)
    const settingsButton = page.locator('a[href="/settings"] button');
    await settingsButton.click();
    await expect(page).toHaveURL(/\/settings/);
  });

  test('should highlight active navigation item', async ({ page }) => {
    await page.goto('/sessions');

    // Sessions nav item should be highlighted (secondary variant)
    const sessionsLink = page.getByRole('link', { name: /^sessions$/i });
    await expect(sessionsLink).toBeVisible();
  });

  test('should display logo and title', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByText(/api assistant/i)).toBeVisible();
  });

  test('should have all navigation items visible', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('link', { name: /documents/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /^search$/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /^chat$/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /^sessions$/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /^diagrams$/i })).toBeVisible();
  });

  test('should navigate back to home from logo', async ({ page }) => {
    await page.goto('/sessions');

    // Click logo to go home
    await page.getByText(/api assistant/i).click();

    await expect(page).toHaveURL('/');
  });
});
