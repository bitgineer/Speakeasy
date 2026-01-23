# Architecture Documentation

## Module Dependency Diagram

This document describes the module architecture of faster-whisper-hotkey.

### Viewing the Diagram

The dependency diagram is maintained in `docs/dependencies.dot` (Graphviz DOT format).

**Options for viewing:**

1. **Online**: Use [GraphvizOnline](https://dreampuf.github.io/GraphvizOnline/)
   - Copy the contents of `docs/dependencies.dot` and paste it

2. **Command line** (requires graphviz):
   ```bash
   # Generate PNG
   make diagram-png

   # Generate SVG
   make diagram-svg
   ```

3. **VS Code**: Install the "Graphviz Preview" extension

### Updating the Diagram

The diagram is automatically generated from the source code. To update it:

```bash
# Using make
make diagram

# Or directly with Python
python3 scripts/generate_dependency_diagram.py -o docs/dependencies.dot
```

### Module Categories

- **ENTRY**: Entry points (`__main__`, `cli`)
- **CORE**: Core transcription engine (`models`, `settings`, `transcriber`)
- **UI**: User interface components (`gui`, `history_panel`, `hotkey_dialog`, etc.)
- **CONFIG**: Configuration and setup (`config`, `transcribe`)
- **PLATFORM**: Platform-specific code (`clipboard`, `paste`, `terminal`)
- **UTILS**: Utility modules (`shortcuts_manager`)

### Dependency Rules

The codebase follows these architectural principles:

1. **Core modules** should not depend on UI modules
2. **Platform modules** are isolated and may be imported by core
3. **UI modules** can depend on core and settings
4. **Entry points** orchestrate other modules

### Checking for Circular Dependencies

The diagram generator will warn about circular dependencies:

```bash
python3 scripts/generate_dependency_diagram.py --summary-only
```

Currently, the codebase has **no circular dependencies**.

### Current Dependency Summary

```
Total modules: 18
Total dependencies: 26
```

**Key dependencies:**
- `__main__` → `cli`
- `cli` → `config`, `models`, `settings`, `transcribe`, `transcriber`
- `gui` → `history_panel`, `hotkey_dialog`, `onboarding`, `settings`, `shortcuts_panel`, `transcriber`
- `transcriber` → `clipboard`, `models`, `paste`, `settings`
- `transcribe` → `config`, `settings`, `transcriber`, `ui`
