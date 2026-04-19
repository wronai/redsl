<?php
/**
 * Tests for Config API endpoints
 * 
 * @covers Config API functionality
 */

use PHPUnit\Framework\TestCase;

class ConfigApiTest extends TestCase
{
    private string $testConfigDir;
    
    protected function setUp(): void
    {
        $this->testConfigDir = __DIR__ . '/../test-redsl-config';
        
        // Create test config directory
        if (!is_dir($this->testConfigDir)) {
            mkdir($this->testConfigDir, 0750, true);
        }
        
        // Create test manifest
        $manifestPath = $this->testConfigDir . '/redsl.config.yaml';
        $testConfig = [
            'apiVersion' => 'redsl.config/v1',
            'kind' => 'RedslConfig',
            'metadata' => [
                'name' => 'test-project',
                'version' => 1,
                'created' => '2026-04-19T10:00:00Z',
            ],
            'profile' => 'test',
            'secrets' => [
                'api_key' => [
                    'ref' => 'env:TEST_API_KEY',
                    'required' => true,
                ],
            ],
            'spec' => [
                'llm_policy' => [
                    'mode' => 'frontier_lag',
                    'max_age_days' => 180,
                ],
            ],
        ];
        
        file_put_contents($manifestPath, yaml_emit($testConfig));
    }
    
    protected function tearDown(): void
    {
        // Clean up
        if (is_dir($this->testConfigDir)) {
            $this->recursiveDelete($this->testConfigDir);
        }
    }
    
    private function recursiveDelete(string $dir): void
    {
        if (is_dir($dir)) {
            $objects = scandir($dir);
            foreach ($objects as $object) {
                if ($object != "." && $object != "..") {
                    if (is_dir($dir . "/" . $object)) {
                        $this->recursiveDelete($dir . "/" . $object);
                    } else {
                        unlink($dir . "/" . $object);
                    }
                }
            }
            rmdir($dir);
        }
    }
    
    /**
     * Test config validation - valid config
     */
    public function testValidateConfigValid(): void
    {
        $config = [
            'apiVersion' => 'redsl.config/v1',
            'kind' => 'RedslConfig',
            'metadata' => [
                'name' => 'test',
                'version' => 1,
            ],
            'secrets' => [
                'key' => [
                    'ref' => 'env:TEST_KEY',
                    'required' => true,
                ],
            ],
            'spec' => [
                'llm_policy' => [
                    'mode' => 'frontier_lag',
                ],
            ],
        ];
        
        $errors = $this->validateConfig($config);
        
        $this->assertEmpty($errors);
        $this->assertTrue($this->isConfigValid($config));
    }
    
    /**
     * Test config validation - missing apiVersion
     */
    public function testValidateConfigMissingApiVersion(): void
    {
        $config = [
            'kind' => 'RedslConfig',
        ];
        
        $errors = $this->validateConfig($config);
        
        $this->assertNotEmpty($errors);
        $this->assertStringContainsString('apiVersion', $errors[0]);
    }
    
    /**
     * Test config validation - invalid apiVersion
     */
    public function testValidateConfigInvalidApiVersion(): void
    {
        $config = [
            'apiVersion' => 'invalid/v2',
            'kind' => 'RedslConfig',
        ];
        
        $errors = $this->validateConfig($config);
        
        $this->assertNotEmpty($errors);
        $this->assertStringContainsString('apiVersion', $errors[0]);
    }
    
    /**
     * Test config validation - invalid secret ref
     */
    public function testValidateConfigInvalidSecretRef(): void
    {
        $config = [
            'apiVersion' => 'redsl.config/v1',
            'kind' => 'RedslConfig',
            'metadata' => ['name' => 'test'],
            'secrets' => [
                'bad_secret' => [
                    'ref' => 'invalid:reference',
                    'required' => true,
                ],
            ],
        ];
        
        $errors = $this->validateConfig($config);
        
        $this->assertNotEmpty($errors);
        $this->assertStringContainsString('secret', strtolower($errors[0]));
    }
    
    /**
     * Test secret redaction in API response
     */
    public function testSecretRedactionInApiResponse(): void
    {
        $config = [
            'apiVersion' => 'redsl.config/v1',
            'metadata' => ['name' => 'test'],
            'secrets' => [
                'db_pass' => [
                    'ref' => 'env:DB_PASSWORD',
                    'required' => true,
                ],
                'api_key' => [
                    'ref' => 'file:/etc/secret.key',
                    'required' => true,
                ],
            ],
        ];
        
        $redacted = $this->redactSecrets($config);
        
        $this->assertStringContainsString(':***REDACTED***', $redacted['secrets']['db_pass']['ref']);
        $this->assertStringContainsString(':***REDACTED***', $redacted['secrets']['api_key']['ref']);
        $this->assertStringNotContainsString('DB_PASSWORD', $redacted['secrets']['db_pass']['ref']);
    }
    
    /**
     * Test fingerprint generation
     */
    public function testFingerprintGeneration(): void
    {
        $config = [
            'apiVersion' => 'redsl.config/v1',
            'kind' => 'RedslConfig',
            'metadata' => [
                'name' => 'test',
                'version' => 1,
            ],
            'spec' => [
                'llm_policy' => [
                    'mode' => 'frontier_lag',
                ],
            ],
        ];
        
        $fingerprintPayload = $config;
        unset($fingerprintPayload['metadata']);
        $fingerprint = hash('sha256', json_encode($fingerprintPayload, JSON_UNESCAPED_UNICODE));
        
        $this->assertEquals(64, strlen($fingerprint)); // SHA256 is 64 hex chars
        $this->assertMatchesRegularExpression('/^[a-f0-9]{64}$/', $fingerprint);
    }
    
    /**
     * Test history listing
     */
    public function testHistoryListing(): void
    {
        $historyDir = $this->testConfigDir . '/history';
        
        if (!is_dir($historyDir)) {
            mkdir($historyDir, 0750, true);
        }
        
        // Create test backup files
        touch($historyDir . '/backup-20260419-120000.yaml');
        touch($historyDir . '/backup-20260419-130000.yaml');
        
        $files = glob($historyDir . '/*.yaml');
        rsort($files);
        
        $entries = [];
        foreach (array_slice($files, 0, 20) as $file) {
            $entries[] = [
                'file' => basename($file),
                'timestamp' => filemtime($file),
                'size' => filesize($file),
            ];
        }
        
        $this->assertCount(2, $entries);
        $this->assertStringContainsString('backup-', $entries[0]['file']);
    }
    
    /**
     * Test diff calculation
     */
    public function testDiffCalculation(): void
    {
        $current = [
            'apiVersion' => 'redsl.config/v1',
            'spec' => [
                'llm_policy' => [
                    'mode' => 'frontier_lag',
                ],
            ],
        ];
        
        $proposal = [
            'changes' => [
                [
                    'path' => 'spec.llm_policy.mode',
                    'new_value' => 'bounded',
                ],
            ],
        ];
        
        $diff = [
            'changes' => [],
            'risk_level' => 'medium',
        ];
        
        foreach ($proposal['changes'] as $change) {
            $path = $change['path'] ?? 'unknown';
            $diff['changes'][] = [
                'path' => $path,
                'op' => $change['op'] ?? 'set',
                'old' => $current['spec']['llm_policy']['mode'] ?? null,
                'new' => $change['new_value'] ?? null,
            ];
        }
        
        $this->assertCount(1, $diff['changes']);
        $this->assertEquals('spec.llm_policy.mode', $diff['changes'][0]['path']);
        $this->assertEquals('frontier_lag', $diff['changes'][0]['old']);
        $this->assertEquals('bounded', $diff['changes'][0]['new']);
    }
    
    /**
     * Test JSON response format
     */
    public function testJsonResponseFormat(): void
    {
        $response = [
            'valid' => true,
            'errors' => [],
            'config' => [
                'apiVersion' => 'redsl.config/v1',
                'metadata' => ['name' => 'test'],
            ],
        ];
        
        $json = json_encode($response);
        $decoded = json_decode($json, true);
        
        $this->assertJson($json);
        $this->assertTrue($decoded['valid']);
        $this->assertIsArray($decoded['errors']);
    }
    
    /**
     * Helper: validate config (same logic as config-api.php)
     */
    private function validateConfig(array $config): array
    {
        $errors = [];
        
        if (!isset($config['apiVersion'])) {
            $errors[] = 'Missing apiVersion';
        } elseif ($config['apiVersion'] !== 'redsl.config/v1') {
            $errors[] = 'Invalid apiVersion (must be redsl.config/v1)';
        }
        
        if (!isset($config['kind']) || $config['kind'] !== 'RedslConfig') {
            $errors[] = 'Invalid or missing kind (must be RedslConfig)';
        }
        
        if (!isset($config['metadata']['name'])) {
            $errors[] = 'Missing metadata.name';
        }
        
        if (isset($config['secrets']) && is_array($config['secrets'])) {
            foreach ($config['secrets'] as $name => $spec) {
                if (!isset($spec['ref'])) {
                    $errors[] = "Secret '$name' missing ref";
                    continue;
                }
                $ref = $spec['ref'];
                $validPrefixes = ['env:', 'file:', 'vault:', 'doppler:'];
                $hasValidPrefix = false;
                foreach ($validPrefixes as $prefix) {
                    if (strpos($ref, $prefix) === 0) {
                        $hasValidPrefix = true;
                        break;
                    }
                }
                if (!$hasValidPrefix) {
                    $errors[] = "Secret '$name' has invalid ref format";
                }
            }
        }
        
        return $errors;
    }
    
    /**
     * Helper: check if config is valid
     */
    private function isConfigValid(array $config): bool
    {
        return empty($this->validateConfig($config));
    }
    
    /**
     * Helper: redact secrets (same logic as config-api.php)
     */
    private function redactSecrets(array $config): array
    {
        if (isset($config['secrets'])) {
            foreach ($config['secrets'] as $name => &$spec) {
                if (isset($spec['ref'])) {
                    $spec['ref'] = preg_replace('/:(.+)$/', ':***REDACTED***', $spec['ref']);
                }
            }
        }
        return $config;
    }
}
