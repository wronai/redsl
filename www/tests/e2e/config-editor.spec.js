// @ts-check
/**
 * E2E Tests for Config Editor
 * @see config-editor.php
 */

const { test, expect } = require('@playwright/test');

test.describe('Config Editor', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/config-editor.php');
  });

  test('should display config editor page', async ({ page }) => {
    await expect(page).toHaveTitle(/ReDSL Config Editor/);
    await expect(page.locator('h1')).toContainText('ReDSL Config Editor');
  });

  test('should show "No configuration" when config does not exist', async ({ page }) => {
    await expect(page.locator('.alert')).toContainText('No configuration found');
    await expect(page.locator('button:has-text("Create Default Config")')).toBeVisible();
  });

  test('should create default config on button click', async ({ page }) => {
    // Click create default config
    await page.click('button:has-text("Create Default Config")');
    
    // Should show editor with default config
    await expect(page.locator('textarea[name="config_yaml"]')).toBeVisible();
    await expect(page.locator('.badge')).toContainText('Config Found');
  });

  test('should display risk levels in sidebar', async ({ page }) => {
    // First create a config
    await page.click('button:has-text("Create Default Config")');
    
    // Check risk levels are displayed
    await expect(page.locator('.risk-list')).toContainText('Low Risk');
    await expect(page.locator('.risk-list')).toContainText('High Risk');
    await expect(page.locator('.risk-list')).toContainText('Critical');
  });

  test('should redact secrets in display', async ({ page }) => {
    // Create default config
    await page.click('button:has-text("Create Default Config")');
    
    // Check that secrets are shown with refs, not values
    const textarea = page.locator('textarea[name="config_yaml"]');
    await expect(textarea).toContainText('env:OPENROUTER_API_KEY');
    await expect(textarea).not.toContainText('sk-'); // Should not show real API keys
  });

  test('should allow editing and saving config', async ({ page }) => {
    // Create default config
    await page.click('button:has-text("Create Default Config")');
    
    // Edit the config
    const textarea = page.locator('textarea[name="config_yaml"]');
    await textarea.fill(`apiVersion: redsl.config/v1
kind: RedslConfig
metadata:
  name: edited-project
  version: 2
profile: development`);
    
    // Save
    await page.click('button:has-text("Save Changes")');
    
    // Should show success message
    await expect(page.locator('.alert')).toContainText('saved successfully');
  });

  test('should show common paths in sidebar', async ({ page }) => {
    // Create default config
    await page.click('button:has-text("Create Default Config")');
    
    // Check common paths
    await expect(page.locator('.path-list')).toContainText('spec.llm_policy.mode');
    await expect(page.locator('.path-list')).toContainText('spec.llm_policy.max_age_days');
  });

  test('should validate YAML syntax on save', async ({ page }) => {
    // Create default config
    await page.click('button:has-text("Create Default Config")');
    
    // Enter invalid YAML
    const textarea = page.locator('textarea[name="config_yaml"]');
    await textarea.fill('invalid: yaml: syntax: [');
    
    // Save
    await page.click('button:has-text("Save Changes")');
    
    // Should show error
    await expect(page.locator('.alert')).toContainText('Invalid YAML');
  });

  test('should display config info in sidebar', async ({ page }) => {
    // Create default config
    await page.click('button:has-text("Create Default Config")');
    
    // Check config info
    await expect(page.locator('.panel')).toContainText('Version');
    await expect(page.locator('.panel')).toContainText('Profile');
    await expect(page.locator('.panel')).toContainText('Secrets');
  });
});

test.describe('Config Editor - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('should be responsive on mobile', async ({ page }) => {
    await page.goto('/config-editor.php');
    
    // Create config
    await page.click('button:has-text("Create Default Config")');
    
    // Editor should be visible and usable
    await expect(page.locator('textarea[name="config_yaml"]')).toBeVisible();
    
    // Sidebar should be below editor on mobile
    const editorPane = page.locator('.editor-pane');
    const sidebar = page.locator('.sidebar');
    
    await expect(editorPane).toBeVisible();
    await expect(sidebar).toBeVisible();
  });
});
