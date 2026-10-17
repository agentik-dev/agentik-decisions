# The interpreter .python-version names (pyenv 3.12.7; its first line the
# virtualenv agentik-decisions, its second the one before the rename, which pyenv
# takes while the first is absent: agentik-r1 c10), never Apple's python3; resolved
# once, so no recipe line waits on the pyenv shim's rehash lock.
ifndef PY
PY := $(shell pyenv which python3 2>/dev/null || command -v python3)
endif
export PY

# conventions section 5: `check` runs under scripts/bounded, one per tree by the
# lock file .check.lock (a flock), an 840 s wall, held off above load 4 x cores; r6 edge 1: every
# `claude` start is bounded too, and a machine without claude reads unrun.

.PHONY: check check-unlocked gates test lint doclint hygiene plugin-version-check validate decisions doctor install venv readme

check:
	@$(PY) scripts/bounded --lock .check.lock --wall 840 --load 4 -- $(MAKE) check-unlocked

check-unlocked: gates test lint doclint hygiene plugin-version-check validate decisions
	@if [ ! -f design/readme/source.md ]; then echo "readme: refused, absent design/readme/source.md"; exit 2; \
	elif shasum -c --status design/readme/rendered.sha256 2>/dev/null; then echo "readme: fresh"; \
	else echo "readme: stale, run make readme"; exit 2; fi

gates:
	@$(BASE) [ -n "$$harness" ] || { echo "$(NO_BASE)" >&2; exit 2; }; \
	$(call HARNESS,tests/gates.py tests/skips.allow) \
	echo "gates: tests/gates.py at $$harness"; \
	$(PY) "$$tmp/tests/gates.py" --skips-allow "$$tmp/tests/skips.allow"

test:
	@$(BASE) [ -n "$$harness" ] || { echo "$(NO_BASE)" >&2; exit 2; }; \
	$(call HARNESS,tests/run.py tests/gates.py tests/skips.allow) \
	echo "test: tests/run.py at $$harness"; \
	PYTHONPATH=src $(PY) "$$tmp/tests/run.py" --skips-allow "$$tmp/tests/skips.allow"

lint:
	$(PY) -m compileall -q src tests

doclint:
	$(PY) scripts/doclint

# The guide section 6: scripts/{agentik,hygiene,bounded} are agentik-commons'
# canonical copies, vendored by its scripts/sync with their sums in
# scripts/vendored.sha256; scripts/doclint stays byte-identical across the repos
# until r2 vendors it. A drifted copy stops the gate.
DOCLINT_SHA = 26eaf2c84aadb822f8d63a0257b063afcc0ba6d9bbcf1d2d856abe4c6388341f
hygiene:
	@shasum -a 256 -c --status scripts/vendored.sha256 || { echo "hygiene: scripts/{agentik,hygiene,bounded} differ from scripts/vendored.sha256; rerun agentik-commons' scripts/sync"; exit 2; }
	@printf '%s  %s\n' $(DOCLINT_SHA) scripts/doclint | shasum -a 256 -c --status || { echo "hygiene: scripts/doclint differs from the canonical copy (the guide section 6)"; exit 2; }
	$(PY) scripts/hygiene

plugin-version-check:
	$(PY) scripts/plugin-version-check

validate:
	@command -v claude >/dev/null 2>&1 || { echo "validate: unrun, no claude on PATH"; exit 2; }
	$(PY) scripts/bounded --wall 60 -- claude plugin validate plugin/

# ADV11-1: `test` and `gates` run the harness (tests/{run.py,gates.py,skips.allow})
# extracted at HARNESS_REV over the working tree: HEAD on main, the merge base with
# main on a branch. ADV10-5 and ADV10-2: no fallback (a missing base is exit 2), and
# `override`, so neither the command line nor the environment moves it. ADV11-2:
# DECISIONS_BASE, the driver's stage-time sha of main, must be a commit in HEAD's
# history, else exit 2; on a branch it replaces the base. Unset, a run by hand.
ifeq ($(shell git rev-parse --abbrev-ref HEAD 2>/dev/null),main)
override HARNESS_REV := $(shell git rev-parse --verify --quiet HEAD^{commit} 2>/dev/null)
override NO_BASE := harness: no HEAD on main
override PIN_HARNESS :=
else
override HARNESS_REV := $(shell git merge-base main HEAD 2>/dev/null)
override NO_BASE := harness: no merge base with main
override PIN_HARNESS := harness=$$pin;
endif
export DECISIONS_BASE
# Sets $$harness, or exits 2 naming a bad pin.
override BASE = harness="$(HARNESS_REV)"; \
	if [ -n "$$DECISIONS_BASE" ]; then \
	pin=$$(git rev-parse --verify --quiet "$$DECISIONS_BASE^{commit}") \
	|| { echo "decisions: DECISIONS_BASE $$DECISIONS_BASE is not a commit" >&2; exit 2; }; \
	git merge-base --is-ancestor "$$pin" HEAD \
	|| { echo "decisions: DECISIONS_BASE $$DECISIONS_BASE is not an ancestor of HEAD" >&2; exit 2; }; \
	$(PIN_HARNESS) fi;
# Extracts the paths $(1) at $$harness into $$tmp, removed on exit.
override HARNESS = tmp=$$(mktemp -d) || exit 2; trap 'rm -rf "$$tmp"' EXIT; \
	for path in $(1); do git cat-file -e "$$harness:$$path" 2>/dev/null \
	|| { echo "harness: $$path absent at $$harness" >&2; exit 2; }; done; \
	git archive "$$harness" $(1) | tar -x -C "$$tmp" || exit 2;
# The decision-records design section 6: each repo's check runs `agentik decisions render
# --check` over its ledger; this repo keeps no DECISIONS.md, so the step says so.
decisions:
	@if [ -f DECISIONS.md ]; then echo "decisions: render --check"; \
	PYTHONPATH=src $(PY) -m decisions render --check; \
	else echo "decisions: no DECISIONS.md, no block to check"; fi

doctor:
	PYTHONPATH=src $(PY) -m decisions doctor

# The tool, `agentik-decisions` and its alias `decisions` (until 2026-12-31), as a
# uv tool; then the `agentik` front door from its vendored copy (agentik-r1 D3).
# The plugin comes from agentik-commons' `agentik` marketplace (agentik-r1 5.2).
BINDIR ?= $(HOME)/.local/bin
install:
	uv tool install .
	install -m 755 scripts/agentik $(BINDIR)/agentik

# The virtualenv .python-version names first, with pyflakes for the gate. No .pth:
# every `-m decisions` line sets PYTHONPATH=src, and the installed tool comes from
# `uv tool install` only (r6 decision 3).
venv:
	@pyenv virtualenvs --bare | grep -qx '3.12.7/envs/agentik-decisions' \
		|| pyenv virtualenv 3.12.7 agentik-decisions
	"$$(pyenv prefix agentik-decisions)/bin/python3" -m pip install --quiet pyflakes
	@echo "venv: agentik-decisions, pyflakes installed"

# conventions sections 5 and 6: README.md is rendered from design/readme/source.md by the
# installed respeak renderer in technical mode under design/readme/contract.txt; edit the
# source, never the README. scripts/readme-render writes the status line, picks the newest
# installed respeak by version tuple (RESPEAK_ROOT overrides), refuses a render inside a
# render (RESPEAK_DEPTH), runs respeak's verifier before the move and writes the two-line
# sidecar design/readme/rendered.sha256 (source, README) that `check` verifies.
# RESPEAK_PYTHON is respeak's virtualenv python (PyYAML), the new name's else the old's
# (agentik-r1 c10); RESPEAK_RENDER_MODEL passes through.
# ADV10-6: the whole render under a 900 s wall; each child inside it has its own timeout.
RESPEAK_PYTHON ?= $(shell { pyenv prefix agentik-respeak || pyenv prefix claude-code-respeak; } 2>/dev/null)/bin/python3
readme:
	PYTHONPATH=src $(PY) scripts/bounded --wall 900 -- $(PY) scripts/readme-render --python "$(RESPEAK_PYTHON)" $(if $(RESPEAK_ROOT),--plugin-root "$(RESPEAK_ROOT)")
