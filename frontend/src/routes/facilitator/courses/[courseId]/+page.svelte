<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { api } from '$lib/api/client';
	import { isLoggedIn } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/toast';
	import { QUEST_TYPE_LABELS } from '$lib/types';
	import type { Quest, Student, BonusScoreOut, StudentRubricResponse } from '$lib/types';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';

	let loading = $state(true);
	let quests = $state<Quest[]>([]);
	let courseId = $derived(page.params.courseId);

	// Quest create modal
	let showModal = $state(false);
	let modalLoading = $state(false);
	let questNumber = $state(1);
	let questType = $state<string>('main');
	let questTitle = $state('');
	let questDate = $state(new Date().toISOString().split('T')[0]);

	// Edit state
	let editingQuest = $state<Quest | null>(null);

	// Selection state for batch delete
	let selectedQuestIds = $state<Set<string>>(new Set());
	let batchDeleting = $state(false);
	let allSelected = $derived(quests.length > 0 && selectedQuestIds.size === quests.length);

	function toggleSelectQuest(id: string) {
		const next = new Set(selectedQuestIds);
		if (next.has(id)) {
			next.delete(id);
		} else {
			next.add(id);
		}
		selectedQuestIds = next;
	}

	function toggleSelectAll() {
		if (allSelected) {
			selectedQuestIds = new Set();
		} else {
			selectedQuestIds = new Set(quests.map((q) => q.id));
		}
	}

	async function batchDeleteQuests() {
		if (selectedQuestIds.size === 0) return;
		const count = selectedQuestIds.size;
		if (!confirm(`선택한 ${count}개 퀘스트를 삭제하시겠습니까?\n연관된 점수도 함께 삭제됩니다.`)) return;
		batchDeleting = true;
		try {
			await api.post(`/api/v1/facilitator/courses/${courseId}/quests/batch-delete`, {
				quest_ids: [...selectedQuestIds]
			});
			addToast(`${count}개 퀘스트가 삭제되었습니다.`, 'success');
			selectedQuestIds = new Set();
			await loadQuests();
		} catch {
			addToast('퀘스트 삭제에 실패했습니다.', 'error');
		} finally {
			batchDeleting = false;
		}
	}

	// Sheet import modal
	let showImportModal = $state(false);
	let importUrl = $state('');
	let importSheetName = $state('퀘스트');
	let importLoading = $state(false);
	let importResult = $state<{
		quests_created: number;
		quests_updated: number;
		scores_created: number;
		scores_updated: number;
		errors: string[];
	} | null>(null);

	// Students & Bonus scores
	let students = $state<Student[]>([]);
	let bonusScores = $state<BonusScoreOut[]>([]);
	let bonusLoading = $state(false);
	let bonusStudentId = $state<number | null>(null);
	let bonusScoreValue = $state<number>(0);
	let bonusReason = $state('');
	let bonusSubmitting = $state(false);

	// Rubric View Modal
	let showStudentModal = $state(false);
	let selectedStudent = $state<Student | null>(null);
	let studentRubricLoading = $state(false);
	let studentRubricData = $state<StudentRubricResponse | null>(null);

	async function openStudentModal(student: Student) {
		selectedStudent = student;
		showStudentModal = true;
		studentRubricLoading = true;
		studentRubricData = null;
		try {
			studentRubricData = await api.get<StudentRubricResponse>(
				`/api/v1/facilitator/courses/${courseId}/students/${student.legacy_user_id}/rubrics`
			);
		} catch {
			addToast('루브릭 데이터를 불러올 수 없습니다.', 'error');
		} finally {
			studentRubricLoading = false;
		}
	}

	onMount(async () => {
		if (!$isLoggedIn) { goto(`${base}/login`); return; }
		// Auto-sync students in background (silent), then load everything
		api.post(`/api/v1/admin/sync/students/${courseId}`).catch(() => {});
		await Promise.all([loadQuests(), loadStudents(), loadBonusScores()]);
	});

	async function loadQuests() {
		loading = true;
		try {
			quests = await api.get<Quest[]>(`/api/v1/facilitator/courses/${courseId}/quests`);
			selectedQuestIds = new Set();
		} catch (err) {
			addToast('퀘스트 목록을 불러올 수 없습니다.', 'error');
		} finally {
			loading = false;
		}
	}

	async function loadStudents() {
		try {
			students = await api.get<Student[]>(`/api/v1/facilitator/courses/${courseId}/students`);
		} catch {
			// Students load silently — needed for bonus score dropdown
		}
	}

	async function loadBonusScores() {
		bonusLoading = true;
		try {
			bonusScores = await api.get<BonusScoreOut[]>(`/api/v1/facilitator/courses/${courseId}/bonus-scores`);
		} catch {
			addToast('비정규 점수를 불러올 수 없습니다.', 'error');
		} finally {
			bonusLoading = false;
		}
	}

	async function addBonusScore() {
		if (!bonusStudentId || bonusScoreValue <= 0 || !bonusReason.trim()) {
			addToast('학생, 점수, 사유를 모두 입력해주세요.', 'error');
			return;
		}
		bonusSubmitting = true;
		try {
			await api.post(`/api/v1/facilitator/courses/${courseId}/bonus-scores`, {
				legacy_student_id: bonusStudentId,
				score: bonusScoreValue,
				reason: bonusReason.trim()
			});
			addToast('비정규 점수가 부여되었습니다.', 'success');
			bonusStudentId = null;
			bonusScoreValue = 0;
			bonusReason = '';
			await loadBonusScores();
		} catch {
			addToast('비정규 점수 부여에 실패했습니다.', 'error');
		} finally {
			bonusSubmitting = false;
		}
	}

	async function deleteBonusScore(id: string) {
		if (!confirm('이 비정규 점수를 삭제하시겠습니까?')) return;
		try {
			await api.del(`/api/v1/facilitator/bonus-scores/${id}`);
			addToast('비정규 점수가 삭제되었습니다.', 'success');
			await loadBonusScores();
		} catch {
			addToast('비정규 점수 삭제에 실패했습니다.', 'error');
		}
	}

	function extractSpreadsheetId(input: string): string {
		// Accept full URL or bare ID
		const match = input.match(/\/spreadsheets\/d\/([a-zA-Z0-9_-]+)/);
		return match ? match[1] : input.trim();
	}

	function openImportModal() {
		importUrl = '';
		importSheetName = '퀘스트';
		importResult = null;
		showImportModal = true;
	}

	async function handleImportSheet() {
		const spreadsheetId = extractSpreadsheetId(importUrl);
		if (!spreadsheetId) {
			addToast('스프레드시트 URL 또는 ID를 입력해주세요.', 'error');
			return;
		}
		importLoading = true;
		importResult = null;
		try {
			const res = await api.post<{
				quests_created: number;
				quests_updated: number;
				scores_created: number;
				scores_updated: number;
				errors: string[];
			}>(`/api/v1/facilitator/courses/${courseId}/import-sheet`, {
				spreadsheet_id: spreadsheetId,
				sheet_name: importSheetName.trim() || '퀘스트'
			});
			importResult = res;
			addToast(
				`가져오기 완료: 퀘스트 ${res.quests_created}개 생성, ${res.quests_updated}개 갱신 / 점수 ${res.scores_created}개 생성, ${res.scores_updated}개 갱신`,
				res.errors.length > 0 ? 'error' : 'success'
			);
			await loadQuests();
		} catch {
			addToast('시트 가져오기에 실패했습니다.', 'error');
		} finally {
			importLoading = false;
		}
	}

	function openCreateModal() {
		editingQuest = null;
		questNumber = quests.length > 0 ? Math.max(...quests.map((q) => q.quest_number)) + 1 : 1;
		questType = 'main';
		questTitle = '';
		questDate = new Date().toISOString().split('T')[0];
		showModal = true;
	}

	function openEditModal(quest: Quest) {
		editingQuest = quest;
		questNumber = quest.quest_number;
		questType = quest.quest_type;
		questTitle = quest.title || '';
		questDate = quest.quest_date;
		showModal = true;
	}

	async function handleSubmitQuest() {
		modalLoading = true;
		try {
			const body = {
				quest_number: questNumber,
				quest_type: questType,
				title: questTitle.trim() || null,
				quest_date: questDate
			};

			if (editingQuest) {
				await api.put(`/api/v1/facilitator/quests/${editingQuest.id}`, body);
				addToast('퀘스트가 수정되었습니다.', 'success');
			} else {
				await api.post(`/api/v1/facilitator/courses/${courseId}/quests`, body);
				addToast('퀘스트가 생성되었습니다.', 'success');
			}

			showModal = false;
			await loadQuests();
		} catch (err) {
			addToast(editingQuest ? '퀘스트 수정에 실패했습니다.' : '퀘스트 생성에 실패했습니다.', 'error');
		} finally {
			modalLoading = false;
		}
	}

	async function deleteQuest(quest: Quest) {
		if (!confirm(`"${quest.title || `#${quest.quest_number}`}" 퀘스트를 삭제하시겠습니까?`)) return;
		try {
			await api.del(`/api/v1/facilitator/quests/${quest.id}`);
			addToast('퀘스트가 삭제되었습니다.', 'success');
			await loadQuests();
		} catch (err) {
			addToast('퀘스트 삭제에 실패했습니다.', 'error');
		}
	}
</script>

<div class="max-w-[1600px] mx-auto p-6">
	<div class="mb-6">
		<button
			onclick={() => goto(`${base}/facilitator`)}
			class="text-sm text-blue-600 hover:text-blue-800 mb-2 cursor-pointer"
		>
			← 과정 목록
		</button>
		<h1 class="text-2xl font-bold text-gray-800">퀘스트 관리</h1>
	</div>

	<!-- Two-column layout: Quests (left) | Bonus (right) -->
	<div class="flex gap-6 items-start">
		<!-- LEFT: Quest list -->
		<div class="flex-1 min-w-0">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-lg font-semibold text-gray-700">퀘스트 목록</h2>
				<div class="flex gap-2">
					<button
						onclick={openImportModal}
						class="px-3 py-2 text-sm border border-green-600 text-green-700 rounded-lg hover:bg-green-50 transition-colors cursor-pointer"
					>
						📥 시트에서 가져오기
					</button>
					<button
						onclick={openCreateModal}
						class="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer"
					>
						+ 퀘스트 추가
					</button>
				</div>
			</div>

			{#if loading}
				<LoadingSkeleton type="card" lines={4} />
			{:else if quests.length === 0}
				<div class="text-center py-12 text-gray-500">
					<p class="mb-4">등록된 퀘스트가 없습니다.</p>
					<p class="text-sm">위의 "+ 퀘스트 추가" 버튼으로 퀘스트를 생성하세요.</p>
				</div>
			{:else}
				<!-- Selection toolbar -->
				<div class="flex items-center justify-between mb-3 px-1">
					<label class="flex items-center gap-2 cursor-pointer select-none">
						<input
							type="checkbox"
							checked={allSelected}
							onchange={toggleSelectAll}
							class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
						/>
						<span class="text-sm text-gray-600">전체 선택 ({selectedQuestIds.size}/{quests.length})</span>
					</label>
					{#if selectedQuestIds.size > 0}
						<button
							onclick={batchDeleteQuests}
							disabled={batchDeleting}
							class="px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors cursor-pointer"
						>
							{batchDeleting ? '삭제 중...' : `선택 삭제 (${selectedQuestIds.size})`}
						</button>
					{/if}
				</div>

				<div class="space-y-3">
					{#each [...quests].sort((a, b) => a.quest_number - b.quest_number) as quest}
						<div
							class="bg-white rounded-lg border p-4 flex items-center justify-between hover:shadow-sm transition-shadow {selectedQuestIds.has(quest.id) ? 'border-blue-400 bg-blue-50/30' : 'border-gray-200'}"
						>
							<div class="flex items-center gap-3 flex-1">
								<input
									type="checkbox"
									checked={selectedQuestIds.has(quest.id)}
									onchange={() => toggleSelectQuest(quest.id)}
									class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer flex-shrink-0"
								/>
								<button
									class="flex-1 text-left cursor-pointer"
									onclick={() => goto(`${base}/facilitator/quests/${quest.id}`)}
								>
									<div class="flex items-center gap-3">
										<span class="text-lg font-bold text-gray-400">#{quest.quest_number}</span>
										<div>
											<span class="font-medium text-gray-800"
												>{quest.title || QUEST_TYPE_LABELS[quest.quest_type]}</span
											>
											<div class="flex items-center gap-2 mt-1 text-xs">
												<span class="px-2 py-0.5 bg-blue-50 text-blue-700 rounded">
													{QUEST_TYPE_LABELS[quest.quest_type]}
												</span>
												<span class="text-gray-400">{quest.quest_date}</span>
												<span class="text-gray-400">·</span>
												<span class={quest.graded_count === quest.total_students && quest.total_students > 0 ? 'text-green-600 font-medium' : 'text-gray-500'}>
													채점 {quest.graded_count}/{quest.total_students}
												</span>
												{#if quest.total_students > 0}
													<div class="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
														<div
															class="h-full rounded-full transition-all {quest.graded_count === quest.total_students ? 'bg-green-500' : 'bg-blue-500'}"
															style="width: {(quest.graded_count / quest.total_students) * 100}%"
														></div>
	</div>
{/if}

<!-- Student Detail Modal -->
{#if showStudentModal && selectedStudent}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
		<div class="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
			<div class="p-5 border-b border-gray-200 flex justify-between items-center">
				<h2 class="text-lg font-bold text-gray-800">
					{selectedStudent.name} 학생 상세 정보
				</h2>
				<button
					onclick={() => (showStudentModal = false)}
					class="text-gray-400 hover:text-gray-600 p-1"
				>
					✕
				</button>
			</div>
			
			<div class="p-6 overflow-y-auto">
				{#if studentRubricLoading}
					<LoadingSkeleton type="card" lines={3} />
				{:else if studentRubricData && studentRubricData.tasks.length > 0}
					<h3 class="font-medium text-purple-800 mb-4 flex items-center gap-2">
						<span class="w-2 h-6 bg-purple-600 rounded-full"></span>
						LMS 루브릭 평가
					</h3>
					
					<div class="space-y-6">
						{#each studentRubricData.tasks as task}
							<div class="bg-gray-50 rounded-lg border border-gray-200 p-4">
								<div class="flex justify-between items-start mb-3">
									<h4 class="font-medium text-gray-900">{task.task_title}</h4>
									<div class="flex gap-2">
										<span class="text-xs font-bold bg-white border border-gray-200 px-2 py-1 rounded text-gray-600">
											H: {task.total_human}
										</span>
										<span class="text-xs font-bold bg-purple-100 border border-purple-200 px-2 py-1 rounded text-purple-700">
											G: {task.total_gpt}
										</span>
									</div>
								</div>

								{#if task.overall_feedback}
									<div class="bg-white p-3 rounded border border-gray-200 text-sm text-gray-600 mb-3">
										{task.overall_feedback}
									</div>
								{/if}

								<table class="w-full text-xs">
									<thead>
										<tr class="text-gray-500 border-b border-gray-200">
											<th class="py-2 text-left">항목</th>
											<th class="py-2 text-center w-10">H</th>
											<th class="py-2 text-center w-10">G</th>
											<th class="py-2 text-left">피드백</th>
										</tr>
									</thead>
									<tbody class="divide-y divide-gray-200">
										{#each task.rubric_items as item}
											<tr>
												<td class="py-2 pr-2 text-gray-700 font-medium">{item.rubric_metric}</td>
												<td class="py-2 text-center text-gray-600">{item.human_score ?? '-'}</td>
												<td class="py-2 text-center text-purple-600">{item.gpt_score ?? '-'}</td>
												<td class="py-2 pl-2 text-gray-500">{item.feedback || '-'}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						{/each}
					</div>
				{:else}
					<div class="text-center py-12 text-gray-500 bg-gray-50 rounded-lg border border-gray-200 border-dashed">
						<p>루브릭 평가 데이터가 없습니다.</p>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

											</div>
										</div>
									</div>
								</button>
							</div>
							<div class="flex gap-1 ml-4">
								<button
									onclick={() => openEditModal(quest)}
									class="p-2 text-gray-400 hover:text-blue-600 cursor-pointer text-sm"
								>
									수정
								</button>
								<button
									onclick={() => deleteQuest(quest)}
									class="p-2 text-gray-400 hover:text-red-600 cursor-pointer text-sm"
								>
									삭제
								</button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- RIGHT: Bonus scores (sticky sidebar) -->
		<div class="w-[380px] flex-shrink-0 sticky top-6">
			<h2 class="text-lg font-semibold text-gray-700 mb-4">비정규 점수 관리</h2>

			<!-- Add bonus score form -->
			<div class="bg-white rounded-lg border border-gray-200 p-4 mb-4">
				<h3 class="text-sm font-medium text-gray-700 mb-3">비정규 점수 부여</h3>
				<div class="space-y-3">
					<div>
						<label class="block text-xs text-gray-500 mb-1">학생</label>
						<select
							bind:value={bonusStudentId}
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							<option value={null}>학생 선택</option>
							{#each students as s}
								<option value={s.legacy_user_id}>{s.name}</option>
							{/each}
						</select>
					</div>
					<div class="flex gap-3">
						<div class="w-24">
							<label class="block text-xs text-gray-500 mb-1">점수</label>
							<input
								type="number"
								bind:value={bonusScoreValue}
								step="0.5"
								min="0"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							/>
						</div>
						<div class="flex-1">
							<label class="block text-xs text-gray-500 mb-1">사유</label>
							<input
								type="text"
								bind:value={bonusReason}
								placeholder="예: 발표 우수"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							/>
						</div>
					</div>
					<button
						onclick={addBonusScore}
						disabled={bonusSubmitting}
						class="w-full px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors cursor-pointer"
					>
						{bonusSubmitting ? '부여 중...' : '+ 부여'}
					</button>
				</div>
			</div>

			<!-- Bonus scores list -->
			{#if bonusLoading}
				<LoadingSkeleton type="card" lines={3} />
			{:else if bonusScores.length === 0}
				<div class="text-center py-8 text-gray-400 text-sm">
					부여된 비정규 점수가 없습니다.
				</div>
			{:else}
				<div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
					<div class="max-h-[calc(100vh-400px)] overflow-y-auto">
						<table class="w-full text-sm">
							<thead class="bg-gray-50 sticky top-0">
								<tr>
									<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">학생</th>
									<th class="px-3 py-2 text-center text-xs font-medium text-gray-500">점수</th>
									<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">사유</th>
									<th class="px-3 py-2 text-center text-xs font-medium text-gray-500 w-10"></th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								{#each bonusScores as bs}
									<tr class="hover:bg-gray-50" title="{bs.given_by_name} · {new Date(bs.given_at).toLocaleDateString('ko-KR')}">
										<td class="px-3 py-2 font-medium text-gray-800 truncate max-w-[100px]">{bs.student_name}</td>
										<td class="px-3 py-2 text-center font-bold text-green-600">+{bs.score}</td>
										<td class="px-3 py-2 text-gray-600 truncate max-w-[120px]">{bs.reason}</td>
										<td class="px-3 py-2 text-center">
											<button
												onclick={() => deleteBonusScore(bs.id)}
												class="text-red-400 hover:text-red-600 cursor-pointer text-xs"
											>
												삭제
											</button>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{/if}
		</div>

		<!-- Student List -->
		<div class="mt-6">
			<h2 class="text-lg font-semibold text-gray-700 mb-4">학생 목록</h2>
			<div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
				<div class="max-h-[300px] overflow-y-auto">
					{#if students.length === 0}
						<div class="p-4 text-center text-gray-500 text-sm">학생이 없습니다.</div>
					{:else}
						<ul class="divide-y divide-gray-100">
							{#each students as student}
								<li>
									<button
										onclick={() => openStudentModal(student)}
										class="w-full text-left px-4 py-3 hover:bg-gray-50 flex items-center justify-between group cursor-pointer"
									>
										<span class="font-medium text-gray-800">{student.name}</span>
										<span class="text-xs text-gray-400 group-hover:text-blue-600">상세보기 &rarr;</span>
									</button>
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>

<!-- Quest Create/Edit Modal -->
{#if showModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
		<div class="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
			<h2 class="text-lg font-bold text-gray-800 mb-4">
				{editingQuest ? '퀘스트 수정' : '퀘스트 추가'}
			</h2>

			<form
				onsubmit={(e) => {
					e.preventDefault();
					handleSubmitQuest();
				}}
				class="space-y-4"
			>
				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">퀘스트 번호</label>
					<input
						type="number"
						bind:value={questNumber}
						min="1"
						class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">유형</label>
					<select
						bind:value={questType}
						class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						<option value="sub">서브퀘스트 (0~1)</option>
						<option value="main">메인퀘스트 (0~5)</option>
						<option value="datathon">데이터톤 (0~10)</option>
						<option value="ideathon">아이디어톤 (0~20)</option>
					</select>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">제목 (선택)</label>
					<input
						type="text"
						bind:value={questTitle}
						placeholder="예: 머신러닝 기초"
						class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">날짜</label>
					<input
						type="date"
						bind:value={questDate}
						class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>

				<div class="flex gap-2 pt-2">
					<button
						type="button"
						onclick={() => (showModal = false)}
						class="flex-1 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 cursor-pointer"
					>
						취소
					</button>
					<button
						type="submit"
						disabled={modalLoading}
						class="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
					>
						{modalLoading ? '저장 중...' : editingQuest ? '수정' : '추가'}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<!-- Sheet Import Modal -->
{#if showImportModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
		<div class="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6">
			<h2 class="text-lg font-bold text-gray-800 mb-1">📥 시트에서 퀘스트 가져오기</h2>
			<p class="text-xs text-gray-500 mb-4">
				Google 스프레드시트의 "퀘스트" 시트에서 퀘스트 목록과 점수를 자동으로 가져옵니다.
			</p>

			<div class="space-y-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">스프레드시트 URL 또는 ID</label>
					<input
						type="text"
						bind:value={importUrl}
						placeholder="https://docs.google.com/spreadsheets/d/... 또는 ID"
						class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
					/>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">시트 이름</label>
					<input
						type="text"
						bind:value={importSheetName}
						placeholder="퀘스트"
						class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
					/>
					<p class="text-xs text-gray-400 mt-1">기본값: "퀘스트"</p>
				</div>

				{#if importResult}
					<div class="rounded-lg border p-3 {importResult.errors.length > 0 ? 'border-yellow-300 bg-yellow-50' : 'border-green-300 bg-green-50'}">
						<p class="text-sm font-medium {importResult.errors.length > 0 ? 'text-yellow-800' : 'text-green-800'} mb-2">
							가져오기 결과
						</p>
						<div class="grid grid-cols-2 gap-1 text-xs">
							<span class="text-gray-600">퀘스트 생성:</span>
							<span class="font-medium">{importResult.quests_created}개</span>
							<span class="text-gray-600">퀘스트 갱신:</span>
							<span class="font-medium">{importResult.quests_updated}개</span>
							<span class="text-gray-600">점수 생성:</span>
							<span class="font-medium">{importResult.scores_created}개</span>
							<span class="text-gray-600">점수 갱신:</span>
							<span class="font-medium">{importResult.scores_updated}개</span>
						</div>
						{#if importResult.errors.length > 0}
							<div class="mt-2 pt-2 border-t border-yellow-200">
								<p class="text-xs font-medium text-yellow-700 mb-1">오류 ({importResult.errors.length}건):</p>
								<ul class="text-xs text-yellow-600 space-y-0.5 max-h-24 overflow-y-auto">
									{#each importResult.errors as err}
										<li>· {err}</li>
									{/each}
								</ul>
							</div>
						{/if}
					</div>
				{/if}

				<div class="flex gap-2 pt-2">
					<button
						type="button"
						onclick={() => (showImportModal = false)}
						class="flex-1 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 cursor-pointer"
					>
						{importResult ? '닫기' : '취소'}
					</button>
					<button
						type="button"
						onclick={handleImportSheet}
						disabled={importLoading || !importUrl.trim()}
						class="flex-1 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50 cursor-pointer"
					>
						{importLoading ? '가져오는 중...' : '가져오기'}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
