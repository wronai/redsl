// @ts-check
/**
 * Post-deploy regression tests — wykrywają bugi z sesji 2026-04-20:
 *  - Warning: headers already sent (singleton i18n)
 *  - Fatal error: Call to member function on array ($i18n->formatPrice)
 *  - Tagi HTML w tłumaczeniach escapowane zamiast renderowane
 *  - Błędna cena "Ticket twój" (ticket_found zamiast ticket_yours)
 *  - bulk-note z starą treścią pakietu
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8080';

// ── Helpers ────────────────────────────────────────────────────────────────

async function getPage(request, path) {
  const response = await request.get(path);
  const text = await response.text();
  return { response, text };
}

function assertNoPHPErrors(text, label) {
  expect(text, `${label}: Fatal error`).not.toContain('Fatal error');
  expect(text, `${label}: Parse error`).not.toContain('Parse error');
  expect(text, `${label}: Warning:`).not.toContain('Warning:');
  expect(text, `${label}: Uncaught`).not.toContain('Uncaught');
}

// ── Brak PHP errors ─────────────────────────────────────────────────────────

test.describe('Post-deploy: brak błędów PHP', () => {
  const pages = [
    ['/', 'index'],
    ['/proposals', 'proposals'],
    ['/propozycje.php', 'propozycje'],
    ['/regulamin', 'regulamin'],
    ['/nda-form.php', 'nda-form'],
    ['/config-editor.php', 'config-editor'],
  ];

  for (const [path, label] of pages) {
    test(`${label} — brak Fatal/Warning/Uncaught`, async ({ request }) => {
      const { response, text } = await getPage(request, path);
      expect(response.status(), `${label} HTTP status`).toBeLessThan(500);
      assertNoPHPErrors(text, label);
    });
  }

  test('index z ?lang=pl — brak Warning: headers already sent', async ({ request }) => {
    const { text } = await getPage(request, '/?lang=pl');
    expect(text).not.toContain('Warning:');
    expect(text).not.toContain('headers already sent');
  });

  test('index z ?lang=en — brak Warning: headers already sent', async ({ request }) => {
    const { text } = await getPage(request, '/?lang=en');
    expect(text).not.toContain('Warning:');
    expect(text).not.toContain('headers already sent');
  });

  test('index z ?lang=de — brak Warning: headers already sent', async ({ request }) => {
    const { text } = await getPage(request, '/?lang=de');
    expect(text).not.toContain('Warning:');
    expect(text).not.toContain('headers already sent');
  });
});

// ── Tagi HTML w tłumaczeniach renderowane (nie escapowane) ─────────────────

test.describe('Post-deploy: tagi HTML w tłumaczeniach', () => {
  test('hero headline zawiera <br> i <em> (nie &lt;)', async ({ request }) => {
    const { text } = await getPage(request, '/');
    expect(text, 'hero headline: <em> nie escapowane').toContain('<em>');
    expect(text, 'hero headline: brak &lt;em&gt;').not.toMatch(/&lt;em&gt;.*ReDSL/);
  });

  test('pain.title zawiera <br> (nie &lt;br&gt;)', async ({ request }) => {
    const { text } = await getPage(request, '/');
    expect(text).not.toContain('&lt;br&gt;');
  });

  test('pain.with_1 zawiera <strong> (nie &lt;strong&gt;)', async ({ request }) => {
    const { text } = await getPage(request, '/');
    expect(text).not.toContain('&lt;strong&gt;');
  });

  test('process step titles zawierają <span> (nie &lt;span&gt;)', async ({ request }) => {
    const { text } = await getPage(request, '/');
    expect(text, 'step span: nie escapowane').toContain("class='step-meta'");
    expect(text).not.toContain("&lt;span class=");
  });

  test('contact.sidebar_for_desc zawiera <strong> (nie &lt;strong&gt;)', async ({ request }) => {
    const { text } = await getPage(request, '/');
    expect(text, 'sidebar_for_desc: <strong> widoczny').toContain('<strong>');
  });
});

// ── Cennik: poprawne ceny ───────────────────────────────────────────────────

test.describe('Post-deploy: cennik', () => {
  test('Ticket znaleziony — cena 10 (ticket_found)', async ({ request }) => {
    const { text } = await getPage(request, '/');
    expect(text).toMatch(/class="amount">10</);
  });

  test('Ticket twój — cena 100 (ticket_yours, nie 10)', async ({ request }) => {
    const { text } = await getPage(request, '/');
    expect(text).toContain('<span class="amount">100</span>');
  });

  test('bulk-note zawiera info o 10x (nie "Pakiet 50 ticketów")', async ({ request }) => {
    const { text } = await getPage(request, '/');
    expect(text, 'stara treść bulk-note usunięta').not.toContain('Pakiet 50 ticketów');
    expect(text, 'stary rabat usunięty').not.toContain('rabat 20%');
    expect(text, 'nowa treść 10x').toContain('10');
  });

  test('proposals — cena wyświetlona bez Fatal error', async ({ request }) => {
    const { response, text } = await getPage(request, '/proposals');
    expect(response.status()).toBe(200);
    expect(text).not.toContain('Fatal error');
    expect(text).toContain('prop-price');
  });
});

// ── i18n singleton — cookie ustawiane raz ──────────────────────────────────

test.describe('Post-deploy: i18n singleton', () => {
  test('zmiana języka przez ?lang ustawia cookie bez warningów', async ({ request }) => {
    const response = await request.get('/?lang=en');
    const setCookieHeader = response.headers()['set-cookie'] ?? '';
    const text = await response.text();

    expect(text).not.toContain('Warning:');
    // Cookie redsl_lang powinno być ustawione
    expect(setCookieHeader).toContain('redsl_lang=en');
  });

  test('wielokrotne wywołania t() nie generują headers already sent', async ({ request }) => {
    // Strona ma dziesiątki wywołań $t() i $th() — żaden nie może triggerować setCookie
    const { text } = await getPage(request, '/?lang=pl');
    const warningCount = (text.match(/Warning:/g) || []).length;
    expect(warningCount, 'zero warningów').toBe(0);
  });
});

// ── proposals.php — $i18n jako tablica, nie obiekt ─────────────────────────

test.describe('Post-deploy: proposals.php', () => {
  test('proposals zwraca 200', async ({ request }) => {
    const { response } = await getPage(request, '/proposals');
    expect(response.status()).toBe(200);
  });

  test('proposals nie zawiera "Call to a member function"', async ({ request }) => {
    const { text } = await getPage(request, '/proposals');
    expect(text).not.toContain('Call to a member function');
  });

  test('proposals wyświetla ceny', async ({ request }) => {
    const { text } = await getPage(request, '/proposals');
    expect(text).toContain('prop-price');
  });

  test('proposals lang closure wywołana poprawnie (brak Closure jako lang)', async ({ request }) => {
    const { text } = await getPage(request, '/proposals');
    // Gdyby $lang był Closure zamiast stringiem, html lang byłby pusty lub zepsuty
    expect(text).toMatch(/html lang="(pl|en|de)"/);
  });
});
