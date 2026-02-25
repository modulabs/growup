import { e as ensure_array_like, b as stringify } from "../../../../../chunks/index2.js";
import { p as page } from "../../../../../chunks/index3.js";
import "@sveltejs/kit/internal";
import "../../../../../chunks/exports.js";
import "../../../../../chunks/utils.js";
import { a as attr } from "../../../../../chunks/attributes.js";
import "@sveltejs/kit/internal/server";
import "../../../../../chunks/state.svelte.js";
import "../../../../../chunks/client.js";
import "../../../../../chunks/auth.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
const QUEST_TYPE_LABELS = {
  sub: "서브퀘스트",
  main: "메인퀘스트",
  datathon: "데이터톤",
  ideathon: "아이디어톤"
};
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let quests = [];
    page.params.courseId;
    let sortedQuests = [...quests].sort((a, b) => a.quest_number - b.quest_number);
    (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    let selectedQuestIds = /* @__PURE__ */ new Set();
    quests.length > 0 && selectedQuestIds.size === quests.length;
    let students = [];
    let bonusScores = [];
    let bonusStudentId = null;
    let bonusScoreValue = 0;
    let bonusCategory = "퍼실재량점수";
    let bonusReason = "";
    let bonusSubmitting = false;
    const BONUS_CATEGORIES = ["퍼실재량점수", "아낌없이 주는 그루", "디스코드 소통왕", "쉐밸그투", "직접 입력"];
    $$renderer2.push(`<div class="max-w-[1600px] mx-auto px-3 py-6 sm:px-6"><div class="mb-6"><button class="text-sm text-blue-600 hover:text-blue-800 mb-2 cursor-pointer">← 과정 목록</button> <h1 class="text-2xl font-bold text-gray-800">퀘스트 관리</h1></div> <div class="space-y-6"><div class="flex-1 min-w-0"><div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4"><h2 class="text-lg font-semibold text-gray-700">학생 x 퀘스트 점수표</h2> <div class="flex flex-col sm:flex-row gap-2"><button class="px-3 py-2 text-sm border border-green-600 text-green-700 rounded-lg hover:bg-green-50 transition-colors cursor-pointer">📥 시트에서 가져오기</button> <button class="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer">+ 퀘스트 추가</button></div></div> <div class="border border-gray-300 bg-white overflow-hidden mb-3"><div class="overflow-auto"><table class="w-full min-w-[980px] text-sm border-collapse"><thead class="bg-gray-100"><tr><th class="sticky left-0 z-20 bg-gray-100 px-1 py-1 text-center font-semibold text-gray-700 min-w-[112px] border-r border-b border-gray-300">학생</th><!--[-->`);
    const each_array = ensure_array_like(sortedQuests);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let quest = each_array[$$index];
      $$renderer2.push(`<th class="px-1 py-1 text-center min-w-[120px] border-r border-b border-gray-300"><div class="flex flex-col items-center gap-1"><button class="text-xs font-semibold text-gray-700 hover:text-blue-700 cursor-pointer">${escape_html(quest.title || `${QUEST_TYPE_LABELS[quest.quest_type]} #${quest.quest_number}`)}</button></div></th>`);
    }
    $$renderer2.push(`<!--]--><th class="px-1 py-1 text-center min-w-[60px] border-b border-gray-300"><button class="w-8 h-8 rounded-md border border-dashed border-gray-300 text-gray-500 hover:text-blue-600 hover:border-blue-400 cursor-pointer">+</button></th><th class="sticky right-0 z-20 bg-gray-100 px-2 py-1 text-center font-semibold text-gray-700 min-w-[92px] border-l border-b border-gray-300">총합</th></tr></thead><tbody>`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<tr><td${attr("colspan", sortedQuests.length + 3)} class="px-3 py-6 text-center text-gray-500">점수표를 불러오는 중입니다...</td></tr>`);
    }
    $$renderer2.push(`<!--]--></tbody></table></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="w-full"><h2 class="text-lg font-semibold text-gray-700 mb-4">비정규 점수 관리</h2> <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start"><div class="bg-white rounded-lg border border-gray-200 p-4"><h3 class="text-sm font-medium text-gray-700 mb-3">비정규 점수 부여</h3> <div class="space-y-3"><div><label class="block text-xs text-gray-500 mb-1">학생</label> `);
    $$renderer2.select(
      {
        value: bonusStudentId,
        class: "w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      },
      ($$renderer3) => {
        $$renderer3.option({ value: null }, ($$renderer4) => {
          $$renderer4.push(`학생 선택`);
        });
        $$renderer3.push(`<!--[-->`);
        const each_array_6 = ensure_array_like(students);
        for (let $$index_6 = 0, $$length = each_array_6.length; $$index_6 < $$length; $$index_6++) {
          let s = each_array_6[$$index_6];
          $$renderer3.option({ value: s.legacy_user_id }, ($$renderer4) => {
            $$renderer4.push(`${escape_html(s.name)}`);
          });
        }
        $$renderer3.push(`<!--]-->`);
      }
    );
    $$renderer2.push(`</div> <div class="flex flex-col sm:flex-row gap-3"><div class="w-20"><label class="block text-xs text-gray-500 mb-1">점수</label> <input type="number"${attr("value", bonusScoreValue)} step="0.5" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/></div> <div class="flex-1 space-y-2"><div><label class="block text-xs text-gray-500 mb-1">카테고리</label> `);
    $$renderer2.select(
      {
        value: bonusCategory,
        class: "w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      },
      ($$renderer3) => {
        $$renderer3.push(`<!--[-->`);
        const each_array_7 = ensure_array_like(BONUS_CATEGORIES);
        for (let $$index_7 = 0, $$length = each_array_7.length; $$index_7 < $$length; $$index_7++) {
          let cat = each_array_7[$$index_7];
          $$renderer3.option({ value: cat }, ($$renderer4) => {
            $$renderer4.push(`${escape_html(cat)}`);
          });
        }
        $$renderer3.push(`<!--]-->`);
      }
    );
    $$renderer2.push(`</div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div><input type="text"${attr("value", bonusReason)} placeholder="상세 사유 (선택)" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/></div></div></div> <button${attr("disabled", bonusSubmitting, true)} class="w-full px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors cursor-pointer">${escape_html("+ 부여")}</button></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
      if (bonusScores.length === 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="text-center py-8 text-gray-400 text-sm bg-white rounded-lg border border-gray-200">부여된 비정규 점수가 없습니다.</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="bg-white rounded-lg border border-gray-200 overflow-hidden"><div class="max-h-[360px] overflow-y-auto"><table class="w-full text-sm"><thead class="bg-gray-50 sticky top-0"><tr><th class="px-3 py-2 text-left text-xs font-medium text-gray-500">학생</th><th class="px-3 py-2 text-center text-xs font-medium text-gray-500">점수</th><th class="px-3 py-2 text-left text-xs font-medium text-gray-500">카테고리</th><th class="px-3 py-2 text-left text-xs font-medium text-gray-500">사유</th><th class="px-3 py-2 text-center text-xs font-medium text-gray-500 w-10"></th></tr></thead><tbody class="divide-y divide-gray-100"><!--[-->`);
        const each_array_8 = ensure_array_like(bonusScores);
        for (let $$index_8 = 0, $$length = each_array_8.length; $$index_8 < $$length; $$index_8++) {
          let bs = each_array_8[$$index_8];
          $$renderer2.push(`<tr class="hover:bg-gray-50"${attr("title", `${stringify(bs.given_by_name)} · ${stringify(new Date(bs.given_at).toLocaleDateString("ko-KR"))}`)}><td class="px-3 py-2 font-medium text-gray-800 max-w-full lg:max-w-[80px] truncate">${escape_html(bs.student_name)}</td><td class="px-3 py-2 text-center font-bold text-green-600">+${escape_html(bs.score)}</td><td class="px-3 py-2 text-xs text-gray-800 max-w-full lg:max-w-[80px] truncate">${escape_html(bs.category)}</td><td class="px-3 py-2 text-gray-600 max-w-full lg:max-w-[100px] truncate">${escape_html(bs.reason)}</td><td class="px-3 py-2 text-center"><button class="text-red-400 hover:text-red-600 cursor-pointer text-xs">삭제</button></td></tr>`);
        }
        $$renderer2.push(`<!--]--></tbody></table></div></div>`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _page as default
};
