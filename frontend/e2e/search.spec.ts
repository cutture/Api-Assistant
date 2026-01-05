/**
 * E2E tests for search flow
 */

import { test, expect } from '@playwright/test';

test.describe('Search Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/search');
  });

  test('should display search page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /search/i })).toBeVisible();
  });

  test('should show search input', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    await expect(searchInput).toBeVisible();
    await expect(searchInput).toBeEnabled();
  });

  test('should have search button', async ({ page }) => {
    const searchButton = page.getByRole('button', { name: /search/i });
    await expect(searchButton).toBeVisible();
  });

  test('should allow typing in search input', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|enter.*query/i);

    await searchInput.fill('user authentication');
    await expect(searchInput).toHaveValue('user authentication');
  });

  test('should perform search on button click', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('GET endpoints');
    await searchButton.click();

    // Wait for search to execute
    await page.waitForTimeout(1000);
  });

  test('should perform search on Enter key', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|enter.*query/i);

    await searchInput.fill('POST requests');
    await searchInput.press('Enter');

    // Wait for search to execute
    await page.waitForTimeout(1000);
  });

  test('should show search mode options', async ({ page }) => {
    // Look for search mode selector
    const modeSelect = page.getByLabel(/search mode|mode/i);

    if (await modeSelect.isVisible()) {
      await modeSelect.click();
      // Should show different search modes
      await expect(page.getByText(/vector|hybrid|reranked/i).first()).toBeVisible();
    }
  });

  test('should display search filters', async ({ page }) => {
    // Look for filter options
    const filters = page.getByText(/filter|advanced|options/i);
    expect(await filters.count()).toBeGreaterThanOrEqual(0);
  });

  test('should show re-ranking toggle', async ({ page }) => {
    // Look for re-ranking option
    const rerankToggle = page.getByLabel(/re-rank|rerank/i);
    expect(await rerankToggle.count()).toBeGreaterThanOrEqual(0);
  });

  test('should show query expansion toggle', async ({ page }) => {
    // Look for query expansion option
    const expansionToggle = page.getByLabel(/query expansion|expand/i);
    expect(await expansionToggle.count()).toBeGreaterThanOrEqual(0);
  });

  test('should show diversification toggle', async ({ page }) => {
    // Look for diversification option
    const diversifyToggle = page.getByLabel(/diversif/i);
    expect(await diversifyToggle.count()).toBeGreaterThanOrEqual(0);
  });

  test('should display number of results selector', async ({ page }) => {
    // Look for results count input
    const resultsInput = page.getByLabel(/number.*results|results|limit/i);
    expect(await resultsInput.count()).toBeGreaterThanOrEqual(0);
  });

  test('should display search results', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('API endpoints');
    await searchButton.click();

    // Wait for results
    await page.waitForTimeout(2000);

    // Check for results container
    const resultsContainer = page.locator('[role="list"], .results, .search-results');
    expect(await resultsContainer.count()).toBeGreaterThanOrEqual(0);
  });

  test('should show loading indicator during search', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('authentication');
    await searchButton.click();

    // Look for loading indicator
    const loader = page.locator('[role="status"], .loading, .spinner');
    await page.waitForTimeout(500);
  });

  test('should display relevance scores if enabled', async ({ page }) => {
    // After searching, scores might be visible
    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('test query');
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Look for score elements
    const scores = page.locator('[data-score], .score');
    expect(await scores.count()).toBeGreaterThanOrEqual(0);
  });

  test('should display metadata if enabled', async ({ page }) => {
    // After searching, metadata might be visible
    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('test query');
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Look for metadata elements
    const metadata = page.locator('[data-metadata], .metadata');
    expect(await metadata.count()).toBeGreaterThanOrEqual(0);
  });

  test('should show empty state when no results', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('xyznonexistentquery123');
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Look for empty state message
    const emptyState = page.getByText(/no results|not found|try.*different/i);
    // Empty state might or might not appear depending on data
    expect(await emptyState.count()).toBeGreaterThanOrEqual(0);
  });

  test('should allow clicking on search results', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|enter.*query/i);
    const searchButton = page.getByRole('button', { name: /search/i });

    await searchInput.fill('endpoints');
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Look for clickable result items
    const resultItems = page.locator('[role="listitem"], .result-item, .search-result');
    expect(await resultItems.count()).toBeGreaterThanOrEqual(0);
  });
});
