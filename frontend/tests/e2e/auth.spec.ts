import { expect, test } from '@playwright/test';

async function interceptLogin(page: any, response: any) {
	await page.route('**/api/v1/auth/login', async (route: any) => {
		const request = route.request();
		if (request.method() === 'OPTIONS') {
			await route.fulfill({
				status: 204,
				headers: {
					'access-control-allow-origin': '*',
					'access-control-allow-methods': 'POST, OPTIONS',
					'access-control-allow-headers': 'content-type, authorization'
				}
			});
			return;
		}

		const raw = request.postData() || '{}';
		let body: any = {};
		try {
			body = JSON.parse(raw);
		} catch {
			body = {};
		}

		expect(body).toHaveProperty('email');
		expect(body).toHaveProperty('phone');
		expect(String(body.phone)).toMatch(/^\d+$/);

		await route.fulfill({
			status: 200,
			headers: {
				'access-control-allow-origin': '*'
			},
			contentType: 'application/json',
			body: JSON.stringify(response)
		});
	});
}

test.beforeEach(async ({ page }) => {
	await page.addInitScript(() => localStorage.clear());
	await page.goto('/login');
	await page.waitForTimeout(800);
});

test('login routes to /student on student role', async ({ page }) => {
	await interceptLogin(page, {
		access_token: 'test-token',
		token_type: 'bearer',
		legacy_user_id: 1,
		name: 'Test User',
		role: 'student',
		active_courses: []
	});

	await page.locator('input#email').fill('test@example.com');
	await page.locator('input#phone').fill('010-1234-5678');
	const loginBtn = page.getByRole('button', { name: '로그인' });
	const res = await Promise.all([page.waitForResponse('**/api/v1/auth/login'), loginBtn.click()]);
	expect(res[0].ok()).toBeTruthy();

	await expect(page).toHaveURL(/\/student/);
	await expect(page.getByRole('heading', { name: '내 수강 과정' })).toBeVisible();
});

test('login routes to /facilitator on facilitator role', async ({ page }) => {
	await interceptLogin(page, {
		access_token: 'test-token',
		token_type: 'bearer',
		legacy_user_id: 2,
		name: 'Test Facilitator',
		role: 'facilitator',
		active_courses: []
	});

	await page.route('**/api/v1/facilitator/courses', async (route: any) => {
		await route.fulfill({
			status: 200,
			headers: {
				'access-control-allow-origin': '*'
			},
			contentType: 'application/json',
			body: JSON.stringify([])
		});
	});

	await page.locator('input#email').fill('fac@example.com');
	await page.locator('input#phone').fill('010-0000-0000');
	const loginBtn = page.getByRole('button', { name: '로그인' });
	const res = await Promise.all([page.waitForResponse('**/api/v1/auth/login'), loginBtn.click()]);
	expect(res[0].ok()).toBeTruthy();

	await expect(page).toHaveURL(/\/facilitator/);
	await expect(page.getByRole('heading', { name: '과정 관리' })).toBeVisible();
});

test('mobile: no global horizontal overflow on login page', async ({ page }) => {
	await page.goto('/login');
	const ok = await page.evaluate(() => {
		const doc = document.documentElement;
		return doc.scrollWidth <= window.innerWidth + 1;
	});
	expect(ok).toBeTruthy();
});
