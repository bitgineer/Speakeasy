# Architecture Decision Records (ADRs)

This directory contains the Architecture Decision Records (ADRs) for the faster-whisper-hotkey project. ADRs document significant architectural decisions, their context, and the rationale behind them.

## What is an ADR?

An Architecture Decision Record is a short text file that describes an important architectural decision for the project. Each ADR captures:

- **Context:** The problem or situation that required a decision
- **Decision:** What was chosen
- **Options Considered:** Alternatives that were evaluated
- **Rationale:** Why this option was chosen over others
- **Consequences:** Positive and negative impacts of the decision

## Why ADRs?

- **New developers:** Understand why certain patterns or technologies were chosen
- **Historical context:** Prevent repeating past debates
- **Decision traceability:** See the evolution of the architecture
- **Onboarding:** Faster ramp-up for contributors

## Structure

Each ADR is numbered (`0001`, `0002`, etc.) and titled with the decision it documents. ADRs should:

1. Be written when a significant architectural decision is made
2. Be numbered sequentially
3. Never be deleted or modified (except for status updates)
4. Reference related ADRs when applicable

## ADR Status

An ADR can have one of the following statuses:

- **Proposed:** The decision is being considered
- **Accepted:** The decision has been made and implemented
- **Deprecated:** The decision is still in use but being phased out
- **Superseded:** The decision has been replaced by a new one (link to new ADR)

## Creating a New ADR

When making a significant architectural decision:

1. Copy the `template.md` file
2. Name it with the next sequential number and a descriptive title
3. Fill in all sections of the template
4. Include the PR or commit that implemented the decision
5. Update the index below

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-dual-interface-architecture.md) | Dual Interface Architecture (CLI + GUI) | Accepted | 2026-01-20 |
| [0002](0002-multi-model-architecture.md) | Multi-Model ASR Architecture | Accepted | 2026-01-20 |
| [0003](0003-cross-platform-support.md) | Cross-Platform Support Strategy | Accepted | 2026-01-20 |
| [0004](0004-settings-persistence.md) | Settings Persistence Architecture | Accepted | 2026-01-20 |
| [0005](0005-threading-architecture.md) | Threading and Concurrency Architecture | Accepted | 2026-01-20 |

## References

- Michael Nygard's original [ADR pattern](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ThoughtWorks Technology Radar on ADRs](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)
