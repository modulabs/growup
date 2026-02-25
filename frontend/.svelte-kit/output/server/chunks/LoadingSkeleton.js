import { e as ensure_array_like, c as attr_style, b as stringify } from "./index2.js";
function LoadingSkeleton($$renderer, $$props) {
  let { lines = 3, type = "text" } = $$props;
  if (type === "card") {
    $$renderer.push("<!--[-->");
    $$renderer.push(`<div class="space-y-4"><!--[-->`);
    const each_array = ensure_array_like(Array(lines));
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      each_array[$$index];
      $$renderer.push(`<div class="bg-white rounded-lg border border-gray-200 p-4 animate-pulse"><div class="h-5 bg-gray-200 rounded w-3/4 mb-3"></div> <div class="h-4 bg-gray-100 rounded w-1/2"></div></div>`);
    }
    $$renderer.push(`<!--]--></div>`);
  } else {
    $$renderer.push("<!--[!-->");
    if (type === "table") {
      $$renderer.push("<!--[-->");
      $$renderer.push(`<div class="animate-pulse"><div class="h-10 bg-gray-200 rounded mb-2"></div> <!--[-->`);
      const each_array_1 = ensure_array_like(Array(lines));
      for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
        each_array_1[$$index_1];
        $$renderer.push(`<div class="h-8 bg-gray-100 rounded mb-1"></div>`);
      }
      $$renderer.push(`<!--]--></div>`);
    } else {
      $$renderer.push("<!--[!-->");
      $$renderer.push(`<div class="animate-pulse space-y-2"><!--[-->`);
      const each_array_2 = ensure_array_like(Array(lines));
      for (let i = 0, $$length = each_array_2.length; i < $$length; i++) {
        each_array_2[i];
        $$renderer.push(`<div class="h-4 bg-gray-200 rounded"${attr_style(`width: ${stringify(80 - i * 10)}%`)}></div>`);
      }
      $$renderer.push(`<!--]--></div>`);
    }
    $$renderer.push(`<!--]-->`);
  }
  $$renderer.push(`<!--]-->`);
}
export {
  LoadingSkeleton as L
};
