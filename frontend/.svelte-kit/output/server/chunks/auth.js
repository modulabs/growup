import { d as derived, w as writable } from "./index.js";
function createPersistedStore(key, initial) {
  const stored = typeof window !== "undefined" ? localStorage.getItem(key) : null;
  const value = stored ? JSON.parse(stored) : initial;
  const store = writable(value);
  store.subscribe((v) => {
    if (typeof window !== "undefined") {
      if (v === null || v === void 0) {
        localStorage.removeItem(key);
      } else {
        localStorage.setItem(key, JSON.stringify(v));
      }
    }
  });
  return store;
}
const authToken = createPersistedStore("growup_token", null);
const currentUser = createPersistedStore("growup_user", null);
const activeCourses = createPersistedStore("growup_courses", []);
const isLoggedIn = derived(authToken, ($token) => !!$token);
derived(currentUser, ($user) => $user?.role ?? null);
export {
  activeCourses as a,
  currentUser as c,
  isLoggedIn as i
};
