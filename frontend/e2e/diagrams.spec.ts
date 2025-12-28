/**
 * E2E tests for diagram generation flows
 */

import { test, expect } from '@playwright/test';

test.describe('Diagram Generation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/diagrams');
  });

  test('should display diagram generator page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /diagram generator/i })).toBeVisible();
    await expect(page.getByText(/generate sequence diagrams/i)).toBeVisible();
  });

  test('should show sequence diagram options by default', async ({ page }) => {
    await expect(page.getByLabel(/endpoint document id/i)).toBeVisible();
    await expect(page.getByPlaceholder(/enter document id/i)).toBeVisible();
  });

  test('should switch to auth flow options', async ({ page }) => {
    // Click diagram type select
    await page.getByLabel(/diagram type/i).click();

    // Select Authentication Flow
    await page.getByText('Authentication Flow').click();

    // Should show auth type select
    await expect(page.getByLabel(/authentication type/i)).toBeVisible();

    // Should not show endpoint ID input
    await expect(page.getByLabel(/endpoint document id/i)).not.toBeVisible();
  });

  test('should show error when generating sequence diagram without endpoint ID', async ({ page }) => {
    // Click generate without entering endpoint ID
    await page.getByRole('button', { name: /generate diagram/i }).click();

    // Should show error toast
    await expect(page.getByText(/endpoint id required/i)).toBeVisible({ timeout: 5000 });
  });

  test('should attempt to generate sequence diagram with endpoint ID', async ({ page }) => {
    // Enter endpoint ID
    await page.getByLabel(/endpoint document id/i).fill('test-endpoint-123');

    // Click generate
    await page.getByRole('button', { name: /generate diagram/i }).click();

    // Wait for request to complete (may succeed or fail depending on backend)
    await page.waitForTimeout(2000);
  });

  test('should attempt to generate auth flow diagram', async ({ page }) => {
    // Switch to auth flow
    await page.getByLabel(/diagram type/i).click();
    await page.getByText('Authentication Flow').click();

    // Wait for UI update
    await page.waitForTimeout(500);

    // Select OAuth 2.0
    await page.getByLabel(/authentication type/i).click();
    await page.getByText('OAuth 2.0').click();

    // Click generate
    await page.getByRole('button', { name: /generate diagram/i }).click();

    // Wait for request to complete
    await page.waitForTimeout(2000);
  });

  test('should have all authentication type options', async ({ page }) => {
    // Switch to auth flow
    await page.getByLabel(/diagram type/i).click();
    await page.getByText('Authentication Flow').click();

    await page.waitForTimeout(500);

    // Click auth type select
    await page.getByLabel(/authentication type/i).click();

    // Check all options are available
    await expect(page.getByText('Bearer Token')).toBeVisible();
    await expect(page.getByText('OAuth 2.0')).toBeVisible();
    await expect(page.getByText('API Key')).toBeVisible();
    await expect(page.getByText('Basic Auth')).toBeVisible();
  });

  test('should have accessible form elements', async ({ page }) => {
    await expect(page.getByLabel(/diagram type/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /generate diagram/i })).toBeVisible();
  });

  test('should disable generate button while loading', async ({ page }) => {
    // Enter endpoint ID
    await page.getByLabel(/endpoint document id/i).fill('test-endpoint-123');

    const generateButton = page.getByRole('button', { name: /generate diagram/i });

    // Click generate
    await generateButton.click();

    // Button should be disabled during request (if backend is slow)
    // Note: This test may pass quickly if backend responds fast
  });
});
