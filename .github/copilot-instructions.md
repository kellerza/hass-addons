# hass-addons — align with Cursor rules

This project keeps its agent and contributor policies in **`.cursor/rules/`** as
Markdown-with-frontmatter files (**`*.mdc`**). **Follow those files as the source of truth** for how
to work in this repository.

## What to do

1. **Before** suggesting or applying changes in an area covered by a rule’s `globs` (see the YAML
   frontmatter at the top of each `.mdc` file), **read the relevant `.cursor/rules/*.mdc` file** in
   the repo and obey its body (the markdown after the closing `---` of the frontmatter block).
2. **Repository-wide / always-on rules:** if a rule sets `alwaysApply: true` in its frontmatter,
   treat it as binding for **all** work in this repo unless the user explicitly overrides it in the
   current conversation.
3. **When new rules are added** under `.cursor/rules/`, use them the same way: prefer the rule text
   over assumptions from similar projects.

## Current rule files (index)

| Path | Typical scope | Topic |
| ------ | ---------------- | -------- |
| `.cursor/rules/kiss-ponytail.mdc` | Always on | Lazy senior dev mode: pick the simplest solution that works; reuse before writing; root-cause bug fixes; one runnable check for non-trivial logic. |
| `.cursor/rules/synced-addons.mdc` | Always on | Which add-on folders are **CI-synced mirrors** (`hass-addon-sunsynk-edge/`, `hass-addon-sunsynk-multi/`, `hass-addon-mbusd/`, `hass-addon-sma-em-edge/`) and must not be hand-edited, vs the add-ons maintained here; packaging-vs-behaviour split. |
| `.cursor/rules/python-tooling.mdc` | `src/**/*.py`, `pyproject.toml` | Python 3.13, uv, ruff, pytest conventions for the add-on source packages. |

If this index drifts, **trust the `.mdc` files**; update this table when you add or rename rules.

## Conflicts

If another document in the repo disagrees with a **`.cursor/rules/*.mdc`** rule,
**follow the `.mdc` rule** unless the user or maintainer explicitly says otherwise in the current
thread.
