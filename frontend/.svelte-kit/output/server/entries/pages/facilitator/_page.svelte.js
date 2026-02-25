import { a as attr } from "../../../chunks/attributes.js";
import { e as escape_html } from "../../../chunks/escaping.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/client.js";
import "../../../chunks/auth.js";
import { L as LoadingSkeleton } from "../../../chunks/LoadingSkeleton.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let syncing = false;
    let courses = [];
    [...courses].filter((c) => c.is_favorite).sort((a, b) => a.name.localeCompare(b.name));
    [...courses].sort((a, b) => {
      if (a.is_favorite !== b.is_favorite) return a.is_favorite ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
    $$renderer2.push(`<div class="max-w-6xl mx-auto px-3 py-6 sm:px-6"><div class="flex items-center justify-between mb-4"><h1 class="text-2xl font-bold text-gray-800">과정 관리</h1> <button${attr("disabled", syncing, true)} class="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors cursor-pointer">${escape_html("과정 동기화")}</button></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      LoadingSkeleton($$renderer2, { type: "card", lines: 4 });
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
