module.exports = (output) => {
  if (!output || typeof output !== "object") return false;

  if (typeof output.answer !== "string" || output.answer.length < 1) {
    return false;
  }

  if (typeof output.run_id !== "string" || output.run_id.length < 8) {
    return false;
  }

  if (!Array.isArray(output.tool_runs)) {
    return false;
  }

  // Validate each tool run has at least a tool name, and ideally rows.
  for (let i = 0; i < output.tool_runs.length; i++) {
    const tr = output.tool_runs[i];
    if (!tr || typeof tr !== "object") return false;

    if (typeof tr.tool !== "string" || tr.tool.length < 1) {
      return false;
    }

    // rows is optional depending on your implementation, but if present, should be an array
    if ("rows" in tr && tr.rows != null && !Array.isArray(tr.rows)) {
      return false;
    }
  }

  return true;
};