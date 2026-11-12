"""layabench - a small, reproducible benchmark for the Laya decision engine.

The benchmark imagines one concrete production use case: a *multilingual
support-ticket triage gateway*. Every incoming ticket is turned into four typed
decisions - a department (``choice``), an urgency (``score``) and two yes/no
flags (``noul``) - answered in a single forward pass, and we measure how well a
Laya checkpoint does that against the cheap baselines a team would otherwise
reach for (a keyword rules engine, a majority-class guess and random).

The package is deliberately dependency-light: the metric math in
:mod:`layabench.metrics` mirrors ``laya.evals`` but only needs numpy, so the
harness runs with or without the ``laya`` package and its weights.

Public entry points:

* :func:`layabench.harness.run` - score a dataset against a backend.
* :func:`layabench.backends.build_backend` - pick a decision backend.
* ``python -m layabench run ...`` - the command line (see :mod:`layabench.cli`).
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
