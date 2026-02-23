<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { isLoggedIn, userRole, activeCourses } from '$lib/stores/auth';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';

	onMount(() => {
		if (!$isLoggedIn) {
			goto(`${base}/login`);
			return;
		}
		if ($userRole !== 'student') {
			goto(`${base}/facilitator`);
			return;
		}

		// Auto-redirect if student has only one course
		if ($activeCourses.length === 1) {
			goto(`${base}/student/${$activeCourses[0].legacy_course_id}`);
		}
	});
</script>

<div class="max-w-4xl mx-auto px-3 py-6 sm:px-6">
	<h1 class="text-2xl font-bold text-gray-800 mb-6">내 수강 과정</h1>

	{#if $activeCourses.length === 0}
		<div class="text-center py-12 text-gray-500">
			<p>등록된 수강 과정이 없습니다.</p>
		</div>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2">
			{#each $activeCourses as course}
				<button
					class="bg-white rounded-lg border border-gray-200 p-5 text-left hover:shadow-md hover:border-blue-300 transition-all cursor-pointer"
					onclick={() => goto(`${base}/student/${course.legacy_course_id}`)}
				>
					<h2 class="font-semibold text-gray-800">{course.name}</h2>
				</button>
			{/each}
		</div>
	{/if}
</div>
