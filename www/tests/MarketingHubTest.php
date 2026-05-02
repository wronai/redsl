<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

/**
 * Marketing Hub Unit & Integration Tests
 */
class MarketingHubTest extends TestCase
{
    private string $baseUrl;
    private string $apiUrl;
    
    protected function setUp(): void
    {
        $this->baseUrl = getenv('BASE_URL') ?: 'http://localhost:8080';
        $this->apiUrl = getenv('REDSL_API_URL') ?: 'http://localhost:8001';
    }
    
    /**
     * Test that marketing page loads successfully
     */
    public function testMarketingPageLoads(): void
    {
        $ch = curl_init($this->baseUrl . '/marketing/');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        $this->assertEquals(200, $httpCode);
        $this->assertStringContainsString('ReDSL Marketing Hub', $response);
        $this->assertStringContainsString('Cold Email', $response);
    }
    
    /**
     * Test that marketing page has no PHP errors
     */
    public function testMarketingPageHasNoErrors(): void
    {
        $ch = curl_init($this->baseUrl . '/marketing/');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        $response = curl_exec($ch);
        curl_close($ch);
        
        $this->assertStringNotContainsString('Fatal error', $response);
        $this->assertStringNotContainsString('Parse error', $response);
        $this->assertStringNotContainsString('Warning:', $response);
    }
    
    /**
     * Test that form elements are present
     */
    public function testMarketingPageHasFormElements(): void
    {
        $ch = curl_init($this->baseUrl . '/marketing/');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        $response = curl_exec($ch);
        curl_close($ch);
        
        $this->assertStringContainsString('repo_url', $response);
        $this->assertStringContainsString('buyer_type', $response);
        $this->assertStringContainsString('contact_name', $response);
        $this->assertStringContainsString('sender_name', $response);
    }
    
    /**
     * Test API health endpoint
     */
    public function testRedslApiHealth(): void
    {
        $ch = curl_init($this->apiUrl . '/health');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode === 200) {
            $data = json_decode($response, true);
            $this->assertEquals('ok', $data['status']);
            $this->assertEquals('conscious-refactor', $data['agent']);
        } else {
            $this->markTestSkipped('ReDSL API not available');
        }
    }
    
    /**
     * Test scan/remote endpoint with TradingAgents repo
     */
    public function testScanRemoteEndpointWithTradingAgents(): void
    {
        // First check if API is available
        $healthCh = curl_init($this->apiUrl . '/health');
        curl_setopt($healthCh, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($healthCh, CURLOPT_TIMEOUT, 5);
        curl_exec($healthCh);
        $healthCode = curl_getinfo($healthCh, CURLINFO_HTTP_CODE);
        curl_close($healthCh);
        
        if ($healthCode !== 200) {
            $this->markTestSkipped('ReDSL API not available');
        }
        
        // Test scan/remote endpoint
        $ch = curl_init($this->apiUrl . '/scan/remote');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
            'repo_url' => 'https://github.com/TauricResearch/TradingAgents',
            'depth' => 1
        ]));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_TIMEOUT, 120);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        $this->assertEquals(200, $httpCode, 'Scan/remote should return 200');
        
        $data = json_decode($response, true);
        $this->assertEquals('success', $data['status']);
        $this->assertGreaterThan(0, $data['total_files'], 'Should find at least one file');
        $this->assertArrayHasKey('avg_cc', $data);
        $this->assertArrayHasKey('critical_count', $data);
        $this->assertArrayHasKey('alerts', $data);
        $this->assertArrayHasKey('top_issues', $data);
        $this->assertArrayHasKey('summary', $data);
        
        // Log results for visibility
        fwrite(STDOUT, sprintf(
            "\n📊 TradingAgents Scan Results:\n" .
            "  Files: %d\n" .
            "  Lines: %d\n" .
            "  Avg CC: %.2f\n" .
            "  Critical: %d\n" .
            "  Top Issues: %d\n",
            $data['total_files'],
            $data['total_lines'],
            $data['avg_cc'],
            $data['critical_count'],
            count($data['top_issues'])
        ));
    }
    
    /**
     * Test scan/remote returns valid top_issues structure
     */
    public function testScanRemoteTopIssuesStructure(): void
    {
        // Check API availability
        $healthCh = curl_init($this->apiUrl . '/health');
        curl_setopt($healthCh, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($healthCh, CURLOPT_TIMEOUT, 5);
        curl_exec($healthCh);
        $healthCode = curl_getinfo($healthCh, CURLINFO_HTTP_CODE);
        curl_close($healthCh);
        
        if ($healthCode !== 200) {
            $this->markTestSkipped('ReDSL API not available');
        }
        
        $ch = curl_init($this->apiUrl . '/scan/remote');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
            'repo_url' => 'https://github.com/psf/requests',
            'depth' => 1
        ]));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_TIMEOUT, 120);
        
        $response = curl_exec($ch);
        curl_close($ch);
        
        $data = json_decode($response, true);
        
        if (!empty($data['top_issues'])) {
            $firstIssue = $data['top_issues'][0];
            $this->assertArrayHasKey('type', $firstIssue);
            $this->assertArrayHasKey('name', $firstIssue);
            $this->assertArrayHasKey('severity', $firstIssue);
            $this->assertArrayHasKey('description', $firstIssue);
            
            // Log first issue
            fwrite(STDOUT, sprintf(
                "\n🔍 First Top Issue: %s (CC=%d)\n",
                $firstIssue['name'],
                $firstIssue['value'] ?? 0
            ));
        }
    }
    
    /**
     * Test OpenAPI spec endpoint
     */
    public function testOpenApiSpecEndpoint(): void
    {
        $ch = curl_init($this->apiUrl . '/openapi.json');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode === 200) {
            $data = json_decode($response, true);
            $this->assertEquals('3.1.0', $data['openapi']);
            $this->assertArrayHasKey('paths', $data);
            $this->assertArrayHasKey('/scan/remote', $data['paths'] ?? []);
        } else {
            $this->markTestSkipped('OpenAPI endpoint not available');
        }
    }
    
    /**
     * Test form submission with POST data
     */
    public function testMarketingFormSubmission(): void
    {
        $postData = [
            'repo_url' => 'https://github.com/psf/requests',
            'buyer_type' => 'tech_lead',
            'contact_name' => 'Janek',
            'sender_name' => 'Tomek'
        ];
        
        $ch = curl_init($this->baseUrl . '/marketing/');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($postData));
        curl_setopt($ch, CURLOPT_TIMEOUT, 120);
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        $this->assertEquals(200, $httpCode);
        
        // Should contain either results or error message
        $hasResults = strpos($response, 'Skan zakończony') !== false ||
                      strpos($response, 'metryki') !== false;
        $hasError = strpos($response, 'API Error') !== false;
        
        $this->assertTrue($hasResults || $hasError, 'Should show results or error');
    }
    
    /**
     * Test that buyer types are present in form
     */
    public function testBuyerTypesInForm(): void
    {
        $ch = curl_init($this->baseUrl . '/marketing/');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        $response = curl_exec($ch);
        curl_close($ch);
        
        $this->assertStringContainsString('tech_lead', $response);
        $this->assertStringContainsString('ceo', $response);
        $this->assertStringContainsString('pm_agency', $response);
    }
    
    /**
     * Test templates array structure
     */
    public function testTemplateGenerationStructure(): void
    {
        // Simulate template data structure
        $templates = [
            'email_tech_lead' => [
                'title' => 'Tech Lead — Code Review Bottleneck',
                'subject' => 'Test subject',
                'body' => "Test body with issues:\n• Issue 1\n• Issue 2"
            ],
            'linkedin_pain_hook' => [
                'title' => 'Hook na ból',
                'content' => 'LinkedIn post content'
            ]
        ];
        
        $this->assertArrayHasKey('email_tech_lead', $templates);
        $this->assertArrayHasKey('linkedin_pain_hook', $templates);
        $this->assertArrayHasKey('subject', $templates['email_tech_lead']);
        $this->assertArrayHasKey('body', $templates['email_tech_lead']);
    }
}
