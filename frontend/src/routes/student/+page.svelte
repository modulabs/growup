<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isLoggedIn, userRole, activeCourses } from '$lib/stores/auth';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';

	onMount(() => {
		if (!$isLoggedIn) goto('/login');
		if ($userRole !== 'student') goto('/facilitator');
	});
</script>

<div class="max-w-4xl mx-auto p-6">
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
					onclick={() => goto(`/student/${course.legacy_course_id}`)}
				>
					<h2 class="font-semibold text-gray-800 mb-1">{course.name}</h2>
					<div class="flex gap-2 text-xs">
						<span class="px-2 py-0.5 bg-blue-50 text-blue-600 rounded">{course.cohort}</span>
						<span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded">{course.category}</span>
					</div>
				</button>
			{/each}
		</div>
	{/if}
</div>
