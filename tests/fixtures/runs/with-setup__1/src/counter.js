export function createCounter(initial = 0) {
  let value = initial;
  return {
    get: () => value,
    increment: () => ++value,
    decrement: () => (value = Math.max(0, value - 1)),
    reset: () => (value = initial),
  };
}
