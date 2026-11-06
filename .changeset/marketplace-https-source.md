---
"slack": patch
---

Updating the plugin from the `slack` Claude Code marketplace now works without a GitHub SSH key. `claude plugin update slack@slack` used to fail with `Permission denied (publickey)` on machines that clone GitHub over HTTPS, even though the install itself worked.
