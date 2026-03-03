<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { api } from '$lib/api/client';
	import { isLoggedIn } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/toast';
	import { QUEST_TYPE_LABELS } from '$lib/types';
	import type { Quest, Student, BonusScoreOut, StudentRubricResponse, ScoreOut } from '$lib/types';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';

	let loading = $state(true);
	let quests = $state<Quest[]>([]);
	let courseId = $derived(page.params.courseId);

	type MatrixCell = {
		score: string;
		isSubmitted: boolean;
		saving: boolean;
		error: boolean;
	};

	let matrixLoading = $state(false);
	let scoreMatrix = $state<Record<string, MatrixCell>>({});
	const saveTimers = new Map<string, ReturnType<typeof setTimeout>>();
	let sortedQuests = $derived([...quests].sort((a, b) => a.quest_number - b.quest_number));

	function cellKey(studentId: number, questId: string): string {
		return `${studentId}:${questId}`;
	}

	function getCell(studentId: number, questId: string): MatrixCell {
		return (
			scoreMatrix[cellKey(studentId, questId)] || {
				score: '',
				isSubmitted: false,
				saving: false,
				error: false
			}
		);
	}

	function setCell(studentId: number, questId: string, patch: Partial<MatrixCell>) {
		const key = cellKey(studentId, questId);
		scoreMatrix = {
			...scoreMatrix,
			[key]: {
				...getCell(studentId, questId),
				...patch
			}
		};
	}

	function matrixScoreTone(scoreText: string, questType: string, isSubmitted: boolean): string {
		if (!isSubmitted || scoreText.trim() === '') return 'bg-slate-50 text-slate-500';
		const score = Number(scoreText);
		if (Number.isNaN(score)) return 'bg-slate-50 text-slate-500';

		if (questType === 'sub') {
			if (score <= 0) return 'bg-red-50 text-red-700';
			if (score < 0.5) return 'bg-amber-50 text-amber-700';
			if (score < 1) return 'bg-lime-50 text-lime-700';
			return 'bg-emerald-100 text-emerald-800';
		}

		if (questType === 'main') {
			if (score <= 0) return 'bg-red-50 text-red-700';
			if (score < 2) return 'bg-orange-50 text-orange-700';
			if (score < 3) return 'bg-amber-50 text-amber-700';
			if (score < 4) return 'bg-lime-50 text-lime-700';
			if (score < 5) return 'bg-emerald-50 text-emerald-700';
			return 'bg-indigo-100 text-indigo-800';
		}

		if (questType === 'datathon') {
			if (score <= 0) return 'bg-red-50 text-red-700';
			if (score < 4) return 'bg-amber-50 text-amber-700';
			if (score < 7) return 'bg-lime-50 text-lime-700';
			return 'bg-emerald-100 text-emerald-800';
		}

		if (score <= 0) return 'bg-red-50 text-red-700';
		if (score < 8) return 'bg-amber-50 text-amber-700';
		if (score < 14) return 'bg-lime-50 text-lime-700';
		return 'bg-emerald-100 text-emerald-800';
	}

	function studentRowQuestTotal(studentId: number): number {
		let total = 0;
		for (const quest of sortedQuests) {
			const cell = getCell(studentId, quest.id);
			if (!cell.isSubmitted) continue;
			const value = Number(cell.score);
			if (Number.isNaN(value)) continue;
			total += value;
		}
		return total;
	}

	function formatStudentRowQuestTotal(studentId: number): string {
		const total = studentRowQuestTotal(studentId);
		return Number.isInteger(total) ? String(total) : total.toFixed(1);
	}

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
			await loadMatrix();
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
	let activeStudents = $state<Student[]>([]);
	let inactiveStudents = $state<Student[]>([]);
	let studentTab = $state<'active' | 'inactive'>('active');
	let matrixStudentScope = $state<'filtered' | 'all'>('filtered');
	let togglingStudentId = $state<number | null>(null);
	let bonusScores = $state<BonusScoreOut[]>([]);
	let bonusLoading = $state(false);
	let bonusStudentId = $state<number | null>(null);
	let bonusScoreValue = $state<number>(0);
	let bonusCategory = $state('퍼실재량점수');
	let bonusCustomCategory = $state('');
	let bonusReason = $state('');
	let bonusSubmitting = $state(false);

	const BONUS_CATEGORIES = ['퍼실재량점수', '아낌없이 주는 그루', '디스코드 소통왕', '쉐밸그투', '직접 입력'];
	let allMatrixStudents = $derived([...activeStudents, ...inactiveStudents]);
	let matrixStudents = $derived(
		matrixStudentScope === 'all' ? allMatrixStudents : activeStudents
	);

	function isActiveMatrixStudent(studentId: number): boolean {
		return activeStudents.some((student) => student.legacy_user_id === studentId);
	}

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
		await loadQuests();
		await loadStudents();
		await loadMatrix();
		await loadBonusScores();
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
			const [active, inactive] = await Promise.all([
				api.get<Student[]>(`/api/v1/facilitator/courses/${courseId}/students?active=true`),
				api.get<Student[]>(`/api/v1/facilitator/courses/${courseId}/students?active=false`)
			]);
			activeStudents = active;
			inactiveStudents = inactive;
			students = active;
		} catch {
			// Students load silently
		}
	}

	async function loadMatrix() {
		if (sortedQuests.length === 0 || allMatrixStudents.length === 0) {
			scoreMatrix = {};
			return;
		}
		matrixLoading = true;
		try {
			const matrix: Record<string, MatrixCell> = {};
			await Promise.all(
				sortedQuests.map(async (quest) => {
					const rows = await api.get<ScoreOut[]>(`/api/v1/facilitator/quests/${quest.id}/students`);
					for (const row of rows) {
						matrix[cellKey(row.legacy_student_id, quest.id)] = {
							score: row.score === null ? '' : String(row.score),
							isSubmitted: row.is_submitted,
							saving: false,
							error: false
						};
					}
				})
			);
			scoreMatrix = matrix;
		} catch {
			addToast('점수 매트릭스를 불러오지 못했습니다.', 'error');
		} finally {
			matrixLoading = false;
		}
	}

	function handleMatrixInput(studentId: number, quest: Quest, raw: string) {
		const value = raw.trim();
		if (value !== '' && !/^\d+(\.\d+)?$/.test(value)) return;
		setCell(studentId, quest.id, { score: value, isSubmitted: value !== '', error: false });
		scheduleCellSave(studentId, quest.id, quest.quest_type);
	}

	function scheduleCellSave(studentId: number, questId: string, questType: string) {
		const key = cellKey(studentId, questId);
		const prev = saveTimers.get(key);
		if (prev) clearTimeout(prev);
		saveTimers.set(
			key,
			setTimeout(() => {
				void persistCell(studentId, questId, questType);
			}, 450)
		);
	}

	async function persistCell(studentId: number, questId: string, _questType: string) {
		const cell = getCell(studentId, questId);
		setCell(studentId, questId, { saving: true, error: false });
		try {
			const score = cell.score === '' ? null : Number(cell.score);
			await api.post(`/api/v1/facilitator/quests/${questId}/scores`, {
				scores: [
					{
						legacy_student_id: studentId,
						score,
						is_submitted: score !== null
					}
				]
			});
			setCell(studentId, questId, { saving: false, error: false, isSubmitted: score !== null });
		} catch {
			setCell(studentId, questId, { saving: false, error: true });
			addToast('점수 저장에 실패했습니다.', 'error');
		}
	}

	async function toggleStudentActive(studentId: number) {
		togglingStudentId = studentId;
		try {
			const res = await api.patch<{ legacy_user_id: number; is_active: boolean }>(
				`/api/v1/facilitator/courses/${courseId}/students/${studentId}/active`
			);
			addToast(res.is_active ? '학생이 활성화되었습니다.' : '학생이 비활성화되었습니다.', 'success');
			await loadStudents();
		} catch {
			addToast('학생 상태 변경에 실패했습니다.', 'error');
		} finally {
			togglingStudentId = null;
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
		let finalCategory = bonusCategory;
		if (bonusCategory === '직접 입력') {
			finalCategory = bonusCustomCategory.trim();
		}

		if (!bonusStudentId || bonusScoreValue <= 0 || !finalCategory) {
			addToast('학생, 점수, 카테고리를 입력해주세요.', 'error');
			return;
		}
		bonusSubmitting = true;
		try {
			await api.post(`/api/v1/facilitator/courses/${courseId}/bonus-scores`, {
				legacy_student_id: bonusStudentId,
				score: bonusScoreValue,
				category: finalCategory,
				reason: bonusReason.trim()
			});
			addToast('비정규 점수가 부여되었습니다.', 'success');
			bonusStudentId = null;
			bonusScoreValue = 0;
			bonusReason = '';
			bonusCategory = '퍼실재량점수';
			bonusCustomCategory = '';
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
			await loadMatrix();
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
			await loadMatrix();
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
			await loadMatrix();
		} catch (err) {
			addToast('퀘스트 삭제에 실패했습니다.', 'error');
		}
	}

</script>

<div class="max-w-[1600px] mx-auto px-3 py-6 sm:px-6">
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
	<div class="space-y-6">
		
		<div class="flex-1 min-w-0">
			<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
				<h2 class="text-lg font-semibold text-gray-700">학생 x 퀘스트 점수표</h2>
				<div class="flex flex-wrap items-center gap-2">
					<div class="inline-flex rounded-lg border border-gray-300 overflow-hidden text-xs">
						<button
							onclick={() => (matrixStudentScope = 'filtered')}
							class={`px-2.5 py-1.5 font-medium transition-colors cursor-pointer ${matrixStudentScope === 'filtered' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
						>
							필터 인원 {activeStudents.length}
						</button>
						<button
							onclick={() => (matrixStudentScope = 'all')}
							class={`px-2.5 py-1.5 font-medium transition-colors cursor-pointer ${matrixStudentScope === 'all' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
						>
							전체 인원 {allMatrixStudents.length}
						</button>
					</div>
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

			<div class="border border-gray-300 bg-white overflow-hidden mb-3">
				<div class="overflow-auto">
					<table class="w-full min-w-[980px] text-sm border-collapse">
						<thead class="bg-gray-100">
							<tr>
							<th class="sticky left-0 z-20 bg-gray-100 px-1 py-1 text-center font-semibold text-gray-700 min-w-[112px] border-r border-b border-gray-300">학생</th>
								{#each sortedQuests as quest}
									<th class="px-1 py-1 text-center min-w-[120px] border-r border-b border-gray-300">
										<div class="flex flex-col items-center gap-1">
											<button class="text-xs font-semibold text-gray-700 hover:text-blue-700 cursor-pointer" onclick={() => openEditModal(quest)}>
												{quest.title || `${QUEST_TYPE_LABELS[quest.quest_type]} #${quest.quest_number}`}
											</button>
											<button
												type="button"
												onclick={() => deleteQuest(quest)}
												class="text-[10px] px-1.5 py-0.5 rounded border border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300 cursor-pointer"
												title="퀘스트 열 삭제"
												aria-label="퀘스트 열 삭제"
											>
												삭제
											</button>
										</div>
									</th>
								{/each}
								<th class="px-1 py-1 text-center min-w-[60px] border-b border-gray-300">
									<button onclick={openCreateModal} class="w-8 h-8 rounded-md border border-dashed border-gray-300 text-gray-500 hover:text-blue-600 hover:border-blue-400 cursor-pointer">+</button>
								</th>
								<th class="sticky right-0 z-20 bg-gray-100 px-2 py-1 text-center font-semibold text-gray-700 min-w-[92px] border-l border-b border-gray-300">총합</th>
							</tr>
						</thead>
						<tbody>
							{#if loading || matrixLoading}
								<tr><td colspan={sortedQuests.length + 3} class="px-3 py-6 text-center text-gray-500">점수표를 불러오는 중입니다...</td></tr>
							{:else if sortedQuests.length === 0}
								<tr><td colspan={3} class="px-3 py-6 text-center text-gray-500">열 끝 + 버튼으로 퀘스트를 추가하세요.</td></tr>
							{:else if matrixStudents.length === 0}
								<tr><td colspan={sortedQuests.length + 3} class="px-3 py-6 text-center text-gray-500">표시할 학생이 없습니다.</td></tr>
							{:else}
								{#each matrixStudents as student}
									<tr class="border-b border-gray-300 hover:bg-gray-50/70">
										<td class="sticky left-0 z-10 bg-white px-1 py-1 font-medium text-gray-800 border-r border-gray-300 text-center">
											<div class="flex items-center justify-center gap-1">
												{#if matrixStudentScope === 'all'}
													<button
														onclick={() => toggleStudentActive(student.legacy_user_id)}
														disabled={togglingStudentId === student.legacy_user_id}
														class={`h-4 w-4 rounded border flex items-center justify-center transition-colors cursor-pointer ${isActiveMatrixStudent(student.legacy_user_id) ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300 bg-white text-transparent hover:border-blue-400'} disabled:opacity-50 disabled:cursor-not-allowed`}
														title={isActiveMatrixStudent(student.legacy_user_id) ? '필터 인원에서 제외' : '필터 인원에 포함'}
														aria-label={isActiveMatrixStudent(student.legacy_user_id) ? '필터 인원에서 제외' : '필터 인원에 포함'}
													>
														<span class="text-[10px] leading-none">✓</span>
													</button>
												{/if}
												<button onclick={() => goto(`${base}/student/${courseId}?student_id=${student.legacy_user_id}`)} class="text-center hover:text-blue-700 cursor-pointer truncate max-w-[95px] leading-tight">{student.name}</button>
											</div>
										</td>
										{#each sortedQuests as quest}
											<td class="p-0 border-r border-gray-200 group">
												<div class="relative flex items-center justify-center gap-0.5 h-7">
													<input
														type="text"
														inputmode="decimal"
														value={getCell(student.legacy_user_id, quest.id).score}
														oninput={(e) => handleMatrixInput(student.legacy_user_id, quest, (e.currentTarget as HTMLInputElement).value)}
														class={`w-full h-7 px-1 py-0 text-center border-0 rounded-none text-xs font-semibold cursor-text transition-colors duration-100 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-300 focus:bg-white ${matrixScoreTone(getCell(student.legacy_user_id, quest.id).score, quest.quest_type, getCell(student.legacy_user_id, quest.id).isSubmitted)} ${getCell(student.legacy_user_id, quest.id).error ? 'bg-red-100 text-red-800' : ''}`}
														placeholder="입력"
													/>
													<span class="absolute right-1 top-1 h-1 w-1 rounded-full bg-gray-300 group-hover:bg-blue-400"></span>
													{#if getCell(student.legacy_user_id, quest.id).saving}
														<span class="absolute right-1 bottom-0.5 text-[9px] text-blue-500">저장</span>
													{:else if getCell(student.legacy_user_id, quest.id).error}
														<span class="absolute right-1 bottom-0.5 text-[9px] text-red-500">실패</span>
													{/if}
												</div>
											</td>
										{/each}
											<td class="p-0"></td>
											<td class="sticky right-0 z-10 bg-white px-2 py-1 text-center border-l border-gray-300 font-semibold text-indigo-700">{formatStudentRowQuestTotal(student.legacy_user_id)}</td>
									</tr>
								{/each}
							{/if}
						</tbody>
					</table>
				</div>
			</div>

			{#if false}

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
					{selectedStudent?.name} 학생 상세 정보
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
				{:else if (studentRubricData?.tasks?.length ?? 0) > 0}
					<h3 class="font-medium text-purple-800 mb-4 flex items-center gap-2">
						<span class="w-2 h-6 bg-purple-600 rounded-full"></span>
						LMS 루브릭 평가
					</h3>
					
					<div class="space-y-6">
						{#each studentRubricData?.tasks ?? [] as task}
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
			{/if}
		</div>

		<!-- RIGHT: Bonus scores (sticky sidebar) -->
		<div class="w-full">
			<h2 class="text-lg font-semibold text-gray-700 mb-4">비정규 점수 관리</h2>
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
			<div class="bg-white rounded-lg border border-gray-200 p-4">
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
					<div class="flex flex-col sm:flex-row gap-3">
						<div class="w-20">
							<label class="block text-xs text-gray-500 mb-1">점수</label>
							<input
								type="number"
								bind:value={bonusScoreValue}
								step="0.5"
								min="0"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							/>
						</div>
						<div class="flex-1 space-y-2">
							<div>
								<label class="block text-xs text-gray-500 mb-1">카테고리</label>
								<select
									bind:value={bonusCategory}
									class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
								>
									{#each BONUS_CATEGORIES as cat}
										<option value={cat}>{cat}</option>
									{/each}
								</select>
							</div>
							{#if bonusCategory === '직접 입력'}
								<input
									type="text"
									bind:value={bonusCustomCategory}
									placeholder="카테고리 입력"
									class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
							{/if}
							<div>
								<input
									type="text"
									bind:value={bonusReason}
									placeholder="상세 사유 (선택)"
									class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
							</div>
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

			{#if bonusLoading}
				<LoadingSkeleton type="card" lines={3} />
			{:else if bonusScores.length === 0}
				<div class="text-center py-8 text-gray-400 text-sm bg-white rounded-lg border border-gray-200">
					부여된 비정규 점수가 없습니다.
				</div>
			{:else}
				<div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
					<div class="max-h-[360px] overflow-y-auto">
						<table class="w-full text-sm">
							<thead class="bg-gray-50 sticky top-0">
								<tr>
									<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">학생</th>
									<th class="px-3 py-2 text-center text-xs font-medium text-gray-500">점수</th>
									<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">카테고리</th>
									<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">사유</th>
									<th class="px-3 py-2 text-center text-xs font-medium text-gray-500 w-10"></th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								{#each bonusScores as bs}
									<tr class="hover:bg-gray-50" title="{bs.given_by_name} · {new Date(bs.given_at).toLocaleDateString('ko-KR')}">
					<td class="px-3 py-2 font-medium text-gray-800 max-w-full lg:max-w-[80px] truncate">{bs.student_name}</td>
						<td class="px-3 py-2 text-center font-bold text-green-600">+{bs.score}</td>
						<td class="px-3 py-2 text-xs text-gray-800 max-w-full lg:max-w-[80px] truncate">{bs.category}</td>
						<td class="px-3 py-2 text-gray-600 max-w-full lg:max-w-[100px] truncate">{bs.reason}</td>
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
		</div>

		{#if false}
		<div class="mt-6">
			<h2 class="text-lg font-semibold text-gray-700 mb-4">학생 목록</h2>
			<div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
				<div class="border-b border-gray-200 overflow-x-auto">
					<div class="flex min-w-max">
						<button
							onclick={() => (studentTab = 'active')}
							class={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${studentTab === 'active'
								? 'border-blue-600 text-blue-600'
								: 'border-transparent text-gray-500 hover:text-gray-700'}`}
						>
							활성 학생 ({activeStudents.length})
						</button>
						<button
							onclick={() => (studentTab = 'inactive')}
							class={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${studentTab === 'inactive'
								? 'border-blue-600 text-blue-600'
								: 'border-transparent text-gray-500 hover:text-gray-700'}`}
						>
							비활성 학생 ({inactiveStudents.length})
						</button>
					</div>
				</div>

				<div class="max-h-[300px] overflow-y-auto">
					{#if studentTab === 'active'}
						{#if activeStudents.length === 0}
							<div class="p-4 text-center text-gray-500 text-sm">활성 학생이 없습니다.</div>
						{:else}
							<ul class="divide-y divide-gray-100">
								{#each activeStudents as student}
									<li class="px-4 py-3 flex items-center justify-between gap-3 hover:bg-gray-50">
										<button
											onclick={() => openStudentModal(student)}
											class="text-left min-w-0 flex-1 group cursor-pointer"
										>
											<span class="font-medium text-gray-800 block truncate">{student.name}</span>
											<span class="text-xs text-gray-400 group-hover:text-blue-600">상세보기 &rarr;</span>
										</button>
										<button
											onclick={() => toggleStudentActive(student.legacy_user_id)}
											disabled={togglingStudentId === student.legacy_user_id}
											class="shrink-0 px-3 py-1.5 text-xs font-medium rounded-md border border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
										>
											{togglingStudentId === student.legacy_user_id ? '처리중...' : '비활성화'}
										</button>
									</li>
								{/each}
							</ul>
						{/if}
					{:else}
						{#if inactiveStudents.length === 0}
							<div class="p-4 text-center text-gray-500 text-sm">비활성 학생이 없습니다.</div>
						{:else}
							<ul class="divide-y divide-gray-100">
								{#each inactiveStudents as student}
									<li class="px-4 py-3 flex items-center justify-between gap-3 hover:bg-gray-50">
										<button
											onclick={() => openStudentModal(student)}
											class="text-left min-w-0 flex-1 group cursor-pointer"
										>
											<span class="font-medium text-gray-800 block truncate">{student.name}</span>
											<span class="text-xs text-gray-400 group-hover:text-blue-600">상세보기 &rarr;</span>
										</button>
										<button
											onclick={() => toggleStudentActive(student.legacy_user_id)}
											disabled={togglingStudentId === student.legacy_user_id}
											class="shrink-0 px-3 py-1.5 text-xs font-medium rounded-md border border-green-200 text-green-700 hover:bg-green-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
										>
											{togglingStudentId === student.legacy_user_id ? '처리중...' : '활성화'}
										</button>
									</li>
								{/each}
							</ul>
						{/if}
					{/if}
				</div>
			</div>
		</div>
		{/if}
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
