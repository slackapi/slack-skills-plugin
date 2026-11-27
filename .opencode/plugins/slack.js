// OpenCode plugin for the Slack skills.
//
// One module serves both OpenCode generations:
//
// - OpenCode 1 calls `server()`, whose `config` hook adds `skills/` to the
//   skill search paths.
// - OpenCode 2 calls `setup()`, which registers each skill through
//   `ctx.skill.transform()`, because OpenCode 2 has no `config` hook.
//
// `skills/` stays the single source of truth. Nothing is copied or written to
// disk. The commands and the Slack MCP server are not registered yet: the
// commands call Slack MCP tools, and the MCP server needs a Slack client ID for
// OpenCode, which doesn't exist yet.
//
// Thanks to @youenchene, whose OpenCode work in
// https://github.com/slackapi/slack-skills-plugin/pull/125 mapped out both
// plugin APIs. The dual-generation shape follows obra/superpowers:
// https://github.com/obra/superpowers/blob/main/.opencode/plugins/superpowers.js

import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

export const SKILLS_DIR = fileURLToPath(new URL("../../skills", import.meta.url));

const LOG_PREFIX = "[slack]";

/**
 * Read a top-level `key: value` from SKILL.md frontmatter, unquoting single or
 * double quoted values. Every skill in this repo keeps `name` and
 * `description` on one line. `tests/unit/test_opencode_plugin.py` checks that
 * this reads the same values as a YAML parser.
 */
function frontmatterField(frontmatter, key) {
  const raw = frontmatter.match(new RegExp(`^${key}:[ \\t]*(.+)$`, "m"))?.[1]?.trim();
  if (!raw) return undefined;
  const quoted = raw.match(/^(['"])([\s\S]*)\1$/);
  if (!quoted) return raw;
  return quoted[1] === "'" ? quoted[2].replaceAll("''", "'") : quoted[2].replaceAll('\\"', '"');
}

/** Load every `skills/<name>/SKILL.md` as an OpenCode 2 skill object. */
export function loadSkills(skillsDir = SKILLS_DIR) {
  const skills = [];
  for (const entry of readdirSync(skillsDir, { withFileTypes: true })) {
    if (!entry.isDirectory() || entry.name.startsWith(".")) continue;
    const path = join(skillsDir, entry.name, "SKILL.md");
    let source;
    try {
      source = readFileSync(path, "utf8").replaceAll("\r\n", "\n");
    } catch {
      continue;
    }
    const match = source.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
    if (!match) continue;
    const description = frontmatterField(match[1], "description");
    skills.push({
      id: entry.name,
      name: frontmatterField(match[1], "name") ?? entry.name,
      ...(description ? { description } : {}),
      path,
      content: match[2].trim(),
    });
  }
  return skills;
}

/** OpenCode 1: add `skills/` to the skill search paths. */
export async function SlackPlugin() {
  return {
    config: async (config) => {
      // A flat array is the OpenCode 2 shape, which `setup()` handles.
      if (Array.isArray(config.skills)) return;
      config.skills ??= {};
      config.skills.paths ??= [];
      if (!config.skills.paths.includes(SKILLS_DIR)) config.skills.paths.push(SKILLS_DIR);
    },
  };
}

/** OpenCode 2: register each skill through the skill domain. */
export async function setup(ctx) {
  // OpenCode 1 can also call `setup()`, without the skill domain. `server()`
  // covers it there.
  if (typeof ctx?.skill?.transform !== "function") return;

  let skills;
  try {
    skills = loadSkills();
  } catch (err) {
    console.error(`${LOG_PREFIX} could not read ${SKILLS_DIR}:`, err);
    return;
  }

  try {
    await ctx.skill.transform((draft) => {
      // A throw that escapes this callback disables the whole plugin, so each
      // skill gets its own try/catch.
      if (typeof draft.add !== "function") {
        // Older OpenCode 2 builds take a directory source instead.
        draft.source?.({ type: "directory", path: SKILLS_DIR });
        return;
      }
      for (const skill of skills) {
        try {
          draft.add(skill);
        } catch (err) {
          console.error(`${LOG_PREFIX} skill "${skill.id}" was rejected, skipping:`, err);
        }
      }
    });
  } catch (err) {
    console.error(`${LOG_PREFIX} skill registration failed:`, err);
  }
}

export default {
  id: "slack",
  server: SlackPlugin,
  setup,
};
