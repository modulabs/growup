import { env } from '$env/dynamic/public';
import { base } from '$app/paths';
import { get } from 'svelte/store';
import { authToken, logout } from '$lib/stores/auth';

const API_BASE = env.PUBLIC_API_BASE_URL || 'http://localhost:8000';

class ApiError extends Error {
	status: number;
	constructor(message: string, status: number) {
		super(message);
		this.status = status;
	}
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
	const token = get(authToken);
	const headers: Record<string, string> = {
		'Content-Type': 'application/json'
	};
	if (token) {
		headers['Authorization'] = `Bearer ${token}`;
	}

	const res = await fetch(`${API_BASE}${path}`, {
		method,
		headers,
		body: body ? JSON.stringify(body) : undefined
	});

	if (res.status === 401) {
		logout();
		if (typeof window !== 'undefined') {
			window.location.href = `${base}/login`;
		}
		throw new ApiError('인증이 만료되었습니다. 다시 로그인해주세요.', 401);
	}

	if (res.status === 204) {
		return undefined as T;
	}

	if (!res.ok) {
		const errorData = await res.json().catch(() => ({ detail: '알 수 없는 오류가 발생했습니다.' }));
		throw new ApiError(errorData.detail || `HTTP ${res.status}`, res.status);
	}

	return res.json();
}

export const api = {
	get: <T>(path: string) => request<T>('GET', path),
	post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
	put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
	patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body),
	del: <T>(path: string) => request<T>('DELETE', path)
};

export { ApiError };
