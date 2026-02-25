import { s as store_get, e as ensure_array_like, u as unsubscribe_stores } from "../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import { e as escape_html } from "../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import { a as activeCourses } from "../../../chunks/auth.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    $$renderer2.push(`<div class="max-w-4xl mx-auto px-3 py-6 sm:px-6"><h1 class="text-2xl font-bold text-gray-800 mb-6">내 수강 과정</h1> `);
    if (store_get($$store_subs ??= {}, "$activeCourses", activeCourses).length === 0) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-12 text-gray-500"><p>등록된 수강 과정이 없습니다.</p></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="grid gap-4 sm:grid-cols-2"><!--[-->`);
      const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$activeCourses", activeCourses));
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let course = each_array[$$index];
        $$renderer2.push(`<button class="bg-white rounded-lg border border-gray-200 p-5 text-left hover:shadow-md hover:border-blue-300 transition-all cursor-pointer"><h2 class="font-semibold text-gray-800">${escape_html(course.name)}</h2></button>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
