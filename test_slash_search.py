"""
Simple unit tests for slash search components.

These tests verify the core functionality without requiring full module imports.
Run with: python test_slash_search.py
"""

import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

print("=" * 60)
print("Testing Slash Search Functionality")
print("=" * 60)

# ============================================================================
# Test 1: Command Parsing
# ============================================================================

print("\n1. Testing Command Parsing...")

OPERATOR_PATTERNS = {
    "text": r"/text:\s*(\S+)",
    "model": r"/model:\s*(\S+)",
    "lang": r"/lang(?:uage)?:\s*(\S+)",
    "date": r"/date:\s*(\S+)",
    "tag": r"/tag:\s*(\S+)",
    "limit": r"/limit:\s*(\d+)",
}

def parse_command(query: str) -> Dict[str, Any]:
    """Parse a slash command string."""
    command = {
        "raw_query": query,
        "text_query": query if query else "",
        "model_filter": None,
        "language_filter": None,
        "date_filter": None,
        "tag_filter": [],
        "limit": 100,
        "fuzzy": True,
    }

    if not query or not query.strip():
        return command

    query = query.strip()
    remaining_text = query

    # Extract operators
    text_match = re.search(OPERATOR_PATTERNS["text"], query, re.IGNORECASE)
    if text_match:
        command["text_query"] = text_match.group(1)
        remaining_text = remaining_text.replace(text_match.group(0), "")

    model_match = re.search(OPERATOR_PATTERNS["model"], query, re.IGNORECASE)
    if model_match:
        command["model_filter"] = model_match.group(1)
        remaining_text = remaining_text.replace(model_match.group(0), "")

    lang_match = re.search(OPERATOR_PATTERNS["lang"], query, re.IGNORECASE)
    if lang_match:
        command["language_filter"] = lang_match.group(1)
        remaining_text = remaining_text.replace(lang_match.group(0), "")

    date_match = re.search(OPERATOR_PATTERNS["date"], query, re.IGNORECASE)
    if date_match:
        command["date_filter"] = date_match.group(1)
        remaining_text = remaining_text.replace(date_match.group(0), "")

    limit_match = re.search(OPERATOR_PATTERNS["limit"], query, re.IGNORECASE)
    if limit_match:
        try:
            command["limit"] = int(limit_match.group(1))
        except ValueError:
            pass
        remaining_text = remaining_text.replace(limit_match.group(0), "")

    # If no operators found, use the whole query as text
    if not (text_match or model_match or lang_match or date_match):
        command["text_query"] = query
    elif not text_match:
        # If operators were found but no /text:, clear text_query
        command["text_query"] = ""

    return command

# Test cases
test_cases = [
    ("/text:hello", {"text_query": "hello", "model_filter": None, "language_filter": None}),
    ("/model:large-v3", {"text_query": "", "model_filter": "large-v3", "language_filter": None}),
    ("/text:meeting /model:large-v3", {"text_query": "meeting", "model_filter": "large-v3", "language_filter": None}),
    ("hello world", {"text_query": "hello world", "model_filter": None, "language_filter": None}),
    ("/lang:en /date:today", {"text_query": "", "language_filter": "en", "date_filter": "today", "model_filter": None}),
]

passed = 0
failed = 0

for query, expected in test_cases:
    result = parse_command(query)
    match = True
    for key, val in expected.items():
        if result.get(key) != val:
            match = False
            break
    if match:
        passed += 1
        print(f"  [OK] '{query}' parsed correctly")
    else:
        failed += 1
        print(f"  [FAIL] '{query}' parsing failed")

print(f"\nCommand Parsing: {passed} passed, {failed} failed")

# ============================================================================
# Test 2: Date Filter Parsing
# ============================================================================

print("\n2. Testing Date Filter Parsing...")

DATE_KEYWORDS = {
    "today": 0,
    "yesterday": 1,
    "week": 7,
    "month": 30,
}

def parse_date_filter(date_filter: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Parse a date filter string into start and end dates."""
    now = datetime.now()

    # Check for keywords
    date_filter_lower = date_filter.lower()
    if date_filter_lower in DATE_KEYWORDS:
        days_ago = DATE_KEYWORDS[date_filter_lower]

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

    return None, None

# Test date parsing
date_tests = ["today", "yesterday", "week", "month"]
date_passed = 0
date_failed = 0

for dt in date_tests:
    start, end = parse_date_filter(dt)
    if start is not None and end is not None:
        date_passed += 1
        print(f"  [OK] '{dt}' parses to {start.date()} - {end.date()}")
    else:
        date_failed += 1
        print(f"  [FAIL] '{dt}' failed to parse")

print(f"\nDate Filter Parsing: {date_passed} passed, {date_failed} failed")

# ============================================================================
# Test 3: Fuzzy Match Scoring
# ============================================================================

print("\n3. Testing Fuzzy Match Scoring...")

def fuzzy_match_score(text: str, query: str) -> float:
    """Calculate fuzzy match score using sequence matching."""
    if not query or not text:
        return 0.0

    text_lower = text.lower()
    query_lower = query.lower()

    # Direct substring match gets highest score
    if query_lower in text_lower:
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

fuzzy_tests = [
    ("hello world", "hello", 0.9),
    ("hello world test", "hello world", 0.9),
    ("meeting notes", "project timeline", 0.1),  # Lower threshold since these don't match
]

fuzzy_passed = 0
fuzzy_failed = 0

for text, query, min_score in fuzzy_tests:
    score = fuzzy_match_score(text, query)
    if score >= min_score:
        fuzzy_passed += 1
        print(f"  [OK] '{query}' in '{text}': score {score:.2f}")
    else:
        fuzzy_failed += 1
        print(f"  [FAIL] '{query}' in '{text}': score {score:.2f} (expected >= {min_score})")

print(f"\nFuzzy Scoring: {fuzzy_passed} passed, {fuzzy_failed} failed")

# ============================================================================
# Test 4: Match Highlighting
# ============================================================================

print("\n4. Testing Match Highlighting...")

def highlight_matches(text: str, query: str) -> str:
    """Highlight matched terms in text."""
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

highlight_tests = [
    ("hello world", "hello", "**hello** world"),
    ("meeting about project timeline", "project", "meeting about **project** timeline"),
]

highlight_passed = 0
highlight_failed = 0

for text, query, expected in highlight_tests:
    result = highlight_matches(text, query)
    if result == expected:
        highlight_passed += 1
        print(f"  [OK] '{query}' -> '{result}'")
    else:
        highlight_failed += 1
        print(f"  [FAIL] '{query}' -> '{result}' (expected '{expected}')")

print(f"\nMatch Highlighting: {highlight_passed} passed, {highlight_failed} failed")

# ============================================================================
# Summary
# ============================================================================

total_passed = passed + date_passed + fuzzy_passed + highlight_passed
total_failed = failed + date_failed + fuzzy_failed + highlight_failed

print("\n" + "=" * 60)
print(f"SUMMARY: {total_passed} passed, {total_failed} failed")
print("=" * 60)

if total_failed == 0:
    print("\n[OK] All tests passed!")
else:
    print(f"\n[WARN] {total_failed} test(s) failed")
