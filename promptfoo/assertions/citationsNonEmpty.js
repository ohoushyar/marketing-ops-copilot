module.exports = (output) => {
  const result = output && typeof output === "object" ? output : {};
  const answer = String(result.answer || "").toLowerCase();
  const c = result.citations;

  const isRefusal =
    answer.includes("don't know") ||
    answer.includes("do not know") ||
    answer.includes("don't have enough information") ||
    answer.includes("do not have enough information") ||
    answer.includes("cannot find") ||
    answer.includes("not provided") ||
    answer.includes("need more context");

  if (isRefusal) {
    return true;
  }

  if (!Array.isArray(c)) {
    return false;
  }
  if (c.length === 0) {
    return false;
  }
  return true;
};