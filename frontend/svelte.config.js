import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),

	kit: {
		adapter: adapter({
			fallback: 'index.html' // SPA mode
		}),
		paths: {
			base: process.env.NODE_ENV === 'production' ? '/growup' : ''
		},
		version: {
			pollInterval: 60000 // check for new version every 60s
		}
	}
};

export default config;
