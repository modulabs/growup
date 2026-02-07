<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';
	import { isLoggedIn } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/toast';
	import { QUEST_TYPE_LABELS } from '$lib/types';
	import type { Quest, Course } from '$lib/types';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';

	let loading = $state(true);
	let syncing = $state(false);
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

	onMount(async () => {
		if (!$isLoggedIn) { goto('/login'); return; }
		await loadQuests();
	});

	async function loadQuests() {
		loading = true;
		try {
			quests = await api.get<Quest[]>(`/api/v1/facilitator/courses/${courseId}/quests`);
		} catch (err) {
			addToast('퀘스트 목록을 불러올 수 없습니다.', 'error');
		} finally {
			loading = false;
		}
	}

	async function syncStudents() {
		syncing = true;
		try {
			await api.post(`/api/v1/admin/sync/students/${courseId}`);
			addToast('학생 명단이 동기화되었습니다.', 'success');
		} catch (err) {
			addToast('학생 동기화에 실패했습니다.', 'error');
		} finally {
			syncing = false;
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

<div class="max-w-6xl mx-auto p-6">
	<div class="mb-6">
		<button
			onclick={() => goto('/facilitator')}
			class="text-sm text-blue-600 hover:text-blue-800 mb-2 cursor-pointer"
		>
			← 과정 목록
		</button>
		<div class="flex items-center justify-between">
			<h1 class="text-2xl font-bold text-gray-800">퀘스트 관리</h1>
			<div class="flex gap-2">
				<button
					onclick={syncStudents}
					disabled={syncing}
					class="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors cursor-pointer"
				>
					{syncing ? '동기화 중...' : '학생 동기화'}
				</button>
				<button
					onclick={openCreateModal}
					class="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer"
				>
					+ 퀘스트 추가
				</button>
			</div>
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
		<div class="space-y-3">
			{#each quests.sort((a, b) => a.quest_number - b.quest_number) as quest}
				<div
					class="bg-white rounded-lg border border-gray-200 p-4 flex items-center justify-between hover:shadow-sm transition-shadow"
				>
					<button
						class="flex-1 text-left cursor-pointer"
						onclick={() => goto(`/facilitator/quests/${quest.id}`)}
					>
						<div class="flex items-center gap-3">
							<span class="text-lg font-bold text-gray-400">#{quest.quest_number}</span>
							<div>
								<span class="font-medium text-gray-800"
									>{quest.title || QUEST_TYPE_LABELS[quest.quest_type]}</span
								>
								<div class="flex gap-2 mt-1 text-xs">
									<span class="px-2 py-0.5 bg-blue-50 text-blue-700 rounded">
										{QUEST_TYPE_LABELS[quest.quest_type]}
									</span>
									<span class="text-gray-400">{quest.quest_date}</span>
								</div>
							</div>
						</div>
					</button>
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
