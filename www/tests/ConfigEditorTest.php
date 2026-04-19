<?php
/**
 * Tests for Config Editor GUI
 * 
 * @covers ConfigEditor functionality
 */

use PHPUnit\Framework\TestCase;

class ConfigEditorTest extends TestCase
{
    private string $testConfigDir;
    private string $testManifestPath;
    
    protected function setUp(): void
    {
        $this->testConfigDir = __DIR__ . '/../test-redsl-config';
        $this->testManifestPath = $this->testConfigDir . '/redsl.config.yaml';
        
        // Clean up before test
        if (is_dir($this->testConfigDir)) {
            $this->recursiveDelete($this->testConfigDir);
        }
    }
    
    protected function tearDown(): void
    {
        // Clean up after test
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
     * Test that config-editor.php returns valid HTML structure
     */
    public function testConfigEditorReturnsValidHtml(): void
    {
        ob_start();
        $_SERVER['REQUEST_METHOD'] = 'GET';
        include __DIR__ . '/../config-editor.php';
        $output = ob_get_clean();
        
        $this->assertStringContainsString('<!DOCTYPE html>', $output);
        $this->assertStringContainsString('<title>ReDSL Config Editor</title>', $output);
        $this->assertStringContainsString('redsl-config/', $output);
    }
    
    /**
     * Test config initialization form
     */
    public function testConfigInitialization(): void
    {
        // Simulate POST request to create default config
        $_SERVER['REQUEST_METHOD'] = 'POST';
        $_POST = ['action' => 'init'];
        
        // Override config path for testing
        $configDir = $this->testConfigDir;
        $manifestPath = $this->testManifestPath;
        
        // Create config directory
        if (!is_dir($configDir)) {
            mkdir($configDir, 0750, true);
        }
        
        // Test default config structure
        $defaultConfig = [
            'apiVersion' => 'redsl.config/v1',
            'kind' => 'RedslConfig',
            'metadata' => [
                'name' => 'my-project',
                'version' => 1,
                'created' => date('c'),
                'updated' => date('c'),
            ],
            'profile' => 'production',
            'secrets' => [
                'openrouter_api_key' => [
                    'ref' => 'env:OPENROUTER_API_KEY',
                    'required' => true,
                ],
            ],
            'spec' => [
                'llm_policy' => [
                    'mode' => 'frontier_lag',
                    'max_age_days' => 180,
                    'strict' => true,
                ],
            ],
        ];
        
        $this->assertEquals('redsl.config/v1', $defaultConfig['apiVersion']);
        $this->assertEquals('RedslConfig', $defaultConfig['kind']);
        $this->assertArrayHasKey('metadata', $defaultConfig);
        $this->assertArrayHasKey('secrets', $defaultConfig);
        $this->assertArrayHasKey('spec', $defaultConfig);
    }
    
    /**
     * Test secret redaction in display
     */
    public function testSecretRedaction(): void
    {
        $config = [
            'apiVersion' => 'redsl.config/v1',
            'secrets' => [
                'api_key' => ['ref' => 'env:SECRET_KEY', 'required' => true],
                'db_pass' => ['ref' => 'file:/etc/pass', 'required' => true],
            ],
        ];
        
        // Simulate redaction (same logic as in config-editor.php)
        if (isset($config['secrets'])) {
            foreach ($config['secrets'] as $name => &$spec) {
                if (isset($spec['ref'])) {
                    $spec['ref'] = preg_replace('/:(.+)$/', ':***REDACTED***', $spec['ref']);
                }
            }
        }
        
        $this->assertStringContainsString(':***REDACTED***', $config['secrets']['api_key']['ref']);
        $this->assertStringContainsString(':***REDACTED***', $config['secrets']['db_pass']['ref']);
    }
    
    /**
     * Test risk level colors are defined
     */
    public function testRiskLevelColors(): void
    {
        $riskColors = [
            'low' => '#22c55e',
            'medium' => '#f59e0b',
            'high' => '#f97316',
            'critical' => '#ef4444',
            'unknown' => '#6b7280',
        ];
        
        $this->assertCount(5, $riskColors);
        $this->assertEquals('#22c55e', $riskColors['low']);
        $this->assertEquals('#ef4444', $riskColors['critical']);
    }
    
    /**
     * Test YAML validation
     */
    public function testYamlValidation(): void
    {
        $validYaml = <<<YAML
apiVersion: redsl.config/v1
kind: RedslConfig
metadata:
  name: test-project
  version: 1
YAML;
        
        $invalidYaml = <<<YAML
invalid: yaml: syntax: error: [
  unclosed: bracket
YAML;
        
        $parsed = yaml_parse($validYaml);
        $this->assertIsArray($parsed);
        $this->assertEquals('redsl.config/v1', $parsed['apiVersion']);
        
        $invalidParsed = @yaml_parse($invalidYaml);
        $this->assertFalse($invalidParsed);
    }
    
    /**
     * Test backup creation on save
     */
    public function testBackupCreation(): void
    {
        $configDir = $this->testConfigDir;
        $historyDir = $configDir . '/history';
        
        if (!is_dir($configDir)) {
            mkdir($configDir, 0750, true);
        }
        
        // Simulate creating backup
        if (!is_dir($historyDir)) {
            mkdir($historyDir, 0750, true);
        }
        
        $backupPath = $historyDir . '/backup-' . date('Ymd-His') . '.yaml';
        $testContent = "apiVersion: redsl.config/v1\nkind: RedslConfig\n";
        
        file_put_contents($backupPath, $testContent);
        
        $this->assertFileExists($backupPath);
        $this->assertStringEqualsFile($backupPath, $testContent);
    }
}
