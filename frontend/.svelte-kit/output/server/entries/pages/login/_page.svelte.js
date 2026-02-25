import { a as attr } from "../../../chunks/attributes.js";
import { e as escape_html } from "../../../chunks/escaping.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/client.js";
import "../../../chunks/auth.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let email = "";
    let phone = "";
    let loading = false;
    $$renderer2.push(`<div class="flex items-center justify-center min-h-screen bg-gray-50 px-4"><div class="w-full max-w-sm"><div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8"><div class="text-center mb-8"><h1 class="text-3xl font-bold text-blue-600 mb-2">GrowUp</h1> <p class="text-sm text-gray-500">퀘스트 점수 관리 시스템</p></div> <div class="space-y-4"><div><label for="email" class="block text-sm font-medium text-gray-700 mb-1">이메일</label> <input id="email" type="email" inputmode="email" autocapitalize="off" autocomplete="email"${attr("value", email)} placeholder="name@example.com" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"${attr("disabled", loading, true)}/></div> <div><label for="phone" class="block text-sm font-medium text-gray-700 mb-1">전화번호</label> <input id="phone" type="tel" inputmode="tel" autocomplete="tel"${attr("value", phone)} placeholder="010-1234-5678" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"${attr("disabled", loading, true)}/></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <button type="button"${attr("disabled", loading, true)} class="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer">${escape_html("로그인")}</button></div></div></div></div>`);
  });
}
export {
  _page as default
};
