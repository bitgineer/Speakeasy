"""
App-specific paste rules manager for faster-whisper-hotkey Flet GUI.

This module manages per-application paste method rules, allowing users to
configure how text should be pasted into different applications. It builds
on the existing app_rules_manager infrastructure.

Classes
-------
AppPasteRule
    Represents a paste rule for a specific application.

AppPasteRulesManager
    Manages paste rules with CRUD operations.

Functions
---------
get_app_paste_rules_manager
    Get singleton instance of the paste rules manager.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict

from ..app_detector import AppMatcher, MatchType, get_active_window_info
from ..settings import settings_dir
from .paste_types import PasteMethod

logger = logging.getLogger(__name__)

# Paste rules file path
PASTE_RULES_FILE = os.path.join(settings_dir, "app_paste_rules.json")


@dataclass
class AppPasteRule:
    """
    Represents a paste rule for a specific application.

    Attributes
    ----------
    id
        Unique identifier for this rule.
    name
        Display name for the rule.
    matchers
        List of matchers to identify the application.
    paste_method
        The paste method to use for this app (clipboard, typing, direct).
    priority
        Higher priority rules are checked first.
    enabled
        Whether the rule is enabled.
    created_at
        ISO timestamp of when the rule was created.
    notes
        User notes for this rule.
    """
    id: str
    name: str
    matchers: List[Dict[str, Any]]
    paste_method: str
    priority: int = 0
    enabled: bool = True
    created_at: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppPasteRule":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            matchers=[
                {
                    "match_type": m.get("match_type", "window_class"),
                    "pattern": m.get("pattern", ""),
                    "case_sensitive": m.get("case_sensitive", False),
                }
                for m in data.get("matchers", [])
            ],
            paste_method=data.get("paste_method", "clipboard"),
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at", ""),
            notes=data.get("notes", ""),
        )

    def matches(self, window_class: str = "", window_title: str = "", process_name: str = "") -> bool:
        """
        Check if this rule matches the given window info.

        Parameters
        ----------
        window_class
            Window class to match against.
        window_title
            Window title to match against.
        process_name
            Process name to match against.

        Returns
        -------
        bool
            True if all matchers pass.
        """
        if not self.enabled:
            return False

        for m in self.matchers:
            match_type = m.get("match_type", "window_class")
            pattern = m.get("pattern", "")
            case_sensitive = m.get("case_sensitive", False)

            target = ""
            if match_type == "window_class":
                target = window_class
            elif match_type == "window_title":
                target = window_title
            elif match_type == "process_name":
                target = process_name
            elif match_type == "regex_title":
                target = window_title
            elif match_type == "regex_class":
                target = window_class
            else:
                continue

            if not case_sensitive:
                target = target.lower()
                pattern = pattern.lower()

            if match_type in ["regex_title", "regex_class"]:
                import re
                try:
                    if not re.search(pattern, target):
                        return False
                except re.error:
                    logger.warning(f"Invalid regex pattern: {pattern}")
                    return False
            else:
                if pattern not in target:
                    return False

        return True

    def get_paste_method(self) -> PasteMethod:
        """
        Get the paste method for this rule.

        Returns
        -------
        PasteMethod
            The paste method enum value.
        """
        try:
            return PasteMethod(self.paste_method)
        except (ValueError, AttributeError):
            return PasteMethod.CLIPBOARD


class AppPasteRulesManager:
    """
    Manages per-application paste rules.

    This manager handles loading, saving, and matching paste rules
    against the active window. Rules are evaluated by priority.
    """

    # Pre-configured rules for common applications
    DEFAULT_RULES = [
        {
            "name": "Visual Studio Code",
            "matchers": [
                {"match_type": "window_class", "pattern": "Chrome_WidgetWin_1", "case_sensitive": False}
            ],
            "paste_method": "clipboard",
            "priority": 100,
            "notes": "VS Code supports standard clipboard paste"
        },
        {
            "name": "Windows Terminal",
            "matchers": [
                {"match_type": "window_class", "pattern": "WindowsTerminal", "case_sensitive": False}
            ],
            "paste_method": "typing",
            "priority": 100,
            "notes": "Terminal needs character-by-character typing"
        },
        {
            "name": "Command Prompt",
            "matchers": [
                {"match_type": "window_class", "pattern": "ConsoleWindowClass", "case_sensitive": False}
            ],
            "paste_method": "typing",
            "priority": 100,
            "notes": "CMD needs character-by-character typing"
        },
        {
            "name": "PuTTY",
            "matchers": [
                {"match_type": "window_class", "pattern": "PuTTY", "case_sensitive": False}
            ],
            "paste_method": "typing",
            "priority": 100,
            "notes": "PuTTY needs typing mode"
        },
        {
            "name": "Discord",
            "matchers": [
                {"match_type": "window_class", "pattern": "Chrome_WidgetWin_1", "case_sensitive": False},
                {"match_type": "process_name", "pattern": "Discord", "case_sensitive": False}
            ],
            "paste_method": "clipboard",
            "priority": 90,
            "notes": "Discord supports standard clipboard paste"
        },
        {
            "name": "Slack",
            "matchers": [
                {"match_type": "process_name", "pattern": "slack", "case_sensitive": False}
            ],
            "paste_method": "clipboard",
            "priority": 90,
            "notes": "Slack supports standard clipboard paste"
        },
        {
            "name": "Browsers (Chrome/Edge)",
            "matchers": [
                {"match_type": "window_class", "pattern": "Chrome_WidgetWin_1", "case_sensitive": False}
            ],
            "paste_method": "clipboard",
            "priority": 50,
            "notes": "Browsers support standard clipboard paste"
        },
        {
            "name": "Firefox",
            "matchers": [
                {"match_type": "window_class", "pattern": "MozillaWindowClass", "case_sensitive": False}
            ],
            "paste_method": "clipboard",
            "priority": 50,
            "notes": "Firefox supports standard clipboard paste"
        },
    ]

    def __init__(self):
        """Initialize the paste rules manager."""
        self.rules: List[AppPasteRule] = []
        self._load_rules()

    def _load_rules(self):
        """Load rules from disk."""
        try:
            if os.path.exists(PASTE_RULES_FILE):
                with open(PASTE_RULES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.rules = [AppPasteRule.from_dict(r) for r in data]
                    logger.info(f"Loaded {len(self.rules)} app paste rules")
            else:
                # Initialize with default rules
                self._initialize_default_rules()
        except Exception as e:
            logger.error(f"Failed to load app paste rules: {e}")
            self.rules = []
            self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize with default rules for common apps."""
        self.rules = []
        for rule_data in self.DEFAULT_RULES:
            rule_id = str(uuid.uuid4())[:8]
            rule = AppPasteRule(
                id=rule_id,
                name=rule_data["name"],
                matchers=rule_data["matchers"],
                paste_method=rule_data["paste_method"],
                priority=rule_data.get("priority", 0),
                notes=rule_data.get("notes", ""),
                created_at=datetime.now().isoformat(),
            )
            self.rules.append(rule)
        self._sort_rules()
        self._save_rules()

    def _save_rules(self):
        """Save rules to disk."""
        try:
            os.makedirs(settings_dir, exist_ok=True)
            with open(PASTE_RULES_FILE, "w", encoding="utf-8") as f:
                data = [r.to_dict() for r in self.rules]
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.rules)} app paste rules")
        except Exception as e:
            logger.error(f"Failed to save app paste rules: {e}")

    def _sort_rules(self):
        """Sort rules by priority (highest first)."""
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def add_rule(self, rule: AppPasteRule):
        """
        Add a new rule.

        Parameters
        ----------
        rule
            The rule to add.
        """
        self.rules.append(rule)
        self._sort_rules()
        self._save_rules()

    def update_rule(self, rule_id: str, updated_rule: AppPasteRule) -> bool:
        """
        Update an existing rule.

        Parameters
        ----------
        rule_id
            ID of the rule to update.
        updated_rule
            The updated rule data.

        Returns
        -------
        bool
            True if updated, False if not found.
        """
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                self.rules[i] = updated_rule
                self._sort_rules()
                self._save_rules()
                return True
        return False

    def delete_rule(self, rule_id: str) -> bool:
        """
        Delete a rule by ID.

        Parameters
        ----------
        rule_id
            ID of the rule to delete.

        Returns
        -------
        bool
            True if deleted, False if not found.
        """
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]
        if len(self.rules) < initial_count:
            self._save_rules()
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[AppPasteRule]:
        """
        Get a rule by ID.

        Parameters
        ----------
        rule_id
            ID of the rule to get.

        Returns
        -------
        AppPasteRule or None
            The rule if found, None otherwise.
        """
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def get_all_rules(self) -> List[AppPasteRule]:
        """
        Get all rules, sorted by priority.

        Returns
        -------
        List[AppPasteRule]
            All enabled and disabled rules.
        """
        return sorted(self.rules, key=lambda r: r.priority, reverse=True)

    def match_active_window(self) -> Optional[AppPasteRule]:
        """
        Find the highest priority rule matching the active window.

        Returns
        -------
        AppPasteRule or None
            The matching rule with highest priority, or None if no match.
        """
        window_info = get_active_window_info()

        for rule in self.rules:
            if rule.enabled and rule.matches(
                window_class=window_info.window_class,
                window_title=window_info.window_title,
                process_name=window_info.process_name
            ):
                logger.info(f"App paste rule matched: {rule.name} (priority {rule.priority})")
                return rule

        return None

    def get_paste_method_for_active_window(self) -> PasteMethod:
        """
        Get the paste method for the active window.

        Returns
        -------
        PasteMethod
            The paste method to use, or clipboard default.
        """
        rule = self.match_active_window()
        if rule:
            return rule.get_paste_method()
        return PasteMethod.CLIPBOARD

    def create_rule(
        self,
        name: str,
        matchers: List[Dict[str, Any]],
        paste_method: str = "clipboard",
        priority: int = 0,
        enabled: bool = True,
        notes: str = "",
    ) -> AppPasteRule:
        """
        Create a new rule with a unique ID.

        Parameters
        ----------
        name
            Display name for the rule.
        matchers
            List of matcher dictionaries.
        paste_method
            Paste method: clipboard, typing, or direct.
        priority
            Priority for rule ordering (higher = checked first).
        enabled
            Whether the rule is enabled.
        notes
            User notes for this rule.

        Returns
        -------
        AppPasteRule
            The created rule.
        """
        rule_id = str(uuid.uuid4())[:8]
        created_at = datetime.now().isoformat()

        rule = AppPasteRule(
            id=rule_id,
            name=name,
            matchers=matchers,
            paste_method=paste_method,
            priority=priority,
            enabled=enabled,
            created_at=created_at,
            notes=notes
        )

        self.add_rule(rule)
        return rule

    def import_rule(self, rule_data: dict) -> Optional[AppPasteRule]:
        """
        Import a rule from dictionary data.

        Parameters
        ----------
        rule_data
            Dictionary containing rule data.

        Returns
        -------
        AppPasteRule or None
            The imported rule, or None if import failed.
        """
        try:
            rule = AppPasteRule.from_dict(rule_data)
            self.add_rule(rule)
            return rule
        except Exception as e:
            logger.error(f"Failed to import rule: {e}")
            return None

    def export_rules(self) -> str:
        """
        Export rules as JSON string.

        Returns
        -------
        str
            JSON string of all rules.
        """
        return json.dumps([r.to_dict() for r in self.rules], indent=2)

    def import_rules(self, json_data: str, replace: bool = False) -> int:
        """
        Import rules from JSON string.

        Parameters
        ----------
        json_data
            JSON string containing rules.
        replace
            If True, replace all existing rules; if False, append.

        Returns
        -------
        int
            Number of rules imported.
        """
        try:
            data = json.loads(json_data)
            imported = [AppPasteRule.from_dict(r) for r in data]

            if replace:
                self.rules = imported
            else:
                self.rules.extend(imported)

            self._sort_rules()
            self._save_rules()
            return len(imported)
        except Exception as e:
            logger.error(f"Failed to import rules: {e}")
            return 0

    def get_next_priority(self) -> int:
        """
        Get the next available priority (current max + 10).

        Returns
        -------
        int
            Suggested priority value for a new rule.
        """
        if not self.rules:
            return 10
        return max(r.priority for r in self.rules) + 10

    def reindex_priorities(self):
        """Reindex all rules with consistent priority intervals (10, 20, 30...)."""
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        for i, rule in enumerate(self.rules):
            rule.priority = (len(self.rules) - i) * 10
        self._save_rules()

    def get_suggested_rules(self) -> List[Dict[str, Any]]:
        """
        Get list of suggested rules for common applications.

        Returns
        -------
        List[Dict]
            List of suggested rule configurations.
        """
        return [
            {
                "name": "Visual Studio Code",
                "matchers": [
                    {"match_type": "window_class", "pattern": "Chrome_WidgetWin_1", "case_sensitive": False}
                ],
                "paste_method": "clipboard",
                "notes": "VS Code supports standard clipboard paste (Ctrl+V)"
            },
            {
                "name": "Windows Terminal",
                "matchers": [
                    {"match_type": "window_class", "pattern": "WindowsTerminal", "case_sensitive": False}
                ],
                "paste_method": "typing",
                "notes": "Terminal needs character-by-character typing for best compatibility"
            },
            {
                "name": "Command Prompt / CMD",
                "matchers": [
                    {"match_type": "window_class", "pattern": "ConsoleWindowClass", "case_sensitive": False}
                ],
                "paste_method": "typing",
                "notes": "CMD window requires typing mode"
            },
            {
                "name": "PowerShell",
                "matchers": [
                    {"match_type": "window_class", "pattern": "ConsoleWindowClass", "case_sensitive": False}
                ],
                "paste_method": "typing",
                "notes": "PowerShell console requires typing mode"
            },
            {
                "name": "PuTTY",
                "matchers": [
                    {"match_type": "window_class", "pattern": "PuTTY", "case_sensitive": False}
                ],
                "paste_method": "typing",
                "notes": "PuTTY SSH client requires typing mode"
            },
            {
                "name": "Discord",
                "matchers": [
                    {"match_type": "process_name", "pattern": "Discord", "case_sensitive": False}
                ],
                "paste_method": "clipboard",
                "notes": "Discord supports standard clipboard paste"
            },
            {
                "name": "Slack",
                "matchers": [
                    {"match_type": "process_name", "pattern": "slack", "case_sensitive": False}
                ],
                "paste_method": "clipboard",
                "notes": "Slack supports standard clipboard paste"
            },
            {
                "name": "Microsoft Teams",
                "matchers": [
                    {"match_type": "process_name", "pattern": "Teams", "case_sensitive": False}
                ],
                "paste_method": "clipboard",
                "notes": "Teams supports standard clipboard paste"
            },
            {
                "name": "Google Chrome",
                "matchers": [
                    {"match_type": "window_class", "pattern": "Chrome_WidgetWin_1", "case_sensitive": False}
                ],
                "paste_method": "clipboard",
                "notes": "Chrome supports standard clipboard paste"
            },
            {
                "name": "Microsoft Edge",
                "matchers": [
                    {"match_type": "window_class", "pattern": "Chrome_WidgetWin_1", "case_sensitive": False},
                    {"match_type": "process_name", "pattern": "msedge", "case_sensitive": False}
                ],
                "paste_method": "clipboard",
                "notes": "Edge supports standard clipboard paste"
            },
            {
                "name": "Firefox",
                "matchers": [
                    {"match_type": "window_class", "pattern": "MozillaWindowClass", "case_sensitive": False}
                ],
                "paste_method": "clipboard",
                "notes": "Firefox supports standard clipboard paste"
            },
            {
                "name": "Notepad",
                "matchers": [
                    {"match_type": "window_class", "pattern": "Notepad", "case_sensitive": False}
                ],
                "paste_method": "clipboard",
                "notes": "Notepad supports standard clipboard paste"
            },
            {
                "name": "Notepad++",
                "matchers": [
                    {"match_type": "window_class", "pattern": "Notepad++", "case_sensitive": False}
                ],
                "paste_method": "clipboard",
                "notes": "Notepad++ supports standard clipboard paste"
            },
            {
                "name": "Sublime Text",
                "matchers": [
                    {"match_type": "window_class", "pattern": "PX_WINDOW_CLASS", "case_sensitive": False}
                ],
                "paste_method": "clipboard",
                "notes": "Sublime Text supports standard clipboard paste"
            },
        ]


# Singleton instance
_manager_instance: Optional[AppPasteRulesManager] = None


def get_app_paste_rules_manager() -> AppPasteRulesManager:
    """
    Get singleton instance of the paste rules manager.

    Returns
    -------
    AppPasteRulesManager
        The singleton manager instance.
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = AppPasteRulesManager()
    return _manager_instance
