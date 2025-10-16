import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface TestResult {
  name: string;
  status: 'pending' | 'running' | 'pass' | 'fail';
  message?: string;
  duration?: number;
  timestamp?: string;
}

export default function TestDashboard() {
  const [apiBase, setApiBase] = useState(import.meta.env.VITE_API_BASE || '');
  const [email, setEmail] = useState('test@example.com');
  const [password, setPassword] = useState('password123');
  const [token, setToken] = useState('');
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const updateTestResult = (name: string, updates: Partial<TestResult>) => {
    setTestResults(prev => {
      const index = prev.findIndex(r => r.name === name);
      if (index >= 0) {
        const newResults = [...prev];
        newResults[index] = { ...newResults[index], ...updates };
        return newResults;
      }
      return [...prev, { name, status: 'pending', ...updates }];
    });
  };

  const runTest = async (
    name: string,
    testFn: () => Promise<void>
  ): Promise<boolean> => {
    const startTime = Date.now();
    updateTestResult(name, { status: 'running', timestamp: new Date().toISOString() });

    try {
      await testFn();
      const duration = Date.now() - startTime;
      updateTestResult(name, {
        status: 'pass',
        message: 'Success',
        duration
      });
      return true;
    } catch (error) {
      const duration = Date.now() - startTime;
      updateTestResult(name, {
        status: 'fail',
        message: error instanceof Error ? error.message : 'Unknown error',
        duration
      });
      return false;
    }
  };

  const runAllTests = async () => {
    setIsRunning(true);
    setTestResults([]);

    // Test 1: Health Check
    await runTest('Health Check', async () => {
      const response = await fetch(`${apiBase}/health`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      if (!data.ok || !data.version || !data.git) {
        throw new Error('Missing required fields');
      }

      const keys = Object.keys(data);
      if (keys.length !== 3) {
        throw new Error(`Expected 3 keys, got ${keys.length}: ${keys.join(', ')}`);
      }
    });

    // Test 2: Login
    const loginSuccess = await runTest('Login', async () => {
      const response = await fetch(`${apiBase}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      if (!data.access_token) {
        throw new Error('No access token returned');
      }

      setToken(data.access_token);
    });

    if (!loginSuccess) {
      setIsRunning(false);
      return;
    }

    // Test 3: List Templates
    let templateId = '';
    await runTest('List Templates', async () => {
      const response = await fetch(`${apiBase}/api/v1/templates`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      if (!data.templates || data.templates.length < 3) {
        throw new Error(`Expected ≥3 templates, got ${data.templates?.length || 0}`);
      }

      templateId = data.templates[0].id;
    });

    // Test 4: Create Job with intensity (integer)
    let jobId = '';
    const idempotencyKey = `test-${Date.now()}`;

    await runTest('Create Job (intensity=7)', async () => {
      const response = await fetch(`${apiBase}/api/v1/use`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Idempotency-Key': idempotencyKey
        },
        body: JSON.stringify({
          template_id: templateId,
          inputs: {
            title: 'UAT Test Title',
            description: 'UAT Test Description'
          },
          temperature: 0.7,
          intensity: 7  // Integer 1-10
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      if (!data.job_id) {
        throw new Error('No job_id returned');
      }

      jobId = data.job_id;
    });

    // Test 5: Idempotency Check
    await runTest('Idempotency (same key)', async () => {
      const response = await fetch(`${apiBase}/api/v1/use`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Idempotency-Key': idempotencyKey  // Same key
        },
        body: JSON.stringify({
          template_id: templateId,
          inputs: {
            title: 'UAT Test Title',
            description: 'UAT Test Description'
          },
          temperature: 0.7,
          intensity: 7
        })
      });

      const data = await response.json();
      if (data.job_id !== jobId) {
        throw new Error(`Expected job_id ${jobId}, got ${data.job_id}`);
      }
    });

    // Test 6: Get Job Status
    await runTest('Get Job Status', async () => {
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s

      const response = await fetch(`${apiBase}/api/v1/jobs/${jobId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const validStatuses = ['pending', 'processing', 'completed', 'failed'];
      if (!validStatuses.includes(data.status)) {
        throw new Error(`Invalid status: ${data.status}`);
      }
    });

    // Test 7: 422 Token Budget Exceeded
    await runTest('422 Token Budget', async () => {
      const largeText = 'A'.repeat(12000);

      const response = await fetch(`${apiBase}/api/v1/use`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Idempotency-Key': `test-token-exceeded-${Date.now()}`
        },
        body: JSON.stringify({
          template_id: templateId,
          inputs: { title: largeText },
          temperature: 1.0,
          intensity: 10
        })
      });

      if (response.status !== 422) {
        throw new Error(`Expected 422, got ${response.status}`);
      }

      const data = await response.json();
      if (data.error?.code !== 'TOKEN_BUDGET_EXCEEDED') {
        throw new Error(`Expected TOKEN_BUDGET_EXCEEDED, got ${data.error?.code}`);
      }
    });

    // Test 8: Rate Limiting (429)
    await runTest('429 Rate Limit (6 rapid requests)', async () => {
      let got429 = false;

      for (let i = 0; i < 6; i++) {
        const response = await fetch(`${apiBase}/api/v1/use`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'Idempotency-Key': `rate-test-${i}-${Date.now()}`
          },
          body: JSON.stringify({
            template_id: templateId,
            inputs: { title: `Rate Test ${i}` },
            temperature: 0.5,
            intensity: 5
          })
        });

        if (response.status === 429) {
          got429 = true;
          break;
        }

        await new Promise(resolve => setTimeout(resolve, 100));
      }

      if (!got429) {
        throw new Error('Rate limit (429) not triggered after 6 requests');
      }
    });

    setIsRunning(false);
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'pass': return '✓';
      case 'fail': return '✗';
      case 'running': return '⋯';
      default: return '○';
    }
  };

  const getStatusColor = (status: TestResult['status']) => {
    switch (status) {
      case 'pass': return 'text-green-600';
      case 'fail': return 'text-red-600';
      case 'running': return 'text-blue-600';
      default: return 'text-gray-400';
    }
  };

  const passCount = testResults.filter(r => r.status === 'pass').length;
  const failCount = testResults.filter(r => r.status === 'fail').length;
  const totalCount = testResults.length;

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">UAT Test Dashboard</h1>
        <p className="text-gray-600">Preview Environment Testing - 2025-10-16</p>
      </div>

      <Tabs defaultValue="tests" className="space-y-4">
        <TabsList>
          <TabsTrigger value="tests">Test Suite</TabsTrigger>
          <TabsTrigger value="manual">Manual Testing</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>

        <TabsContent value="tests" className="space-y-4">
          {/* Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Test Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="apiBase">API Base URL</Label>
                <Input
                  id="apiBase"
                  value={apiBase}
                  onChange={(e) => setApiBase(e.target.value)}
                  placeholder="https://tepure-api-preview-xxx.run.app"
                  className="font-mono text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>

              <Button
                onClick={runAllTests}
                disabled={isRunning || !apiBase}
                className="w-full"
              >
                {isRunning ? 'Running Tests...' : 'Run All Tests (8 tests)'}
              </Button>
            </CardContent>
          </Card>

          {/* Test Results */}
          {testResults.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Test Results</CardTitle>
                <div className="text-sm text-gray-600">
                  {passCount} passed, {failCount} failed, {totalCount} total
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {testResults.map((result, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <span className={`text-2xl ${getStatusColor(result.status)}`}>
                          {getStatusIcon(result.status)}
                        </span>
                        <div>
                          <div className="font-medium">{result.name}</div>
                          {result.message && (
                            <div className={`text-sm ${
                              result.status === 'fail' ? 'text-red-600' : 'text-gray-600'
                            }`}>
                              {result.message}
                            </div>
                          )}
                        </div>
                      </div>
                      {result.duration && (
                        <div className="text-sm text-gray-500">
                          {result.duration}ms
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {failCount === 0 && totalCount === 8 && (
                  <Alert className="mt-4 bg-green-50 border-green-200">
                    <AlertDescription className="text-green-800">
                      ✓ All tests passed! The Preview environment is ready for UAT.
                    </AlertDescription>
                  </Alert>
                )}

                {failCount > 0 && (
                  <Alert className="mt-4 bg-red-50 border-red-200">
                    <AlertDescription className="text-red-800">
                      ✗ {failCount} test(s) failed. Please review the errors above.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="manual" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Manual Testing Checklist</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Authentication</h3>
                  <ul className="space-y-1 text-sm">
                    <li>□ Login with valid credentials</li>
                    <li>□ Login with invalid credentials (should fail)</li>
                    <li>□ Logout and verify token is cleared</li>
                    <li>□ Token refresh after 15 minutes</li>
                  </ul>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Templates</h3>
                  <ul className="space-y-1 text-sm">
                    <li>□ View template list (≥3 templates)</li>
                    <li>□ Filter templates by category (LP/Banner/SNS/WebApp)</li>
                    <li>□ Search templates by tag</li>
                    <li>□ View template details with preview_url</li>
                  </ul>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Job Creation</h3>
                  <ul className="space-y-1 text-sm">
                    <li>□ Create job with intensity=1 (minimal)</li>
                    <li>□ Create job with intensity=5 (balanced)</li>
                    <li>□ Create job with intensity=10 (creative)</li>
                    <li>□ Verify intensity=0 returns validation error (400)</li>
                    <li>□ Verify intensity=11 returns validation error (400)</li>
                  </ul>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Idempotency</h3>
                  <ul className="space-y-1 text-sm">
                    <li>□ Create job with Idempotency-Key header</li>
                    <li>□ Retry with same key returns same job_id</li>
                    <li>□ Different key creates new job</li>
                  </ul>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Error Handling</h3>
                  <ul className="space-y-1 text-sm">
                    <li>□ 422 Token Budget (large input text)</li>
                    <li>□ 429 Rate Limit (6 rapid requests)</li>
                    <li>□ Error format has {`{error: {code, message, hint}}`}</li>
                  </ul>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Performance</h3>
                  <ul className="space-y-1 text-sm">
                    <li>□ API response time &lt; 2 seconds (P95)</li>
                    <li>□ Frontend page load &lt; 3 seconds</li>
                    <li>□ No console errors in browser DevTools</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Test Environment Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm font-mono">
              <div><strong>API Base:</strong> {apiBase || 'Not set'}</div>
              <div><strong>Git SHA:</strong> {import.meta.env.VITE_GIT_SHA || 'Unknown'}</div>
              <div><strong>Environment:</strong> {import.meta.env.MODE}</div>
              <div><strong>Timestamp:</strong> {new Date().toISOString()}</div>
            </CardContent>
          </Card>

          {testResults.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="text-3xl font-bold text-green-600">{passCount}</div>
                    <div className="text-sm text-gray-600">Passed</div>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg">
                    <div className="text-3xl font-bold text-red-600">{failCount}</div>
                    <div className="text-sm text-gray-600">Failed</div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-3xl font-bold text-gray-600">{totalCount}</div>
                    <div className="text-sm text-gray-600">Total</div>
                  </div>
                </div>

                {testResults.length > 0 && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm font-semibold mb-2">Test Details (JSON)</div>
                    <pre className="text-xs overflow-auto max-h-96">
                      {JSON.stringify(testResults, null, 2)}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
