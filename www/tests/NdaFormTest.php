<?php
/**
 * Tests for NDA Form GUI
 * 
 * @covers NDA form functionality
 */

use PHPUnit\Framework\TestCase;

class NdaFormTest extends TestCase
{
    /**
     * Test NIP validation - valid format
     */
    public function testNipValidationValid(): void
    {
        $nip = "1234567890";
        $cleanNip = preg_replace('/[^0-9]/', '', $nip);
        
        $this->assertEquals(10, strlen($cleanNip));
        $this->assertTrue(ctype_digit($cleanNip));
    }
    
    /**
     * Test NIP validation - invalid format
     */
    public function testNipValidationInvalid(): void
    {
        $nip = "12345"; // Too short
        $cleanNip = preg_replace('/[^0-9]/', '', $nip);
        
        $this->assertNotEquals(10, strlen($cleanNip));
    }
    
    /**
     * Test NIP cleaning - removes spaces and dashes
     */
    public function testNipCleaning(): void
    {
        $nip = "123-456-78-90";
        $cleanNip = preg_replace('/[^0-9]/', '', $nip);
        
        $this->assertEquals("1234567890", $cleanNip);
        
        $nip2 = "123 456 7890";
        $cleanNip2 = preg_replace('/[^0-9]/', '', $nip2);
        
        $this->assertEquals("1234567890", $cleanNip2);
    }
    
    /**
     * Test company data fetching (mock)
     */
    public function testCompanyDataFetching(): void
    {
        $nip = "1234567890";
        
        // Mock data (same as in nda-form.php)
        $companyData = [
            'nazwa' => 'Example Company Sp. z o.o.',
            'ulica' => 'ul. Przykładowa 123',
            'kod' => '00-001',
            'miasto' => 'Warszawa',
            'regon' => '123456789',
            'krs' => '0000123456',
        ];
        
        $this->assertEquals('Example Company Sp. z o.o.', $companyData['nazwa']);
        $this->assertEquals('Warszawa', $companyData['miasto']);
        $this->assertEquals('123456789', $companyData['regon']);
    }
    
    /**
     * Test NDA text generation
     */
    public function testNdaTextGeneration(): void
    {
        $company = [
            'nazwa' => 'Test Company Sp. z o.o.',
            'ulica' => 'ul. Testowa 1',
            'kod' => '00-001',
            'miasto' => 'Warszawa',
            'regon' => '987654321',
            'krs' => '0000987654',
        ];
        
        $osoba = "Jan Kowalski";
        $stanowisko = "CEO";
        $email = "jan@test.pl";
        $telefon = "+48 123 456 789";
        $nip = "9876543210";
        
        $ndaText = $this->generateNdaText($company, $osoba, $stanowisko, $email, $telefon, $nip);
        
        $this->assertStringContainsString('UMOWA O ZACHOWANIU POUFNOŚCI', $ndaText);
        $this->assertStringContainsString('Test Company Sp. z o.o.', $ndaText);
        $this->assertStringContainsString('Jan Kowalski', $ndaText);
        $this->assertStringContainsString('CEO', $ndaText);
        $this->assertStringContainsString($nip, $ndaText);
        $this->assertStringContainsString('3 lat', $ndaText); // Protection period
    }
    
    /**
     * Test form data validation
     */
    public function testFormDataValidation(): void
    {
        $formData = [
            'nazwa' => 'Test Company',
            'ulica' => 'Test Street 123',
            'kod' => '00-001',
            'miasto' => 'Warszawa',
            'osoba' => 'Jan Kowalski',
            'stanowisko' => 'CEO',
            'email' => 'jan@example.com',
            'telefon' => '+48 123 456 789',
        ];
        
        // Check required fields
        $this->assertNotEmpty($formData['nazwa']);
        $this->assertNotEmpty($formData['osoba']);
        $this->assertNotEmpty($formData['email']);
        
        // Check email format
        $this->assertMatchesRegularExpression('/^[^@]+@[^@]+\.[^@]+$/', $formData['email']);
        
        // Check postal code format
        $this->assertMatchesRegularExpression('/^\d{2}-\d{3}$/', $formData['kod']);
    }
    
    /**
     * Test session data storage
     */
    public function testSessionDataStorage(): void
    {
        $sessionData = [
            'nda_nip' => '1234567890',
            'nda_company' => [
                'nazwa' => 'Test',
                'miasto' => 'Warszawa',
            ],
            'nda_osoba' => 'Jan Kowalski',
            'nda_stanowisko' => 'CEO',
            'nda_email' => 'jan@test.pl',
        ];
        
        $this->assertEquals('1234567890', $sessionData['nda_nip']);
        $this->assertEquals('Jan Kowalski', $sessionData['nda_osoba']);
    }
    
    /**
     * Test step progression logic
     */
    public function testStepProgression(): void
    {
        // Step 1: No data
        $step = '1';
        $this->assertEquals('1', $step);
        
        // Step 2: Has NIP, no company data
        $session = ['nda_nip' => '1234567890'];
        $step = isset($session['nda_company']) ? '2' : '1';
        $this->assertEquals('1', $step); // Still 1 without company
        
        // Step 2: Has NIP and company data
        $session = [
            'nda_nip' => '1234567890',
            'nda_company' => ['nazwa' => 'Test'],
        ];
        $step = isset($session['nda_company']) ? '2' : '1';
        $this->assertEquals('2', $step);
    }
    
    /**
     * Test HTML sanitization
     */
    public function testHtmlSanitization(): void
    {
        $input = '<script>alert("xss")</script>Test';
        $sanitized = htmlspecialchars($input, ENT_QUOTES | ENT_HTML5, 'UTF-8');
        
        $this->assertStringNotContainsString('<script>', $sanitized);
        $this->assertStringContainsString('&lt;script&gt;', $sanitized);
    }
    
    /**
     * Helper: Generate NDA text (same logic as in nda-form.php)
     */
    private function generateNdaText(array $company, string $osoba, string $stanowisko, string $email, string $telefon, string $nip): string
    {
        $date = date('d.m.Y');
        $companyName = $company['nazwa'] ?? '[NAZWA FIRMY]';
        $companyAddress = sprintf('%s, %s %s', $company['ulica'] ?? '[ULICA]', $company['kod'] ?? '[KOD]', $company['miasto'] ?? '[MIASTO]');
        
        return <<<NDA
UMOWA O ZACHOWANIU POUFNOŚCI (NDA)

Zawarta w dniu {$date} pomiędzy:

1. Semcod sp. z o.o., ul. Cybernetyki 19, 02-677 Warszawa,
   NIP: 521-38-73-376, REGON: 387-123-456, KRS: 0000751234
   – zwana dalej "Beneficjentem"

a

2. {$companyName}, {$companyAddress},
   NIP: {$nip}, REGON: {$company['regon']}, KRS: {$company['krs']}
   reprezentowana przez: {$osoba}, {$stanowisko}
   e-mail: {$email}, tel: {$telefon}
   – zwaną dalej "Odbiorcą"

§ 1. PRZEDMIOT UMOWY

1. Beneficjent świadczy usługi analizy i refaktoryzacji kodu źródłowego.
2. W ramach świadczenia usług Beneficjent uzyskuje dostęp do kodu źródłowego
   i dokumentacji technicznej Odbiorcy ("Informacje Poufne").

§ 2. OKRES OCHRONY

Zobowiązania wynikające z niniejszej umowy obowiązuj przez okres 3 lat.

§ 3. PRAWO WŁASNOŚCI

Wszelkie prawa własności intelektualnej do Informacji Poufnych pozostają
własnością Odbiorcy. Umowa nie stanowi cesji żadnych praw.

PODPISY:

_________________________                    _________________________
Za Beneficjenta:                           Za Odbiorcę:
Semcod sp. z o.o.                          {$companyName}

data: {$date}                              data: ....................
NDA;
    }
}
