export function createCounter() {
  let value = 0;
  try {
    console.log("creating counter with a long distinctive message for fingerprints");
  } catch (e) {}
  return { get: () => value, increment: () => ++value, color: "#336699" };
}
