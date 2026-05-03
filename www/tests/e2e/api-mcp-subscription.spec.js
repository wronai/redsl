// @ts-check
/**
 * API contract tests for /api/redsl.php
 * Includes MCP subscription resale endpoints.
 */

const { test, expect } = require('@playwright/test');

test.describe('API Proxy - Core and MCP actions', () => {
  test('health action returns expected status contract', async ({ request }) => {
    const response = await request.get('/api/redsl.php?action=health', {
      headers: { 'X-REDSL-SECRET': process.env.REDSL_API_SECRET || 'secret' }
    });

    test.skip(response.status() === 401, 'API wymaga X-REDSL-SECRET');
    expect([200, 502]).toContain(response.status());

    const data = await response.json();
    expect(data).toBeTruthy();

    if (response.status() === 200) {
      expect(data.status).toBe('ok');
    } else {
      expect(data.status).toContain('unreachable');
    }
  });

  test('unknown action returns 400 with actions list', async ({ request }) => {
    const response = await request.get('/api/redsl.php?action=unknown_action_for_test', {
      headers: { 'X-REDSL-SECRET': process.env.REDSL_API_SECRET || 'secret' }
    });

    test.skip(response.status() === 401, 'API wymaga X-REDSL-SECRET');
    expect(response.status()).toBe(400);

    const data = await response.json();
    expect(data.error).toContain('Unknown action');
    expect(data.actions).toContain('mcp_subscription');
    expect(data.actions).toContain('mcp_health');
  });

  test('mcp_health works in not-configured mode', async ({ request }) => {
    const response = await request.get('/api/redsl.php?action=mcp_health', {
      headers: { 'X-REDSL-SECRET': process.env.REDSL_API_SECRET || 'secret' }
    });

    test.skip(response.status() === 401, 'API wymaga X-REDSL-SECRET');
    expect([200, 502]).toContain(response.status());

    const data = await response.json();
    expect(data).toBeTruthy();

    if (response.status() === 200) {
      expect(data.status).toBe('ok');
      expect(data.mcp).toBeTruthy();
      expect(typeof data.mcp.configured).toBe('boolean');
    } else {
      expect(data.status).toContain('unreachable');
    }
  });

  test('mcp_subscription validates required fields', async ({ request }) => {
    const response = await request.post('/api/redsl.php?action=mcp_subscription', {
      data: {
        client_name: 'ACME',
        plan: 'starter',
      },
      headers: { 'X-REDSL-SECRET': process.env.REDSL_API_SECRET || 'secret' }
    });

    test.skip(response.status() === 401, 'API wymaga X-REDSL-SECRET');
    expect(response.status()).toBe(400);

    const data = await response.json();
    expect(data.error).toContain('client_email');
  });

  test('mcp_subscription returns deterministic monthly pricing in dry-run', async ({ request }) => {
    const response = await request.post('/api/redsl.php?action=mcp_subscription', {
      data: {
        client_name: 'ACME Sp. z o.o.',
        client_email: 'billing@acme.test',
        repo_url: 'https://github.com/acme/platform',
        plan: 'pro',
        seats: 2,
        tickets_per_month: 3,
        mcp_margin_percent: 12.5,
      },
      headers: { 'X-REDSL-SECRET': process.env.REDSL_API_SECRET || 'secret' }
    });

    test.skip(response.status() === 401, 'API wymaga X-REDSL-SECRET');
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.status).toBe('ok');
    expect(['dry_run', 'live']).toContain(data.mode);

    const subscription = data.subscription;
    expect(subscription.billing_cycle).toBe('monthly');
    expect(subscription.plan).toBe('pro');
    expect(subscription.client.email).toBe('billing@acme.test');

    expect(subscription.pricing.subtotal_pln).toBe(1014);
    expect(subscription.pricing.mcp_fee_pln).toBe(126.75);
    expect(subscription.pricing.monthly_total_pln).toBe(1140.75);

    expect(subscription.line_items.length).toBeGreaterThanOrEqual(4);
  });
});
