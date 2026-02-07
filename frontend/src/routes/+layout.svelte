<script lang="ts">
	import '../app.css';
	import Navbar from '$lib/components/Navbar.svelte';
	import Toast from '$lib/components/Toast.svelte';
	import { isLoggedIn } from '$lib/stores/auth';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();
</script>

{#if $isLoggedIn}
	<Navbar />
{/if}

<main class="min-h-screen bg-gray-50">
	{@render children()}
</main>

<Toast />
