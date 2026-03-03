<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { api } from '$lib/api/client';
	import { isLoggedIn, activeCourses, userRole } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/toast';
	import { SCORE_RULES, QUEST_TYPE_LABELS } from '$lib/types';
	import type { BonusScoreOut, CourseScoreSummary, Quest, ScoreOut, StudentRubricResponse } from '$lib/types';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';

	let loading = $state(true);
	let data = $state<CourseScoreSummary | null>(null);
	let rubricData = $state<StudentRubricResponse | null>(null);
	let courseId = $derived(page.params.courseId);
	let viewedStudentId = $derived(page.url.searchParams.get('student_id'));
	let viewedStudentName = $derived(page.url.searchParams.get('student_name'));
	let viewedStudentLabel = $derived(
		viewedStudentName?.trim() || (viewedStudentId ? `학생 ${viewedStudentId}` : '')
	);
	let courseName = $derived(
		$activeCourses.find((c) => String(c.legacy_course_id) === courseId)?.name || '과정'
	);

	async function goBack() {
		if (viewedStudentId && $userRole === 'facilitator') {
			await goto(`${base}/facilitator/courses/${courseId}`);
			return;
		}
		await goto(`${base}/student`);
	}

	// Derived metrics
	let totalQuests = $derived(data?.scores.length || 0);
	let completedQuests = $derived(data?.scores.filter((s) => s.is_submitted).length || 0);

	let completedRubrics = $derived(rubricData?.tasks.length || 0);

	let growthTemp = $derived.by(() => {
		if (!data) return 0;
		return Math.round(data.total_quest_score + data.total_bonus_score);
	});
	let growthTempProgress = $derived.by(() => Math.max(0, Math.min(100, growthTemp)));

	let passionTemp = $derived.by(() => {
		if (!data || totalQuests === 0) return 0;
		return Math.round((completedQuests / totalQuests) * 100);
	});
	let passionTempProgress = $derived.by(() => Math.max(0, Math.min(100, passionTemp)));

	let activeTab = $state<'quests' | 'rubrics' | 'bonus'>('quests');


	onMount(async () => {
		if (!$isLoggedIn) {
			goto(`${base}/login`);
			return;
		}
		if (viewedStudentId && $userRole === 'facilitator') {
			await Promise.all([loadScoresAsFacilitatorView(), loadRubricsAsFacilitatorView()]);
		} else {
			await Promise.all([loadScores(), loadRubrics()]);
		}
	});

	async function loadScores() {
		loading = true;
		try {
			const query = viewedStudentId ? `?student_id=${viewedStudentId}` : '';
			data = await api.get<CourseScoreSummary>(`/api/v1/student/courses/${courseId}/scores${query}`);
		} catch (err) {
			addToast('점수 데이터를 불러올 수 없습니다.', 'error');
		} finally {
			loading = false;
		}
	}

	async function loadScoresAsFacilitatorView() {
		loading = true;
		try {
			const studentId = Number(viewedStudentId);
			const [quests, bonusAll] = await Promise.all([
				api.get<Quest[]>(`/api/v1/facilitator/courses/${courseId}/quests`),
				api.get<BonusScoreOut[]>(`/api/v1/facilitator/courses/${courseId}/bonus-scores`)
			]);

			const questRows = await Promise.all(
				quests
					.sort((a, b) => a.quest_number - b.quest_number)
					.map(async (q) => {
						const rows = await api.get<ScoreOut[]>(`/api/v1/facilitator/quests/${q.id}/students`);
						const mine = rows.find((r) => r.legacy_student_id === studentId);
						return {
							quest_id: q.id,
							quest_number: q.quest_number,
							quest_type: q.quest_type,
							title: q.title,
							quest_date: q.quest_date,
							score: mine?.score ?? null,
							is_submitted: mine?.is_submitted ?? false
						};
					})
			);

			const bonus = bonusAll.filter((b) => b.legacy_student_id === studentId);
			const totalQuest = questRows.reduce((sum, r) => sum + (r.score ?? 0), 0);
			const totalBonus = bonus.reduce((sum, b) => sum + b.score, 0);

			data = {
				legacy_course_id: Number(courseId),
				course_name: courseName,
				scores: questRows,
				bonus_scores: bonus,
				total_quest_score: totalQuest,
				total_bonus_score: totalBonus,
				total_score: totalQuest + totalBonus
			};
		} catch {
			addToast('점수 데이터를 불러올 수 없습니다.', 'error');
		} finally {
			loading = false;
		}
	}

	async function loadRubrics() {
		try {
			const query = viewedStudentId ? `?student_id=${viewedStudentId}` : '';
			rubricData = await api.get<StudentRubricResponse>(`/api/v1/student/courses/${courseId}/rubrics${query}`);
		} catch (err) {
			console.error('Failed to load rubrics:', err);
		}
	}

	async function loadRubricsAsFacilitatorView() {
		try {
			rubricData = await api.get<StudentRubricResponse>(
				`/api/v1/facilitator/courses/${courseId}/students/${viewedStudentId}/rubrics`
			);
		} catch (err) {
			console.error('Failed to load rubrics:', err);
		}
	}

	function questTypeBadgeClass(questType: string): string {
		switch (questType) {
			case 'sub':
				return 'bg-cyan-100 text-cyan-900 border-cyan-300';
			case 'main':
				return 'bg-indigo-100 text-indigo-900 border-indigo-300';
			case 'datathon':
				return 'bg-emerald-100 text-emerald-900 border-emerald-300';
			case 'ideathon':
				return 'bg-fuchsia-100 text-fuchsia-900 border-fuchsia-300';
			default:
				return 'bg-gray-100 text-gray-800 border-gray-300';
		}
	}

	function getQuestMaxScore(questType: string, score: number | null): number {
		const baseMax = (SCORE_RULES[questType] || SCORE_RULES['main']).max;
		if (score === null) return baseMax;
		return baseMax;
	}

	function scoreVisualClass(score: number | null, isSubmitted: boolean, questType: string): string {
		if (!isSubmitted) return 'bg-gray-100 text-gray-400 border-gray-200';
		if (score === null) return 'bg-gray-100 text-gray-500 border-gray-200';
		if (questType === 'main') {
			if (score >= 5) return 'bg-indigo-100 text-indigo-900 border-indigo-300';
			if (score >= 4) return 'bg-emerald-100 text-emerald-900 border-emerald-300';
			if (score >= 3) return 'bg-lime-100 text-lime-900 border-lime-300';
			if (score >= 2) return 'bg-amber-100 text-amber-900 border-amber-300';
			if (score >= 1) return 'bg-orange-100 text-orange-900 border-orange-300';
			return 'bg-red-100 text-red-900 border-red-300';
		}
		const max = getQuestMaxScore(questType, score);
		const ratio = max > 0 ? score / max : 0;
		if (ratio <= 0) return 'bg-red-100 text-red-900 border-red-300';
		if (ratio < 0.4) return 'bg-orange-100 text-orange-900 border-orange-300';
		if (ratio < 0.75) return 'bg-yellow-100 text-yellow-900 border-yellow-300';
		if (ratio < 1) return 'bg-lime-100 text-lime-900 border-lime-300';
		return 'bg-emerald-200 text-emerald-950 border-emerald-400';
	}

	function scoreLabel(score: number | null, isSubmitted: boolean, questType: string): string {
		if (!isSubmitted) return '미제출';
		if (score === null) return '-';
		if (questType === 'main') return String(score);
		const max = getQuestMaxScore(questType, score);
		if (score > max) return `${score}점`;
		return `${score} / ${max}`;
	}

	function formatDate(dateStr: string): string {
		try {
			return new Date(dateStr).toLocaleDateString('ko-KR');
		} catch {
			return dateStr;
		}
	}

	function nodeStarCount(score: number): number {
		return Math.max(0, Math.min(3, Math.round(score)));
	}

	function displayTaskTitle(taskTitle: string): string {
		return taskTitle
			.replace(/^[A-Z0-9]+(?:-[A-Z0-9]+)*\.\s*/i, '')
			.replace(/^프로젝트\s*[:：]?\s*/i, '')
			.replace(/^\d+\.\s*/, '')
			.trim();
	}

	function needsProjectPrefix(taskTitle: string): boolean {
		return !/프로젝트/i.test(taskTitle);
	}
</script>

<div class="max-w-4xl mx-auto px-3 py-6 sm:px-6">
	<div class="mb-6">
		<div class="mb-3 flex items-center justify-between gap-2">
			<button
				type="button"
				onclick={goBack}
				class="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 cursor-pointer"
			>
				<span aria-hidden="true">←</span>
				뒤로가기
			</button>
			{#if viewedStudentLabel}
				<span class="inline-flex items-center rounded-md border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
					{viewedStudentLabel} 페이지
				</span>
			{/if}
		</div>
		<h1 class="text-2xl font-bold text-gray-800">{courseName}</h1>
	</div>

	{#if loading}
		<LoadingSkeleton type="table" lines={5} />
	{:else if data}
		<!-- Dashboard Header: Temperatures & Metrics -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
			<!-- Left: Temperatures (Impressive) -->
			<div class="space-y-4">
				<!-- Growth Temp -->
				<div class="bg-gradient-to-r from-red-50 to-white rounded-xl border border-red-100 p-6 relative overflow-hidden">
					<div class="flex justify-between items-end mb-2 relative z-10">
						<div>
							<h3 class="text-red-800 font-bold text-lg flex items-center gap-2">
								❤️ 성장 온도
							</h3>
							<p class="text-red-600 text-xs mt-1">퀘스트 점수 + 비정규 점수 합산 지표입니다.</p>
						</div>
						<span class="text-4xl font-black text-red-600">{growthTemp}°C</span>
					</div>
					<div class="w-full bg-red-100 rounded-full h-4 mt-2 relative z-10">
						<div 
							class="bg-gradient-to-r from-red-400 to-red-600 h-4 rounded-full transition-all duration-1000 shadow-sm" 
							style="width: {growthTempProgress}%"
						></div>
					</div>
					<!-- Background Deco -->
					<div class="absolute -right-6 -bottom-6 text-red-100 opacity-50">
						<svg width="120" height="120" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" /></svg>
					</div>
				</div>

				<!-- Passion Temp -->
				<div class="bg-gradient-to-r from-orange-50 to-white rounded-xl border border-orange-100 p-6 relative overflow-hidden">
					<div class="flex justify-between items-end mb-2 relative z-10">
						<div>
							<h3 class="text-orange-800 font-bold text-lg flex items-center gap-2">
								🔥 열정 온도
							</h3>
							<p class="text-orange-600 text-xs mt-1">전체 퀘스트 제출률 지표입니다.</p>
						</div>
						<span class="text-4xl font-black text-orange-500">{passionTemp}°C</span>
					</div>
					<div class="w-full bg-orange-100 rounded-full h-4 mt-2 relative z-10">
						<div 
							class="bg-gradient-to-r from-orange-400 to-orange-600 h-4 rounded-full transition-all duration-1000 shadow-sm" 
							style="width: {passionTempProgress}%"
						></div>
					</div>
					<!-- Background Deco -->
					<div class="absolute -right-6 -bottom-6 text-orange-100 opacity-50">
						<svg width="120" height="120" viewBox="0 0 24 24" fill="currentColor"><path d="M13.5 10c0-2.21-1.79-4-4-4s-4 1.79-4 4c0 .3.03.6.09.88.07-.02.14-.04.22-.04.83 0 1.5.67 1.5 1.5 0 .83-.67 1.5-1.5 1.5-.26 0-.5-.07-.72-.19-.4.92-.79 2.15-.79 3.35 0 2.76 2.24 5 5 5s5-2.24 5-5c0-2.3-1.63-4.25-3.8-4.82zM15 2c0 5 4 8 4 11 0 4.42-3.58 8-8 8S3 17.42 3 13c0-3 2-5 2-5s.5-.5 1.5 0c1 .5 2 2 2 2s-.5-4 2.5-6 3-2 4-2z" /></svg>
					</div>
				</div>
			</div>

			<!-- Right: Metric Cards -->
			<div class="grid grid-cols-2 gap-4">
				<div class="bg-white rounded-xl border border-gray-200 p-5 flex flex-col justify-center items-center text-center">
					<div class="text-gray-500 text-sm font-medium mb-2">퀘스트 진행률</div>
					<div class="relative w-24 h-24 flex items-center justify-center">
						<svg class="w-full h-full transform -rotate-90">
							<circle cx="48" cy="48" r="40" stroke="currentColor" stroke-width="8" fill="transparent" class="text-gray-100" />
							<circle 
								cx="48" cy="48" r="40" 
								stroke="currentColor" stroke-width="8" 
								fill="transparent" 
								stroke-dasharray={2 * Math.PI * 40} 
								stroke-dashoffset={2 * Math.PI * 40 * (1 - (totalQuests > 0 ? completedQuests / totalQuests : 0))} 
								class="text-blue-500 transition-all duration-1000" 
							/>
						</svg>
						<span class="absolute text-xl font-bold text-gray-700">
							{totalQuests > 0 ? Math.round(completedQuests/totalQuests*100) : 0}%
						</span>
					</div>
					<p class="text-xs text-gray-400 mt-2">{completedQuests} / {totalQuests} 완료</p>
				</div>

				<!-- Rubric Progress -->
				<div class="bg-white rounded-xl border border-gray-200 p-5 flex flex-col justify-center items-center text-center">
					<div class="text-gray-500 text-sm font-medium mb-2">노드 진행률</div>
					<div class="relative w-24 h-24 flex items-center justify-center">
						<svg class="w-full h-full transform -rotate-90">
							<circle cx="48" cy="48" r="40" stroke="currentColor" stroke-width="8" fill="transparent" class="text-gray-100" />
							<circle 
								cx="48" cy="48" r="40" 
								stroke="currentColor" stroke-width="8" 
								fill="transparent" 
								stroke-dasharray={2 * Math.PI * 40} 
								stroke-dashoffset="0" 
								class="text-purple-500 transition-all duration-1000" 
							/>
						</svg>
						<span class="absolute text-xl font-bold text-gray-700">
							{completedRubrics}건
						</span>
					</div>
					<p class="text-xs text-gray-400 mt-2">평가 완료</p>
				</div>

				<div class="bg-white rounded-xl border border-gray-200 p-5 flex flex-col justify-center col-span-2">
					<p class="text-sm text-gray-500 font-medium mb-1">총 획득 점수</p>
					<span class="text-4xl font-bold text-gray-800 mb-1">{data.total_score}</span>
					<div class="text-xs text-gray-400 flex flex-col gap-1">
						<span>퀘스트: <span class="text-blue-600 font-medium">{data.total_quest_score}</span></span>
						<span>비정규: <span class="text-amber-600 font-medium">+{data.total_bonus_score}</span></span>
					</div>
				</div>
			</div>
		</div>

		<!-- Tabbed Score View -->
		<div class="bg-white rounded-lg border border-gray-200 overflow-hidden min-h-[500px]">
			<!-- Tab Headers -->
			<div class="flex border-b border-gray-200">
				<button 
					class="px-6 py-4 text-sm font-medium transition-colors border-b-2 {activeTab === 'quests' ? 'border-blue-600 text-blue-600 bg-blue-50/50' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'} cursor-pointer"
					onclick={() => activeTab = 'quests'}
				>
					퀘스트 점수
				</button>
				<button 
					class="px-6 py-4 text-sm font-medium transition-colors border-b-2 {activeTab === 'rubrics' ? 'border-purple-600 text-purple-600 bg-purple-50/50' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'} cursor-pointer"
					onclick={() => activeTab = 'rubrics'}
				>
					노드 점수
				</button>
				<button 
					class="px-6 py-4 text-sm font-medium transition-colors border-b-2 {activeTab === 'bonus' ? 'border-amber-600 text-amber-600 bg-amber-50/50' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'} cursor-pointer"
					onclick={() => activeTab = 'bonus'}
				>
					비정규 점수
					{#if data.bonus_scores.length > 0}
						<span class="ml-2 bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full text-xs">{data.bonus_scores.length}</span>
					{/if}
				</button>
			</div>

			<!-- Tab Content -->
			<div class="p-0">
				<!-- Tab: Quests -->
				{#if activeTab === 'quests'}
					{#if data.scores.length > 0}
					<div class="overflow-x-auto">
						<table class="w-full text-sm min-w-[680px]">
							<thead class="bg-gray-50">
								<tr>
									<th class="px-4 py-2.5 text-left font-medium text-gray-600">퀘스트</th>
									<th class="px-4 py-2.5 text-left font-medium text-gray-600">유형</th>
									<th class="px-4 py-2.5 text-left font-medium text-gray-600">제목</th>
									<th class="px-4 py-2.5 text-left font-medium text-gray-600">날짜</th>
									<th class="px-4 py-2.5 text-center font-medium text-gray-600">점수</th>
									<th class="px-4 py-2.5 text-center font-medium text-gray-600">상태</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								{#each data.scores as row}
									<tr class="hover:bg-gray-50 transition-colors">
										<td class="px-4 py-2.5 font-medium text-gray-900">#{row.quest_number}</td>
										<td class="px-4 py-2.5">
											<span class={`px-2 py-1 text-xs rounded border ${questTypeBadgeClass(row.quest_type)}`}>
												{QUEST_TYPE_LABELS[row.quest_type] || row.quest_type}
											</span>
										</td>
										<td class="px-4 py-2.5 text-gray-700 font-medium">{row.title || '-'}</td>
										<td class="px-4 py-2.5 text-gray-500">{row.quest_date}</td>
										<td class="px-4 py-2.5 text-center">
											<span class={`inline-flex items-center rounded-md border px-2 py-1 text-xs font-semibold ${scoreVisualClass(row.score, row.is_submitted, row.quest_type)}`}>
												{scoreLabel(row.score, row.is_submitted, row.quest_type)}
											</span>
										</td>
										<td class="px-4 py-2.5 text-center">
											{#if row.is_submitted}
												<span class="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">제출됨</span>
											{:else}
												<span class="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-400">미제출</span>
											{/if}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
					{:else}
						<div class="text-center py-20 text-gray-500">
							<p>등록된 퀘스트가 없습니다.</p>
						</div>
					{/if}
				{/if}

				{#if activeTab === 'rubrics'}
					{#if rubricData && rubricData.tasks.length > 0}
						<div class="divide-y divide-gray-100">
							{#each rubricData.tasks as task}
								<div class="p-3">
									<div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between bg-purple-50/40 border border-purple-100 rounded-lg px-3 py-2.5">
										<h4 class="font-semibold text-gray-800 text-base sm:text-lg flex items-center gap-2">
											<span class="w-1.5 h-5 bg-purple-600 rounded-full"></span>
											{needsProjectPrefix(displayTaskTitle(task.task_title)) ? '프로젝트: ' : ''}{displayTaskTitle(task.task_title)}
										</h4>
										<div class="flex items-center gap-2">
											<div class="flex items-center gap-1" aria-label={`휴먼 점수 ${nodeStarCount(task.total_human)}점`}>
												{#each [0, 1, 2] as star}
													<span class={`text-xl leading-none ${star < nodeStarCount(task.total_human) ? 'text-amber-400' : 'text-gray-300'}`}>★</span>
												{/each}
											</div>
											<span class="text-xs font-semibold text-gray-600">{nodeStarCount(task.total_human)}점</span>
										</div>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div class="text-center py-20 text-gray-500 bg-gray-50/50">
							<p class="mb-2">노드 점수 데이터가 없습니다.</p>
							<p class="text-sm text-gray-400">아직 평가가 진행되지 않았거나 데이터가 연동되지 않았습니다.</p>
						</div>
					{/if}
				{/if}

				<!-- Tab: Bonus -->
				{#if activeTab === 'bonus'}
					{#if data.bonus_scores.length > 0}
					<div class="overflow-x-auto">
						<table class="w-full text-sm min-w-[720px]">
							<thead class="bg-amber-50/50">
								<tr>
									<th class="px-6 py-3 text-left font-medium text-amber-900/60">카테고리</th>
									<th class="px-6 py-3 text-left font-medium text-amber-900/60">상세 사유</th>
									<th class="px-6 py-3 text-center font-medium text-amber-900/60">점수</th>
									<th class="px-6 py-3 text-left font-medium text-amber-900/60">부여자</th>
									<th class="px-6 py-3 text-left font-medium text-amber-900/60">날짜</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								{#each data.bonus_scores as bonus}
									<tr class="hover:bg-amber-50/30 transition-colors">
										<td class="px-6 py-4 text-gray-800 font-medium">{bonus.category || '-'}</td>
										<td class="px-6 py-4 text-gray-600">{bonus.reason || '-'}</td>
										<td class="px-6 py-4 text-center font-bold text-amber-600">+{bonus.score}</td>
										<td class="px-6 py-4 text-gray-500">{bonus.given_by_name}</td>
										<td class="px-6 py-4 text-gray-400 text-xs">{formatDate(bonus.given_at)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
					{:else}
						<div class="text-center py-20 text-gray-500">
							<p>비정규 점수 내역이 없습니다.</p>
						</div>
					{/if}
				{/if}
			</div>
		</div>
	{:else}
		<div class="text-center py-12 text-gray-500">
			<p>점수 데이터를 불러올 수 없습니다.</p>
		</div>
	{/if}
</div>
