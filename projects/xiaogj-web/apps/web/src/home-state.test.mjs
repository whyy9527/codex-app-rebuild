import test from "node:test";
import assert from "node:assert/strict";
import { useHomeState } from "./home-state.ts";

const store = () => useHomeState.getState();
function start() {
  store().begin();
  store().reset();
  store().save();
  store().begin();
}

test("cancel discards hidden cards, order, and todo configuration together", () => {
  start();
  const saved = structuredClone(store().layout);
  store().hide("quick");
  store().move("overview", "todo");
  store().setTodos([2, 0]);
  store().setMetrics([3, 0]);
  store().setQuick(["邀约查询"]);
  assert.notDeepEqual(store().draft, saved);
  store().cancel();
  assert.deepEqual(store().layout, saved);
  assert.equal(store().draft, null);
});

test("save applies draft and future edits do not mutate saved layout", () => {
  start();
  store().setTodos([2, 0]);
  store().hide("quick");
  store().save();
  const saved = structuredClone(store().layout);
  store().begin();
  store().add("quick");
  store().setTodos([1]);
  store().setMetrics([0]);
  store().setQuick([]);
  assert.deepEqual(store().layout, saved);
  store().cancel();
  assert.deepEqual(store().layout.todos, [2, 0]);
});

test("todo selection keeps at least one item and adding a card is idempotent", () => {
  start();
  store().setTodos([1]);
  store().setTodos([]);
  assert.deepEqual(store().draft.todos, [1]);
  store().add("recent");
  store().add("recent");
  assert.equal(store().draft.cards.filter((x) => x === "recent").length, 1);
  store().cancel();
});
