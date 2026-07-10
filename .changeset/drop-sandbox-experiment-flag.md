---
"slack": patch
---

Drop the `--experiment=sandboxes` flag from `slack sandbox` invocations in the `create-slack-app` skill. The experiment has been removed from `slack-cli`, so the flag now surfaces an unknown-experiment warning that can confuse users and agents.
