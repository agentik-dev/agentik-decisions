"""decisions: six verbs over one sectioned DECISIONS.md per repo, plus doctor and backlog.

The package re-exports every module's `__all__` in dependency order, so
`decisions.<name>` resolves without naming the module.  A loop, not
`from .<module> import *`: pyflakes refuses a star import outright.
`questions` is not re-exported, since its `parse` reads OPEN-QUESTIONS.md;
it is `decisions.questions`, loaded by `ledger`.
"""

from . import answer, ask, backlog, cli, common, doctor, ledger, lookup, render, selector, speak

__all__ = []
for _module in (common, ledger, lookup, ask, render, answer, speak, selector, doctor,
                backlog, cli):
    for _name in _module.__all__:
        globals()[_name] = getattr(_module, _name)
    __all__ += _module.__all__
del _module, _name
