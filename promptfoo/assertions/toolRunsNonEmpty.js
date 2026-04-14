module.exports = (output) => {
  const result = output && typeof output === "object" ? output : {};
  return Array.isArray(result.tool_runs) && result.tool_runs.length > 0;
};