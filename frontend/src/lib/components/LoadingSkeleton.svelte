<script lang="ts">
	interface Props {
		lines?: number;
		type?: 'card' | 'table' | 'text';
	}

	let { lines = 3, type = 'text' }: Props = $props();
</script>

{#if type === 'card'}
	<div class="space-y-4">
		{#each Array(lines) as _}
			<div class="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
				<div class="h-5 bg-gray-200 rounded w-3/4 mb-3"></div>
				<div class="h-4 bg-gray-100 rounded w-1/2"></div>
			</div>
		{/each}
	</div>
{:else if type === 'table'}
	<div class="animate-pulse">
		<div class="h-10 bg-gray-200 rounded mb-2"></div>
		{#each Array(lines) as _}
			<div class="h-8 bg-gray-100 rounded mb-1"></div>
		{/each}
	</div>
{:else}
	<div class="animate-pulse space-y-2">
		{#each Array(lines) as _, i}
			<div class="h-4 bg-gray-200 rounded" style="width: {80 - i * 10}%"></div>
		{/each}
	</div>
{/if}
