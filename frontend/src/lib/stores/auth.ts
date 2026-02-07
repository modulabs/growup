import { writable, derived } from 'svelte/store';
import type { User, CourseInfo, LoginResponse } from '$lib/types';

function createPersistedStore<T>(key: string, initial: T) {
	const stored = typeof window !== 'undefined' ? localStorage.getItem(key) : null;
	const value = stored ? JSON.parse(stored) : initial;
	const store = writable<T>(value);
	store.subscribe((v) => {
		if (typeof window !== 'undefined') {
			if (v === null || v === undefined) {
				localStorage.removeItem(key);
			} else {
				localStorage.setItem(key, JSON.stringify(v));
			}
		}
	});
	return store;
}

export const authToken = createPersistedStore<string | null>('growup_token', null);
export const currentUser = createPersistedStore<User | null>('growup_user', null);
export const activeCourses = createPersistedStore<CourseInfo[]>('growup_courses', []);

export const isLoggedIn = derived(authToken, ($token) => !!$token);
export const userRole = derived(currentUser, ($user) => $user?.role ?? null);

export function setAuth(data: LoginResponse) {
	authToken.set(data.access_token);
	currentUser.set({
		legacy_user_id: data.legacy_user_id,
		name: data.name,
		role: data.role
	});
	activeCourses.set(data.active_courses);
}

export function logout() {
	authToken.set(null);
	currentUser.set(null);
	activeCourses.set([]);
}
