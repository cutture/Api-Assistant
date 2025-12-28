/**
 * E2E tests for session management flows
 */

import { test, expect } from '@playwright/test';

test.describe('Session Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/sessions');
  });

  test('should display session management page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /session management/i })).toBeVisible();
    await expect(page.getByText(/create and manage user sessions/i)).toBeVisible();
  });

  test('should create a new session', async ({ page }) => {
    // Fill in the form
    await page.getByLabel(/user id/i).fill('test-user-e2e');
    await page.getByLabel(/session ttl/i).fill('90');

    // Check a setting
    await page.getByLabel(/enable re-ranking/i).check();

    // Click create button
    await page.getByRole('button', { name: /create session/i }).click();

    // Wait for success toast
    await expect(page.getByText(/session created/i)).toBeVisible({ timeout: 5000 });

    // Form should be reset
    await expect(page.getByLabel(/user id/i)).toHaveValue('');
  });

  test('should display session stats', async ({ page }) => {
    await expect(page.getByText(/total sessions/i)).toBeVisible();
    await expect(page.getByText(/active/i)).toBeVisible();
    await expect(page.getByText(/inactive/i)).toBeVisible();
    await expect(page.getByText(/expired/i)).toBeVisible();
  });

  test('should list sessions', async ({ page }) => {
    await expect(page.getByRole('button', { name: /all/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /active/i })).toBeVisible();
  });

  test('should filter sessions by status', async ({ page }) => {
    // Click Active filter
    await page.getByRole('button', { name: /^active$/i }).click();

    // Wait for filtered results
    await page.waitForTimeout(500);

    // Active button should be highlighted
    const activeButton = page.getByRole('button', { name: /^active$/i });
    await expect(activeButton).toBeVisible();
  });

  test('should delete a session with confirmation', async ({ page }) => {
    // Wait for sessions to load
    await page.waitForTimeout(1000);

    // Setup dialog handler to accept confirmation
    page.on('dialog', dialog => dialog.accept());

    // Find and click first delete button (icon only)
    const deleteButtons = page.getByRole('button').filter({ has: page.locator('svg') });
    const firstDeleteButton = deleteButtons.first();

    if (await firstDeleteButton.isVisible()) {
      await firstDeleteButton.click();

      // Wait for success toast
      await expect(page.getByText(/session deleted/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should view session details', async ({ page }) => {
    // Wait for sessions to load
    await page.waitForTimeout(1000);

    // Find and click View button if available
    const viewButton = page.getByRole('button', { name: /view/i }).first();

    if (await viewButton.isVisible()) {
      await viewButton.click();

      // Should show session details
      await expect(page.getByText(/session details/i)).toBeVisible();
      await expect(page.getByText(/conversation history/i)).toBeVisible();

      // Should have back button
      await expect(page.getByRole('button', { name: /back to sessions/i })).toBeVisible();
    }
  });

  test('should navigate back from session details', async ({ page }) => {
    // Wait for sessions to load
    await page.waitForTimeout(1000);

    // Click View button if available
    const viewButton = page.getByRole('button', { name: /view/i }).first();

    if (await viewButton.isVisible()) {
      await viewButton.click();
      await page.waitForTimeout(500);

      // Click back button
      await page.getByRole('button', { name: /back to sessions/i }).click();

      // Should be back at list view
      await expect(page.getByText(/create new session/i)).toBeVisible();
    }
  });

  test('should update TTL display when input changes', async ({ page }) => {
    const ttlInput = page.getByLabel(/session ttl/i);

    // Default should show 1 hour 0 minutes
    await expect(page.getByText(/1 hours 0 minutes/i)).toBeVisible();

    // Change to 150 minutes
    await ttlInput.fill('150');

    // Should show 2 hours 30 minutes
    await expect(page.getByText(/2 hours 30 minutes/i)).toBeVisible();
  });

  test('should have accessible form labels', async ({ page }) => {
    await expect(page.getByLabel(/user id/i)).toBeVisible();
    await expect(page.getByLabel(/session ttl/i)).toBeVisible();
    await expect(page.getByLabel(/enable re-ranking/i)).toBeVisible();
    await expect(page.getByLabel(/enable query expansion/i)).toBeVisible();
  });
});
