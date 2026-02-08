<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { api } from '$lib/api/client';
	import { isLoggedIn, userRole } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/toast';
	import type { Course } from '$lib/types';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';

	let loading = $state(true);
	let syncing = $state(false);
	let courses = $state<Course[]>([]);
	let activeTab = $state<'favorites' | 'all'>('favorites');

	let favoriteCourses = $derived(
		[...courses].filter((c) => c.is_favorite).sort((a, b) => a.name.localeCompare(b.name))
	);

	let allCourses = $derived(
		[...courses].sort((a, b) => {
			if (a.is_favorite !== b.is_favorite) return a.is_favorite ? -1 : 1;
			return a.name.localeCompare(b.name);
		})
	);

	let displayedCourses = $derived(activeTab === 'favorites' ? favoriteCourses : allCourses);

	// Default to 'all' if no favorites exist
	$effect(() => {
		if (!loading && favoriteCourses.length === 0) {
			activeTab = 'all';
		}
	});

	onMount(async () => {
		if (!$isLoggedIn) { goto(`${base}/login`); return; }
		if ($userRole !== 'facilitator') { goto(`${base}/student`); return; }
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

	async function toggleFavorite(e: Event, courseId: number) {
		e.stopPropagation();
		try {
			const res = await api.post<{ is_favorite: boolean }>(`/api/v1/facilitator/courses/${courseId}/favorite`);
			courses = courses.map((c) =>
				c.legacy_course_id === courseId ? { ...c, is_favorite: res.is_favorite } : c
			);
		} catch (err) {
			addToast('즐겨찾기 변경에 실패했습니다.', 'error');
		}
	}
</script>

<div class="max-w-6xl mx-auto p-6">
	<div class="flex items-center justify-between mb-4">
		<h1 class="text-2xl font-bold text-gray-800">과정 관리</h1>
		<button
			onclick={syncCourses}
			disabled={syncing}
			class="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors cursor-pointer"
		>
			{syncing ? '동기화 중...' : '과정 동기화'}
		</button>
	</div>

	{#if !loading && courses.length > 0}
		<div class="flex gap-1 mb-6 border-b border-gray-200">
			<button
				onclick={() => (activeTab = 'favorites')}
				class="flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer {activeTab === 'favorites'
					? 'border-yellow-400 text-yellow-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
			>
				<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
					<path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
				</svg>
				내 과정
				{#if favoriteCourses.length > 0}
					<span class="px-1.5 py-0.5 text-xs rounded-full {activeTab === 'favorites' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-500'}">{favoriteCourses.length}</span>
				{/if}
			</button>
			<button
				onclick={() => (activeTab = 'all')}
				class="flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer {activeTab === 'all'
					? 'border-blue-500 text-blue-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
			>
				전체 보기
				<span class="px-1.5 py-0.5 text-xs rounded-full {activeTab === 'all' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'}">{courses.length}</span>
			</button>
		</div>
	{/if}

	{#if loading}
		<LoadingSkeleton type="card" lines={4} />
	{:else if courses.length === 0}
		<div class="text-center py-12 text-gray-500">
			<p class="mb-4">등록된 과정이 없습니다.</p>
			<p class="text-sm">위의 "과정 동기화" 버튼을 눌러 Legacy 시스템에서 과정을 가져오세요.</p>
		</div>
	{:else if displayedCourses.length === 0}
		<div class="text-center py-12 text-gray-500">
			<p class="mb-2">즐겨찾기한 과정이 없습니다.</p>
			<p class="text-sm">과정 카드의 ★ 버튼으로 즐겨찾기를 추가하거나, "전체 보기" 탭에서 과정을 확인하세요.</p>
		</div>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each displayedCourses as course}
				<div class="relative bg-white rounded-lg border border-gray-200 hover:shadow-md hover:border-blue-300 transition-all">
					<button
						class="w-full p-5 text-left cursor-pointer"
						onclick={() => goto(`${base}/facilitator/courses/${course.legacy_course_id}`)}
					>
						<h2 class="font-semibold text-gray-800 mb-2 pr-8">{course.name}</h2>
						<div class="flex flex-wrap gap-2 text-xs">
							{#if course.cohort}
								<span class="px-2 py-0.5 bg-purple-50 text-purple-600 rounded">{course.cohort}</span>
							{/if}
							{#if course.category}
								<span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded">{course.category}</span>
							{/if}
							{#if course.is_active}
								<span class="px-2 py-0.5 bg-green-50 text-green-600 rounded">활성</span>
							{/if}
						</div>
					</button>
					<button
						class="absolute top-3 right-3 p-1.5 rounded-full hover:bg-yellow-50 transition-colors cursor-pointer"
						onclick={(e) => toggleFavorite(e, course.legacy_course_id)}
						title={course.is_favorite ? '즐겨찾기 해제' : '즐겨찾기 추가'}
					>
						{#if course.is_favorite}
							<svg class="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
								<path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
							</svg>
						{:else}
							<svg class="w-5 h-5 text-gray-300 hover:text-yellow-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 20 20">
								<path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
							</svg>
						{/if}
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>
