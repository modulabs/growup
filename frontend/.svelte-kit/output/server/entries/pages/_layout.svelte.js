import { s as store_get, a as attr_class, b as stringify, u as unsubscribe_stores, e as ensure_array_like } from "../../chunks/index2.js";
import { b as base } from "../../chunks/server.js";
import "@sveltejs/kit/internal/server";
import { c as currentUser, i as isLoggedIn } from "../../chunks/auth.js";
import { a as attr } from "../../chunks/attributes.js";
import { e as escape_html } from "../../chunks/escaping.js";
import { w as writable } from "../../chunks/index.js";
function Navbar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const roleBadge = { student: "학생", facilitator: "퍼실리테이터" };
    $$renderer2.push(`<nav class="bg-white border-b border-gray-200 px-4 py-3"><div class="max-w-6xl mx-auto flex items-center justify-between"><a${attr("href", `${stringify(base)}/`)} class="text-xl font-bold text-blue-600">GrowUp</a> `);
    if (store_get($$store_subs ??= {}, "$currentUser", currentUser)) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="flex items-center gap-2 sm:gap-4 min-w-0"><span class="text-sm text-gray-600 max-w-[120px] sm:max-w-none truncate">${escape_html(store_get($$store_subs ??= {}, "$currentUser", currentUser).name)}</span> <span${attr_class(`text-xs px-2 py-0.5 rounded-full font-medium ${stringify(store_get($$store_subs ??= {}, "$currentUser", currentUser).role === "facilitator" ? "bg-purple-100 text-purple-700" : "bg-blue-100 text-blue-700")}`)}>${escape_html(roleBadge[store_get($$store_subs ??= {}, "$currentUser", currentUser).role] || store_get($$store_subs ??= {}, "$currentUser", currentUser).role)}</span> <button class="text-sm text-gray-500 hover:text-gray-700 cursor-pointer">로그아웃</button></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div></nav>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
const toasts = writable([]);
function Toast($$renderer) {
  var $$store_subs;
  const typeClasses = {
    success: "bg-green-500",
    error: "bg-red-500",
    info: "bg-blue-500"
  };
  $$renderer.push(`<div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-[calc(100vw-2rem)]"><!--[-->`);
  const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$toasts", toasts));
  for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
    let toast = each_array[$$index];
    $$renderer.push(`<div${attr_class(`px-4 py-3 rounded-lg text-white text-sm shadow-lg w-full sm:max-w-sm ${stringify(typeClasses[toast.type])}`)} role="alert">${escape_html(toast.message)}</div>`);
  }
  $$renderer.push(`<!--]--></div>`);
  if ($$store_subs) unsubscribe_stores($$store_subs);
}
function _layout($$renderer, $$props) {
  var $$store_subs;
  let { children } = $$props;
  if (store_get($$store_subs ??= {}, "$isLoggedIn", isLoggedIn)) {
    $$renderer.push("<!--[-->");
    Navbar($$renderer);
  } else {
    $$renderer.push("<!--[!-->");
  }
  $$renderer.push(`<!--]--> <main class="min-h-screen bg-gray-50">`);
  children($$renderer);
  $$renderer.push(`<!----></main> `);
  Toast($$renderer);
  $$renderer.push(`<!---->`);
  if ($$store_subs) unsubscribe_stores($$store_subs);
}
export {
  _layout as default
};
