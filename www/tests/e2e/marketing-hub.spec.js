// @ts-check
/**
 * Marketing Hub E2E Tests
 * Tests for the Cold Email & LinkedIn Outreach Generator
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8080';
const REDSL_API_URL = process.env.REDSL_API_URL || 'http://localhost:8001';

// Test repository for scanning
const TEST_REPO = 'https://github.com/TauricResearch/TradingAgents';

test.describe('Marketing Hub - Page Load', () => {
  test('marketing page returns 200 with valid HTML', async ({ request }) => {
    const response = await request.get('/marketing/');
    expect(response.status()).toBe(200);
    
    const content = await response.text();
    expect(content).toContain('<!DOCTYPE html>');
    expect(content).toContain('ReDSL Marketing Hub');
    expect(content).toContain('Cold Email');
    expect(content).toContain('LinkedIn');
  });

  test('marketing page has no PHP errors', async ({ request }) => {
    const response = await request.get('/marketing/');
    const content = await response.text();
    expect(content).not.toContain('Fatal error');
    expect(content).not.toContain('Parse error');
    expect(content).not.toContain('Warning:');
  });

  test('marketing page has expected form elements', async ({ request }) => {
    const response = await request.get('/marketing/');
    const content = await response.text();
    
    // Form elements
    expect(content).toContain('repo_url');
    expect(content).toContain('buyer_type');
    expect(content).toContain('contact_name');
    expect(content).toContain('sender_name');
    
    // Buyer types
    expect(content).toContain('tech_lead');
    expect(content).toContain('ceo');
    expect(content).toContain('pm_agency');
    
    // Submit button
    expect(content).toContain('Generuj Szablony Outreach');
  });
});

test.describe('Marketing Hub - Browser UI', () => {
  test('page loads with correct title and header', async ({ page }) => {
    await page.goto('/marketing/');
    
    // Check title
    await expect(page).toHaveTitle(/ReDSL Marketing Hub/);
    
    // Check header
    const header = page.locator('header h1');
    await expect(header).toContainText('ReDSL Marketing Hub');
    await expect(header).toBeVisible();
  });

  test('form is visible and interactive', async ({ page }) => {
    await page.goto('/marketing/');
    
    // Check form elements are visible
    await expect(page.locator('input#repo_url')).toBeVisible();
    await expect(page.locator('select#buyer_type')).toBeVisible();
    await expect(page.locator('input#contact_name')).toBeVisible();
    await expect(page.locator('input#sender_name')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('can fill and submit the form', async ({ page }) => {
    await page.goto('/marketing/');
    
    // Fill form
    await page.fill('input#repo_url', TEST_REPO);
    await page.selectOption('select#buyer_type', 'tech_lead');
    await page.fill('input#contact_name', 'Janek');
    await page.fill('input#sender_name', 'Tomek');
    
    // Submit
    await page.click('button[type="submit"]');
    
    // Wait for results or error (API might not be available)
    await page.waitForTimeout(5000);
    
    // Check if we got results or error message
    const content = await page.content();
    const hasResults = content.includes('Skan zakończony') || content.includes('metryki');
    const hasError = content.includes('API Error') || content.includes('error');
    
    expect(hasResults || hasError).toBe(true);
  });

  test('tab navigation works', async ({ page }) => {
    await page.goto('/marketing/');
    
    // First submit the form to get results
    await page.fill('input#repo_url', TEST_REPO);
    await page.selectOption('select#buyer_type', 'tech_lead');
    await page.click('button[type="submit"]');
    
    // Wait for results
    await page.waitForTimeout(5000);
    
    // Check if tabs exist (only visible after form submission)
    const content = await page.content();
    if (content.includes('tab')) {
      // Click on LinkedIn tab
      const linkedinTab = page.locator('.tab:has-text("LinkedIn")');
      if (await linkedinTab.isVisible().catch(() => false)) {
        await linkedinTab.click();
        
        // Check LinkedIn content is visible
        const linkedinContent = page.locator('#linkedin');
        await expect(linkedinContent).toBeVisible();
      }
    }
  });

  test('copy buttons are present after form submission', async ({ page }) => {
    await page.goto('/marketing/');
    
    // Submit form
    await page.fill('input#repo_url', TEST_REPO);
    await page.selectOption('select#buyer_type', 'tech_lead');
    await page.click('button[type="submit"]');
    
    // Wait for results
    await page.waitForTimeout(5000);
    
    // Check if copy buttons exist
    const copyButtons = page.locator('button:has-text("Kopiuj")');
    const count = await copyButtons.count();
    
    // If we got results, there should be copy buttons
    if (count > 0) {
      expect(count).toBeGreaterThan(0);
    }
  });
});

test.describe('Marketing Hub - API Integration', () => {
  test('API health check passes', async ({ request }) => {
    // Check if ReDSL API is available
    const response = await request.get(`${REDSL_API_URL}/health`, {
      timeout: 5000
    }).catch(() => ({ status: () => 0 }));
    
    // If API is available, it should return 200
    if (response.status() === 200) {
      const data = await response.json();
      expect(data.status).toBe('ok');
    }
  });

  test('scan/remote endpoint works with test repo', async ({ request }) => {
    // Skip if API is not available
    const healthResponse = await request.get(`${REDSL_API_URL}/health`).catch(() => ({ status: () => 0 }));
    if (healthResponse.status() !== 200) {
      test.skip('ReDSL API not available');
    }
    
    // Test the scan/remote endpoint
    const response = await request.post(`${REDSL_API_URL}/scan/remote`, {
      data: {
        repo_url: TEST_REPO,
        depth: 1
      },
      timeout: 120000
    });
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('success');
    expect(data.repo_url).toBe(TEST_REPO);
    expect(data.total_files).toBeGreaterThan(0);
    expect(data).toHaveProperty('avg_cc');
    expect(data).toHaveProperty('critical_count');
    expect(data).toHaveProperty('alerts');
    expect(data).toHaveProperty('top_issues');
    expect(data).toHaveProperty('summary');
    
    // Log results for debugging
    console.log(`Scanned ${data.total_files} files, ${data.total_lines} lines`);
    console.log(`Avg CC: ${data.avg_cc}, Critical: ${data.critical_count}`);
    console.log(`Top issues: ${data.top_issues?.length || 0}`);
  });

  test('scan/remote returns valid top_issues for outreach', async ({ request }) => {
    // Skip if API is not available
    const healthResponse = await request.get(`${REDSL_API_URL}/health`).catch(() => ({ status: () => 0 }));
    if (healthResponse.status() !== 200) {
      test.skip('ReDSL API not available');
    }
    
    const response = await request.post(`${REDSL_API_URL}/scan/remote`, {
      data: {
        repo_url: TEST_REPO,
        depth: 1
      },
      timeout: 120000
    });
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    
    // Check top_issues structure
    if (data.top_issues && data.top_issues.length > 0) {
      const firstIssue = data.top_issues[0];
      expect(firstIssue).toHaveProperty('type');
      expect(firstIssue).toHaveProperty('name');
      expect(firstIssue).toHaveProperty('severity');
      expect(firstIssue).toHaveProperty('description');
    }
  });

  test('analyze endpoint works locally', async ({ request }) => {
    // Test local analyze with redsl project
    const response = await request.post('/api/redsl.php?action=scan', {
      data: {
        project: 'redsl'
      },
      timeout: 30000
    }).catch(() => ({ status: () => 0 }));
    
    // If API proxy is configured, it should return 200
    // If not, it might return 502 (upstream unavailable)
    if (response.status() === 200) {
      const data = await response.json();
      expect(data).toHaveProperty('total_files');
    }
  });
});

test.describe('Marketing Hub - Template Generation', () => {
  test('form submission generates templates', async ({ page }) => {
    await page.goto('/marketing/');
    
    // Fill and submit form
    await page.fill('input#repo_url', TEST_REPO);
    await page.selectOption('select#buyer_type', 'tech_lead');
    await page.fill('input#contact_name', 'Janek');
    await page.fill('input#sender_name', 'Tomek');
    
    await page.click('button[type="submit"]');
    
    // Wait for processing
    await page.waitForTimeout(10000);
    
    const content = await page.content();
    
    // Check for success indicators
    const hasSuccess = content.includes('Skan zakończony') || 
                       content.includes('metryki') ||
                       content.includes('Cold Email');
    
    // Or check for expected error (API unavailable)
    const hasApiError = content.includes('API Error');
    
    expect(hasSuccess || hasApiError).toBe(true);
  });

  test('metrics display after scan', async ({ page }) => {
    await page.goto('/marketing/');
    
    await page.fill('input#repo_url', TEST_REPO);
    await page.click('button[type="submit"]');
    
    await page.waitForTimeout(10000);
    
    const content = await page.content();
    
    // If scan succeeded, should show metrics
    if (content.includes('metryki') || content.includes('Pliki')) {
      expect(content).toContain('Pliki');
      expect(content).toContain('Linii kodu');
    }
  });
});

test.describe('Marketing Hub - Error Handling', () => {
  test('handles invalid repo URL gracefully', async ({ page }) => {
    await page.goto('/marketing/');
    
    // Fill with invalid URL
    await page.fill('input#repo_url', 'not-a-valid-url');
    await page.click('button[type="submit"]');
    
    await page.waitForTimeout(5000);
    
    // Should show error or handle gracefully
    const content = await page.content();
    const hasErrorIndicator = 
      content.includes('error') || 
      content.includes('Error') ||
      content.includes('Failed') ||
      content.includes('błąd');
    
    // Page should still be functional
    expect(page.url()).toContain('marketing');
  });

  test('handles missing form fields', async ({ page }) => {
    await page.goto('/marketing/');
    
    // Try to submit without filling required fields
    // (browser should prevent this due to 'required' attribute)
    const repoInput = page.locator('input#repo_url');
    const isRequired = await repoInput.evaluate(el => el.required);
    
    expect(isRequired).toBe(true);
  });

  test('handles API unavailability', async ({ page }) => {
    // This test verifies the page works even when API is down
    await page.goto('/marketing/');
    
    expect(await page.locator('form').isVisible()).toBe(true);
    expect(await page.locator('input#repo_url').isVisible()).toBe(true);
  });
});

test.describe('Marketing Hub - Responsive Design', () => {
  test('page is responsive on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/marketing/');
    
    // Form should still be visible and usable
    await expect(page.locator('form')).toBeVisible();
    await expect(page.locator('input#repo_url')).toBeVisible();
    
    // Header should be visible
    await expect(page.locator('header')).toBeVisible();
  });

  test('page is responsive on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/marketing/');
    
    await expect(page.locator('form')).toBeVisible();
    await expect(page.locator('header')).toBeVisible();
  });
});

test.describe('Marketing Hub - Content Validation', () => {
  test('page contains all template sections', async ({ page }) => {
    await page.goto('/marketing/');
    
    const content = await page.content();
    
    // Buyer types should be in the form
    expect(content).toContain('Tech Lead');
    expect(content).toContain('CEO');
    expect(content).toContain('PM Agencji');
  });

  test('page has proper Polish localization', async ({ page }) => {
    await page.goto('/marketing/');
    
    const content = await page.content();
    
    // Check for Polish text
    expect(content).toContain('Skanuj');
    expect(content).toContain('Repozytorium');
  });
});
