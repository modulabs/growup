<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, ApiError } from '$lib/api/client';
	import { setAuth, isLoggedIn, userRole } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/toast';
	import type { LoginResponse } from '$lib/types';
	import { onMount } from 'svelte';

	let name = $state('');
	let phone = $state('');
	let loading = $state(false);
	let errorMsg = $state('');

	onMount(() => {
		if ($isLoggedIn) {
			goto($userRole === 'facilitator' ? '/facilitator' : '/student');
		}
	});

	function formatPhone(value: string): string {
		const digits = value.replace(/\D/g, '');
		if (digits.length <= 3) return digits;
		if (digits.length <= 7) return `${digits.slice(0, 3)}-${digits.slice(3)}`;
		return `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7, 11)}`;
	}

	function handlePhoneInput(e: Event) {
		const input = e.target as HTMLInputElement;
		phone = formatPhone(input.value);
	}

	async function handleLogin(e: Event) {
		e.preventDefault();
		if (!name.trim() || !phone.trim()) {
			errorMsg = '이름과 전화번호를 입력해주세요.';
			return;
		}

		loading = true;
		errorMsg = '';

		try {
			const rawPhone = phone.replace(/-/g, '');
			const data = await api.post<LoginResponse>('/api/v1/auth/login', {
				name: name.trim(),
				phone: rawPhone
			});

			setAuth(data);
			addToast(`${data.name}님, 환영합니다!`, 'success');

			if (data.role === 'facilitator') {
				goto('/facilitator');
			} else {
				goto('/student');
			}
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) {
					errorMsg = '등록되지 않은 사용자입니다. 모두연 LMS 등록 여부를 확인해주세요.';
				} else {
					errorMsg = err.message;
				}
			} else {
				errorMsg = '서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.';
			}
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex items-center justify-center min-h-screen bg-gray-50 px-4">
	<div class="w-full max-w-sm">
		<div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
			<div class="text-center mb-8">
				<h1 class="text-3xl font-bold text-blue-600 mb-2">GrowUp</h1>
				<p class="text-sm text-gray-500">퀘스트 점수 관리 시스템</p>
			</div>

			<form onsubmit={handleLogin} class="space-y-4">
				<div>
					<label for="name" class="block text-sm font-medium text-gray-700 mb-1">이름</label>
					<input
						id="name"
						type="text"
						bind:value={name}
						placeholder="홍길동"
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
						disabled={loading}
					/>
				</div>

				<div>
					<label for="phone" class="block text-sm font-medium text-gray-700 mb-1">전화번호</label>
					<input
						id="phone"
						type="tel"
						value={phone}
						oninput={handlePhoneInput}
						placeholder="010-1234-5678"
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
						disabled={loading}
					/>
				</div>

				{#if errorMsg}
					<div class="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{errorMsg}</div>
				{/if}

				<button
					type="submit"
					disabled={loading}
					class="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
				>
					{loading ? '로그인 중...' : '로그인'}
				</button>
			</form>
		</div>
	</div>
</div>
