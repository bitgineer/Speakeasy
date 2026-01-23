"""
Snippets manager for voice-activated text expansion.

This module provides a comprehensive system for managing text snippets
that can be triggered by voice commands. Features include variable
substitution, category organization, usage tracking, and search/filter.

Classes
-------
Snippet
    Represents a single text snippet with trigger and metadata.

SnippetCategory
    Represents a category for organizing snippets.

SnippetsManager
    Main class for managing snippets with persistence and expansion.

Functions
---------
get_snippets_manager
    Get the global snippets manager instance.

Notes
-----
Snippets are stored in ~/.config/faster_whisper_hotkey/snippets_config.json
Variables in snippets use {variable_name} syntax.
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from .settings import settings_dir

logger = logging.getLogger(__name__)

# Path to snippets configuration file
SNIPPETS_FILE = os.path.join(settings_dir, "snippets_config.json")

# Default categories
DEFAULT_CATEGORIES = {
    "general": {
        "id": "general",
        "name": "General",
        "description": "General purpose snippets",
    },
    "contact": {
        "id": "contact",
        "name": "Contact Info",
        "description": "Email, phone, and address snippets",
    },
    "professional": {
        "id": "professional",
        "name": "Professional",
        "description": "Work-related snippets and templates",
    },
}

# Default snippets
DEFAULT_SNIPPETS = {
    "calendar": {
        "id": "calendar",
        "name": "Calendar Link",
        "trigger": "calendar",
        "content": "https://calendly.com/yourname",
        "description": "Insert Calendly link",
        "category": "general",
        "enabled": True,
        "variables": [],
        "created_at": datetime.now().isoformat(),
        "usage_count": 0,
        "last_used": None,
    },
    "email": {
        "id": "email",
        "name": "My Email",
        "trigger": "my email",
        "content": "your.email@example.com",
        "description": "Insert email address",
        "category": "contact",
        "enabled": True,
        "variables": [],
        "created_at": datetime.now().isoformat(),
        "usage_count": 0,
        "last_used": None,
    },
}


@dataclass
class SnippetVariable:
    """Represents a variable in a snippet."""
    name: str
    default_value: str = ""
    prompt: str = ""


@dataclass
class Snippet:
    """Represents a single text snippet."""

    id: str
    name: str
    trigger: str
    content: str
    description: str
    category: str = "general"
    enabled: bool = True
    variables: List[Dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0
    last_used: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Snippet':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SnippetCategory:
    """Represents a category for organizing snippets."""

    id: str
    name: str
    description: str = ""


class SnippetsManager:
    """Manages text snippets with expansion and usage tracking."""

    def __init__(self):
        self.snippets: Dict[str, Snippet] = {}
        self.categories: Dict[str, SnippetCategory] = {}
        self.callbacks: List[Callable[[str, str], None]] = []

        self.load()

    def load(self) -> None:
        """Load snippets from the configuration file."""
        try:
            with open(SNIPPETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._load_from_dict(data)
        except FileNotFoundError:
            logger.info("No snippets config found, using defaults")
            self._load_defaults()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse snippets config: {e}")
            self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default snippets and categories."""
        # Load categories
        for cat_data in DEFAULT_CATEGORIES.values():
            category = SnippetCategory(**cat_data)
            self.categories[category.id] = category

        # Load snippets
        for snippet_data in DEFAULT_SNIPPETS.values():
            snippet = Snippet.from_dict(snippet_data)
            self.snippets[snippet.id] = snippet

    def _load_from_dict(self, data: Dict) -> None:
        """Load snippets and categories from a dictionary structure."""
        self.snippets.clear()
        self.categories.clear()

        # Load categories
        for cat_data in data.get("categories", []):
            category = SnippetCategory(**cat_data)
            self.categories[category.id] = category

        # Ensure default categories exist
        for cat_id, cat_data in DEFAULT_CATEGORIES.items():
            if cat_id not in self.categories:
                self.categories[cat_id] = SnippetCategory(**cat_data)

        # Load snippets
        for snippet_data in data.get("snippets", []):
            snippet = Snippet.from_dict(snippet_data)
            self.snippets[snippet.id] = snippet

    def save(self) -> None:
        """Save snippets to the configuration file."""
        data = {
            "categories": [
                asdict(cat) for cat in self.categories.values()
            ],
            "snippets": [
                snippet.to_dict() for snippet in self.snippets.values()
            ],
        }

        try:
            with open(SNIPPETS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save snippets: {e}")

    def get(self, snippet_id: str) -> Optional[Snippet]:
        """Get a snippet by ID."""
        return self.snippets.get(snippet_id)

    def get_by_trigger(self, trigger: str) -> Optional[Snippet]:
        """Get a snippet by its trigger phrase."""
        for snippet in self.snippets.values():
            if snippet.enabled and snippet.trigger.lower() == trigger.lower():
                return snippet
        return None

    def get_all(self) -> List[Snippet]:
        """Get all snippets."""
        return list(self.snippets.values())

    def get_by_category(self, category_id: str) -> List[Snippet]:
        """Get all snippets in a category."""
        return [
            s for s in self.snippets.values()
            if s.category == category_id
        ]

    def get_categories(self) -> List[SnippetCategory]:
        """Get all categories."""
        return list(self.categories.values())

    def add_snippet(self, snippet: Snippet) -> Tuple[bool, str]:
        """Add a new snippet."""
        if snippet.id in self.snippets:
            return False, f"Snippet ID '{snippet.id}' already exists"

        # Check for duplicate trigger
        existing = self.get_by_trigger(snippet.trigger)
        if existing:
            return False, f"Trigger '{snippet.trigger}' already used by '{existing.name}'"

        self.snippets[snippet.id] = snippet
        self.save()
        return True, ""

    def update_snippet(self, snippet_id: str, **kwargs) -> Tuple[bool, str]:
        """Update a snippet's properties."""
        snippet = self.snippets.get(snippet_id)
        if not snippet:
            return False, f"Snippet '{snippet_id}' not found"

        # Check trigger uniqueness if changing trigger
        if "trigger" in kwargs:
            new_trigger = kwargs["trigger"]
            existing = self.get_by_trigger(new_trigger)
            if existing and existing.id != snippet_id:
                return False, f"Trigger '{new_trigger}' already used by '{existing.name}'"

        # Update fields
        for key, value in kwargs.items():
            if hasattr(snippet, key):
                setattr(snippet, key, value)

        self.save()
        return True, ""

    def remove_snippet(self, snippet_id: str) -> bool:
        """Remove a snippet."""
        if snippet_id in self.snippets:
            del self.snippets[snippet_id]
            self.save()
            return True
        return False

    def expand_snippet(
        self,
        trigger: str,
        variables: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Expand a snippet trigger to its content.

        Args:
            trigger: The trigger phrase to match
            variables: Optional dictionary of variable values

        Returns:
            The expanded content, or None if no match found
        """
        snippet = self.get_by_trigger(trigger)
        if not snippet:
            return None

        # Update usage stats
        snippet.usage_count += 1
        snippet.last_used = datetime.now().isoformat()
        self.save()

        # Expand content with variables
        content = snippet.content
        if variables:
            for var_name, var_value in variables.items():
                content = content.replace(f"{{{var_name}}}", var_value)

        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(snippet.id, content)
            except Exception as e:
                logger.error(f"Error in snippet callback: {e}")

        return content

    def check_and_expand(
        self,
        text: str,
        variables: Optional[Dict[str, str]] = None
    ) -> Tuple[str, bool]:
        """Check if text contains a snippet trigger and expand it.

        Args:
            text: The text to check
            variables: Optional dictionary of variable values

        Returns:
            Tuple of (expanded_text, was_expanded)
        """
        text_lower = text.strip().lower()

        # Check for exact trigger match
        for snippet in self.snippets.values():
            if snippet.enabled and snippet.trigger.lower() == text_lower:
                expanded = self.expand_snippet(snippet.trigger, variables)
                if expanded is not None:
                    return expanded, True

        # Check if text starts with a trigger (for "calendar my link" -> "calendar")
        for snippet in self.snippets.values():
            if snippet.enabled:
                trigger_words = snippet.trigger.lower().split()
                text_words = text_lower.split()

                # Check if text starts with trigger words
                if len(text_words) >= len(trigger_words):
                    prefix = " ".join(text_words[:len(trigger_words)])
                    if prefix == snippet.trigger.lower():
                        expanded = self.expand_snippet(snippet.trigger, variables)
                        if expanded is not None:
                            # Append any remaining text
                            remaining = " ".join(text_words[len(trigger_words):])
                            return f"{expanded} {remaining}".strip(), True

        return text, False

    def extract_variables(self, content: str) -> List[SnippetVariable]:
        """Extract variables from snippet content.

        Args:
            content: The snippet content

        Returns:
            List of SnippetVariable objects
        """
        # Find all {variable} patterns
        pattern = r"\{([^}]+)\}"
        matches = re.findall(pattern, content)

        variables = []
        seen = set()
        for match in matches:
            if match not in seen:
                seen.add(match)
                # Check if it has a default value (format: {name=default})
                if "=" in match:
                    name, default = match.split("=", 1)
                    variables.append(SnippetVariable(
                        name=name.strip(),
                        default_value=default.strip(),
                        prompt=f"Enter value for {name}"
                    ))
                else:
                    variables.append(SnippetVariable(
                        name=match,
                        prompt=f"Enter value for {match}"
                    ))

        return variables

    def search_snippets(self, query: str) -> List[Snippet]:
        """Search snippets by name, trigger, or content.

        Args:
            query: Search query string

        Returns:
            List of matching snippets
        """
        query_lower = query.lower()
        results = []

        for snippet in self.snippets.values():
            if (query_lower in snippet.name.lower() or
                query_lower in snippet.trigger.lower() or
                query_lower in snippet.content.lower() or
                query_lower in snippet.description.lower()):
                results.append(snippet)

        return results

    def register_callback(self, callback: Callable[[str, str], None]) -> None:
        """Register a callback for snippet expansion events.

        Args:
            callback: Function that receives (snippet_id, expanded_content)
        """
        self.callbacks.append(callback)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all snippets.

        Returns:
            Dictionary with usage statistics
        """
        total_usage = sum(s.usage_count for s in self.snippets.values())
        most_used = sorted(
            self.snippets.values(),
            key=lambda s: s.usage_count,
            reverse=True
        )[:10]

        return {
            "total_snippets": len(self.snippets),
            "enabled_snippets": sum(1 for s in self.snippets.values() if s.enabled),
            "total_usage": total_usage,
            "most_used": [
                {"id": s.id, "name": s.name, "count": s.usage_count}
                for s in most_used if s.usage_count > 0
            ],
            "recently_used": [
                {"id": s.id, "name": s.name, "last_used": s.last_used}
                for s in sorted(
                    self.snippets.values(),
                    key=lambda s: s.last_used or "",
                    reverse=True
                )[:10] if s.last_used
            ],
        }

    def export_config(self, path: str) -> Tuple[bool, str]:
        """Export snippets configuration to a file.

        Args:
            path: Path to save the export file

        Returns:
            Tuple of (success, message)
        """
        try:
            data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "categories": [asdict(cat) for cat in self.categories.values()],
                "snippets": [snippet.to_dict() for snippet in self.snippets.values()],
            }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            return True, f"Configuration exported to {path}"
        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            return False, f"Failed to export: {e}"

    def import_config(self, path: str, merge: bool = False) -> Tuple[bool, str]:
        """Import snippets configuration from a file.

        Args:
            path: Path to the import file
            merge: If True, merge with existing snippets. If False, replace all.

        Returns:
            Tuple of (success, message)
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not merge:
                # Clear existing
                self.snippets.clear()
                self.categories.clear()

            self._load_from_dict(data)
            self.save()

            return True, "Configuration imported successfully"
        except FileNotFoundError:
            return False, f"File not found: {path}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {e}"
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
            return False, f"Failed to import: {e}"


# Global snippets manager instance
_manager: Optional[SnippetsManager] = None


def get_snippets_manager() -> SnippetsManager:
    """Get the global snippets manager instance."""
    global _manager
    if _manager is None:
        _manager = SnippetsManager()
    return _manager
