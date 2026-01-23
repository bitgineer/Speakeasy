"""
Slash-based search functionality for transcription history.

This module provides a command-based search system with fuzzy matching,
operators for filtering by date, model, language, and keyboard navigation
for quick access to transcription history.

Classes
-------
SearchCommand
    Dataclass representing a parsed search command.

SearchResult
    Dataclass representing a search result with highlighted matches.

SlashSearch
    Main search engine with fuzzy matching and operator parsing.
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from difflib import SequenceMatcher

from .history_manager import HistoryItem

logger = logging.getLogger(__name__)


@dataclass
class SearchCommand:
    """
    A parsed search command from slash syntax.

    Attributes
    ----------
    raw_query
        The original raw query string.
    text_query
        The text content to search for (if no /text: operator).
    model_filter
        Filter by model name (e.g., "large-v3").
    language_filter
        Filter by language code (e.g., "en", "es").
    date_filter
        Date filter: "today", "yesterday", "week", or specific date.
    tag_filter
        Filter by tags.
    limit
        Maximum number of results to return.
    fuzzy
        Whether to use fuzzy matching for text search.
    """
    raw_query: str = ""
    text_query: str = ""
    model_filter: Optional[str] = None
    language_filter: Optional[str] = None
    date_filter: Optional[str] = None
    tag_filter: Optional[List[str]] = None
    limit: int = 100
    fuzzy: bool = True

    def __post_init__(self):
        if self.tag_filter is None:
            self.tag_filter = []

    @property
    def has_filters(self) -> bool:
        """Check if any filters are active."""
        return bool(
            self.text_query or
            self.model_filter or
            self.language_filter or
            self.date_filter or
            self.tag_filter
        )


@dataclass
class SearchResult:
    """
    A search result with highlighted matches.

    Attributes
    ----------
    item
        The history item that matched.
    score
        Relevance score (0.0 to 1.0).
    highlighted_text
        Text with matched terms highlighted.
    matched_fields
        List of fields that matched the query.
    """
    item: HistoryItem
    score: float = 0.0
    highlighted_text: str = ""
    matched_fields: List[str] = field(default_factory=list)


class SlashSearch:
    """
    Slash-based search engine for transcription history.

    This class provides:
    - Command parsing with operators (/text:, /model:, /date:, /lang:)
    - Fuzzy text matching using configurable algorithms
    - Result ranking and highlighting
    - Keyboard navigation support
    - Date range parsing (today, yesterday, week, month)

    Examples
    --------
    >>> search = SlashSearch(history_manager)
    >>> results = search.search("/text:hello /model:large-v3")
    >>> for result in results:
    ...     print(f"{result.score:.2f}: {result.item.text[:50]}")
    """

    # Operator patterns
    OPERATOR_PATTERNS = {
        "text": r"/text:\s*(\S+)",
        "model": r"/model:\s*(\S+)",
        "lang": r"/lang(?:uage)?:\s*(\S+)",
        "date": r"/date:\s*(\S+)",
        "tag": r"/tag:\s*(\S+)",
        "limit": r"/limit:\s*(\d+)",
    }

    # Date keywords
    DATE_KEYWORDS = {
        "today": 0,
        "yesterday": 1,
        "week": 7,
        "month": 30,
    }

    def __init__(self, history_manager):
        """
        Initialize the slash search engine.

        Parameters
        ----------
        history_manager
            The HistoryManager instance to search.
        """
        self.history_manager = history_manager
        self._last_command: Optional[SearchCommand] = None
        self._last_results: List[SearchResult] = []
        self._selected_index = 0

    def parse_command(self, query: str) -> SearchCommand:
        """
        Parse a slash command string into a SearchCommand.

        Parameters
        ----------
        query
            The raw query string (e.g., "/text:hello /model:large-v3").

        Returns
        -------
        SearchCommand
            Parsed command with all extracted filters.
        """
        command = SearchCommand(raw_query=query)

        if not query or not query.strip():
            return command

        query = query.strip()
        command.text_query = query  # Default to full text search

        # Extract operators
        remaining_text = query

        # Extract /text: operator
        text_match = re.search(self.OPERATOR_PATTERNS["text"], query, re.IGNORECASE)
        if text_match:
            command.text_query = text_match.group(1)
            remaining_text = remaining_text.replace(text_match.group(0), "")

        # Extract /model: operator
        model_match = re.search(self.OPERATOR_PATTERNS["model"], query, re.IGNORECASE)
        if model_match:
            command.model_filter = model_match.group(1)
            remaining_text = remaining_text.replace(model_match.group(0), "")

        # Extract /lang: or /language: operator
        lang_match = re.search(self.OPERATOR_PATTERNS["lang"], query, re.IGNORECASE)
        if lang_match:
            command.language_filter = lang_match.group(1)
            remaining_text = remaining_text.replace(lang_match.group(0), "")

        # Extract /date: operator
        date_match = re.search(self.OPERATOR_PATTERNS["date"], query, re.IGNORECASE)
        if date_match:
            command.date_filter = date_match.group(1)
            remaining_text = remaining_text.replace(date_match.group(0), "")

        # Extract /tag: operator (can have multiple)
        tag_matches = re.finditer(self.OPERATOR_PATTERNS["tag"], query, re.IGNORECASE)
        for tag_match in tag_matches:
            command.tag_filter.append(tag_match.group(1))
            remaining_text = remaining_text.replace(tag_match.group(0), "")

        # Extract /limit: operator
        limit_match = re.search(self.OPERATOR_PATTERNS["limit"], query, re.IGNORECASE)
        if limit_match:
            try:
                command.limit = int(limit_match.group(1))
            except ValueError:
                pass
            remaining_text = remaining_text.replace(limit_match.group(0), "")

        # If no operators found, use the whole query as text
        if not (text_match or model_match or lang_match or date_match or tag_matches):
            command.text_query = query
        elif not text_match:
            # If filter operators were found but no /text:, clear text_query
            command.text_query = ""

        # Clean up remaining text
        remaining_text = re.sub(r'\s+/', ' /', remaining_text).strip()

        return command

    def _parse_date_filter(self, date_filter: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Parse a date filter string into start and end dates.

        Parameters
        ----------
        date_filter
            Date filter like "today", "yesterday", "week", "2024-01-15",
            or a range like "2024-01-01:2024-01-31".

        Returns
        -------
        tuple
            (start_date, end_date) tuple, either can be None.
        """
        now = datetime.now()

        # Check for date range separator
        if ":" in date_filter:
            parts = date_filter.split(":")
            if len(parts) == 2:
                try:
                    start = datetime.fromisoformat(parts[0])
                    end = datetime.fromisoformat(parts[1] + " 23:59:59")
                    return start, end
                except ValueError:
                    pass

        # Check for keywords
        date_filter_lower = date_filter.lower()
        if date_filter_lower in self.DATE_KEYWORDS:
            days_ago = self.DATE_KEYWORDS[date_filter_lower]

            if days_ago == 0:  # today
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                return start, now
            elif days_ago == 1:  # yesterday
                start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end = now.replace(hour=0, minute=0, second=0, microsecond=0)
                return start, end
            else:  # week, month
                start = (now - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0, microsecond=0)
                return start, now

        # Try parsing as ISO date
        try:
            date = datetime.fromisoformat(date_filter)
            start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start, end
        except ValueError:
            pass

        return None, None

    def _fuzzy_match_score(self, text: str, query: str) -> float:
        """
        Calculate fuzzy match score using sequence matching.

        Parameters
        ----------
        text
            The text to search in.
        query
            The query to match against.

        Returns
        -------
        float
            Similarity score from 0.0 to 1.0.
        """
        if not query or not text:
            return 0.0

        text_lower = text.lower()
        query_lower = query.lower()

        # Direct substring match gets highest score
        if query_lower in text_lower:
            # Score based on how much of the query is found
            return 1.0

        # Use SequenceMatcher for fuzzy matching
        ratio = SequenceMatcher(None, query_lower, text_lower).ratio()

        # Boost if all query words appear in text
        query_words = query_lower.split()
        if query_words:
            words_found = sum(1 for word in query_words if word in text_lower)
            if words_found == len(query_words):
                return 0.9 + (ratio * 0.1)
            elif words_found > 0:
                return 0.5 + (words_found / len(query_words)) * 0.3

        return ratio

    def _highlight_matches(self, text: str, query: str) -> str:
        """
        Highlight matched terms in text.

        Parameters
        ----------
        text
            The text to highlight.
        query
            The query terms to highlight.

        Returns
        -------
        str
            Text with matches surrounded by ** markers.
        """
        if not query:
            return text

        text_lower = text.lower()
        query_lower = query.lower()

        # Find all query terms
        query_terms = query_lower.split()

        # Track which positions to highlight
        highlight_positions = set()

        for term in query_terms:
            start = 0
            while True:
                pos = text_lower.find(term, start)
                if pos == -1:
                    break
                for i in range(pos, pos + len(term)):
                    highlight_positions.add(i)
                start = pos + 1

        # Build highlighted string
        result = []
        i = 0
        in_highlight = False

        while i < len(text):
            if i in highlight_positions:
                if not in_highlight:
                    result.append("**")
                    in_highlight = True
                result.append(text[i])
            else:
                if in_highlight:
                    result.append("**")
                    in_highlight = False
                result.append(text[i])
            i += 1

        if in_highlight:
            result.append("**")

        return "".join(result)

    def search(self, query: str) -> List[SearchResult]:
        """
        Execute a search query and return ranked results.

        Parameters
        ----------
        query
            The search query string.

        Returns
        -------
        list[SearchResult]
            Ranked list of search results.
        """
        command = self.parse_command(query)
        self._last_command = command
        self._selected_index = 0

        # If no meaningful query, return recent items
        if not command.has_filters:
            items = self.history_manager.get_all(limit=20)
            self._last_results = [
                SearchResult(item=item, score=1.0, highlighted_text=item.text[:100])
                for item in items
            ]
            return self._last_results

        # Parse date filter
        start_date, end_date = None, None
        if command.date_filter:
            start_date, end_date = self._parse_date_filter(command.date_filter)

        # Execute search based on available filters
        if start_date or end_date or command.model_filter or command.language_filter or command.tag_filter:
            # Use advanced search for multiple filters
            items = self.history_manager.advanced_search(
                text_query=command.text_query or None,
                model=command.model_filter,
                language=command.language_filter,
                start_date=start_date,
                end_date=end_date,
                tags=command.tag_filter if command.tag_filter else None,
                limit=command.limit,
            )
        elif command.text_query:
            # Simple text search
            items = self.history_manager.search_by_text(
                query=command.text_query,
                limit=command.limit,
                fuzzy=command.fuzzy,
            )
        else:
            items = []

        # Score and highlight results
        results = []
        for item in items:
            score = 1.0
            matched_fields = []

            if command.text_query:
                text_score = self._fuzzy_match_score(item.text, command.text_query)
                score = text_score
                if text_score > 0.3:
                    matched_fields.append("text")

            # Check model match
            if command.model_filter and item.model:
                if command.model_filter.lower() in item.model.lower():
                    matched_fields.append("model")

            # Check language match
            if command.language_filter and item.language:
                if command.language_filter.lower() == item.language.lower():
                    matched_fields.append("language")

            highlighted = self._highlight_matches(
                (item.text[:100] + "...") if len(item.text) > 100 else item.text,
                command.text_query or ""
            )

            results.append(SearchResult(
                item=item,
                score=score,
                highlighted_text=highlighted,
                matched_fields=matched_fields,
            ))

        # Sort by score (highest first)
        results.sort(key=lambda r: r.score, reverse=True)

        self._last_results = results
        return results

    def navigate(self, direction: str) -> Optional[SearchResult]:
        """
        Navigate through search results.

        Parameters
        ----------
        direction
            "up", "down", "first", or "last".

        Returns
        -------
        SearchResult or None
            The selected result, or None if no results.
        """
        if not self._last_results:
            return None

        if direction == "first":
            self._selected_index = 0
        elif direction == "last":
            self._selected_index = len(self._last_results) - 1
        elif direction == "up":
            self._selected_index = max(0, self._selected_index - 1)
        elif direction == "down":
            self._selected_index = min(len(self._last_results) - 1, self._selected_index + 1)

        return self.get_selected()

    def get_selected(self) -> Optional[SearchResult]:
        """
        Get the currently selected search result.

        Returns
        -------
        SearchResult or None
            The selected result, or None if no results.
        """
        if self._last_results and 0 <= self._selected_index < len(self._last_results):
            return self._last_results[self._selected_index]
        return None

    @property
    def result_count(self) -> int:
        """Get the number of results in the last search."""
        return len(self._last_results)

    @property
    def selected_index(self) -> int:
        """Get the currently selected result index."""
        return self._selected_index

    def get_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """
        Get search suggestions based on partial query.

        Parameters
        ----------
        partial_query
            The partial query to complete.
        limit
            Maximum suggestions to return.

        Returns
        -------
        list[str]
            List of suggestion strings.
        """
        suggestions = []

        # Operator suggestions
        if "/" in partial_query or not partial_query:
            partial = partial_query.split("/")[-1] if "/" in partial_query else ""

            operator_suggestions = [
                "/text:",
                "/model:",
                "/lang:",
                "/date:",
                "/tag:",
                "/limit:",
            ]

            for op in operator_suggestions:
                if op.startswith(partial) or partial == "":
                    suggestions.append(op)

        # Date keyword suggestions
        if "/date:" in partial_query:
            date_part = partial_query.split("/date:")[1] if "/date:" in partial_query else ""
            date_keywords = ["today", "yesterday", "week", "month"]
            for kw in date_keywords:
                if kw.startswith(date_part.lower()):
                    full_query = partial_query.split("/date:")[0] + f"/date:{kw}"
                    suggestions.append(full_query)

        return suggestions[:limit]

    def get_quick_commands(self) -> List[Dict[str, str]]:
        """
        Get list of quick commands for reference.

        Returns
        -------
        list[dict]
            List of command dictionaries with name, example, and description.
        """
        return [
            {
                "name": "Text Search",
                "example": "/text:hello world",
                "description": "Search for text content",
            },
            {
                "name": "Model Filter",
                "example": "/model:large-v3",
                "description": "Filter by model name",
            },
            {
                "name": "Language Filter",
                "example": "/lang:en",
                "description": "Filter by language code",
            },
            {
                "name": "Date Filter",
                "example": "/date:today",
                "description": "Filter by date (today, yesterday, week, month)",
            },
            {
                "name": "Tag Filter",
                "example": "/tag:important",
                "description": "Filter by tag",
            },
            {
                "name": "Limit Results",
                "example": "/limit:10",
                "description": "Limit number of results",
            },
            {
                "name": "Combined",
                "example": "/text:meeting /date:week /limit:20",
                "description": "Combine multiple filters",
            },
        ]


class SearchNavigation:
    """
    Keyboard navigation handler for search results.

    This class handles keyboard events for navigating through
    search results with up/down arrows and Enter selection.
    """

    def __init__(self, slash_search: SlashSearch):
        """
        Initialize navigation handler.

        Parameters
        ----------
        slash_search
            The SlashSearch instance to navigate.
        """
        self.search = slash_search
        self._callbacks = {
            "selection_changed": [],
            "item_selected": [],
        }

    def on_key(self, key: str) -> bool:
        """
        Handle a key press event.

        Parameters
        ----------
        key
            The key name (e.g., "up", "down", "enter", "escape").

        Returns
        -------
        bool
            True if the key was handled, False otherwise.
        """
        if key == "up":
            result = self.search.navigate("up")
            self._emit("selection_changed", result)
            return True

        elif key == "down":
            result = self.search.navigate("down")
            self._emit("selection_changed", result)
            return True

        elif key == "enter":
            result = self.search.get_selected()
            if result:
                self._emit("item_selected", result)
            return True

        elif key == "page_up":
            # Move up 5 items
            for _ in range(5):
                self.search.navigate("up")
            self._emit("selection_changed", self.search.get_selected())
            return True

        elif key == "page_down":
            # Move down 5 items
            for _ in range(5):
                self.search.navigate("down")
            self._emit("selection_changed", self.search.get_selected())
            return True

        elif key == "home":
            result = self.search.navigate("first")
            self._emit("selection_changed", result)
            return True

        elif key == "end":
            result = self.search.navigate("last")
            self._emit("selection_changed", result)
            return True

        return False

    def on(self, event: str, callback):
        """
        Register a callback for an event.

        Parameters
        ----------
        event
            Event type: "selection_changed" or "item_selected".
        callback
            Function to call when event occurs.

        Returns
        -------
        callable
            Unsubscribe function.
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)

            def unsubscribe():
                if callback in self._callbacks[event]:
                    self._callbacks[event].remove(callback)

            return unsubscribe
        return lambda: None

    def _emit(self, event: str, data):
        """Emit an event to all registered callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.warning(f"Error in {event} callback: {e}")
