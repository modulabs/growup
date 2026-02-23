<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { api } from '$lib/api/client';
	import { isLoggedIn } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/toast';
	import { SCORE_RULES, QUEST_TYPE_LABELS } from '$lib/types';
	import type { Quest, ScoreOut, ScoreEntry } from '$lib/types';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';

	let loading = $state(true);
	let saving = $state(false);
	let quest = $state<Quest | null>(null);
	let scores = $state<ScoreOut[]>([]);
	let questId = $derived(page.params.questId);
	let syncAttempted = $state(false);

	// Editable score map: legacy_student_id -> { score, is_submitted }
	let editMap = $state<Map<number, { score: number | null; is_submitted: boolean }>>(new Map());
	// Track original values to detect dirty
	let originalMap = $state<Map<number, { score: number | null; is_submitted: boolean }>>(new Map());

	let rule = $derived(quest ? SCORE_RULES[quest.quest_type] : SCORE_RULES['main']);
	let isDirty = $derived(() => {
		for (const [id, edit] of editMap) {
			const orig = originalMap.get(id);
			if (!orig) return true;
			if (edit.score !== orig.score || edit.is_submitted !== orig.is_submitted) return true;
		}
		return false;
	});
	let dirtyCount = $derived(() => {
		let count = 0;
		for (const [id, edit] of editMap) {
			const orig = originalMap.get(id);
			if (!orig || edit.score !== orig.score || edit.is_submitted !== orig.is_submitted) count++;
		}
		return count;
	});

	onMount(async () => {
		if (!$isLoggedIn) { goto(`${base}/login`); return; }
		await loadScores();
	});

	async function loadScores() {
		loading = true;
		try {
			const [questData, scoreList] = await Promise.all([
				api.get<Quest>(`/api/v1/facilitator/quests/${questId}`),
				api.get<ScoreOut[]>(`/api/v1/facilitator/quests/${questId}/students`)
			]);
			quest = questData;
			scores = scoreList;
			initEditMap();

			// Auto-sync: if no students and haven't tried yet, trigger sync and reload
			if (scores.length === 0 && quest && !syncAttempted) {
				syncAttempted = true;
				try {
					await api.post(`/api/v1/admin/sync/students/${quest.cached_course_id}`);
					// Reload scores after sync
					const retryScores = await api.get<ScoreOut[]>(`/api/v1/facilitator/quests/${questId}/students`);
					scores = retryScores;
					initEditMap();
				} catch {
					// Sync failed silently — page will show empty state
				}
			}
		} catch (err) {
			addToast('점수 데이터를 불러올 수 없습니다.', 'error');
		} finally {
			loading = false;
		}
	}

	function initEditMap() {
		const eMap = new Map<number, { score: number | null; is_submitted: boolean }>();
		const oMap = new Map<number, { score: number | null; is_submitted: boolean }>();
		for (const s of scores) {
			const entry = { score: s.score, is_submitted: s.is_submitted };
			eMap.set(s.legacy_student_id, { ...entry });
			oMap.set(s.legacy_student_id, { ...entry });
		}
		editMap = eMap;
		originalMap = oMap;
	}

	function setScore(studentId: number, value: string) {
		const entry = editMap.get(studentId);
		if (!entry) return;
		if (value === '' || value === null || value === undefined) {
			entry.score = null;
		} else {
			const num = parseFloat(value);
			if (!isNaN(num)) {
				entry.score = Math.min(Math.max(num, rule.min), rule.max);
			}
		}
		editMap = new Map(editMap);
	}

	function toggleSubmitted(studentId: number) {
		const entry = editMap.get(studentId);
		if (!entry) return;
		entry.is_submitted = !entry.is_submitted;
		if (!entry.is_submitted) {
			entry.score = null;
		}
		editMap = new Map(editMap);
	}

	function setAllSubmitted() {
		for (const [, entry] of editMap) {
			entry.is_submitted = true;
		}
		editMap = new Map(editMap);
	}

	async function saveScores() {
		saving = true;
		try {
			const changedScores: ScoreEntry[] = [];
			for (const [studentId, edit] of editMap) {
				const orig = originalMap.get(studentId);
				if (!orig || edit.score !== orig.score || edit.is_submitted !== orig.is_submitted) {
					changedScores.push({
						legacy_student_id: studentId,
						score: edit.is_submitted ? edit.score : null,
						is_submitted: edit.is_submitted
					});
				}
			}

			if (changedScores.length === 0) {
				addToast('변경된 점수가 없습니다.', 'info');
				saving = false;
				return;
			}

			await api.post(`/api/v1/facilitator/quests/${questId}/scores`, { scores: changedScores });
			addToast(`${changedScores.length}명의 점수가 저장되었습니다.`, 'success');
			await loadScores();
		} catch (err) {
			addToast('점수 저장에 실패했습니다.', 'error');
		} finally {
			saving = false;
		}
	}

	function getScoreDisplay(questType: string): string {
		const r = SCORE_RULES[questType];
		if (!r) return '0~?';
		if (r.step === 1) return `${r.min}~${r.max} (정수)`;
		return `${r.min}~${r.max} (${r.step}단위)`;
	}
</script>

<div class="max-w-4xl mx-auto px-3 py-6 sm:px-6">
	<!-- Header -->
	<div class="mb-6">
		<button
			onclick={() => history.back()}
			class="text-sm text-blue-600 hover:text-blue-800 mb-2 cursor-pointer"
		>
			&larr; 퀘스트 목록
		</button>

		{#if quest}
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-2xl font-bold text-gray-800">
						#{quest.quest_number} {quest.title || QUEST_TYPE_LABELS[quest.quest_type]}
					</h1>
					<div class="flex gap-2 mt-1 text-sm">
						<span class="px-2 py-0.5 bg-blue-50 text-blue-700 rounded">
							{QUEST_TYPE_LABELS[quest.quest_type]}
						</span>
						<span class="text-gray-400">{quest.quest_date}</span>
						<span class="text-gray-400">| 배점: {getScoreDisplay(quest.quest_type)}</span>
					</div>
				</div>
			</div>
		{/if}
	</div>

	{#if loading}
		<LoadingSkeleton type="table" lines={8} />
	{:else if scores.length === 0}
		<div class="text-center py-12 text-gray-500">
			<p class="mb-4">학생 명단을 불러오는 중...</p>
			<p class="text-sm">잠시만 기다려주세요.</p>
		</div>
	{:else}
		<!-- Action Bar -->
		<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
			<div class="text-sm text-gray-500">
				총 {scores.length}명
				{#if dirtyCount() > 0}
					<span class="ml-2 text-orange-600 font-medium">| {dirtyCount()}명 변경됨</span>
				{/if}
			</div>
			<div class="flex gap-2">
				<button
					onclick={setAllSubmitted}
					class="px-3 py-1.5 text-xs border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
				>
					전체 제출로 표시
				</button>
				<button
					onclick={saveScores}
					disabled={saving || !isDirty()}
					class="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
				>
					{saving ? '저장 중...' : '점수 저장'}
				</button>
			</div>
		</div>

		<!-- Score Table -->
		<div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
			<div class="overflow-x-auto">
				<table class="w-full min-w-[640px]">
					<thead>
					<tr class="bg-gray-50 border-b border-gray-200">
						<th class="text-left px-4 py-3 text-sm font-medium text-gray-600 w-12">#</th>
						<th class="text-left px-4 py-3 text-sm font-medium text-gray-600">학생</th>
						<th class="text-center px-4 py-3 text-sm font-medium text-gray-600 w-32">점수</th>
						<th class="text-center px-4 py-3 text-sm font-medium text-gray-600 w-24">제출</th>
						<th class="text-center px-4 py-3 text-sm font-medium text-gray-600 w-20">상태</th>
					</tr>
				</thead>
				<tbody>
				{#each scores as s, i}
					{#if editMap.get(s.legacy_student_id)}
						<tr class="border-b border-gray-100 last:border-b-0 hover:bg-gray-50/50 {!editMap.get(s.legacy_student_id)?.is_submitted ? 'bg-gray-50/80' : ''}">
							<td class="px-4 py-2.5 text-sm text-gray-400">{i + 1}</td>
							<td class="px-4 py-2.5 text-sm font-medium text-gray-800">{s.student_name}</td>
							<td class="px-4 py-2.5 text-center">
								{#if quest && quest.quest_type === 'sub'}
									<!-- Sub quest: simple pass/fail toggle -->
									<button
										onclick={() => {
											if (!editMap.get(s.legacy_student_id)?.is_submitted) return;
											setScore(s.legacy_student_id, editMap.get(s.legacy_student_id)?.score === 1 ? '0' : '1');
										}}
										disabled={!editMap.get(s.legacy_student_id)?.is_submitted}
										class="px-3 py-1 rounded text-sm font-medium transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed {editMap.get(s.legacy_student_id)?.score === 1 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}"
									>
										{editMap.get(s.legacy_student_id)?.score === 1 ? 'Pass' : 'Non-pass'}
									</button>
								{:else}
									<!-- Numeric score input -->
									<input
										type="number"
										value={editMap.get(s.legacy_student_id)?.is_submitted && editMap.get(s.legacy_student_id)?.score !== null ? editMap.get(s.legacy_student_id)?.score : ''}
										disabled={!editMap.get(s.legacy_student_id)?.is_submitted}
										min={rule.min}
										max={rule.max}
										step={rule.step}
										oninput={(e) => setScore(s.legacy_student_id, (e.target as HTMLInputElement).value)}
										class="w-20 px-2 py-1 text-center border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
									/>
								{/if}
							</td>
							<td class="px-4 py-2.5 text-center">
								<label class="inline-flex items-center cursor-pointer">
									<input
										type="checkbox"
									checked={editMap.get(s.legacy_student_id)?.is_submitted}
									onchange={() => toggleSubmitted(s.legacy_student_id)}
									class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
									/>
								</label>
							</td>
							<td class="px-4 py-2.5 text-center">
								{#if originalMap.get(s.legacy_student_id) && (editMap.get(s.legacy_student_id)?.score !== originalMap.get(s.legacy_student_id)?.score || editMap.get(s.legacy_student_id)?.is_submitted !== originalMap.get(s.legacy_student_id)?.is_submitted)}
									<span class="inline-block w-2 h-2 rounded-full bg-orange-400" title="변경됨"></span>
								{:else if editMap.get(s.legacy_student_id)?.is_submitted && editMap.get(s.legacy_student_id)?.score !== null}
									<span class="inline-block w-2 h-2 rounded-full bg-green-400" title="채점 완료"></span>
								{:else if !editMap.get(s.legacy_student_id)?.is_submitted}
									<span class="inline-block w-2 h-2 rounded-full bg-gray-300" title="미제출"></span>
								{:else}
									<span class="inline-block w-2 h-2 rounded-full bg-yellow-400" title="미채점"></span>
								{/if}
							</td>
						</tr>
					{/if}
				{/each}
				</tbody>
				</table>
			</div>
		</div>

		<!-- Bottom Save Bar (sticky on scroll) -->
		{#if isDirty()}
			<div class="sticky bottom-2 sm:bottom-4 mt-4">
				<div class="bg-orange-50 border border-orange-200 rounded-lg px-4 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 shadow-lg">
					<span class="text-sm text-orange-700 font-medium">
						{dirtyCount()}명의 점수가 변경되었습니다.
					</span>
					<button
						onclick={saveScores}
						disabled={saving}
						class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors cursor-pointer"
					>
						{saving ? '저장 중...' : '변경사항 저장'}
					</button>
				</div>
			</div>
		{/if}
	{/if}
</div>
