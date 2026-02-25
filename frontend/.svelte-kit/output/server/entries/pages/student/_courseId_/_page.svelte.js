import { s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import { p as page } from "../../../../chunks/index3.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/client.js";
import { a as activeCourses } from "../../../../chunks/auth.js";
import { L as LoadingSkeleton } from "../../../../chunks/LoadingSkeleton.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let courseId = page.params.courseId;
    page.url.searchParams.get("student_id");
    let courseName = store_get($$store_subs ??= {}, "$activeCourses", activeCourses).find((c) => String(c.legacy_course_id) === courseId)?.name || "과정";
    $$renderer2.push(`<div class="max-w-4xl mx-auto px-3 py-6 sm:px-6"><div class="mb-6"><h1 class="text-2xl font-bold text-gray-800">${escape_html(courseName)}</h1></div> `);
    {
      $$renderer2.push("<!--[-->");
      LoadingSkeleton($$renderer2, { type: "table", lines: 5 });
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
