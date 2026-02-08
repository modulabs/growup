<script lang="ts">
	import { onMount } from 'svelte';
	import { isLoggedIn, userRole } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';

	onMount(() => {
		if (!$isLoggedIn) {
			goto(`${base}/login`);
		} else if ($userRole === 'facilitator') {
			goto(`${base}/facilitator`);
		} else {
			goto(`${base}/student`);
		}
	});
</script>

<div class="flex items-center justify-center min-h-screen">
	<div class="animate-pulse text-gray-400">로딩 중...</div>
</div>
