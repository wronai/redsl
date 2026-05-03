// @ts-check
/**
 * Client commercial GUI flow:
 * - wejście do systemu
 * - test repo
 * - rejestracja (NDA)
 * - wybór ticketów
 * - symulacja płatności subskrypcyjnej (MCP API)
 */

const { test, expect } = require('@playwright/test');

function assertNoPhpErrors(content) {
  expect(content).not.toContain('Fatal error');
  expect(content).not.toContain('Parse error');
  expect(content).not.toContain('Warning:');
}

test.describe('Client Journey - GUI Commercial Flow', () => {
  test('happy path: enter -> test repo -> register -> choose tickets -> monthly quote', async ({ page, request }) => {
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    await page.goto('/marketing/');
    await expect(page.locator('input#repo_url')).toBeVisible();
    await page.fill('input#repo_url', 'https://github.com/TauricResearch/TradingAgents');
    await page.selectOption('select#buyer_type', 'tech_lead');
    await page.fill('input#contact_name', 'Jan Klient');
    await page.fill('input#sender_name', 'Anna Sales');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(4000);
    assertNoPhpErrors(await page.content());

    await page.goto('/nda-form.php?lang=pl');
    await expect(page.locator('input[name="nip"]')).toBeVisible();
    await page.fill('input[name="nip"]', '1234567890');
    await page.click('button[type="submit"]');

    await expect(page.locator('input[name="nazwa"]')).toBeVisible();
    await page.fill('input[name="osoba"]', 'Jan Kowalski');
    await page.fill('input[name="stanowisko"]', 'CTO');
    await page.fill('input[name="email"]', 'jan.kowalski@example.com');
    await page.fill('input[name="telefon"]', '+48 555 111 222');
    await page.click('button[type="submit"]');

    await expect(page.locator('.nda-preview')).toBeVisible();
    await expect(page.locator('text=Klient ID')).toBeVisible();

    await page.goto('/proposals?lang=pl');
    await expect(page.locator('input[name="selection"][value="custom"]')).toBeVisible();
    await page.check('input[name="selection"][value="custom"]');
    await page.fill('input[name="custom_input"]', '1, 3, 5');
    await page.click('button.btn-submit');

    const proposalAlert = page.locator('.alert').first();
    await expect(proposalAlert).toBeVisible();
    await expect(proposalAlert).toContainText(/3/);

    const paymentResponse = await request.post('/api/redsl.php?action=mcp_subscription', {
      data: {
        client_name: 'Jan Kowalski',
        client_email: 'jan.kowalski@example.com',
        repo_url: 'https://github.com/example/acme-repo',
        plan: 'pro',
        seats: 2,
        tickets_per_month: 3,
      },
    });

    test.skip(paymentResponse.status() === 401, 'API wymaga X-REDSL-SECRET');
    expect(paymentResponse.status()).toBe(200);

    const paymentJson = await paymentResponse.json();
    expect(paymentJson.status).toBe('ok');
    expect(['dry_run', 'live']).toContain(paymentJson.mode);
    expect(paymentJson.subscription.billing_cycle).toBe('monthly');
    expect(paymentJson.subscription.pricing.monthly_total_pln).toBeGreaterThan(0);
  });
});

test.describe('Client Journey - Alternative GUI Scenarios', () => {
  test('nda rejects invalid NIP and keeps form usable', async ({ page }) => {
    await page.goto('/nda-form.php?lang=pl');
    await page.fill('input[name="nip"]', '123');
    await page.click('button[type="submit"]');

    await expect(page.locator('.alert.alert-info')).toContainText('NIP musi mieć 10 cyfr');
    await expect(page.locator('input[name="nip"]')).toBeVisible();
  });

  test('ticket selection works for under_15 option', async ({ page }) => {
    await page.goto('/proposals?lang=pl');
    await page.check('input[name="selection"][value="under_15"]');
    await page.click('button.btn-submit');

    const alert = page.locator('.alert').first();
    await expect(alert).toBeVisible();
    await expect(alert).toContainText(/8/);
  });

  test('unauthorized client panel access redirects safely', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/klient/');

    await expect(page).toHaveURL(/\/?(\?err=login_required)?$/);
    assertNoPhpErrors(await page.content());
  });
});
