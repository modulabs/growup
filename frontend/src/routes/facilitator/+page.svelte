<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';
	import { isLoggedIn, userRole } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/toast';
	import type { Course } from '$lib/types';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';

	let loading = $state(true);
	let syncing = $state(false);
	let courses = $state<Course[]>([]);

	onMount(async () => {
		if (!$isLoggedIn) { goto('/login'); return; }
		if ($userRole !== 'facilitator') { goto('/student'); return; }
		await loadCourses();
	});

	async function loadCourses() {
		loading = true;
		try {
			courses = await api.get<Course[]>('/api/v1/facilitator/courses');
		} catch (err) {
			addToast('과정 목록을 불러올 수 없습니다.', 'error');
		} finally {
			loading = false;
		}
	}

	async function syncCourses() {
		syncing = true;
		try {
			courses = await api.post<Course[]>('/api/v1/admin/sync/courses');
			addToast('과정 목록이 동기화되었습니다.', 'success');
		} catch (err) {
			addToast('과정 동기화에 실패했습니다.', 'error');
		} finally {
			syncing = false;
		}
	}
</script>

<div class="max-w-6xl mx-auto p-6">
	<div class="flex items-center justify-between mb-6">
		<h1 class="text-2xl font-bold text-gray-800">과정 관리</h1>
		<button
			onclick={syncCourses}
			disabled={syncing}
			class="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors cursor-pointer"
		>
			{syncing ? '동기화 중...' : '과정 동기화'}
		</button>
	</div>

	{#if loading}
		<LoadingSkeleton type="card" lines={4} />
	{:else if courses.length === 0}
		<div class="text-center py-12 text-gray-500">
			<p class="mb-4">등록된 과정이 없습니다.</p>
			<p class="text-sm">위의 "과정 동기화" 버튼을 눌러 Legacy 시스템에서 과정을 가져오세요.</p>
		</div>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each courses as course}
				<button
					class="bg-white rounded-lg border border-gray-200 p-5 text-left hover:shadow-md hover:border-blue-300 transition-all cursor-pointer"
					onclick={() => goto(`/facilitator/courses/${course.legacy_course_id}`)}
				>
					<h2 class="font-semibold text-gray-800 mb-2">{course.name}</h2>
					<div class="flex flex-wrap gap-2 text-xs">
						<span class="px-2 py-0.5 bg-purple-50 text-purple-600 rounded">{course.cohort}</span>
						<span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded">{course.category}</span>
						{#if course.is_active}
							<span class="px-2 py-0.5 bg-green-50 text-green-600 rounded">활성</span>
						{/if}
					</div>
				</button>
			{/each}
		</div>
	{/if}
</div>
