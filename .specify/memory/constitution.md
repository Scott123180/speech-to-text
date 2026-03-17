<!--
SYNC IMPACT REPORT
==================
Version change: none → 1.0.0 (initial constitution)
Modified principles: N/A (new document)
Added sections:
  - Core Principles (I–V)
  - Quality Gates
  - Governance
Removed sections: N/A
Templates updated:
  ✅ .specify/templates/plan-template.md — Constitution Check gates align with principles below
  ✅ .specify/templates/spec-template.md — No structural changes required; principles are compatible
  ✅ .specify/templates/tasks-template.md — TDD task ordering (tests before implementation) matches Principle I
Deferred TODOs: none
-->

# Speech-to-Text Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

Tests MUST be written and confirmed to FAIL before any implementation begins.
The Red-Green-Refactor cycle is strictly enforced:

1. Write the test → verify it fails
2. Implement the minimum code to make it pass
3. Refactor while keeping tests green

No feature is considered complete without passing tests. Skipping this cycle
for "small" changes is not permitted.

### II. Clean Code & SOLID Principles

Code MUST be readable, maintainable, and follow SOLID principles:

- **Single Responsibility**: Each module/class/function does one thing well.
- **Open/Closed**: Extend behavior without modifying existing code.
- **Liskov Substitution**: Subtypes MUST be substitutable for their base types.
- **Interface Segregation**: No module is forced to depend on interfaces it does not use.
- **Dependency Inversion**: Depend on abstractions, not concretions.

Functions MUST be small and named to reveal intent. Magic numbers and strings
MUST be named constants. Dead code MUST be removed immediately.

### III. Simplicity & YAGNI

Build only what is required now. Speculative abstractions and premature
generalization are forbidden. When two designs solve the same problem,
the simpler one wins. Complexity MUST be justified with a documented reason.

### IV. User Experience First

Every user-facing interaction MUST prioritize clarity and ease of use:

- Error messages MUST be human-readable and actionable (not stack traces).
- CLI prompts and output MUST be concise and unambiguous.
- Defaults MUST work for the common case without configuration.
- Feedback MUST be provided for long-running operations (e.g., recording,
  transcription progress).

UX regressions are treated as bugs and MUST be fixed before new features land.

### V. Integration Testing

Integration tests MUST cover the full user-facing pipeline (e.g., record →
transcribe → output). New contracts between components require contract tests.
Unit tests alone are insufficient for validating end-to-end correctness.

## Quality Gates

Before any feature is merged:

1. All tests (unit + integration) MUST pass.
2. No new linting or formatting violations introduced.
3. TDD cycle documented in commit history (failing test commit precedes
   implementation commit).
4. UX review: error paths produce friendly messages; happy path is
   straightforward.
5. Complexity violations from Principle III MUST be logged in the plan's
   Complexity Tracking table with justification.

## Governance

This constitution supersedes all other development practices in this repository.
Amendments require:

1. A documented rationale describing what changed and why.
2. A version bump following semantic versioning:
   - MAJOR: principle removed or incompatibly redefined.
   - MINOR: principle added or materially expanded.
   - PATCH: clarification or wording refinement.
3. Updated `Last Amended` date in ISO format.
4. Propagation review across all Speckit templates.

All implementation plans MUST include a Constitution Check section verifying
compliance with Principles I–V before Phase 0 research begins.

**Version**: 1.0.0 | **Ratified**: 2026-03-16 | **Last Amended**: 2026-03-16
