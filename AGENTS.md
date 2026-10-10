# Repository purpose

This repository is a learning project for understanding the internals of
constraint programming solvers through the MiniCP course. The primary goal is
understanding and clarity, not production performance or feature completeness.

Read `README.md` and `docs/LEARNING.md` before proposing architectural changes.

# Development direction

- Implement each concept in readable Python first.
- Treat the Python implementation as the behavioral reference.
- Port stable, understood components to Rust later as a separate learning
  exercise.
- Keep Python and Rust behavior comparable with shared tests where practical.
- Do not introduce a Rust implementation before the corresponding Python
  behavior is understood and tested unless the user explicitly requests it.

# Design principles

- Prefer the simplest implementation that makes the algorithm and state
  transitions easy to follow.
- Avoid premature abstraction, optimization, and production-oriented features.
- Preserve important MiniCP concepts, but do not copy Java-specific boilerplate
  when a simpler Python design communicates the same idea.
- Add an abstraction only when it solves a current problem or represents the
  concept currently being studied.
- Keep changes small and aligned with the current lecture or learning question.
- Do not pull material from later lectures into the implementation unless the
  user requests it or it is necessary for the current concept.

# Collaboration

- Explain non-trivial algorithms and design decisions when changing them.
- Explicitly note intentional differences from the Java MiniCP architecture.
- When several designs are valid, prefer the one that is easiest to inspect,
  experiment with, and explain.
- Preserve useful notebooks and examples that expose intermediate behavior.
- Preserve unrelated user changes in the working tree.
- Update `docs/LEARNING.md` when a change alters the learning progress,
  architecture, a deliberate simplification, or the next-step options.

# Verification

After Python changes, run:

```console
uv run pytest
uv run ruff check src tests notebooks
uv run ty check
```

After Rust changes, rebuild the extension before running the checks:

```console
uv run maturin develop
uv run pytest
```
