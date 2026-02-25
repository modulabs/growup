
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/" | "/facilitator" | "/facilitator/courses" | "/facilitator/courses/[courseId]" | "/facilitator/quests" | "/facilitator/quests/[questId]" | "/login" | "/student" | "/student/[courseId]";
		RouteParams(): {
			"/facilitator/courses/[courseId]": { courseId: string };
			"/facilitator/quests/[questId]": { questId: string };
			"/student/[courseId]": { courseId: string }
		};
		LayoutParams(): {
			"/": { courseId?: string; questId?: string };
			"/facilitator": { courseId?: string; questId?: string };
			"/facilitator/courses": { courseId?: string };
			"/facilitator/courses/[courseId]": { courseId: string };
			"/facilitator/quests": { questId?: string };
			"/facilitator/quests/[questId]": { questId: string };
			"/login": Record<string, never>;
			"/student": { courseId?: string };
			"/student/[courseId]": { courseId: string }
		};
		Pathname(): "/" | "/facilitator" | "/facilitator/" | "/facilitator/courses" | "/facilitator/courses/" | `/facilitator/courses/${string}` & {} | `/facilitator/courses/${string}/` & {} | "/facilitator/quests" | "/facilitator/quests/" | `/facilitator/quests/${string}` & {} | `/facilitator/quests/${string}/` & {} | "/login" | "/login/" | "/student" | "/student/" | `/student/${string}` & {} | `/student/${string}/` & {};
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): string & {};
	}
}