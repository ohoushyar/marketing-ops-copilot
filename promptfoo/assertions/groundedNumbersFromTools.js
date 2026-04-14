module.exports = (output) => {
  const result = output && typeof output === "object" ? output : {};
  const answer = String(result.answer || "");
  const toolRuns = Array.isArray(result.tool_runs) ? result.tool_runs : [];

  const answerNumbers = answer.match(/\b\d+(?:\.\d+)?%?\b/g) || [];
  if (answerNumbers.length === 0) {
    return true;
  }

  const toolText = JSON.stringify(toolRuns);
  return answerNumbers.some(
    (value) => toolText.includes(value.replace(/%$/, "")) || toolText.includes(value)
  );
};