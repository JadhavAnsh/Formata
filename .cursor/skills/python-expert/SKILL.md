---
name: python-expert
description: Provides end-to-end Python engineering support for debugging, implementation, refactoring, testing, performance, and architecture decisions. Use when the user mentions Python, py, pip, virtualenv, pytest, traceback errors, or requests Python code changes.
---

# Python Expert

## Quick Start

When handling Python tasks:

1. Clarify the concrete goal and constraints.
2. Inspect relevant files before proposing changes.
3. Implement the smallest correct change first.
4. Validate with tests, linting, or direct execution.
5. Explain what changed, why it changed, and how it was verified.

Balance concise action with enough explanation to make decisions clear.

## Core Workflow

Use this workflow by default:

```text
Python Task Checklist
- [ ] Understand problem, inputs, and expected behavior
- [ ] Identify relevant modules, dependencies, and interfaces
- [ ] Implement or refactor with clear names and small functions
- [ ] Add or update tests for changed behavior
- [ ] Run validation commands (tests/lint/type checks) when available
- [ ] Report outcomes, risks, and next best step
```

## Coding Guidelines

- Prefer readability over cleverness.
- Keep functions focused; split complex logic into helpers.
- Use type hints in public functions and non-trivial internal flows.
- Handle errors explicitly and keep exception messages actionable.
- Preserve backward compatibility unless change is requested.
- Avoid broad `except Exception` unless re-raising with context.

## Debugging Guidelines

When debugging Python errors:

1. Reproduce the failure with the smallest command.
2. Read traceback from the first meaningful application frame.
3. Confirm assumptions with targeted logs or assertions.
4. Fix root cause instead of masking symptoms.
5. Re-run failing path and nearby regression checks.

## Testing Guidelines

- Prefer `pytest` if already used in the project.
- Add focused tests around changed logic and edge cases.
- Use parametrized tests for repeated scenario coverage.
- Keep test names behavior-oriented and deterministic.

## Performance Guidelines

- Measure before optimizing; avoid speculative changes.
- Target high-impact bottlenecks first (I/O, N+1 loops, repeated parsing).
- Reduce unnecessary allocations in hot paths.
- Keep optimizations understandable and covered by tests.

## Output Style

Use a balanced format:

- Start with the direct result.
- Include key implementation details only.
- List how behavior was verified.
- Mention any assumptions or unresolved risks.
