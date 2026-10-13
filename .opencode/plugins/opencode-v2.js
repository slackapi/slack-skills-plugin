// OpenCode V2 plugin entrypoint (default export of slack.js).
// V1's `config` mutation hook has no V2 equivalent, so each concern moves to its owning domain:
//   skills   -> ctx.skill.transform
//   commands -> ctx.command.transform (template + $ARGUMENTS, prompted into the session)
//   mcp      -> ctx.mcp.transform (an explicitly configured "slack" server stays authoritative)
import { readFile, readdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { CANONICAL_SKILL_NAMES } from "./skill-compatibility.js";
import { CANONICAL_COMMANDS } from "./command-and-mcp.js";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));

const SLACK_MCP_V2 = Object.freeze({
  type: "remote",
  url: "https://mcp.slack.com/mcp",
  oauth: {
    client_id: "{env:SLACK_OPENCODE_CLIENT_ID}",
    redirect_uri: "http://127.0.0.1:19876/mcp/oauth/callback",
    callback_port: 19876,
  },
});

function splitFrontmatter(source, label) {
  const match = source.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!match) throw new Error(`${label} is missing YAML frontmatter`);
  const field = (name) => {
    const raw = match[1].match(new RegExp(`^${name}:\\s*(.+)$`, "m"))?.[1]?.trim();
    return raw?.replace(/^"(.*)"$/, "$1");
  };
  return { field, body: match[2].trim() };
}

async function loadSkills() {
  const available = new Set(await readdir(join(ROOT, "skills")));
  const skills = [];
  for (const id of CANONICAL_SKILL_NAMES) {
    if (!available.has(id)) continue;
    const path = join(ROOT, "skills", id, "SKILL.md");
    const { field, body } = splitFrontmatter(await readFile(path, "utf8"), `Skill ${id}`);
    skills.push({ id, name: field("name") ?? id, description: field("description") ?? "", path, content: body });
  }
  return skills;
}

async function loadCommands() {
  return Promise.all(
    CANONICAL_COMMANDS.map(async ([name, filename]) => {
      const { field, body } = splitFrontmatter(await readFile(join(ROOT, "commands", filename), "utf8"), `Command ${name}`);
      const description = field("description");
      if (!description) throw new Error(`Canonical command ${name} is missing a description`);
      return { name, description, template: body };
    }),
  );
}

export default {
  id: "slack.skills",
  async setup(ctx) {
    const [skills, commands] = await Promise.all([loadSkills(), loadCommands()]);

    await ctx.skill.transform((editor) => {
      for (const skill of skills) if (!editor.get(skill.id)) editor.add({ ...skill });
    });

    await ctx.command.transform((editor) => {
      for (const command of commands) {
        editor.add({
          name: command.name,
          description: command.description,
          execute: async ({ sessionID, prompt, delivery }) => {
            const args = prompt?.text ?? "";
            await ctx.session.prompt({
              ...prompt,
              sessionID,
              text: command.template.replaceAll("$ARGUMENTS", args),
              delivery,
            });
          },
        });
      }
    });

    await ctx.mcp.transform((editor) => {
      if (!editor.get("slack")) editor.set("slack", { ...SLACK_MCP_V2, oauth: { ...SLACK_MCP_V2.oauth } });
    });
  },
};
