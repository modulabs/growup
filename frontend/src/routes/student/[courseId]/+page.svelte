<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { api } from '$lib/api/client';
	import { isLoggedIn, activeCourses } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/toast';
	import { SCORE_RULES, QUEST_TYPE_LABELS } from '$lib/types';
	import type { CourseScoreSummary, StudentRubricResponse } from '$lib/types';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';

	let loading = $state(true);
	let data = $state<CourseScoreSummary | null>(null);
	let rubricData = $state<StudentRubricResponse | null>(null);
	let courseId = $derived(page.params.courseId);
	let courseName = $derived(
		$activeCourses.find((c) => String(c.legacy_course_id) === courseId)?.name || '과정'
	);

	// Derived metrics
	let totalQuests = $derived(data?.scores.length || 0);
	let completedQuests = $derived(data?.scores.filter((s) => s.is_submitted).length || 0);

	let growthTemp = $derived.by(() => {
		if (!data || totalQuests === 0) return 0;
		// Participation (60%)
		const participation = (completedQuests / totalQuests) * 100;
		// Quality (40%)
		let maxPossibleScore = 0;
		data.scores.forEach((s) => {
			const rule = SCORE_RULES[s.quest_type] || SCORE_RULES['main'];
			maxPossibleScore += rule.max;
		});
		const quality = maxPossibleScore > 0 ? (data.total_quest_score / maxPossibleScore) * 100 : 0;
		return Math.round(participation * 0.6 + quality * 0.4);
	});

	let passionTemp = $derived.by(() => {
		if (!data) return 0;
		const now = new Date();
		const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);
		const recentQuests = data.scores.filter((s) => {
			const qDate = new Date(s.quest_date);
			return qDate >= twoWeeksAgo && qDate <= now;
		});
		if (recentQuests.length === 0) return 36.5;
		const recentSubmitted = recentQuests.filter((s) => s.is_submitted).length;
		return Math.round((recentSubmitted / recentQuests.length) * 100);
	});

	let activeTab = $state<'quests' | 'rubrics' | 'bonus'>('quests');

	onMount(async () => {
		if (!$isLoggedIn) {
			goto(`${base}/login`);
			return;
		}
		await Promise.all([loadScores(), loadRubrics()]);
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

	async function loadRubrics() {
		try {
			rubricData = await api.get<StudentRubricResponse>(`/api/v1/student/courses/${courseId}/rubrics`);
		} catch (err) {
			console.error('Failed to load rubrics:', err);
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

	function formatDate(dateStr: string): string {
		try {
			return new Date(dateStr).toLocaleDateString('ko-KR');
		} catch {
			return dateStr;
		}
	}
</script>

<div class="max-w-4xl mx-auto p-6">
	<div class="mb-6">
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
								🔥 성장 온도
							</h3>
							<p class="text-red-600 text-xs mt-1">꾸준한 참여와 성취의 결과입니다.</p>
						</div>
						<span class="text-4xl font-black text-red-600">{growthTemp}°C</span>
					</div>
					<div class="w-full bg-red-100 rounded-full h-4 mt-2 relative z-10">
						<div 
							class="bg-gradient-to-r from-red-400 to-red-600 h-4 rounded-full transition-all duration-1000 shadow-sm" 
							style="width: {growthTemp}%"
						></div>
					</div>
					<!-- Background Deco -->
					<div class="absolute -right-6 -bottom-6 text-red-100 opacity-50">
						<svg width="120" height="120" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" /></svg>
					</div>
				</div>

				<!-- Passion Temp -->
				<div class="bg-gradient-to-r from-orange-50 to-white rounded-xl border border-orange-100 p-6 relative overflow-hidden">
					<div class="flex justify-between items-end mb-2 relative z-10">
						<div>
							<h3 class="text-orange-800 font-bold text-lg flex items-center gap-2">
								❤️ 열정 온도
							</h3>
							<p class="text-orange-600 text-xs mt-1">최근 2주간의 활동 지표입니다.</p>
						</div>
						<span class="text-4xl font-black text-orange-500">{passionTemp}°C</span>
					</div>
					<div class="w-full bg-orange-100 rounded-full h-4 mt-2 relative z-10">
						<div 
							class="bg-gradient-to-r from-orange-400 to-orange-600 h-4 rounded-full transition-all duration-1000 shadow-sm" 
							style="width: {passionTemp}%"
						></div>
					</div>
					<!-- Background Deco -->
					<div class="absolute -right-6 -bottom-6 text-orange-100 opacity-50">
						<svg width="120" height="120" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" /></svg>
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

				<div class="bg-white rounded-xl border border-gray-200 p-5 flex flex-col justify-center">
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
					루브릭 평가
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
						<table class="w-full text-sm">
							<thead class="bg-gray-50">
								<tr>
									<th class="px-6 py-3 text-left font-medium text-gray-600">퀘스트</th>
									<th class="px-6 py-3 text-left font-medium text-gray-600">유형</th>
									<th class="px-6 py-3 text-left font-medium text-gray-600">제목</th>
									<th class="px-6 py-3 text-left font-medium text-gray-600">날짜</th>
									<th class="px-6 py-3 text-center font-medium text-gray-600">점수</th>
									<th class="px-6 py-3 text-center font-medium text-gray-600">상태</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								{#each data.scores as row, i}
									<tr class="hover:bg-gray-50 transition-colors">
										<td class="px-6 py-4 font-medium text-gray-900">#{row.quest_number}</td>
										<td class="px-6 py-4">
											<span class="px-2 py-1 text-xs rounded bg-blue-50 text-blue-700 border border-blue-100">
												{QUEST_TYPE_LABELS[row.quest_type] || row.quest_type}
											</span>
										</td>
										<td class="px-6 py-4 text-gray-700 font-medium">{row.title || '-'}</td>
										<td class="px-6 py-4 text-gray-500">{row.quest_date}</td>
										<td class="px-6 py-4 text-center {scoreClass(row.is_submitted)}">
											{formatScore(row.score, row.is_submitted)}
										</td>
										<td class="px-6 py-4 text-center">
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
					{:else}
						<div class="text-center py-20 text-gray-500">
							<p>등록된 퀘스트가 없습니다.</p>
						</div>
					{/if}
				{/if}

				<!-- Tab: Rubrics -->
				{#if activeTab === 'rubrics'}
					{#if rubricData && rubricData.tasks.length > 0}
						<div class="divide-y divide-gray-100">
							{#each rubricData.tasks as task}
								<div class="p-6">
									<div class="flex justify-between items-start mb-4">
										<h4 class="font-bold text-gray-800 text-lg flex items-center gap-2">
											<span class="w-1.5 h-6 bg-purple-600 rounded-full"></span>
											{task.task_title}
										</h4>
										<div class="flex gap-2">
											<div class="text-center bg-gray-100 px-3 py-1 rounded-lg">
												<div class="text-xs text-gray-500">Human</div>
												<div class="font-bold text-gray-700">{task.total_human}</div>
											</div>
											<div class="text-center bg-purple-100 px-3 py-1 rounded-lg">
												<div class="text-xs text-purple-600">GPT</div>
												<div class="font-bold text-purple-700">{task.total_gpt}</div>
											</div>
										</div>
									</div>

									{#if task.overall_feedback}
										<div class="bg-gray-50 p-4 rounded-lg text-sm text-gray-700 mb-4 border border-gray-100 leading-relaxed">
											<span class="font-bold text-gray-900 block mb-2">💡 총평</span>
											{task.overall_feedback}
										</div>
									{/if}

									<div class="overflow-x-auto border border-gray-100 rounded-lg">
										<table class="w-full text-sm">
											<thead class="bg-gray-50">
												<tr class="text-gray-500 text-xs uppercase">
													<th class="px-4 py-3 text-left w-1/3">평가 항목</th>
													<th class="px-4 py-3 text-center w-20">Human</th>
													<th class="px-4 py-3 text-center w-20">GPT</th>
													<th class="px-4 py-3 text-left">피드백</th>
												</tr>
											</thead>
											<tbody class="divide-y divide-gray-100">
												{#each task.rubric_items as item}
													<tr>
														<td class="px-4 py-3 text-gray-700 font-medium">{item.rubric_metric}</td>
														<td class="px-4 py-3 text-center text-gray-600">{item.human_score ?? '-'}</td>
														<td class="px-4 py-3 text-center text-purple-600 font-medium">{item.gpt_score ?? '-'}</td>
														<td class="px-4 py-3 text-gray-600 text-xs whitespace-pre-wrap leading-relaxed">
															{item.feedback || '-'}
														</td>
													</tr>
												{/each}
											</tbody>
										</table>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div class="text-center py-20 text-gray-500 bg-gray-50/50">
							<p class="mb-2">루브릭 평가 데이터가 없습니다.</p>
							<p class="text-sm text-gray-400">아직 평가가 진행되지 않았거나 데이터가 연동되지 않았습니다.</p>
						</div>
					{/if}
				{/if}

				<!-- Tab: Bonus -->
				{#if activeTab === 'bonus'}
					{#if data.bonus_scores.length > 0}
						<table class="w-full text-sm">
							<thead class="bg-amber-50/50">
								<tr>
									<th class="px-6 py-3 text-left font-medium text-amber-900/60">사유</th>
									<th class="px-6 py-3 text-center font-medium text-amber-900/60">점수</th>
									<th class="px-6 py-3 text-left font-medium text-amber-900/60">부여자</th>
									<th class="px-6 py-3 text-left font-medium text-amber-900/60">날짜</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								{#each data.bonus_scores as bonus}
									<tr class="hover:bg-amber-50/30 transition-colors">
										<td class="px-6 py-4 text-gray-800 font-medium">{bonus.reason || '-'}</td>
										<td class="px-6 py-4 text-center font-bold text-amber-600">+{bonus.score}</td>
										<td class="px-6 py-4 text-gray-500">{bonus.given_by_name}</td>
										<td class="px-6 py-4 text-gray-400 text-xs">{formatDate(bonus.given_at)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
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
