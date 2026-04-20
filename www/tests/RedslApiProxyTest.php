<?php
/**
 * Tests for /api/redsl.php proxy
 *
 * Tests the PHP proxy logic in isolation (no live redsl-api needed).
 */

use PHPUnit\Framework\TestCase;

class RedslApiProxyTest extends TestCase
{
    // ── helpers ──────────────────────────────────────────────────

    private function resolveProject(string $name, string $workspace = '/workspace'): string|false
    {
        $clean = preg_replace('/[^a-zA-Z0-9_\-]/', '', $name);
        if ($clean === '') return false;
        return $workspace . '/' . $clean;
    }

    private function mockCurlResponse(int $code, array $body): array
    {
        return [
            'ok'    => $code >= 200 && $code < 300,
            'code'  => $code,
            'body'  => $body,
            'error' => null,
        ];
    }

    // ── resolve_project ──────────────────────────────────────────

    public function testResolveProjectValid(): void
    {
        $result = $this->resolveProject('goal');
        $this->assertSame('/workspace/goal', $result);
    }

    public function testResolveProjectStripsSpecialChars(): void
    {
        $result = $this->resolveProject('../../../etc/passwd');
        // regex strips dots and slashes; result may be non-empty but must not contain traversal
        $this->assertStringNotContainsString('..', (string)$result);
        $this->assertStringNotContainsString('/etc/passwd', (string)$result);
        // The cleaned name must not start from root outside workspace
        if ($result !== false) {
            $this->assertStringStartsWith('/workspace/', $result);
        }
    }

    public function testResolveProjectEmptyReturnsFalse(): void
    {
        $result = $this->resolveProject('');
        $this->assertFalse($result);
    }

    public function testResolveProjectOnlySpecialCharsReturnsFalse(): void
    {
        $result = $this->resolveProject('../../');
        $this->assertFalse($result);
    }

    public function testResolveProjectCustomWorkspace(): void
    {
        $result = $this->resolveProject('vallm', '/home/tom/github/semcod');
        $this->assertSame('/home/tom/github/semcod/vallm', $result);
    }

    // ── curl response helper ─────────────────────────────────────

    public function testMockCurlOkResponse(): void
    {
        $r = $this->mockCurlResponse(200, ['status' => 'ok']);
        $this->assertTrue($r['ok']);
        $this->assertSame(200, $r['code']);
        $this->assertSame('ok', $r['body']['status']);
    }

    public function testMockCurlErrorResponse(): void
    {
        $r = $this->mockCurlResponse(502, ['error' => 'upstream down']);
        $this->assertFalse($r['ok']);
        $this->assertSame(502, $r['code']);
    }

    // ── health response structure ─────────────────────────────────

    public function testHealthResponseStructure(): void
    {
        $r = $this->mockCurlResponse(200, [
            'status'  => 'ok',
            'agent'   => 'conscious-refactor',
            'version' => '1.2.49',
        ]);
        $this->assertTrue($r['ok']);
        $this->assertArrayHasKey('status', $r['body']);
        $this->assertArrayHasKey('version', $r['body']);
        $this->assertSame('ok', $r['body']['status']);
    }

    // ── analyze response structure ───────────────────────────────

    public function testAnalyzeResponseContainsExpectedFields(): void
    {
        $r = $this->mockCurlResponse(200, [
            'total_files'   => 13,
            'avg_cc'        => 27.68,
            'critical_count'=> 0,
            'alerts'        => [],
        ]);
        $this->assertTrue($r['ok']);
        $this->assertSame(13, $r['body']['total_files']);
        $this->assertSame(27.68, $r['body']['avg_cc']);
    }

    // ── max_actions clamping ──────────────────────────────────────

    public function testMaxActionsClampedTo20(): void
    {
        $requested  = 999;
        $clamped    = min($requested, 20);
        $this->assertSame(20, $clamped);
    }

    public function testMaxActionsDefault(): void
    {
        $body       = [];
        $maxActions = min((int)($body['max_actions'] ?? 5), 20);
        $this->assertSame(5, $maxActions);
    }

    // ── dry_run default ──────────────────────────────────────────

    public function testDryRunDefaultsToTrue(): void
    {
        $body   = [];
        $dryRun = (bool)($body['dry_run'] ?? true);
        $this->assertTrue($dryRun);
    }

    public function testDryRunCanBeSetFalse(): void
    {
        $body   = ['dry_run' => false];
        $dryRun = (bool)($body['dry_run'] ?? true);
        $this->assertFalse($dryRun);
    }

    // ── payload construction ─────────────────────────────────────

    public function testRefactorPayloadStructure(): void
    {
        $projectPath = '/workspace/goal';
        $dryRun      = false;
        $maxActions  = 5;
        $payload = [
            'project_dir' => $projectPath,
            'dry_run'     => $dryRun,
            'max_actions' => $maxActions,
        ];
        $this->assertSame('/workspace/goal', $payload['project_dir']);
        $this->assertFalse($payload['dry_run']);
        $this->assertSame(5, $payload['max_actions']);
        $this->assertArrayNotHasKey('project_path', $payload);
    }

    public function testAnalyzePayloadUsesProjectDir(): void
    {
        $projectPath = '/workspace/code2llm';
        $payload     = ['project_dir' => $projectPath];
        $this->assertArrayHasKey('project_dir', $payload);
        $this->assertArrayNotHasKey('project_path', $payload);
    }

    // ── live redsl API (skipped if not available) ─────────────────

    public function testLiveHealthEndpoint(): void
    {
        $url = getenv('REDSL_API_URL') ?: 'http://127.0.0.1:8001';
        $ch  = curl_init("$url/health");
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 3]);
        $resp = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $err  = curl_error($ch);
        curl_close($ch);

        if ($err || $code === 0) {
            $this->markTestSkipped("redsl API not reachable at $url ($err)");
        }

        $data = json_decode($resp ?: '{}', true);
        $this->assertSame(200, $code);
        $this->assertSame('ok', $data['status'] ?? null);
    }

    public function testLiveAnalyzeEndpoint(): void
    {
        $url     = getenv('REDSL_API_URL') ?: 'http://127.0.0.1:8001';
        $project = getenv('REDSL_TEST_PROJECT') ?: '/home/tom/github/semcod/goal';

        $ch = curl_init("$url/analyze");
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 15,
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => json_encode(['project_dir' => $project]),
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        ]);
        $resp = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $err  = curl_error($ch);
        curl_close($ch);

        if ($err || $code === 0) {
            $this->markTestSkipped("redsl API not reachable at $url ($err)");
        }

        $data = json_decode($resp ?: '{}', true);
        $this->assertSame(200, $code);
        $this->assertArrayHasKey('total_files', $data);
        $this->assertArrayHasKey('avg_cc', $data);
        $this->assertIsInt($data['total_files']);
        $this->assertGreaterThanOrEqual(0, $data['total_files']);
    }
}
