"""
Application rules manager for faster-whisper-hotkey.

This module manages per-application configuration rules, including loading,
saving, and matching rules against active windows.

Classes
-------
AppRulesManager
    Manages application rules and provides matching functionality.

Functions
---------
get_app_rules_manager
    Get singleton instance of the rules manager.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from .app_detector import AppRule, AppMatcher, MatchType, get_active_window_info
from .settings import settings_dir

logger = logging.getLogger(__name__)

# Rules file path
RULES_FILE = os.path.join(settings_dir, "app_rules.json")


class AppRulesManager:
    """Manages per-application configuration rules."""

    def __init__(self):
        """Initialize the rules manager."""
        self.rules: List[AppRule] = []
        self._load_rules()

    def _load_rules(self):
        """Load rules from disk."""
        try:
            if os.path.exists(RULES_FILE):
                with open(RULES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.rules = [AppRule.from_dict(r) for r in data]
                    logger.info(f"Loaded {len(self.rules)} app rules")
            else:
                self.rules = []
        except Exception as e:
            logger.error(f"Failed to load app rules: {e}")
            self.rules = []

    def _save_rules(self):
        """Save rules to disk."""
        try:
            os.makedirs(settings_dir, exist_ok=True)
            with open(RULES_FILE, "w", encoding="utf-8") as f:
                data = [r.to_dict() for r in self.rules]
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.rules)} app rules")
        except Exception as e:
            logger.error(f"Failed to save app rules: {e}")

    def add_rule(self, rule: AppRule):
        """Add a new rule."""
        self.rules.append(rule)
        self._sort_rules()
        self._save_rules()

    def update_rule(self, rule_id: str, updated_rule: AppRule):
        """Update an existing rule."""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                self.rules[i] = updated_rule
                self._sort_rules()
                self._save_rules()
                return True
        return False

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule by ID."""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]
        if len(self.rules) < initial_count:
            self._save_rules()
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[AppRule]:
        """Get a rule by ID."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def get_all_rules(self) -> List[AppRule]:
        """Get all rules, sorted by priority."""
        return self._sort_rules_copy()

    def _sort_rules(self):
        """Sort rules by priority (highest first)."""
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def _sort_rules_copy(self) -> List[AppRule]:
        """Return a sorted copy of rules."""
        return sorted(self.rules, key=lambda r: r.priority, reverse=True)

    def match_active_window(self) -> Optional[AppRule]:
        """Find the highest priority rule matching the active window.

        Returns:
            The matching rule with highest priority, or None if no match
        """
        window_info = get_active_window_info()

        for rule in self.rules:
            if rule.enabled and rule.matches(
                window_class=window_info.window_class,
                window_title=window_info.window_title,
                process_name=window_info.process_name
            ):
                logger.info(f"App rule matched: {rule.name} (priority {rule.priority})")
                return rule

        return None

    def get_app_settings(self, global_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Get settings with app-specific overrides applied.

        Args:
            global_settings: Global settings dictionary

        Returns:
            Settings dictionary with app-specific overrides applied
        """
        result = global_settings.copy()

        # Find matching rule
        rule = self.match_active_window()
        if rule:
            # Apply overrides
            if rule.hotkey is not None:
                result["hotkey"] = rule.hotkey
            if rule.model_type is not None:
                result["model_type"] = rule.model_type
            if rule.model_name is not None:
                result["model_name"] = rule.model_name
            if rule.compute_type is not None:
                result["compute_type"] = rule.compute_type
            if rule.device is not None:
                result["device"] = rule.device
            if rule.language is not None:
                result["language"] = rule.language

            # Merge text processing settings
            if rule.text_processing:
                if "text_processing" not in result:
                    result["text_processing"] = {}
                result["text_processing"].update(rule.text_processing)

        return result

    def create_rule(
        self,
        name: str,
        matchers: List[AppMatcher],
        priority: int = 0,
        hotkey: Optional[str] = None,
        model_type: Optional[str] = None,
        model_name: Optional[str] = None,
        compute_type: Optional[str] = None,
        device: Optional[str] = None,
        language: Optional[str] = None,
        text_processing: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        notes: str = ""
    ) -> AppRule:
        """Create a new rule with a unique ID.

        Args:
            name: Display name for the rule
            matchers: List of matchers for this rule
            priority: Priority for rule ordering (higher = checked first)
            hotkey: Override hotkey for this app
            model_type: Override model type
            model_name: Override model name
            compute_type: Override compute type
            device: Override device
            language: Override language
            text_processing: Override text processing settings
            enabled: Whether the rule is enabled
            notes: User notes for this rule

        Returns:
            The created AppRule
        """
        rule_id = str(uuid.uuid4())[:8]
        created_at = datetime.now().isoformat()

        rule = AppRule(
            id=rule_id,
            name=name,
            matchers=matchers,
            priority=priority,
            hotkey=hotkey,
            model_type=model_type,
            model_name=model_name,
            compute_type=compute_type,
            device=device,
            language=language,
            text_processing=text_processing,
            enabled=enabled,
            created_at=created_at,
            notes=notes
        )

        self.add_rule(rule)
        return rule

    def export_rules(self) -> str:
        """Export rules as JSON string."""
        return json.dumps([r.to_dict() for r in self.rules], indent=2)

    def import_rules(self, json_data: str, replace: bool = False) -> int:
        """Import rules from JSON string.

        Args:
            json_data: JSON string containing rules
            replace: If True, replace all existing rules; if False, append

        Returns:
            Number of rules imported
        """
        try:
            data = json.loads(json_data)
            imported = [AppRule.from_dict(r) for r in data]

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
        """Get the next available priority (current max + 10)."""
        if not self.rules:
            return 10
        return max(r.priority for r in self.rules) + 10

    def get_common_apps(self) -> List[Dict[str, str]]:
        """Get list of common applications for quick setup.

        Returns:
            List of common app configurations
        """
        common_apps = [
            {
                "name": "Visual Studio Code",
                "matchers": [{"match_type": "window_class", "pattern": "code"}],
                "suggested_settings": {"language": "en"}
            },
            {
                "name": "Discord",
                "matchers": [{"match_type": "window_class", "pattern": "discord"}],
                "suggested_settings": {}
            },
            {
                "name": "Slack",
                "matchers": [{"match_type": "window_class", "pattern": "slack"}],
                "suggested_settings": {}
            },
            {
                "name": "Chrome",
                "matchers": [{"match_type": "window_class", "pattern": "chrome"}],
                "suggested_settings": {}
            },
            {
                "name": "Firefox",
                "matchers": [{"match_type": "window_class", "pattern": "firefox"}],
                "suggested_settings": {}
            },
            {
                "name": "Terminal",
                "matchers": [{"match_type": "window_class", "pattern": "terminal"}],
                "suggested_settings": {}
            },
            {
                "name": "Steam",
                "matchers": [{"match_type": "window_class", "pattern": "steam"}],
                "suggested_settings": {"model_type": "parakeet", "model_name": "nvidia/parakeet-tdt-0.6b-v3"}
            },
            {
                "name": "Games (generic)",
                "matchers": [{"match_type": "window_class", "pattern": "UnityClass"}],
                "suggested_settings": {"model_type": "parakeet", "model_name": "nvidia/parakeet-tdt-0.6b-v3"}
            },
        ]
        return common_apps

    def reindex_priorities(self):
        """Reindex all rules with consistent priority intervals (10, 20, 30...)."""
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        for i, rule in enumerate(self.rules):
            rule.priority = (len(self.rules) - i) * 10
        self._save_rules()


# Singleton instance
_manager_instance: Optional[AppRulesManager] = None


def get_app_rules_manager() -> AppRulesManager:
    """Get singleton instance of the rules manager."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = AppRulesManager()
    return _manager_instance
