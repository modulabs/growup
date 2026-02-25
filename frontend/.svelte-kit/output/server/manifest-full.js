export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "growup/_app",
	assets: new Set([]),
	mimeTypes: {},
	_: {
		client: {start:"_app/immutable/entry/start.BebjEnxF.js",app:"_app/immutable/entry/app.BR4ketlx.js",imports:["_app/immutable/entry/start.BebjEnxF.js","_app/immutable/chunks/CSK99l_W.js","_app/immutable/chunks/CcVkWGgp.js","_app/immutable/chunks/CZzCSeUk.js","_app/immutable/chunks/1hPTKaIJ.js","_app/immutable/entry/app.BR4ketlx.js","_app/immutable/chunks/CcVkWGgp.js","_app/immutable/chunks/Dap9sqf4.js","_app/immutable/chunks/_V9dK3ok.js","_app/immutable/chunks/1hPTKaIJ.js","_app/immutable/chunks/BSGnc2-w.js","_app/immutable/chunks/D0cPPFsj.js","_app/immutable/chunks/Dn1l8nLM.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:true},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js')),
			__memo(() => import('./nodes/3.js')),
			__memo(() => import('./nodes/4.js')),
			__memo(() => import('./nodes/5.js')),
			__memo(() => import('./nodes/6.js')),
			__memo(() => import('./nodes/7.js')),
			__memo(() => import('./nodes/8.js'))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			},
			{
				id: "/facilitator",
				pattern: /^\/facilitator\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 3 },
				endpoint: null
			},
			{
				id: "/facilitator/courses/[courseId]",
				pattern: /^\/facilitator\/courses\/([^/]+?)\/?$/,
				params: [{"name":"courseId","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 4 },
				endpoint: null
			},
			{
				id: "/facilitator/quests/[questId]",
				pattern: /^\/facilitator\/quests\/([^/]+?)\/?$/,
				params: [{"name":"questId","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 5 },
				endpoint: null
			},
			{
				id: "/login",
				pattern: /^\/login\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 6 },
				endpoint: null
			},
			{
				id: "/student",
				pattern: /^\/student\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 7 },
				endpoint: null
			},
			{
				id: "/student/[courseId]",
				pattern: /^\/student\/([^/]+?)\/?$/,
				params: [{"name":"courseId","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 8 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();
