import { writable } from 'svelte/store';

export interface Toast {
	id: number;
	message: string;
	type: 'success' | 'error' | 'info';
}

let nextId = 0;

export const toasts = writable<Toast[]>([]);

export function addToast(message: string, type: Toast['type'] = 'info') {
	const id = nextId++;
	toasts.update((t) => [...t, { id, message, type }]);
	setTimeout(() => {
		toasts.update((t) => t.filter((toast) => toast.id !== id));
	}, 3000);
}
