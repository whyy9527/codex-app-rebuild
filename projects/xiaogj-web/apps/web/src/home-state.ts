import { create } from "zustand";
export const defaultCards = [
  "todo",
  "quick",
  "overview",
  "releases",
  "students",
  "people",
  "classes",
  "notices",
];
export type Layout = {
  cards: string[];
  todos: number[];
  quick: string[];
  metrics: number[];
};
const initial = (): Layout => ({
  cards: [...defaultCards],
  todos: [0, 1, 2, 3, 4, 5, 6],
  quick: [
    "意向学员管理",
    "学员信息管理",
    "新学员报名",
    "收费",
    "班级管理",
    "排课管理",
    "收费报表",
  ],
  metrics: [0, 1, 2, 3],
});
type State = {
  layout: Layout;
  draft: Layout | null;
  begin: () => void;
  cancel: () => void;
  save: () => void;
  reset: () => void;
  hide: (id: string) => void;
  add: (id: string) => void;
  move: (from: string, to: string) => void;
  setTodos: (todos: number[]) => void;
  setMetrics: (metrics: number[]) => void;
  setQuick: (quick: string[]) => void;
};
// Draft changes are isolated until Save. Server-side preference parity is still unverified.
export const useHomeState = create<State>((set) => ({
  layout: initial(),
  draft: null,
  begin: () => set((s) => ({ draft: structuredClone(s.layout) })),
  cancel: () => set({ draft: null }),
  save: () => set((s) => (s.draft ? { layout: s.draft, draft: null } : {})),
  reset: () => set({ draft: initial() }),
  hide: (id) =>
    set((s) =>
      s.draft
        ? {
            draft: { ...s.draft, cards: s.draft.cards.filter((x) => x !== id) },
          }
        : {},
    ),
  add: (id) =>
    set((s) =>
      s.draft && !s.draft.cards.includes(id)
        ? { draft: { ...s.draft, cards: [...s.draft.cards, id] } }
        : {},
    ),
  move: (from, to) =>
    set((s) => {
      if (!s.draft || from === to) return {};
      const cards = s.draft.cards.filter((x) => x !== from);
      cards.splice(cards.indexOf(to), 0, from);
      return { draft: { ...s.draft, cards } };
    }),
  setTodos: (todos) =>
    set((s) =>
      s.draft && todos.length ? { draft: { ...s.draft, todos } } : {},
    ),
  setMetrics: (metrics) =>
    set((s) =>
      s.draft && metrics.length ? { draft: { ...s.draft, metrics } } : {},
    ),
  setQuick: (quick) =>
    set((s) => (s.draft ? { draft: { ...s.draft, quick } } : {})),
}));
