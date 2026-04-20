<?php
/**
 * PHPUnit — I18n singleton & regression tests (sesja 2026-04-20)
 *
 * Pokrywa:
 *  - singleton: getInstance() zwraca tę samą instancję
 *  - t() zwraca string (nie tablicę, nie obiekt)
 *  - th() zwraca to samo co t() — surowe HTML
 *  - formatPrice() zwraca string z liczbą
 *  - getPricing() zwraca string
 *  - $i18n z require to tablica (nie obiekt) — bug z $i18n->formatPrice()
 *  - klucze z HTML nie są escapowane przez t() (raw output)
 *  - ticket_yours = 10x ticket_found
 *  - made_note istnieje w JSON (zastąpił bundle_*)
 *  - $lang = $i18n['lang']() zwraca string (nie Closure)
 */

use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/../lib/i18n.php';

class I18nTest extends TestCase
{
    private array $i18n;

    private static function makeI18nArray(): array
    {
        $i18n = I18n::getInstance();
        return [
            'lang'             => fn(): string => $i18n->getLang(),
            'available'        => fn(): array  => $i18n->getAvailable(),
            't'                => fn(string $key, array $p = []): string => $i18n->t($key, $p),
            'get'              => fn(string $key): mixed => $i18n->get($key),
            'setLang'          => function(string $lang) use ($i18n): void { $i18n->setLang($lang); },
            'th'               => fn(string $key, array $p = []): string => $i18n->th($key, $p),
            'getLangUrls'      => fn(): array  => $i18n->getLangUrls(),
            'getLangName'      => fn(string $l): string => $i18n->getLangName($l),
            'formatPrice'      => fn(float $usd, bool $sym = true): string => $i18n->formatPrice($usd, $sym),
            'getCurrencyConfig'=> fn(): array  => $i18n->getCurrencyConfig(),
            'getPricing'       => fn(string $k, bool $sym = true): string => $i18n->getPricing($k, $sym),
        ];
    }

    protected function setUp(): void
    {
        // Reset superglobals to avoid cross-test contamination
        $_GET = [];
        $_COOKIE = [];
        $_SERVER['HTTP_ACCEPT_LANGUAGE'] = '';
        I18n::resetInstance();
        $this->i18n = self::makeI18nArray();
    }

    protected function tearDown(): void
    {
        I18n::resetInstance();
    }

    // ── Singleton ────────────────────────────────────────────────────────────

    public function testGetInstanceReturnsSameObject(): void
    {
        $a = I18n::getInstance();
        $b = I18n::getInstance();
        $this->assertSame($a, $b, 'getInstance() musi zwracać tę samą instancję (singleton)');
    }

    public function testResetInstanceAllowsFreshInstance(): void
    {
        $a = I18n::getInstance();
        I18n::resetInstance();
        $b = I18n::getInstance();
        $this->assertNotSame($a, $b, 'Po resetInstance() powinna powstać nowa instancja');
    }

    // ── require zwraca tablicę, nie obiekt ───────────────────────────────────

    public function testRequireReturnsArray(): void
    {
        $this->assertIsArray($this->i18n, '$i18n z require musi być tablicą (nie obiektem)');
    }

    public function testArrayHasRequiredKeys(): void
    {
        $required = ['t', 'th', 'lang', 'getLangUrls', 'getLangName', 'formatPrice', 'getPricing', 'getCurrencyConfig'];
        foreach ($required as $key) {
            $this->assertArrayHasKey($key, $this->i18n, "Brakuje klucza '$key' w tablicy i18n");
        }
    }

    // ── $lang = $i18n['lang']() — string, nie Closure ───────────────────────

    public function testLangClosureReturnsString(): void
    {
        $lang = ($this->i18n['lang'])();
        $this->assertIsString($lang, '$lang musi być stringiem (nie Closure) — wywołaj $i18n[\'lang\']()');
        $this->assertMatchesRegularExpression('/^(pl|en|de)$/', $lang, '$lang musi być pl|en|de');
    }

    // ── t() i th() ───────────────────────────────────────────────────────────

    public function testTReturnsString(): void
    {
        $t = $this->i18n['t'];
        $result = $t('meta.title');
        $this->assertIsString($result, 't() musi zwracać string');
        $this->assertNotEmpty($result);
    }

    public function testTReturnsFallbackKeyWhenMissing(): void
    {
        $t = $this->i18n['t'];
        $result = $t('nonexistent.key.xyz');
        $this->assertSame('nonexistent.key.xyz', $result, 'Brakujący klucz powinien zwrócić sam klucz');
    }

    public function testThReturnsSameAsT(): void
    {
        $t = $this->i18n['t'];
        $th = $this->i18n['th'];
        $key = 'pricing.found_title';
        $this->assertSame($t($key), $th($key), 'th() i t() muszą zwracać ten sam string');
    }

    public function testThDoesNotEscapeHtml(): void
    {
        $th = $this->i18n['th'];
        // hero.headline zawiera <br><em> — th() NIE może ich escapować
        $result = $th('hero.headline');
        $this->assertStringNotContainsString('&lt;', $result, 'th() nie może escapować tagów HTML');
        $this->assertStringNotContainsString('&gt;', $result, 'th() nie może escapować tagów HTML');
    }

    // ── Klucze z HTML w tłumaczeniach ────────────────────────────────────────

    public function testHeroHeadlineContainsHtmlTags(): void
    {
        $t = $this->i18n['t'];
        $result = $t('hero.headline');
        // Tłumaczenia celowo zawierają <br> i <em>
        $this->assertMatchesRegularExpression('/<(br|em|strong|span)/', $result,
            'hero.headline powinien zawierać tagi HTML (br/em/strong/span)');
    }

    public function testPainTitleContainsBr(): void
    {
        $t = $this->i18n['t'];
        $result = $t('pain.title');
        $this->assertStringContainsString('<br>', $result, 'pain.title powinien zawierać <br>');
    }

    // ── Cennik: ticket_yours = 10x ticket_found ──────────────────────────────

    public function testTicketYoursIsTenTimesTicketFound(): void
    {
        $i18n = I18n::getInstance();
        $found = $i18n->getBasePrice('ticket_found');
        $yours = $i18n->getBasePrice('ticket_yours');
        $this->assertEqualsWithDelta($found * 10, $yours, 0.01,
            'ticket_yours powinien być 10x ticket_found');
    }

    // ── formatPrice() ────────────────────────────────────────────────────────

    public function testFormatPriceReturnsString(): void
    {
        $formatPrice = $this->i18n['formatPrice'];
        $result = $formatPrice(10.0);
        $this->assertIsString($result, 'formatPrice() musi zwracać string');
        $this->assertNotEmpty($result);
    }

    public function testFormatPriceContainsNumber(): void
    {
        $formatPrice = $this->i18n['formatPrice'];
        $result = $formatPrice(10.0);
        $this->assertMatchesRegularExpression('/\d/', $result, 'formatPrice() musi zawierać liczbę');
    }

    public function testFormatPriceAsClosureNotMethod(): void
    {
        // Regresja: proposals.php używało $i18n->formatPrice() zamiast $formatPrice()
        $this->assertIsCallable($this->i18n['formatPrice'],
            'formatPrice z tablicy i18n musi być callable (closure)');
    }

    // ── getPricing() ─────────────────────────────────────────────────────────

    public function testGetPricingTicketFound(): void
    {
        $getPricing = $this->i18n['getPricing'];
        $result = $getPricing('ticket_found');
        $this->assertIsString($result);
        $this->assertMatchesRegularExpression('/\d/', $result);
    }

    public function testGetPricingTicketYours(): void
    {
        $getPricing = $this->i18n['getPricing'];
        $result = $getPricing('ticket_yours');
        $this->assertIsString($result);
        $this->assertMatchesRegularExpression('/\d/', $result);
    }

    // ── JSON: made_note istnieje, bundle_* usunięte ───────────────────────────

    public function testMadeNoteExistsInJson(): void
    {
        $t = $this->i18n['t'];
        $result = $t('pricing.made_note');
        $this->assertNotSame('pricing.made_note', $result,
            'pricing.made_note powinien istnieć w tłumaczeniach');
        $this->assertNotEmpty($result);
    }

    public function testMadeNoteContains10x(): void
    {
        $t = $this->i18n['t'];
        $result = $t('pricing.made_note');
        $this->assertMatchesRegularExpression('/10[×x]/u', $result,
            'pricing.made_note powinien zawierać "10×" lub "10x"');
    }

    public function testBundleTitleRemovedFromJson(): void
    {
        $t = $this->i18n['t'];
        // bundle_title zostało usunięte — powinno zwrócić fallback key
        $result = $t('pricing.bundle_title');
        $this->assertSame('pricing.bundle_title', $result,
            'pricing.bundle_title powinno być usunięte z JSON (zwraca fallback key)');
    }

    // ── Wielojęzyczność ───────────────────────────────────────────────────────

    public function testAllLanguageFilesLoadable(): void
    {
        $langs = ['pl', 'en', 'de'];
        foreach ($langs as $lang) {
            $file = __DIR__ . "/../i18n/{$lang}.json";
            $this->assertFileExists($file, "Brak pliku i18n/{$lang}.json");
            $data = json_decode(file_get_contents($file), true);
            $this->assertIsArray($data, "{$lang}.json musi być poprawnym JSON");
            $this->assertArrayHasKey('pricing', $data, "{$lang}.json musi zawierać sekcję pricing");
            $this->assertArrayHasKey('made_note', $data['pricing'],
                "{$lang}.json: pricing.made_note musi istnieć");
        }
    }
}
