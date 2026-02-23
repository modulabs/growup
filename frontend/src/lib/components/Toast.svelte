<script lang="ts">
	import { toasts } from '$lib/stores/toast';

	const typeClasses: Record<string, string> = {
		success: 'bg-green-500',
		error: 'bg-red-500',
		info: 'bg-blue-500'
	};
</script>

<div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-[calc(100vw-2rem)]">
	{#each $toasts as toast (toast.id)}
		<div
			class="px-4 py-3 rounded-lg text-white text-sm shadow-lg w-full sm:max-w-sm {typeClasses[toast.type]}"
			role="alert"
		>
			{toast.message}
		</div>
	{/each}
</div>
