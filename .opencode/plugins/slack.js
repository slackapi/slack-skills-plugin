import { registerCanonicalSkills } from "./skill-compatibility.js";
import { registerCommandsAndMcp } from "./command-and-mcp.js";
import v2 from "./opencode-v2.js";

// OpenCode V1 entrypoint (function export).
export const SlackPlugin = async () => {
  return {
    config: async (input) => {
      registerCanonicalSkills(input);
      await registerCommandsAndMcp(input);
    },
  };
};

// Dual V1/V2 default export: V2 reads `id` + `setup`; V1 (>= 1.18.29) calls `server()`.
export default {
  ...v2,
  server: SlackPlugin,
};
