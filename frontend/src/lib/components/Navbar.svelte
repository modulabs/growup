<script lang="ts">
	import { base } from '$app/paths';
	import { currentUser, logout } from '$lib/stores/auth';

	function handleLogout() {
		logout();
		window.location.href = `${base}/login`;
	}

	const roleBadge: Record<string, string> = {
		student: '학생',
		facilitator: '퍼실리테이터'
	};
</script>

<nav class="bg-white border-b border-gray-200 px-4 py-3">
	<div class="max-w-6xl mx-auto flex items-center justify-between">
		<a href="{base}/" class="text-xl font-bold text-blue-600">GrowUp</a>

		{#if $currentUser}
			<div class="flex items-center gap-4">
				<span class="text-sm text-gray-600">
					{$currentUser.name}
				</span>
				<span
					class="text-xs px-2 py-0.5 rounded-full font-medium
						{$currentUser.role === 'facilitator'
						? 'bg-purple-100 text-purple-700'
						: 'bg-blue-100 text-blue-700'}"
				>
					{roleBadge[$currentUser.role] || $currentUser.role}
				</span>
				<button
					onclick={handleLogout}
					class="text-sm text-gray-500 hover:text-gray-700 cursor-pointer"
				>
					로그아웃
				</button>
			</div>
		{/if}
	</div>
</nav>
