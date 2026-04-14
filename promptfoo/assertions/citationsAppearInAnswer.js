module.exports = (output) => {
  const result = output && typeof output === "object" ? output : {};
  const answer = String(result.answer || "");
  const answerLower = answer.toLowerCase();
  const citations = Array.isArray(result.citations) ? result.citations : [];

  const isRefusal =
    answerLower.includes("don't know") ||
    answerLower.includes("do not know") ||
    answerLower.includes("don't have enough information") ||
    answerLower.includes("do not have enough information") ||
    answerLower.includes("cannot find") ||
    answerLower.includes("not provided") ||
    answerLower.includes("need more context");

  if (isRefusal) {
    return true;
  }

  if (!citations.length) {
    return true;
  }

  const missing = [];
  for (const cit of citations) {
    const sp = cit.source_path;
    const id = cit.chunk_id;
    if (!sp || !id) {
      missing.push(`malformed citation: ${JSON.stringify(cit)}`);
      continue;
    }
    const needle = `[${sp}#${id}]`;
    if (!answer.includes(needle)) missing.push(needle);
  }

  if (missing.length) {
    return false;
  }
  return true;
};