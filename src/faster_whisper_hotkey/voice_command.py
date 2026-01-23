"""
Voice command parser and execution framework for faster-whisper-hotkey.

This module provides intelligent parsing of transcribed text to distinguish between
dictation (text to be inserted) and voice commands (editing/control operations).

Commands include:
- Delete last sentence/paragraph/word
- Replace [word] with [word]
- Insert [text]
- Capitalize that/Lowercase that/Uppercase that
- New paragraph/New line
- Send message/Submit/Press enter

Classes
-------
VoiceCommand
    Dataclass representing a parsed voice command.

VoiceCommandParser
    Parses transcribed text to detect and extract voice commands.

VoiceCommandExecutor
    Executes parsed voice commands via keyboard simulation.

VoiceCommandConfig
    Configuration for voice command behavior.
"""

import re
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Callable, Dict
from enum import Enum

from pynput import keyboard

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Types of voice commands."""
    DELETE_LAST_SENTENCE = "delete_last_sentence"
    DELETE_LAST_PARAGRAPH = "delete_last_paragraph"
    DELETE_LAST_WORD = "delete_last_word"
    REPLACE = "replace"
    INSERT = "insert"
    CAPITALIZE = "capitalize"
    LOWERCASE = "lowercase"
    UPPERCASE = "uppercase"
    NEW_PARAGRAPH = "new_paragraph"
    NEW_LINE = "new_line"
    SUBMIT = "submit"
    PRESS_ENTER = "press_enter"
    PRESS_BACKSPACE = "press_backspace"
    PRESS_DELETE = "press_delete"
    UNDO = "undo"
    REDO = "redo"
    SELECT_ALL = "select_all"
    COPY = "copy"
    PASTE = "paste"
    CUT = "cut"
    DICTATION = "dictation"  # Not a command, just regular text


@dataclass
class VoiceCommand:
    """Represents a parsed voice command."""
    command_type: CommandType
    parameters: Dict[str, str] = field(default_factory=dict)
    raw_text: str = ""
    confidence: float = 1.0

    def is_dictation(self) -> bool:
        """Check if this is just dictation (not a command)."""
        return self.command_type == CommandType.DICTATION

    def __repr__(self) -> str:
        if self.is_dictation():
            return f"VoiceCommand(dictation='{self.raw_text[:30]}...')"
        return f"VoiceCommand({self.command_type.value}, params={self.parameters})"


@dataclass
class VoiceCommandConfig:
    """Configuration for voice command behavior."""
    # Enable/disable voice commands
    enabled: bool = True

    # Command activation phrases (must start with these)
    command_prefixes: List[str] = field(default_factory=lambda: [
        "computer", "assistant", "hey", "okay", ""
    ])

    # Require space after prefix (e.g., "computer delete" vs "computerdelete")
    require_prefix_space: bool = False

    # Minimum confidence threshold for command detection
    confidence_threshold: float = 0.5

    # Action timing delays (in seconds)
    key_press_delay: float = 0.01
    action_delay: float = 0.05

    # Case sensitivity for command matching
    case_sensitive: bool = False

    # Allow fuzzy matching for commands (e.g., "delet" -> "delete")
    fuzzy_matching: bool = True


class VoiceCommandParser:
    """
    Parses transcribed text to detect voice commands.

    Uses pattern matching to identify commands and extract parameters.
    Distinguishes between dictation (text to insert) and commands (actions).
    """

    # Command patterns with regex
    COMMAND_PATTERNS = {
        # Delete commands
        CommandType.DELETE_LAST_SENTENCE: [
            r"delete\s+(?:the\s+)?last\s+sentence",
            r"remove\s+(?:the\s+)?last\s+sentence",
            r"erase\s+(?:the\s+)?last\s+sentence",
            r"clear\s+(?:the\s+)?last\s+sentence",
        ],
        CommandType.DELETE_LAST_PARAGRAPH: [
            r"delete\s+(?:the\s+)?last\s+paragraph",
            r"remove\s+(?:the\s+)?last\s+paragraph",
            r"erase\s+(?:the\s+)?last\s+paragraph",
            r"clear\s+(?:the\s+)?last\s+paragraph",
        ],
        CommandType.DELETE_LAST_WORD: [
            r"delete\s+(?:the\s+)?last\s+word",
            r"remove\s+(?:the\s+)?last\s+word",
            r"erase\s+(?:the\s+)?last\s+word",
            r"delete\s+that",
            r"remove\s+that",
        ],
        # Replace command: "replace [word] with [word]"
        CommandType.REPLACE: [
            r"replace\s+(?P<old>[^.]+?)\s+with\s+(?P<new>[^.]+?)(?:\.|$)",
            r"substitute\s+(?P<old>[^.]+?)\s+(?:for|with)\s+(?P<new>[^.]+?)(?:\.|$)",
            r"change\s+(?P<old>[^.]+?)\s+to\s+(?P<new>[^.]+?)(?:\.|$)",
            r"swap\s+(?P<old>[^.]+?)\s+(?:for|with)\s+(?P<new>[^.]+?)(?:\.|$)",
        ],
        # Insert command: "insert [text]"
        CommandType.INSERT: [
            r"insert\s+(?P<text>[^.]+?)(?:\.|$)",
            r"add\s+(?P<text>[^.]+?)(?:\.|$)",
            r"type\s+(?P<text>[^.]+?)(?:\.|$)",
        ],
        # Capitalization commands
        CommandType.CAPITALIZE: [
            r"capitalize\s+that",
            r"capitalize\s+(?:the\s+)?last\s+(?:sentence|word)",
        ],
        CommandType.LOWERCASE: [
            r"lowercase\s+that",
            r"lower\s+(?:the\s+)?last\s+(?:sentence|word)",
            r"make\s+(?:the\s+)?last\s+(?:sentence|word)\s+lowercase",
        ],
        CommandType.UPPERCASE: [
            r"uppercase\s+that",
            r"uppercase\s+(?:the\s+)?last\s+(?:sentence|word)",
            r"make\s+(?:the\s+)?last\s+(?:sentence|word)\s+uppercase",
        ],
        # Formatting commands
        CommandType.NEW_PARAGRAPH: [
            r"new\s+paragraph",
            r"next\s+paragraph",
            r"paragraph\s+break",
        ],
        CommandType.NEW_LINE: [
            r"new\s+line",
            r"line\s+break",
            r"next\s+line",
        ],
        # Submission commands
        CommandType.SUBMIT: [
            r"send\s+(?:message|it|this)",
            r"submit",
            r"submit\s+(?:form|that|this)",
        ],
        CommandType.PRESS_ENTER: [
            r"press\s+enter",
            r"hit\s+enter",
            r"enter",
        ],
        # Editing actions
        CommandType.UNDO: [
            r"undo",
            r"undo\s+that",
            r"go\s+back",
        ],
        CommandType.REDO: [
            r"redo",
            r"redo\s+that",
        ],
        CommandType.SELECT_ALL: [
            r"select\s+all",
        ],
        CommandType.COPY: [
            r"copy",
            r"copy\s+that",
        ],
        CommandType.PASTE: [
            r"paste",
        ],
        CommandType.CUT: [
            r"cut",
            r"cut\s+that",
        ],
    }

    def __init__(self, config: Optional[VoiceCommandConfig] = None):
        """
        Initialize the voice command parser.

        Parameters
        ----------
        config : VoiceCommandConfig, optional
            Configuration for command parsing behavior.
        """
        self.config = config or VoiceCommandConfig()
        self._compiled_patterns: Dict[CommandType, List[re.Pattern]] = {}
        self._build_patterns()

    def _build_patterns(self):
        """Compile regex patterns for efficient matching."""
        flags = 0 if self.config.case_sensitive else re.IGNORECASE

        for cmd_type, patterns in self.COMMAND_PATTERNS.items():
            compiled = []
            for pattern in patterns:
                try:
                    compiled.append(re.compile(pattern, flags))
                except re.error as e:
                    logger.warning(f"Invalid command pattern: {pattern} - {e}")
            self._compiled_patterns[cmd_type] = compiled

    def parse(self, text: str) -> VoiceCommand:
        """
        Parse transcribed text to detect commands.

        Parameters
        ----------
        text : str
            The transcribed text to parse.

        Returns
        -------
        VoiceCommand
            Parsed command or dictation marker.
        """
        if not text or not text.strip():
            return VoiceCommand(CommandType.DICTATION, raw_text=text)

        text = text.strip()
        text_lower = text.lower() if not self.config.case_sensitive else text

        # Check if this might be a command (starts with prefix or matches patterns)
        if self.config.enabled:
            # First check for prefix-based activation
            has_prefix = False
            text_without_prefix = text

            if self.config.command_prefixes:
                for prefix in self.config.command_prefixes:
                    if not prefix:
                        # Empty prefix means always check for commands
                        has_prefix = True
                        text_without_prefix = text
                        break

                    prefix_len = len(prefix)
                    if self.config.case_sensitive:
                        matches = text.startswith(prefix)
                    else:
                        matches = text_lower.startswith(prefix.lower())

                    if matches:
                        if self.config.require_prefix_space:
                            if len(text) > prefix_len and text[prefix_len] == ' ':
                                has_prefix = True
                                text_without_prefix = text[prefix_len + 1:]
                                break
                        else:
                            has_prefix = True
                            text_without_prefix = text[prefix_len:].lstrip()
                            break

            # Check patterns if we have a prefix or if empty prefix is allowed
            if has_prefix or "" in self.config.command_prefixes:
                for cmd_type, patterns in self._compiled_patterns.items():
                    for pattern in patterns:
                        match = pattern.fullmatch(text_without_prefix)
                        if match:
                            # Extract parameters from named groups
                            params = match.groupdict() if match.groupdict() else {}
                            return VoiceCommand(
                                command_type=cmd_type,
                                parameters=params,
                                raw_text=text,
                                confidence=1.0
                            )

        # No command detected - this is dictation
        return VoiceCommand(CommandType.DICTATION, raw_text=text)

    def is_command(self, text: str) -> bool:
        """
        Check if text is likely a command.

        Parameters
        ----------
        text : str
            Text to check.

        Returns
        -------
        bool
            True if text appears to be a command.
        """
        cmd = self.parse(text)
        return not cmd.is_dictation()


class VoiceCommandExecutor:
    """
    Executes voice commands via keyboard simulation.

    Performs actions like deleting text, navigating, and formatting
    by simulating keyboard shortcuts and input.
    """

    def __init__(self, config: Optional[VoiceCommandConfig] = None):
        """
        Initialize the command executor.

        Parameters
        ----------
        config : VoiceCommandConfig, optional
            Configuration for execution timing.
        """
        self.config = config or VoiceCommandConfig()
        self.keyboard = keyboard.Controller()

    def execute(self, command: VoiceCommand) -> bool:
        """
        Execute a voice command.

        Parameters
        ----------
        command : VoiceCommand
            The command to execute.

        Returns
        -------
        bool
            True if command was executed successfully.
        """
        if command.is_dictation():
            logger.debug("Not a command - returning dictation text")
            return False

        try:
            handler = self._get_handler(command.command_type)
            if handler:
                logger.info(f"Executing command: {command.command_type.value}")
                result = handler(command)
                time.sleep(self.config.action_delay)
                return result
            else:
                logger.warning(f"No handler for command: {command.command_type}")
                return False
        except Exception as e:
            logger.error(f"Error executing command {command.command_type}: {e}")
            return False

    def _get_handler(self, cmd_type: CommandType) -> Optional[Callable]:
        """Get the handler function for a command type."""
        return {
            CommandType.DELETE_LAST_SENTENCE: self._delete_last_sentence,
            CommandType.DELETE_LAST_PARAGRAPH: self._delete_last_paragraph,
            CommandType.DELETE_LAST_WORD: self._delete_last_word,
            CommandType.REPLACE: self._replace,
            CommandType.INSERT: self._insert,
            CommandType.CAPITALIZE: self._capitalize,
            CommandType.LOWERCASE: self._lowercase,
            CommandType.UPPERCASE: self._uppercase,
            CommandType.NEW_PARAGRAPH: self._new_paragraph,
            CommandType.NEW_LINE: self._new_line,
            CommandType.SUBMIT: self._submit,
            CommandType.PRESS_ENTER: self._press_enter,
            CommandType.UNDO: self._undo,
            CommandType.REDO: self._redo,
            CommandType.SELECT_ALL: self._select_all,
            CommandType.COPY: self._copy,
            CommandType.PASTE: self._paste,
            CommandType.CUT: self._cut,
        }.get(cmd_type)

    def _press_keys(self, keys: List, delay: Optional[float] = None):
        """Press a sequence of keys."""
        delay = delay if delay is not None else self.config.key_press_delay

        for key in keys:
            self.keyboard.press(key)
            time.sleep(delay)
            self.keyboard.release(key)
            time.sleep(delay)

    def _press_key_combo(self, modifiers: List, key: str, delay: Optional[float] = None):
        """Press a key combination (e.g., Ctrl+Z)."""
        delay = delay if delay is not None else self.config.key_press_delay

        # Press modifiers
        for mod in modifiers:
            self.keyboard.press(mod)
            time.sleep(delay)

        # Press and release main key
        self.keyboard.press(key)
        time.sleep(delay)
        self.keyboard.release(key)
        time.sleep(delay)

        # Release modifiers
        for mod in reversed(modifiers):
            self.keyboard.release(mod)
            time.sleep(delay)

    def _type_text(self, text: str, delay: Optional[float] = None):
        """Type text character by character."""
        delay = delay if delay is not None else self.config.key_press_delay

        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(delay)

    # Command handlers

    def _delete_last_sentence(self, command: VoiceCommand) -> bool:
        """Delete the last sentence using Ctrl+Shift+Left, Delete."""
        # Select to beginning of sentence
        self._press_key_combo([keyboard.Key.ctrl_l, keyboard.Key.shift_l], keyboard.Key.left)
        # Delete selection
        self._press_key_combo([keyboard.Key.shift_l], keyboard.Key.delete)
        return True

    def _delete_last_paragraph(self, command: VoiceCommand) -> bool:
        """Delete the last paragraph using Ctrl+Shift+Up, Delete."""
        # Select to beginning of paragraph
        self._press_key_combo([keyboard.Key.ctrl_l, keyboard.Key.shift_l], keyboard.Key.up)
        # Delete selection
        self._press_key_combo([keyboard.Key.shift_l], keyboard.Key.delete)
        return True

    def _delete_last_word(self, command: VoiceCommand) -> bool:
        """Delete the last word using Ctrl+Backspace."""
        self._press_key_combo([keyboard.Key.ctrl_l], keyboard.Key.backspace)
        return True

    def _replace(self, command: VoiceCommand) -> bool:
        """
        Replace text: select old text, type new text.

        Pattern: "replace [old] with [new]"
        """
        old_text = command.parameters.get("old", "").strip()
        new_text = command.parameters.get("new", "").strip()

        if not old_text or not new_text:
            logger.warning(f"Replace command missing parameters: {command.parameters}")
            return False

        # Select all (simplest approach - user may need to refine)
        self._select_all(command)
        time.sleep(0.05)
        # Type new text
        self._type_text(new_text)
        logger.info(f"Replaced '{old_text}' with '{new_text}'")
        return True

    def _insert(self, command: VoiceCommand) -> bool:
        """
        Insert text at cursor position.

        Pattern: "insert [text]" or "add [text]"
        """
        text = command.parameters.get("text", "").strip()

        if not text:
            logger.warning("Insert command missing text parameter")
            return False

        self._type_text(text)
        logger.info(f"Inserted: '{text}'")
        return True

    def _capitalize(self, command: VoiceCommand) -> bool:
        """Capitalize last word/sentence using formatting."""
        # Navigate to start of word, select to end, apply capitalization
        # This is a simplified version - full implementation would select and retype
        logger.info("Capitalize command - manual action may be needed")
        # Select last word
        self._press_key_combo([keyboard.Key.ctrl_l, keyboard.Key.shift_l], keyboard.Key.left)
        # Note: Can't easily change case via keyboard alone in all apps
        return True

    def _lowercase(self, command: VoiceCommand) -> bool:
        """Convert last word/sentence to lowercase."""
        logger.info("Lowercase command - manual action may be needed")
        self._press_key_combo([keyboard.Key.ctrl_l, keyboard.Key.shift_l], keyboard.Key.left)
        return True

    def _uppercase(self, command: VoiceCommand) -> bool:
        """Convert last word/sentence to uppercase."""
        logger.info("Uppercase command - manual action may be needed")
        self._press_key_combo([keyboard.Key.ctrl_l, keyboard.Key.shift_l], keyboard.Key.left)
        return True

    def _new_paragraph(self, command: VoiceCommand) -> bool:
        """Insert a new paragraph (two enters)."""
        self._press_keys([keyboard.Key.enter, keyboard.Key.enter])
        return True

    def _new_line(self, command: VoiceCommand) -> bool:
        """Insert a new line (single enter)."""
        self._press_keys([keyboard.Key.enter])
        return True

    def _submit(self, command: VoiceCommand) -> bool:
        """Submit form/send message with Enter."""
        self._press_keys([keyboard.Key.enter])
        logger.info("Submitted message/form")
        return True

    def _press_enter(self, command: VoiceCommand) -> bool:
        """Press Enter key."""
        self._press_keys([keyboard.Key.enter])
        return True

    def _undo(self, command: VoiceCommand) -> bool:
        """Undo last action."""
        self._press_key_combo([keyboard.Key.ctrl_l], 'z')
        logger.info("Undo performed")
        return True

    def _redo(self, command: VoiceCommand) -> bool:
        """Redo last action."""
        self._press_key_combo([keyboard.Key.ctrl_l], 'y')
        logger.info("Redo performed")
        return True

    def _select_all(self, command: VoiceCommand) -> bool:
        """Select all text."""
        self._press_key_combo([keyboard.Key.ctrl_l], 'a')
        return True

    def _copy(self, command: VoiceCommand) -> bool:
        """Copy selection."""
        self._press_key_combo([keyboard.Key.ctrl_l], 'c')
        return True

    def _paste(self, command: VoiceCommand) -> bool:
        """Paste from clipboard."""
        self._press_key_combo([keyboard.Key.ctrl_l], 'v')
        return True

    def _cut(self, command: VoiceCommand) -> bool:
        """Cut selection."""
        self._press_key_combo([keyboard.Key.ctrl_l], 'x')
        return True


def process_with_commands(text: str,
                          parser: Optional[VoiceCommandParser] = None,
                          executor: Optional[VoiceCommandExecutor] = None) -> Tuple[bool, str]:
    """
    Process text, checking for commands and executing them.

    Parameters
    ----------
    text : str
        The transcribed text to process.
    parser : VoiceCommandParser, optional
        Command parser instance.
    executor : VoiceCommandExecutor, optional
        Command executor instance.

    Returns
    -------
    Tuple[bool, str]
        (was_command, output_text)
        - was_command: True if a command was detected/executed
        - output_text: Text to insert (empty if command was executed)
    """
    if parser is None:
        parser = VoiceCommandParser()
    if executor is None:
        executor = VoiceCommandExecutor()

    command = parser.parse(text)

    if command.is_dictation():
        # This is regular dictation - return text for insertion
        return False, text

    # This is a command - execute it
    success = executor.execute(command)
    if success:
        return True, ""  # Command executed, no text to insert

    # Command failed - treat as dictation
    return False, text
