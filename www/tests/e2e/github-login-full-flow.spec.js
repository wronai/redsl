// @ts-check
/**
 * E2E Tests for COMPLETE GitHub OAuth flow using MOCK GitHub
 * 
 * Requires mock-github/ endpoints + GITHUB_OAUTH_BASE=http://localhost:8080/mock-github
 * in .env so that index.php redirects to local mock instead of real github.com
 */

const { test, expect } = require('@playwright/test');

test.describe('GitHub Login - Full Flow (with Mock)', () => {
  test.beforeEach(async ({ page }) => {
    // Clear session/cookies for fresh flow
    await page.context().clearCookies();
  });

  test('complete flow: landing → github-login → consent → dashboard', async ({ page }) => {
    // Step 1: Landing page
    await page.goto('/');
    await expect(page.locator('a[href="?action=github-login"]').first()).toBeVisible();
    
    // Step 2: Click login → redirects to mock authorize page
    await page.click('a[href="?action=github-login"]');
    
    // Wait for mock authorize page
    await expect(page.locator('text=MOCK GITHUB OAUTH')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Authorize application')).toBeVisible();
    
    // Step 3: Fill consent form and approve
    await page.fill('input[name="username"]', 'playwright-user');
    await page.fill('input[name="name"]', 'Playwright Tester');
    await page.fill('input[name="email"]', 'playwright@example.com');
    await page.fill('input[name="company"]', 'Test Company');
    await page.fill('input[name="public_repos"]', '42');
    
    await page.click('button[name="approve"]');
    
    // Step 4: Redirected back through callback → /klient/
    await page.waitForURL(/\/klient\//, { timeout: 10000 });
    
    // Step 5: Verify dashboard content
    await expect(page.locator('text=@playwright-user').first()).toBeVisible();
    await expect(page.locator('h1')).toContainText(/Witaj/);
    await expect(page.locator('text=playwright@example.com').first()).toBeVisible();
    await expect(page.locator('text=42 publicznych')).toBeVisible();
    await expect(page.locator('text=Test Company')).toBeVisible();
  });
  
  test('login preserves state across redirects (CSRF protection)', async ({ page }) => {
    // Start OAuth
    await page.goto('/?action=github-login');
    
    // Mock authorize page should be loaded
    await expect(page.locator('text=MOCK GITHUB OAUTH')).toBeVisible();
    
    // Verify state parameter is in URL
    const url = page.url();
    expect(url).toMatch(/state=[a-f0-9]{24}/);
  });
  
  test('after login, user can logout and return to landing', async ({ page }) => {
    // Complete login
    await page.goto('/?action=github-login');
    await page.fill('input[name="username"]', 'logouttest');
    await page.click('button[name="approve"]');
    
    await page.waitForURL(/\/klient\//);
    
    // Verify logged in
    await expect(page.locator('text=@logouttest').first()).toBeVisible();
    
    // Click logout link
    await page.click('a[href="?action=logout"]');
    
    // Should be back on landing page
    await page.waitForURL('/');
    const title = await page.title();
    expect(title).toMatch(/REDSL/i);
  });
  
  test('accessing /klient/ without login redirects to landing', async ({ page }) => {
    await page.goto('/klient/');
    
    // Should redirect to landing with err param
    await expect(page).toHaveURL(/\?err=login_required|\/$/);
  });
  
  test('dashboard shows user profile data correctly', async ({ page }) => {
    // Login with specific data
    await page.goto('/?action=github-login');
    await page.fill('input[name="username"]', 'annakowal');
    await page.fill('input[name="name"]', 'Anna Kowalska');
    await page.fill('input[name="email"]', 'anna@firmadev.pl');
    await page.fill('input[name="company"]', 'FirmaDev Sp. z o.o.');
    await page.fill('input[name="public_repos"]', '7');
    await page.click('button[name="approve"]');
    
    await page.waitForURL(/\/klient\//);
    
    // Check all data is displayed
    const content = await page.content();
    expect(content).toContain('@annakowal');
    expect(content).toContain('Anna Kowalska');
    expect(content).toContain('anna@firmadev.pl');
    expect(content).toContain('FirmaDev');
    expect(content).toContain('7 publicznych');
    
    // Check dashboard structure
    await expect(page.locator('h1')).toContainText(/Witaj/);
    await expect(page.locator('text=Twój profil GitHub')).toBeVisible();
    await expect(page.locator('text=Co dalej?')).toBeVisible();
  });
  
  test('dashboard shows all 6 onboarding steps', async ({ page }) => {
    await page.goto('/?action=github-login');
    await page.fill('input[name="username"]', 'steptest');
    await page.click('button[name="approve"]');
    await page.waitForURL(/\/klient\//);
    
    // Count steps in the "Co dalej?" list
    const steps = page.locator('.steps li');
    await expect(steps).toHaveCount(6);
    
    // First step should be marked as done
    const firstStep = steps.first();
    await expect(firstStep).toHaveClass(/done/);
    
    // Verify step texts
    await expect(steps.nth(0)).toContainText('Zalogowałeś się');
    await expect(steps.nth(1)).toContainText('skan');
    await expect(steps.nth(2)).toContainText('raport');
    await expect(steps.nth(5)).toContainText('fakturę');
  });
  
  test('session persists across page reloads', async ({ page }) => {
    // Login
    await page.goto('/?action=github-login');
    await page.fill('input[name="username"]', 'persistuser');
    await page.click('button[name="approve"]');
    await page.waitForURL(/\/klient\//);
    
    // Reload dashboard
    await page.reload();
    
    // Should still be logged in
    await expect(page.locator('text=@persistuser').first()).toBeVisible();
  });
  
  test('mock authorize form has all required fields', async ({ page }) => {
    await page.goto('/?action=github-login');
    
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="name"]')).toBeVisible();
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="company"]')).toBeVisible();
    await expect(page.locator('input[name="public_repos"]')).toBeVisible();
    await expect(page.locator('button[name="approve"]')).toBeVisible();
    
    // Warning about mock mode
    await expect(page.locator('text=MOCK GITHUB OAUTH')).toBeVisible();
  });
});

test.describe('GitHub Login - Dashboard Features', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    // Login as default user
    await page.goto('/?action=github-login');
    await page.fill('input[name="username"]', 'testclient');
    await page.click('button[name="approve"]');
    await page.waitForURL(/\/klient\//);
  });
  
  test('dashboard has navigation links', async ({ page }) => {
    await expect(page.locator('a[href="/"]').first()).toBeVisible();
    await expect(page.locator('a[href="?action=logout"]').first()).toBeVisible();
  });
  
  test('dashboard has status cards (scans, tickets, PRs, invoices)', async ({ page }) => {
    const statLabels = ['Skany', 'Tickety', 'PR-y', 'Zafakturowane'];
    for (const label of statLabels) {
      await expect(page.locator('.stat-label').filter({ hasText: label })).toBeVisible();
    }
  });
  
  test('profile card shows GitHub profile link', async ({ page }) => {
    const githubLink = page.locator('a[href*="github.com/testclient"]');
    await expect(githubLink).toBeVisible();
    await expect(githubLink).toHaveAttribute('target', '_blank');
    await expect(githubLink).toHaveAttribute('rel', /noopener/);
  });
  
  test('dashboard is responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    
    // All cards should still be visible
    await expect(page.locator('.card').first()).toBeVisible();
    await expect(page.locator('text=Twój profil GitHub')).toBeVisible();
  });
});
