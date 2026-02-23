<script lang="ts">
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { api, ApiError } from '$lib/api/client';
	import { setAuth, isLoggedIn, userRole } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/toast';
	import type { LoginResponse } from '$lib/types';
	import { onMount } from 'svelte';

	let email = $state('');
	let phone = $state('');
	let loading = $state(false);
	let errorMsg = $state('');

	onMount(() => {
		if ($isLoggedIn) {
			goto($userRole === 'facilitator' ? `${base}/facilitator` : `${base}/student`);
		}
	});

	async function handleLogin() {
		if (!email.trim() || !phone.trim()) {
			errorMsg = '이메일과 전화번호를 입력해주세요.';
			return;
		}

		loading = true;
		errorMsg = '';

		try {
			const rawPhone = phone.replace(/\D/g, '');
			const data = await api.post<LoginResponse>('/api/v1/auth/login', {
				email: email.trim(),
				phone: rawPhone
			});

			setAuth(data);
			addToast(`${data.name}님, 환영합니다!`, 'success');

			if (data.role === 'facilitator') {
				goto(`${base}/facilitator`);
			} else {
				goto(`${base}/student`);
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

			<div class="space-y-4">
				<div>
					<label for="email" class="block text-sm font-medium text-gray-700 mb-1">이메일</label>
					<input
						id="email"
						type="email"
						inputmode="email"
						autocapitalize="off"
						autocomplete="email"
						bind:value={email}
						placeholder="name@example.com"
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
						disabled={loading}
					/>
				</div>

				<div>
					<label for="phone" class="block text-sm font-medium text-gray-700 mb-1">전화번호</label>
					<input
						id="phone"
						type="tel"
						inputmode="tel"
						autocomplete="tel"
						bind:value={phone}
						placeholder="010-1234-5678"
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
						disabled={loading}
					/>
				</div>

				{#if errorMsg}
					<div class="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{errorMsg}</div>
				{/if}

				<button
					type="button"
					on:click={handleLogin}
					disabled={loading}
					class="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
				>
					{loading ? '로그인 중...' : '로그인'}
				</button>
			</div>
		</div>
	</div>
</div>
