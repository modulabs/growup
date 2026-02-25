import "clsx";
import { p as page } from "../../../../../chunks/index3.js";
import "@sveltejs/kit/internal";
import "../../../../../chunks/exports.js";
import "../../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../../chunks/state.svelte.js";
import "../../../../../chunks/client.js";
import "../../../../../chunks/auth.js";
import { L as LoadingSkeleton } from "../../../../../chunks/LoadingSkeleton.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    page.params.questId;
    $$renderer2.push(`<div class="max-w-4xl mx-auto px-3 py-6 sm:px-6"><div class="mb-6"><button class="text-sm text-blue-600 hover:text-blue-800 mb-2 cursor-pointer">← 퀘스트 목록</button> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[-->");
      LoadingSkeleton($$renderer2, { type: "table", lines: 8 });
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
