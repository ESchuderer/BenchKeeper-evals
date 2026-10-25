import assert from "node:assert/strict";
import { test } from "node:test";
import { createCounter } from "./counter.js";

test("decrement stops at zero", () => {
  const c = createCounter();
  c.decrement();
  assert.equal(c.get(), 0);
});
