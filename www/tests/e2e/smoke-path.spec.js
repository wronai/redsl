// @ts-check
/**
 * Smoke Path Tests - Minimal E2E for Path A Deployment
 * Focused on API-based checks for reliability (no browser page loads)
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8080';

// API-based tests for maximum reliability
test.describe('Smoke Path - Landing Page', () => {
  test('landing page returns 200 with valid HTML', async ({ request }) => {
    const response = await request.get('/');
    expect(response.status()).toBe(200);
    
    const content = await response.text();
    expect(content).toContain('<!DOCTYPE html>');
    expect(content).toContain('</html>');
    expect(content).toContain('ReDSL');
  });

  test('landing page has no PHP errors', async ({ request }) => {
    const response = await request.get('/');
    const content = await response.text();
    expect(content).not.toContain('Fatal error');
    expect(content).not.toContain('Parse error');
    expect(content).not.toContain('Warning:');
  });
});

test.describe('Smoke Path - Static Pages', () => {
  test('config-editor page returns 200 with valid HTML', async ({ request }) => {
    const response = await request.get('/config-editor.php');
    expect(response.status()).toBe(200);
    
    const content = await response.text();
    expect(content).toContain('<!DOCTYPE html>');
    expect(content).not.toContain('Fatal error');
    expect(content).toContain('Config Editor');
  });

  test('propozycje page returns 200 with valid HTML', async ({ request }) => {
    const response = await request.get('/propozycje.php');
    expect(response.status()).toBe(200);
    
    const content = await response.text();
    expect(content).toContain('<!DOCTYPE html>');
    expect(content).not.toContain('Fatal error');
    expect(content).toContain('Propozycje');
  });

  test('NDA form page returns 200 with valid HTML', async ({ request }) => {
    const response = await request.get('/nda-form.php');
    expect(response.status()).toBe(200);
    
    const content = await response.text();
    expect(content).toContain('<!DOCTYPE html>');
    expect(content).not.toContain('Fatal error');
    expect(content).toContain('NDA');
  });
});

test.describe('Smoke Path - API Health', () => {
  test('root endpoint returns 200', async ({ request }) => {
    const response = await request.get('/');
    expect(response.status()).toBe(200);
  });

  test('config-editor returns valid response', async ({ request }) => {
    const response = await request.get('/config-editor.php');
    expect(response.status()).toBe(200);
    
    const content = await response.text();
    expect(content).not.toContain('Fatal error');
  });

  test('propozycje returns valid response', async ({ request }) => {
    const response = await request.get('/propozycje.php');
    expect(response.status()).toBe(200);
    
    const content = await response.text();
    expect(content).not.toContain('Fatal error');
  });
});

test.describe('Smoke Path - Content Validation', () => {
  test('landing page has key content', async ({ request }) => {
    const response = await request.get('/');
    const content = await response.text();
    expect(content).toContain('ReDSL');
    expect(content).toContain('<h1');
  });

  test('config-editor has expected elements', async ({ request }) => {
    const response = await request.get('/config-editor.php');
    const content = await response.text();
    const hasNoConfig = content.includes('No configuration') || content.includes('Create Default Config');
    const hasEditor = content.includes('config_yaml') || content.includes('Save Changes');
    expect(hasNoConfig || hasEditor).toBe(true);
  });

  test('propozycje has expected structure', async ({ request }) => {
    const response = await request.get('/propozycje.php');
    const content = await response.text();
    expect(content).toContain('Propozycje');
    expect(content).toContain('proposal-item');
  });
});

test.describe('Smoke Path - Admin Pages', () => {
  test('admin pages load without errors', async ({ request }) => {
    const pages = ['/admin/index.php', '/admin/clients.php', '/admin/projects.php'];
    
    for (const page of pages) {
      const response = await request.get(page);
      const content = await response.text();
      expect(content).not.toContain('Fatal error');
      expect(content).not.toContain('Parse error');
    }
  });
});

test.describe('Smoke Path - Error Handling', () => {
  test('404 page returns not found', async ({ request }) => {
    const response = await request.get('/nonexistent-page-12345.php');
    expect(response.status()).toBeGreaterThanOrEqual(400);
  });

  test('invalid PHP page returns error', async ({ request }) => {
    const response = await request.get('/this-does-not-exist.php');
    expect(response.status()).toBeGreaterThanOrEqual(400);
  });
});
