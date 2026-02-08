<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
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
			goto(`${base}/login`);
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
			onclick={() => goto(`${base}/student`)}
			class="text-sm text-blue-600 hover:text-blue-800 mb-2 cursor-pointer"
		>
			&larr; 과정 목록
		</button>
		<h1 class="text-2xl font-bold text-gray-800">{courseName}</h1>
	</div>

	{#if loading}
		<LoadingSkeleton type="table" lines={5} />
	{:else if data}
		<!-- Quest Scores Table -->
		{#if data.scores.length > 0}
			<div class="bg-white rounded-lg border border-gray-200 overflow-hidden mb-6">
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
						{#each data.scores as row, i}
							<tr class="{i % 2 === 0 ? 'bg-white' : 'bg-gray-50'} border-b border-gray-100">
								<td class="px-4 py-3 font-medium">#{row.quest_number}</td>
								<td class="px-4 py-3">
									<span class="px-2 py-0.5 text-xs rounded bg-blue-50 text-blue-700">
										{QUEST_TYPE_LABELS[row.quest_type] || row.quest_type}
									</span>
								</td>
								<td class="px-4 py-3 text-gray-700">{row.title || '-'}</td>
								<td class="px-4 py-3 text-gray-500">{row.quest_date}</td>
								<td class="px-4 py-3 text-center {scoreClass(row.is_submitted)}">
									{formatScore(row.score, row.is_submitted)}
								</td>
								<td class="px-4 py-3 text-center">
									{#if row.is_submitted}
										<span class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">제출</span>
									{:else}
										<span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">미제출</span>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else}
			<div class="text-center py-8 text-gray-500 mb-6">
				<p>등록된 퀘스트가 없습니다.</p>
			</div>
		{/if}

		<!-- Bonus Scores -->
		{#if data.bonus_scores.length > 0}
			<div class="bg-white rounded-lg border border-gray-200 overflow-hidden mb-6">
				<div class="px-4 py-3 bg-amber-50 border-b border-gray-200">
					<h3 class="font-medium text-amber-800">비정규 점수</h3>
				</div>
				<table class="w-full text-sm">
					<thead>
						<tr class="bg-gray-50 border-b border-gray-200">
							<th class="px-4 py-2 text-left font-medium text-gray-600">사유</th>
							<th class="px-4 py-2 text-center font-medium text-gray-600">점수</th>
							<th class="px-4 py-2 text-left font-medium text-gray-600">부여자</th>
							<th class="px-4 py-2 text-left font-medium text-gray-600">날짜</th>
						</tr>
					</thead>
					<tbody>
						{#each data.bonus_scores as bonus, i}
							<tr class="{i % 2 === 0 ? 'bg-white' : 'bg-gray-50'} border-b border-gray-100">
								<td class="px-4 py-2 text-gray-700">{bonus.reason || '-'}</td>
								<td class="px-4 py-2 text-center font-medium text-amber-700">+{bonus.score}</td>
								<td class="px-4 py-2 text-gray-500">{bonus.given_by_name}</td>
								<td class="px-4 py-2 text-gray-400 text-xs">{bonus.given_at}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}

		<!-- Total Summary -->
		<div class="bg-white rounded-lg border border-gray-200 p-5">
			<h3 class="font-medium text-gray-800 mb-3">총점 요약</h3>
			<div class="grid grid-cols-3 gap-4 text-center">
				<div class="bg-blue-50 rounded-lg p-3">
					<div class="text-xs text-blue-600 mb-1">퀘스트 점수</div>
					<div class="text-xl font-bold text-blue-800">{data.total_quest_score}</div>
				</div>
				<div class="bg-amber-50 rounded-lg p-3">
					<div class="text-xs text-amber-600 mb-1">비정규 점수</div>
					<div class="text-xl font-bold text-amber-800">+{data.total_bonus_score}</div>
				</div>
				<div class="bg-green-50 rounded-lg p-3">
					<div class="text-xs text-green-600 mb-1">총점</div>
					<div class="text-xl font-bold text-green-800">{data.total_score}</div>
				</div>
			</div>
		</div>
	{:else}
		<div class="text-center py-12 text-gray-500">
			<p>점수 데이터를 불러올 수 없습니다.</p>
		</div>
	{/if}
</div>
