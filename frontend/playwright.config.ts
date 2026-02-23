import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
	fullyParallel: false,
	workers: 1,
	testDir: './tests/e2e',
	reporter: 'list',
	use: {
		baseURL: 'http://127.0.0.1:5173',
		trace: 'on-first-retry'
	},
	projects: [
		{
			name: 'chromium',
			use: { ...devices['Desktop Chrome'] }
		},
		{
			name: 'chromium-mobile',
			use: {
				...devices['Desktop Chrome'],
				viewport: { width: 390, height: 844 },
				isMobile: true,
				hasTouch: true
			}
		}
	],
	webServer: {
		command: 'npm run dev -- --host 127.0.0.1 --port 5173',
		url: 'http://127.0.0.1:5173',
		reuseExistingServer: true,
		timeout: 120_000
	}
});
