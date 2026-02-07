<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';
	import { isLoggedIn, activeCourses } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/toast';
	import { QUEST_TYPE_LABELS } from '$lib/types';
	import type { CourseScoreSummary } from '$lib/types';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';

	let loading = $state(true);
	let data = $state<CourseScoreSummary | null>(null);
	let courseId = $derived(page.params.courseId);
	let courseName = $derived(
		$activeCourses.find((c) => String(c.legacy_course_id) === courseId)?.name || '과정'
	);

	onMount(async () => {
		if (!$isLoggedIn) {
			goto('/login');
			return;
		}
		await loadScores();
	});

	async function loadScores() {
		loading = true;
		try {
			data = await api.get<CourseScoreSummary>(`/api/v1/student/courses/${courseId}/scores`);
		} catch (err) {
			addToast('점수 데이터를 불러올 수 없습니다.', 'error');
		} finally {
			loading = false;
		}
	}

	function formatScore(score: number | null, isSubmitted: boolean): string {
		if (!isSubmitted) return '미제출';
		if (score === null) return '-';
		return String(score);
	}

	function scoreClass(isSubmitted: boolean): string {
		return isSubmitted ? 'text-gray-900' : 'text-gray-400 italic';
	}
</script>

<div class="max-w-4xl mx-auto p-6">
	<div class="mb-6">
		<button
			onclick={() => goto('/student')}
			class="text-sm text-blue-600 hover:text-blue-800 mb-2 cursor-pointer"
		>
			← 과정 목록
		</button>
		<h1 class="text-2xl font-bold text-gray-800">{courseName}</h1>
	</div>

	{#if loading}
		<LoadingSkeleton type="table" lines={5} />
	{:else if data && data.quests.length > 0}
		<div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
			<table class="w-full text-sm">
				<thead>
					<tr class="bg-gray-50 border-b border-gray-200">
						<th class="px-4 py-3 text-left font-medium text-gray-600">퀘스트</th>
						<th class="px-4 py-3 text-left font-medium text-gray-600">유형</th>
						<th class="px-4 py-3 text-left font-medium text-gray-600">제목</th>
						<th class="px-4 py-3 text-left font-medium text-gray-600">날짜</th>
						<th class="px-4 py-3 text-center font-medium text-gray-600">점수</th>
						<th class="px-4 py-3 text-center font-medium text-gray-600">상태</th>
					</tr>
				</thead>
				<tbody>
					{#each data.quests as quest, i}
						{@const score = data.scores.find((s) => s.quest_id === quest.id)}
						<tr class="{i % 2 === 0 ? 'bg-white' : 'bg-gray-50'} border-b border-gray-100">
							<td class="px-4 py-3 font-medium">#{quest.quest_number}</td>
							<td class="px-4 py-3">
								<span class="px-2 py-0.5 text-xs rounded bg-blue-50 text-blue-700">
									{QUEST_TYPE_LABELS[quest.quest_type] || quest.quest_type}
								</span>
							</td>
							<td class="px-4 py-3 text-gray-700">{quest.title || '-'}</td>
							<td class="px-4 py-3 text-gray-500">{quest.quest_date}</td>
							<td class="px-4 py-3 text-center {scoreClass(score?.is_submitted ?? false)}">
								{formatScore(score?.score ?? null, score?.is_submitted ?? false)}
							</td>
							<td class="px-4 py-3 text-center">
								{#if score?.is_submitted}
									<span class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700"
										>제출</span
									>
								{:else}
									<span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500"
										>미제출</span
									>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<div class="text-center py-12 text-gray-500">
			<p>등록된 퀘스트가 없습니다.</p>
		</div>
	{/if}
</div>
