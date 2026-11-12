# AI Skills for Real Engineers → VX Engineering Skills Contract v0.1

External source: https://github.com/mattpocock/skills (MIT). Catalog reference: https://www.aihero.dev/skills-catalog. Verify and pin exact upstream commit before installing or importing contents.

Status: **locally implemented router / NOT CONNECTED to external skill execution**.

The external catalog is an engineering-workflow reference, **not a new autonomous model**. It describes spec-first development, small-ticket decomposition, test-driven implementation and review. We reused the concept, not third-party executable code or prompts.

`vxruntime/engineering_skills.py` supplies deterministic task routing for clarify, design, plan, implement, debug, review and handoff. Every route is tied to source ref/version and emits a content digest; it returns PROPOSED. It neither installs npm packages nor invokes Claude Code, external shell commands, GitHub writes or providers.

VX boundaries:
1. Capture task and repository evidence.
2. Select minimal approved skill chain.
3. Simulate expected change and threat model.
4. Require explicit approval before write effects.
5. Delegate to reviewed handlers under policy gates.
6. Run deterministic tests, independent review, retain source/commit receipts.
7. Propose Ω index changes without altering canonical authority.

Before full integration: review individual upstream SKILL.md instructions for prompt injection/command execution; check license, pin SHA and vulnerability audit; ensure scoped sandbox and immutable test baselines; independently verify skill results; prohibit unrestricted shell, secret access, unapproved push, merge, deployment and finance operations. This is distinct from optional user-installed Claude Code skill/plugin.

Run: `python -m pytest -q tests/test_engineering_skills.py`.
