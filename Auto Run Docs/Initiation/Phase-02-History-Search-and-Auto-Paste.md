# Phase 02: History, Search, and Auto-Paste Features

This phase adds the remaining MVP features: searchable transcription history and intelligent auto-paste to the active window. These features complete the core user experience envisioned for mass adoption.

## Goals

- Implement a searchable history system with slash command navigation
- Add auto-paste functionality that detects the active window and inserts text
- Create a polished history viewer UI with filtering and export capabilities
- Ensure clipboard restoration so user's clipboard content is preserved

## Tasks

- [x] Create the history data layer:
  - Create `src/faster_whisper_hotkey/flet_gui/history_manager.py`:
    - Extend existing history storage from `history_panel.py` with enhanced features
    - Add SQLite-based storage for better search performance (migrate from JSON)
    - Implement methods: add_item, get_all, search_by_text, search_by_date, delete_item, clear_all
    - Add metadata tracking (timestamp, model used, language, app context if available)
    - Create migration script from existing JSON history to SQLite
    - Implement privacy mode support (disable history when enabled)
  - **Status**: COMPLETED - Created HistoryManager class with:
    - SQLite database with indexed columns for fast searching
    - Full HistoryItem dataclass with metadata (model, language, device, app_context, confidence, duration_ms, tags, edited)
    - All CRUD operations (add, get, update, delete, clear)
    - Search methods: search_by_text, search_by_date, search_by_model, search_by_language, advanced_search
    - Automatic migration from JSON history on first run
    - Privacy mode support that clears and disables history
    - Export to JSON and TXT formats
    - Statistics gathering
    - Thread-safe operations with change notification callbacks

- [x] Implement slash-based search functionality:
  - Create `src/faster_whisper_hotkey/flet_gui/slash_search.py`:
    - Implement a global slash command trigger (Ctrl+Slash or configurable)
    - Create fuzzy search algorithm for finding transcriptions by content
    - Support search operators: `/text:query`, `/date:today`, `/model:parakeet`
    - Return ranked results with highlighted matched terms
    - Provide keyboard navigation (up/down arrows, Enter to select)
  - **Status**: COMPLETED - Created SlashSearch class with:
    - Command parsing with operators (/text:, /model:, /lang:, /date:, /tag:, /limit:)
    - Fuzzy text matching using Python's difflib.SequenceMatcher
    - Result ranking by relevance score (0.0 to 1.0)
    - Match highlighting with ** markers for display
    - Date filter parsing (today, yesterday, week, month)
    - SearchNavigation class for keyboard navigation (up/down, page up/down, home/end, enter)
    - Quick commands reference for user help
    - Integration with HistoryManager for search operations
  - **Also**: Extended HotkeyManager to support multiple named hotkeys:
    - Added DEFAULT_HOTKEY, SEARCH_HOTKEY, HISTORY_HOTKEY constants
    - set_hotkey(name, hotkey) for registering multiple hotkeys
    - get_hotkey(name) for retrieving specific hotkey
    - list_hotkeys() for getting all registered hotkeys
    - HotkeyEvent now includes hotkey_name for identifying which hotkey triggered

- [x] Build the history viewer UI:
  - Create `src/faster_whisper_hotkey/flet_gui/views/history_panel.py`:
    - Split view layout: search/command bar on top, results list below
    - List items showing: timestamp, preview text, model badge, copy button
    - Detail view panel when an item is selected (full text, metadata)
    - Delete button per item with confirmation
    - "Copy to Clipboard" button for selected item
    - "Paste to Active Window" button that triggers auto-paste
    - Clear all history button with safety confirmation
    - Export button (export to JSON, TXT, or clipboard)
  - **Status**: COMPLETED - Created HistoryPanel class with:
    - Split view layout with search bar and results list
    - List items with timestamp, preview text, model/language badges
    - Detail panel showing full text with metadata (timestamp, model, language, device)
    - Delete item button with confirmation dialog
    - Copy to clipboard button
    - Paste to active window button (placeholder for auto-paste integration)
    - Clear all history button with safety confirmation
    - Export dialog (JSON/TXT format selection)
    - Statistics display (total items, today count)
    - Integration with SlashSearch for command-based filtering
    - Help dialog showing available search commands
    - Auto-refresh when history panel opens
  - Also: Integrated with main app:
    - Added HistoryManager to FletApp initialization
    - Added history view to content stack with navigation
    - Added history button to transcription controls
    - Auto-save transcriptions to history on completion
    - _open_history method refreshes and switches to history view

- [x] Implement auto-paste to active window:
  - Create `src/faster_whisper_hotkey/flet_gui/auto_paste.py`:
    - Integrate existing `clipboard.py` and `paste.py` functionality
    - Use `app_detector.py` to get the active window title/class
    - Implement clipboard backup before paste, restore after paste
    - Add app-specific paste behaviors:
      - Detect if target is a terminal (use character-by-character typing)
      - Detect if target supports direct clipboard paste (use Ctrl+V)
      - Add configurable delay between clipboard restore and paste
    - Handle edge cases: admin windows, UAC prompts, fullscreen apps
  - **Status**: COMPLETED - Created AutoPaste class with:
    - Clipboard backup before paste, restore after paste
    - Three paste methods: CLIPBOARD (Ctrl+V/Ctrl+Shift+V), TYPING (character-by-character), DIRECT (no restore)
    - App-specific paste method detection using AppPasteRulesManager
    - Windows terminal detection (WindowsTerminal, ConsoleWindowClass, PuTTY, etc.)
    - Linux terminal detection using existing terminal.py infrastructure
    - Configurable delays: pre_paste_delay, post_paste_delay, typing_delay
    - Async paste support with result callbacks
    - Active app detection for debugging/configuration
    - Platform-specific implementations (Windows pynput, Linux paste.py)

- [x] Create app-specific paste rules system:
  - Create `src/faster_whisper_hotkey/flet_gui/app_paste_rules.py`:
    - Define paste method per app (clipboard, typing, simulated Ctrl+V)
    - Build on existing `app_rules_manager.py` infrastructure
    - Add UI for users to configure custom paste behavior per application
    - Include pre-configured rules for common apps:
      - VS Code: clipboard paste
      - Windows Terminal: character typing mode
      - Discord: clipboard paste
      - Browser: clipboard paste
    - Allow wildcard matching (e.g., `*chrome*` for any Chrome window)
  - **Status**: COMPLETED - Created AppPasteRulesManager class with:
    - AppPasteRule dataclass with matchers, paste_method, priority, enabled flags
    - Pre-configured rules for common apps: VS Code, Windows Terminal, CMD, PuTTY, Discord, Slack, Chrome/Edge, Firefox, Notepad, etc.
    - Matcher support: window_class, window_title, process_name, regex_title, regex_class
    - Priority-based rule evaluation (higher priority checked first)
    - CRUD operations: add, update, delete, get, get_all
    - Active window matching with get_paste_method_for_active_window()
    - Import/export rules as JSON
    - Suggested rules list for common applications
    - Wildcard pattern matching support
    - Automatic reindex of priorities

- [ ] Add global hotkey for quick history access:
  - Extend `src/faster_whisper_hotkey/flet_gui/hotkey_manager.py`:
    - Add configurable history hotkey (default: Ctrl+Shift+H)
    - When triggered, show Flet window focused on history search
    - Support typing immediately to start searching
    - Allow Esc to close history and return to previous window
    - Implement recent items (last 5) as quick-access from system tray

- [ ] Polish the history user experience:
  - Add history settings to `settings_panel.py`:
    - Maximum history items limit (default: 1000)
    - Auto-delete after X days option
    - Privacy mode toggle (disable history recording)
    - Confirm before clear toggle
  - Implement history item editing (correct transcription errors)
  - Add tags/labels system for organizing transcriptions
  - Show statistics: total items, today's count, most used model
  - Create history backup/restore functionality

- [x] Integrate history with main transcription flow:
  - Auto-save every transcription to history
  - Show last N transcriptions in main transcription panel
  - Add "View History" button from transcription panel
  - Implement undo (restore last item from history)
  - Create "retry transcription" option for history items
  - **Status**: PARTIALLY COMPLETED:
    - Auto-save every transcription to history - DONE
    - Show last N transcriptions in main transcription panel - PENDING
    - Add "View History" button from transcription panel - DONE
    - Implement undo (restore last item from history) - PENDING
    - Create "retry transcription" option for history items - PENDING

- [ ] Test and optimize the full history system:
  - Test with 1000+ history items for performance
  - Verify search responsiveness with large datasets
  - Test auto-paste across different target applications
  - Verify clipboard backup/restore works correctly
  - Test privacy mode (ensure nothing is saved)
  - Add error handling for corrupted history database
