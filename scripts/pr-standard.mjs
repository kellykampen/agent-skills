const sections = ["Summary", "What", "Why", "Evidence", "Agent"];
const titlePattern =
  /^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9][a-z0-9./-]*\))?!?: [A-Z][A-Z0-9]+-[1-9]\d* \S.*$/;

function meaningful(text) {
  return text.split("\n").some((line) => {
    const value = line
      .replace(/^\s*[-*+]\s*(\[[ xX]\])?/, "")
      .replace(/[`*_~]/g, "")
      .trim();
    return (
      /[a-z0-9]/i.test(value) &&
      !/^(tbd|todo|n\/?a|none|pending|not run|not applicable|no evidence|coming soon)[.!]?$/i.test(
        value,
      ) &&
      !/^(text|sh|bash|shell|console|log|md)$/i.test(value)
    );
  });
}

function parseSections(body) {
  const found = [];
  let current;
  let fence;
  for (const line of body.split("\n")) {
    const marker = line.match(/^\s{0,3}(`{3,}|~{3,})/);
    const heading = !fence && line.match(/^#{1,2}\s+(.+?)\s*#*\s*$/);
    if (heading) {
      current =
        line.startsWith("## ") && sections.includes(heading[1])
          ? { name: heading[1], text: "" }
          : undefined;
      if (current) found.push(current);
    } else if (current) current.text += `${line}\n`;
    if (marker) {
      if (!fence) fence = marker[1];
      else if (
        marker[1][0] === fence[0] &&
        marker[1].length >= fence.length &&
        /^\s*(`+|~+)\s*$/.test(line)
      )
        fence = undefined;
    }
  }
  return found;
}

function hasProof(text) {
  const links = text.match(/https:\/\/[^\s<>\])]+/g) ?? [];
  const accessible = links.some((link) => {
    try {
      const { hostname } = new URL(link);
      return (
        hostname.includes(".") &&
        !/^(localhost|127\.|0\.|192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/.test(
          hostname,
        ) &&
        !/(^|\.)(example\.(com|org|net)|local|localhost|invalid|test)$/.test(
          hostname,
        )
      );
    } catch {
      return false;
    }
  });
  const output = [
    ...text.matchAll(/^\s*(`{3,}|~{3,})[^\n]*\n([\s\S]*?)^\s*\1\s*$/gm),
  ].some((match) => meaningful(match[2]));
  return accessible || output;
}

function outsideFences(text) {
  let fence;
  return text
    .split("\n")
    .filter((line) => {
      const marker = line.match(/^ {0,3}(`{3,}|~{3,})/);
      if (marker && !fence) {
        fence = marker[1];
        return false;
      }
      if (
        fence &&
        marker?.[1][0] === fence[0] &&
        marker[1].length >= fence.length &&
        /^ {0,3}(`+|~+)[ \t]*$/.test(line)
      ) {
        fence = undefined;
        return false;
      }
      return !fence;
    })
    .join("\n");
}

function agentErrors(text) {
  text = outsideFences(text);
  const errors = [];
  for (const field of ["Agent", "Session/thread ID"]) {
    const value = text.match(
      new RegExp(`^[ \\t]*(?:[-*][ \\t]*)?${field}:[ \\t]*([^\\n]+)$`, "m"),
    )?.[1];
    if (!value || !meaningful(value))
      errors.push(
        `In \`## Agent\`, provide \`${field}:\` with the actual agent identity or session/thread ID.`,
      );
  }
  return errors;
}

function linkageErrors(text, title) {
  const ticket = title.match(/: ([A-Z][A-Z0-9]+-[1-9]\d*) /)?.[1];
  if (!ticket) return [];
  const declaration =
    /^[ \t]*(?:[-*][ \t]*)?(?:close[sd]?|closing|fix(?:es|ed|ing)?|resolve[sd]?|resolving|complete[sd]?|completing|implement(?:s|ed|ing)?|linear issue|ref(?:s|erences)?|part of|contributes to|towards?|relate[sd] to)[ \t]+(\S+)[ \t]*$/i;
  const matches = outsideFences(text)
    .split("\n")
    .filter((line) => {
      const target = line.match(declaration)?.[1]?.replace(/^<|[>.,;]$/g, "");
      if (target === ticket) return true;
      try {
        const url = new URL(target);
        return (
          url.protocol === "https:" &&
          url.hostname === "linear.app" &&
          url.pathname.match(
            /^\/[^/]+\/issue\/([A-Z][A-Z0-9]+-[1-9]\d*)(?:\/|$)/,
          )?.[1] === ticket
        );
      } catch {
        return false;
      }
    });
  return matches.length === 1
    ? []
    : [
        `In \`## Summary\`, include exactly one explicit linkage declaration for ${ticket}: \`Fixes ${ticket}\` only when completing it, \`Refs ${ticket}\` for partial work, or \`Relates to ${ticket}\` for a relation without status automation. A full Linear issue URL may replace the ID. Plain ticket links and PR comments do not satisfy this declaration.`,
      ];
}

function uiEvidenceErrors(text, files) {
  text = outsideFences(text);
  const errors = [];
  const declared = text.match(
    /^\s*(?:[-*]\s*)?UI changes:\s*(Yes|No)\s*$/im,
  )?.[1];
  if (!declared)
    errors.push(
      "In `## Evidence`, declare `UI changes: Yes` or `UI changes: No`.",
    );
  const uiFiles = files.some(
    (path) =>
      // README-only branding is documentation, not an application UI.
      path !== "media/fantastic-dev-logo.svg" &&
      !/(^|\/)(tests?|__tests__|fixtures)(\/|$)|\.(test|spec)\./i.test(path) &&
      /\.(tsx|jsx|css|scss|sass|less|html|vue|svelte|svg|png|jpe?g|webp|gif)$/i.test(
        path,
      ),
  );
  if (declared?.toLowerCase() !== "yes" && !uiFiles) return errors;
  const screenshot = text.match(
    /^\s*(?:[-*]\s*)?Screenshot:\s*!\[[^\]\n]*\]\((https:\/\/[^\s)]+)\)/im,
  )?.[1];
  const video = text.match(
    /^\s*(?:[-*]\s*)?Video:[^\n]*?(https:\/\/[^\s)<>]+)/im,
  )?.[1];
  const uploaded = (url) =>
    !!url &&
    /^https:\/\/(github\.com\/user-attachments\/assets\/|(?:user-images|private-user-images)\.githubusercontent\.com\/)[^\s]+$/.test(
      url,
    );
  if (!uploaded(screenshot) && !uploaded(video))
    errors.push(
      "UI changes require screenshots and/or video uploaded through GitHub attachments. In Evidence, include `Screenshot: ![description](https://github.com/user-attachments/assets/...)` and/or `Video: https://github.com/user-attachments/assets/...`. At least one is required.",
    );
  return errors;
}

export function validatePullRequest({ title = "", body = "" }, files = []) {
  const errors = [];
  if (!titlePattern.test(title.trim()))
    errors.push(
      "Use `type(scope): TICKET-123 description` or `type: TICKET-123 description`. Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert. Example: `fix(auth): JIF-65 correct session expiry`.",
    );
  const found = parseSections((body ?? "").replace(/\r\n?/g, "\n").replace(/<!--[\s\S]*?(-->|$)/g, ""));
  for (const name of sections) {
    const matches = found.filter((section) => section.name === name);
    if (matches.length !== 1)
      errors.push(`Include exactly one \`## ${name}\` section.`);
    else if (!meaningful(matches[0].text))
      errors.push(
        `Fill in \`## ${name}\` with meaningful content; empty sections and placeholders do not count.`,
      );
    else if (name === "Evidence" && !hasProof(matches[0].text))
      errors.push(
        "In `## Evidence`, include an HTTPS proof link accessible to reviewers or fenced test/log/API output, with the result and what it demonstrates. Local paths and promises to verify later do not count.",
      );
    if (matches.length === 1 && name === "Agent")
      errors.push(...agentErrors(matches[0].text));
    if (matches.length === 1 && name === "Summary")
      errors.push(...linkageErrors(matches[0].text, title));
    if (matches.length === 1 && name === "Evidence")
      errors.push(...uiEvidenceErrors(matches[0].text, files));
  }
  if (
    found.length === sections.length &&
    found.map((section) => section.name).join() !== sections.join()
  )
    errors.push("Order the sections: Summary, What, Why, Evidence, Agent.");
  return errors;
}
