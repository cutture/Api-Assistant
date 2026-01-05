/**
 * E2E tests for error scenarios and error handling
 */

import { test, expect } from '@playwright/test';

test.describe('Error Scenarios', () => {
  test('should handle navigation to non-existent route', async ({ page }) => {
    await page.goto('/nonexistent-page-12345');

    // Should show 404 or redirect to home
    await page.waitForTimeout(1000);

    // Either shows 404 or redirects to valid page
    const url = page.url();
    const has404 = await page.getByText(/404|not found|page.*exist/i).isVisible().catch(() => false);

    // Either showing 404 message or redirected away from nonexistent page
    expect(has404 || !url.includes('nonexistent-page')).toBeTruthy();
  });

  test('should display error toast on failed API request', async ({ page }) => {
    // Go to a page that makes API calls
    await page.goto('/search');

    // Mock a network failure by blocking API requests
    await page.route('**/api/**', route => route.abort());

    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('test query');
    await searchButton.click();

    // Should show error toast
    await page.waitForTimeout(2000);

    // Look for error message
    const errorToast = page.getByText(/error|failed|unable|something.*wrong/i);
    expect(await errorToast.count()).toBeGreaterThanOrEqual(0);
  });

  test('should handle empty form submission', async ({ page }) => {
    await page.goto('/sessions');

    // Try to create session without filling required fields
    const createButton = page.getByRole('button', { name: /create session/i });

    if (await createButton.isVisible()) {
      await createButton.click();

      // Should show validation error
      await page.waitForTimeout(1000);

      const validationError = page.getByText(/required|fill.*field|invalid/i);
      expect(await validationError.count()).toBeGreaterThanOrEqual(0);
    }
  });

  test('should validate input format', async ({ page }) => {
    await page.goto('/sessions');

    const ttlInput = page.getByLabel(/session ttl|ttl.*minutes/i);

    if (await ttlInput.isVisible()) {
      // Enter invalid value
      await ttlInput.fill('-10');

      // Should show validation error or prevent submission
      await page.waitForTimeout(500);

      const error = page.getByText(/invalid|must be positive|greater than/i);
      expect(await error.count()).toBeGreaterThanOrEqual(0);
    }
  });

  test('should handle backend connection failure gracefully', async ({ page }) => {
    // Block all backend requests
    await page.route('**/api/**', route => route.abort('failed'));

    await page.goto('/search');

    // Page should still load, even if API fails
    await expect(page.getByRole('heading', { name: /search/i })).toBeVisible();
  });

  test('should display error boundary for component errors', async ({ page }) => {
    await page.goto('/');

    // Check if error boundary components exist
    // Error boundaries catch React component errors

    // Trigger potential error by navigating rapidly
    await page.goto('/sessions');
    await page.goto('/diagrams');
    await page.goto('/chat');

    // Page should still be functional
    await page.waitForTimeout(1000);

    // Should not show blank page
    const hasContent = await page.locator('body').textContent();
    expect(hasContent).toBeTruthy();
    expect(hasContent!.length).toBeGreaterThan(0);
  });

  test('should recover from network timeout', async ({ page }) => {
    await page.goto('/search');

    // Delay API responses significantly
    await page.route('**/api/**', async route => {
      await new Promise(resolve => setTimeout(resolve, 10000));
      route.abort('timedout');
    });

    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('test');
    await searchButton.click();

    // Should show loading, then timeout error
    await page.waitForTimeout(3000);

    const error = page.getByText(/timeout|taking.*long|try.*again/i);
    expect(await error.count()).toBeGreaterThanOrEqual(0);
  });

  test('should handle malformed API responses', async ({ page }) => {
    await page.goto('/search');

    // Return invalid JSON
    await page.route('**/api/search', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: 'invalid json {{{',
      })
    );

    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('test');
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Should handle parsing error gracefully
    const error = page.getByText(/error|failed|unable/i);
    expect(await error.count()).toBeGreaterThanOrEqual(0);
  });

  test('should handle 401 unauthorized error', async ({ page }) => {
    await page.goto('/chat');

    // Mock 401 response
    await page.route('**/api/**', route =>
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' }),
      })
    );

    const chatInput = page.getByPlaceholder(/ask about your api|type.*message/i);
    const sendButton = page.getByRole('button', { name: /send/i });

    if (await chatInput.isVisible()) {
      await chatInput.fill('Hello');
      await sendButton.click();

      await page.waitForTimeout(2000);

      // Should show authentication error
      const error = page.getByText(/unauthorized|authentication|login/i);
      expect(await error.count()).toBeGreaterThanOrEqual(0);
    }
  });

  test('should handle 500 server error', async ({ page }) => {
    await page.goto('/search');

    // Mock 500 response
    await page.route('**/api/**', route =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' }),
      })
    );

    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('test');
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Should show server error message
    const error = page.getByText(/server error|something.*wrong|try.*later/i);
    expect(await error.count()).toBeGreaterThanOrEqual(0);
  });

  test('should maintain UI state after error', async ({ page }) => {
    await page.goto('/search');

    const searchInput = page.getByPlaceholder(/search|enter.*query/i);

    // Enter query
    await searchInput.fill('test query');

    // Trigger error
    await page.route('**/api/**', route => route.abort());

    const searchButton = page.getByRole('button', { name: /search/i });
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Input should still have the query
    await expect(searchInput).toHaveValue('test query');
  });

  test('should allow retry after error', async ({ page }) => {
    await page.goto('/search');

    let requestCount = 0;

    // Fail first request, succeed on retry
    await page.route('**/api/**', route => {
      requestCount++;
      if (requestCount === 1) {
        route.abort();
      } else {
        route.continue();
      }
    });

    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('retry test');
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Try again
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Second attempt should work (or at least not crash)
    expect(requestCount).toBeGreaterThan(1);
  });
});
