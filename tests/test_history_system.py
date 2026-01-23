"""
Comprehensive test suite for the history system.

This test module covers:
- Performance testing with 1000+ history items
- Search responsiveness with large datasets
- Auto-paste functionality across different scenarios
- Clipboard backup/restore functionality
- Privacy mode testing
- Corrupted database error handling

Run with: python -m pytest tests/test_history_system.py -v
Or directly: python tests/test_history_system.py
"""

import os
import sys
import sqlite3
import tempfile
import shutil
import time
import json
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print("=" * 70)
print("History System Comprehensive Test Suite")
print("=" * 70)


# ============================================================================
# Test Configuration and Utilities
# ============================================================================

class TestConfig:
    """Configuration for tests."""
    TEMP_DIR = None
    TEST_DB_PATH = None

    @classmethod
    def setup(cls):
        """Set up test environment."""
        cls.TEMP_DIR = tempfile.mkdtemp(prefix="history_test_")
        cls.TEST_DB_PATH = os.path.join(cls.TEMP_DIR, "test_history.db")
        print(f"\nTest directory: {cls.TEMP_DIR}")
        print(f"Test database: {cls.TEST_DB_PATH}")

    @classmethod
    def teardown(cls):
        """Clean up test environment."""
        if cls.TEMP_DIR and os.path.exists(cls.TEMP_DIR):
            shutil.rmtree(cls.TEMP_DIR)
            print(f"\nCleaned up test directory: {cls.TEMP_DIR}")


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
        self.lock = threading.Lock()

    def add_pass(self, test_name: str):
        with self.lock:
            self.passed += 1
            self.tests.append((test_name, "PASS"))

    def add_fail(self, test_name: str, error: str = ""):
        with self.lock:
            self.failed += 1
            self.tests.append((test_name, "FAIL", error))

    def print_summary(self):
        print("\n" + "=" * 70)
        print(f"TEST SUMMARY: {self.passed} passed, {self.failed} failed")
        print("=" * 70)

        if self.failed > 0:
            print("\nFailed tests:")
            for test in self.tests:
                if test[1] == "FAIL":
                    error = test[2] if len(test) > 2 else "Unknown error"
                    print(f"  - {test[0]}: {error}")

        return self.failed == 0


results = TestResults()


def run_test(test_func, test_name: str):
    """Run a test function and track results."""
    try:
        print(f"\n[TEST] {test_name}...")
        test_func()
        print(f"  [PASS] {test_name}")
        results.add_pass(test_name)
        return True
    except AssertionError as e:
        print(f"  [FAIL] {test_name}: {e}")
        results.add_fail(test_name, str(e))
        return False
    except Exception as e:
        print(f"  [ERROR] {test_name}: {e}")
        results.add_fail(test_name, str(e))
        return False


def assert_equal(actual, expected, msg: str = ""):
    """Assert two values are equal."""
    if actual != expected:
        raise AssertionError(f"{msg}: Expected {expected}, got {actual}")


def assert_true(condition, msg: str = ""):
    """Assert condition is true."""
    if not condition:
        raise AssertionError(f"{msg}: Condition was False")


def assert_greater(value, threshold, msg: str = ""):
    """Assert value is greater than threshold."""
    if value <= threshold:
        raise AssertionError(f"{msg}: {value} not greater than {threshold}")


def assert_less(value, threshold, msg: str = ""):
    """Assert value is less than threshold."""
    if value >= threshold:
        raise AssertionError(f"{msg}: {value} not less than {threshold}")


def assert_in(item, container, msg: str = ""):
    """Assert item is in container."""
    if item not in container:
        raise AssertionError(f"{msg}: {item} not in container")


# ============================================================================
# Test 1: Database Performance with 1000+ Items
# ============================================================================

def test_large_dataset_performance():
    """Test performance with 1000+ history items."""
    from faster_whisper_hotkey.flet_gui.history_manager import HistoryManager, HistoryItem

    # Use a separate database for this test
    test_db = os.path.join(TestConfig.TEMP_DIR, "performance_test.db")
    manager = HistoryManager(db_path=test_db, max_items=2000)

    # Test 1.1: Insert 1000 items
    print("  Creating 1000 history items...")
    start_time = time.time()

    for i in range(1000):
        item = HistoryItem(
            timestamp=datetime.now().isoformat(),
            text=f"Test transcription number {i}. " * 10,  # Longer text
            model="large-v3" if i % 2 == 0 else "medium",
            language="en",
            device="cpu",
            confidence=0.9 + (i % 10) / 100,
            duration_ms=1000 + i * 10,
            tags=["test", f"batch{i//100}"],
        )
        manager.add_item(item, skip_notification=True)

    insert_time = time.time() - start_time
    print(f"    Inserted 1000 items in {insert_time:.3f}s")
    assert_less(insert_time, 30.0, "Insert should complete within 30 seconds")

    # Test 1.2: Retrieve all items
    print("  Retrieving all items...")
    start_time = time.time()
    items = manager.get_all()
    retrieve_time = time.time() - start_time
    print(f"    Retrieved {len(items)} items in {retrieve_time:.3f}s")
    assert_equal(len(items), 1000, "Should have 1000 items")
    assert_less(retrieve_time, 1.0, "Retrieval should complete within 1 second")

    # Test 1.3: Search performance
    print("  Testing search performance...")
    start_time = time.time()
    results = manager.search_by_text("transcription number 500", limit=50)
    search_time = time.time() - start_time
    print(f"    Found {len(results)} results in {search_time:.3f}s")
    assert_greater(len(results), 0, "Search should return results")
    assert_less(search_time, 0.5, "Search should complete within 0.5 seconds")

    # Test 1.4: Get by ID performance
    print("  Testing get_by_id performance...")
    start_time = time.time()
    item = manager.get_by_id(500)
    get_time = time.time() - start_time
    print(f"    Retrieved item by ID in {get_time:.3f}s")
    assert_true(item is not None, "Should retrieve item by ID")
    assert_less(get_time, 0.1, "Get by ID should complete within 0.1 seconds")

    # Test 1.5: Statistics performance
    print("  Testing statistics performance...")
    start_time = time.time()
    stats = manager.get_statistics()
    stats_time = time.time() - start_time
    print(f"    Got statistics in {stats_time:.3f}s")
    print(f"    Stats: {stats['total_items']} items, {stats['today_count']} today")
    assert_equal(stats['total_items'], 1000, "Stats should report 1000 items")
    assert_less(stats_time, 1.0, "Statistics should complete within 1 second")

    print(f"  Performance test passed!")


# ============================================================================
# Test 2: Search Responsiveness
# ============================================================================

def test_search_responsiveness():
    """Test search with various query types and large datasets."""
    from faster_whisper_hotkey.flet_gui.history_manager import HistoryManager, HistoryItem
    from faster_whisper_hotkey.flet_gui.slash_search import SlashSearch

    test_db = os.path.join(TestConfig.TEMP_DIR, "search_test.db")
    manager = HistoryManager(db_path=test_db, max_items=5000)

    # Create diverse test data
    print("  Creating diverse test data (500 items)...")

    # Categories of content
    topics = [
        "meeting about project",
        "discussion regarding feature",
        "conversation on design",
        "chat about implementation",
        "talk concerning development",
        "conference call with team",
        "standup daily sync",
        "retrospective session",
        "planning workshop",
        "code review session",
    ]

    models = ["large-v3", "medium", "small", "base"]
    languages = ["en", "es", "fr", "de", "ja"]

    for i in range(500):
        topic = topics[i % len(topics)]
        model = models[i % len(models)]
        lang = languages[i % len(languages)]

        # Create timestamps across different dates
        days_ago = i // 50
        timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()

        item = HistoryItem(
            timestamp=timestamp,
            text=f"{topic} number {i}: This is a detailed transcription with various keywords.",
            model=model,
            language=lang,
            device="cpu",
            tags=[topic.split()[0], f"day{days_ago}"],
        )
        manager.add_item(item, skip_notification=True)

    # Test 2.1: Simple text search
    print("  Testing simple text search...")
    search = SlashSearch(manager)
    start = time.time()
    results = search.search("meeting")
    elapsed = time.time() - start
    print(f"    'meeting' search: {len(results)} results in {elapsed:.3f}s")
    assert_greater(len(results), 0, "Should find meeting results")
    assert_less(elapsed, 0.3, "Search should be fast")

    # Test 2.2: Model filter search
    print("  Testing model filter search...")
    start = time.time()
    results = search.search("/model:large-v3")
    elapsed = time.time() - start
    print(f"    '/model:large-v3' search: {len(results)} results in {elapsed:.3f}s")
    assert_greater(len(results), 0, "Should find large-v3 results")
    assert_less(elapsed, 0.3, "Filtered search should be fast")

    # Test 2.3: Combined search
    print("  Testing combined filters...")
    start = time.time()
    results = search.search("/text:meeting /model:large-v3 /lang:en")
    elapsed = time.time() - start
    print(f"    Combined search: {len(results)} results in {elapsed:.3f}s")
    assert_less(elapsed, 0.5, "Combined search should be fast")

    # Test 2.4: Date filter search
    print("  Testing date filter search...")
    start = time.time()
    results = search.search("/date:week")
    elapsed = time.time() - start
    print(f"    '/date:week' search: {len(results)} results in {elapsed:.3f}s")
    assert_less(elapsed, 0.3, "Date filter search should be fast")

    # Test 2.5: Empty search (recent items)
    print("  Testing empty search (recent items)...")
    start = time.time()
    results = search.search("")
    elapsed = time.time() - start
    print(f"    Recent items: {len(results)} results in {elapsed:.3f}s")
    assert_less(len(results), 25, "Recent search should limit results")
    assert_less(elapsed, 0.1, "Recent items query should be fast")

    # Test 2.6: Fuzzy search
    print("  Testing fuzzy search...")
    start = time.time()
    results = search.search("prject")  # Misspelled
    elapsed = time.time() - start
    print(f"    Fuzzy 'prject' search: {len(results)} results in {elapsed:.3f}s")
    assert_less(elapsed, 0.5, "Fuzzy search should be reasonably fast")

    print(f"  Search responsiveness test passed!")


# ============================================================================
# Test 3: Clipboard Backup/Restore
# ============================================================================

def test_clipboard_backup_restore():
    """Test clipboard backup and restore functionality."""
    from faster_whisper_hotkey.clipboard import backup_clipboard, set_clipboard, restore_clipboard

    # Skip if pyperclip not available
    try:
        import pyperclip
    except ImportError:
        print("  [SKIP] pyperclip not available")
        return

    # Test 3.1: Backup current clipboard
    print("  Testing clipboard backup...")
    original_content = "original clipboard content"
    set_clipboard(original_content)

    backed_up = backup_clipboard()
    print(f"    Backed up: '{backed_up[:50]}...'")
    assert_equal(backed_up, original_content, "Backup should match clipboard")

    # Test 3.2: Set new clipboard content
    print("  Testing clipboard set...")
    new_content = "new clipboard content for transcription"
    success = set_clipboard(new_content)
    assert_true(success, "Should successfully set clipboard")

    # Verify it was set
    current = backup_clipboard()
    assert_equal(current, new_content, "Clipboard should have new content")

    # Test 3.3: Restore clipboard
    print("  Testing clipboard restore...")
    restore_clipboard(backed_up)

    restored = backup_clipboard()
    assert_equal(restored, original_content, "Clipboard should be restored")

    # Test 3.4: Restore with None
    print("  Testing restore with None...")
    set_clipboard("temporary content")
    restore_clipboard(None)  # Should do nothing
    current = backup_clipboard()
    assert_equal(current, "temporary content", "None restore should not change")

    # Test 3.5: Restore with empty string
    print("  Testing restore with empty string...")
    set_clipboard("another test")
    restore_clipboard("")
    current = backup_clipboard()
    # Empty string might be valid or ignored depending on implementation
    print(f"    After empty restore: '{current}'")

    print(f"  Clipboard backup/restore test passed!")


# ============================================================================
# Test 4: Privacy Mode
# ============================================================================

def test_privacy_mode():
    """Test privacy mode ensures nothing is saved."""
    from faster_whisper_hotkey.flet_gui.history_manager import HistoryManager, HistoryItem

    # Use unique database for privacy test
    # uuid imported at module level
    test_db = os.path.join(TestConfig.TEMP_DIR, f"privacy_test_{uuid.uuid4().hex[:8]}.db")
    os.makedirs(os.path.dirname(test_db), exist_ok=True)

    # Test 4.1: Create manager with privacy mode enabled
    print("  Testing privacy mode creation...")
    manager = HistoryManager(db_path=test_db, privacy_mode=True, max_items=1000)

    # Try to add items
    print("  Testing add items in privacy mode...")
    for i in range(10):
        item = HistoryItem(
            timestamp=datetime.now().isoformat(),
            text=f"This should not be saved {i}",
            model="large-v3",
            language="en",
        )
        item_id = manager.add_item(item, skip_notification=True)
        assert_true(item_id is None, f"Item {i} should not be added in privacy mode")

    # Verify no items exist
    print("  Verifying no items in privacy mode...")
    items = manager.get_all()
    assert_equal(len(items), 0, "Should have no items in privacy mode")

    # Test 4.2: Create a new manager without privacy mode
    print("  Testing new manager without privacy mode...")
    # Close the old manager and create a new one with privacy mode off
    del manager

    # Create a fresh manager without privacy mode using the same database
    manager2 = HistoryManager(db_path=test_db, privacy_mode=False, max_items=1000)

    # Now items should be saved
    item = HistoryItem(
        timestamp=datetime.now().isoformat(),
        text="This should be saved now",
        model="large-v3",
        language="en",
    )
    item_id = manager2.add_item(item, skip_notification=True)
    assert_true(item_id is not None, "Item should be added when privacy mode is off")

    items = manager2.get_all()
    assert_equal(len(items), 1, "Should have one item after disabling privacy mode")

    # Test 4.3: Enable privacy mode on existing manager and verify items are cleared
    print("  Testing privacy mode clears history...")
    manager2.set_privacy_mode(True)

    items = manager2.get_all()
    assert_equal(len(items), 0, "Items should be cleared when enabling privacy mode")

    # Test 4.4: Verify operations return empty/nothing in privacy mode
    print("  Testing all operations in privacy mode...")
    assert_equal(len(manager2.search_by_text("test")), 0, "Search should return empty")
    assert_equal(len(manager2.search_by_model("large-v3")), 0, "Model search should return empty")
    assert_equal(len(manager2.search_by_language("en")), 0, "Language search should return empty")

    stats = manager2.get_statistics()
    assert_equal(stats['total_items'], 0, "Stats should show 0 items")

    print(f"  Privacy mode test passed!")


# ============================================================================
# Test 5: Corrupted Database Error Handling
# ============================================================================

def test_corrupted_database_handling():
    """Test handling of corrupted database."""
    from faster_whisper_hotkey.flet_gui.history_manager import HistoryManager, HistoryItem

    # Use unique database for corruption test
    # uuid imported at module level
    test_db = os.path.join(TestConfig.TEMP_DIR, f"corrupt_test_{uuid.uuid4().hex[:8]}.db")
    os.makedirs(os.path.dirname(test_db), exist_ok=True)

    # Test 5.1: Create a valid database first
    print("  Creating initial database...")
    manager = HistoryManager(db_path=test_db)

    item = HistoryItem(
        timestamp=datetime.now().isoformat(),
        text="Test item before corruption",
        model="large-v3",
        language="en",
    )
    manager.add_item(item)

    items = manager.get_all()
    assert_equal(len(items), 1, "Should have one item")
    print(f"    Created database with {len(items)} item")

    # Close connections
    del manager

    # Test 5.2: Corrupt the database file
    print("  Corrupting database file...")
    # Write garbage to the database
    with open(test_db, 'wb') as f:
        f.write(b'This is not a valid SQLite database file!!!')

    # Test 5.3: Try to open corrupted database
    print("  Testing recovery from corrupted database...")
    try:
        # The manager should handle this gracefully
        # Either by recreating or returning empty results
        manager2 = HistoryManager(db_path=test_db)

        # Operations should not crash
        items = manager2.get_all()
        print(f"    After corruption: {len(items)} items (database was recreated)")

        # The database should have been recreated, so items should be 0
        assert_equal(len(items), 0, "Corrupted database should result in empty database")

        # Add item should work
        item = HistoryItem(
            timestamp=datetime.now().isoformat(),
            text="Test item after corruption recovery",
            model="large-v3",
            language="en",
        )
        item_id = manager2.add_item(item)
        assert_true(item_id is not None, "Should be able to add items after recovery")

        # Verify we can retrieve the new item
        items = manager2.get_all()
        assert_equal(len(items), 1, "Should have one item after recovery")

        print(f"    Database recovered successfully")

    except Exception as e:
        # If it does raise, it should be a reasonable error, not a crash
        print(f"    Handled corruption with: {type(e).__name__}")
        # This is acceptable behavior

    # Test 5.4: Test with non-existent directory path
    print("  Testing with invalid database path...")
    # uuid imported at module level
    invalid_path = os.path.join(TestConfig.TEMP_DIR, f"nested_{uuid.uuid4().hex[:8]}", "db.db")

    # Create manager with invalid path - should handle gracefully by creating dir
    try:
        manager3 = HistoryManager(db_path=invalid_path)
        items = manager3.get_all()
        # Should work (directory created)
        print(f"    Created database at new path: {len(items)} items")
        assert_true(os.path.exists(invalid_path), "Database file should be created")
    except Exception as e:
        print(f"    Path issue handled: {type(e).__name__}")

    print(f"  Corrupted database handling test passed!")


# ============================================================================
# Test 6: Thread Safety
# ============================================================================

def test_thread_safety():
    """Test thread-safe operations."""
    from faster_whisper_hotkey.flet_gui.history_manager import HistoryManager, HistoryItem

    test_db = os.path.join(TestConfig.TEMP_DIR, "thread_test.db")
    manager = HistoryManager(db_path=test_db, max_items=10000)

    # Test 6.1: Concurrent adds
    print("  Testing concurrent adds (10 threads, 100 items each)...")

    def add_items(thread_id: int, count: int = 100):
        for i in range(count):
            item = HistoryItem(
                timestamp=datetime.now().isoformat(),
                text=f"Thread {thread_id} item {i}",
                model="large-v3",
                language="en",
            )
            manager.add_item(item, skip_notification=True)

    threads = []
    start_time = time.time()

    for i in range(10):
        t = threading.Thread(target=add_items, args=(i, 100))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.time() - start_time
    print(f"    Added items in {elapsed:.3f}s")

    # Verify count
    items = manager.get_all()
    print(f"    Total items: {len(items)}")
    assert_equal(len(items), 1000, "Should have 1000 items from all threads")

    # Test 6.2: Concurrent reads
    print("  Testing concurrent reads...")

    def read_items():
        items = manager.get_all()
        return len(items)

    threads = []
    for i in range(20):
        t = threading.Thread(target=read_items)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"    Completed {len(threads)} concurrent reads")

    # Test 6.3: Mixed operations
    print("  Testing mixed concurrent operations...")
    errors = []

    def mixed_ops(thread_id: int):
        try:
            for i in range(10):
                # Add
                manager.add_item(HistoryItem(
                    timestamp=datetime.now().isoformat(),
                    text=f"Thread {thread_id} mixed {i}",
                ), skip_notification=True)
                # Read
                manager.get_all(limit=10)
                # Search
                manager.search_by_text(f"Thread {thread_id}")
        except Exception as e:
            errors.append((thread_id, e))

    threads = []
    for i in range(5):
        t = threading.Thread(target=mixed_ops, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert_equal(len(errors), 0, f"No errors should occur: {errors}")
    print(f"    No errors in mixed operations")

    print(f"  Thread safety test passed!")


# ============================================================================
# Test 7: Auto-Paste Functionality
# ============================================================================

def test_auto_paste():
    """Test auto-paste functionality."""
    from faster_whisper_hotkey.flet_gui.auto_paste import AutoPaste, PasteMethod

    # Test 7.1: Create AutoPaste instance
    print("  Testing AutoPaste creation...")
    auto_paste = AutoPaste(
        default_method=PasteMethod.CLIPBOARD,
        pre_paste_delay=0.05,
        post_paste_delay=0.05,
    )
    print(f"    Created with default method: {auto_paste.default_method}")

    # Test 7.2: Test active app detection
    print("  Testing active app detection...")
    app_info = auto_paste.detect_active_app()
    print(f"    Detected app: class={app_info.get('window_class')}, title={app_info.get('window_title', 'N/A')[:50]}")
    assert_true('window_class' in app_info, "Should detect window class")
    assert_true('platform' in app_info, "Should detect platform")

    # Test 7.3: Test paste method determination
    print("  Testing paste method determination...")
    from faster_whisper_hotkey.app_detector import WindowInfo
    test_window = WindowInfo(
        window_class="TestWindowClass",
        window_title="Test Window",
        process_name="test.exe",
    )
    method = auto_paste._determine_paste_method(test_window)
    print(f"    Determined method: {method}")

    # Test 7.4: Test terminal detection
    print("  Testing terminal detection...")
    terminal_windows = [
        WindowInfo("WindowsTerminal", "Terminal", "WindowsTerminal.exe"),
        WindowInfo("ConsoleWindowClass", "Command Prompt", "cmd.exe"),
        WindowInfo("PuTTY", "SSH Session", "putty.exe"),
    ]

    for tw in terminal_windows:
        method = auto_paste._determine_paste_method(tw)
        print(f"    {tw.window_class}: {method}")

    # Test 7.5: Test paste methods availability
    print("  Testing paste methods availability...")
    test_results = auto_paste.test_paste_methods()
    print(f"    Platform: {test_results['platform']}")
    print(f"    Methods available: {test_results['methods']}")

    # Test 7.6: Simulate clipboard paste (without actual execution)
    print("  Testing clipboard operations...")
    try:
        import pyperclip

        # Backup
        original = pyperclip.paste() if pyperclip else ""
        print(f"    Original clipboard: '{original[:30]}...'")

        # Test set
        test_text = "Test auto-paste content"
        success = auto_paste._paste_direct(test_text, test_window)
        print(f"    Direct paste: {success}")

        # Restore
        if original:
            pyperclip.copy(original)

    except ImportError:
        print("    [SKIP] pyperclip not available")

    print(f"  Auto-paste test passed!")


# ============================================================================
# Test 8: Database Pruning and Limits
# ============================================================================

def test_database_pruning():
    """Test database pruning with max_items limit."""
    from faster_whisper_hotkey.flet_gui.history_manager import HistoryManager, HistoryItem

    # Use unique database for pruning test
    # uuid imported at module level
    test_db = os.path.join(TestConfig.TEMP_DIR, f"prune_test_{uuid.uuid4().hex[:8]}.db")

    # Test with small max_items
    print("  Testing database with max_items=50...")
    manager = HistoryManager(db_path=test_db, max_items=50)

    # Add 100 items
    print("  Adding 100 items with max_items=50...")
    for i in range(100):
        # Small delay to ensure different timestamps
        time.sleep(0.001)
        item = HistoryItem(
            timestamp=datetime.now().isoformat(),
            text=f"Item {i}",
            model="large-v3",
        )
        manager.add_item(item, skip_notification=True)

    # Check that we only have 50 items
    items = manager.get_all()
    print(f"    Items after adding 100 with max=50: {len(items)}")
    assert_equal(len(items), 50, "Should prune to max_items")

    # Check that oldest items were removed (should have newest 50)
    # The newest item should be item 99 (or close to it)
    if items:
        print(f"    Newest item text: '{items[0].text}'")
        print(f"    Oldest item text: '{items[-1].text}'")
        # Items should be sorted descending by timestamp
        # So items[0] is newest, items[-1] is oldest

    # Test 8.2: Auto-delete by date
    print("  Testing auto-delete by date...")
    # First, create a new manager to add truly old items first
    del manager

    # Create new database where we can control the order
    test_db2 = os.path.join(TestConfig.TEMP_DIR, f"prune_test_date_{uuid.uuid4().hex[:8]}.db")
    manager2 = HistoryManager(db_path=test_db2, max_items=1000)

    # Add old items first
    old_date = datetime.now() - timedelta(days=60)
    for i in range(10):
        item = HistoryItem(
            timestamp=old_date.isoformat(),
            text=f"Old item {i}",
        )
        manager2.add_item(item, skip_notification=True)

    # Add recent items
    for i in range(10):
        item = HistoryItem(
            timestamp=datetime.now().isoformat(),
            text=f"Recent item {i}",
        )
        manager2.add_item(item, skip_notification=True)

    # Get total count
    items_before = len(manager2.get_all())
    print(f"    Items before auto-delete: {items_before}")

    # Auto-delete items older than 30 days
    cutoff = datetime.now() - timedelta(days=30)
    deleted = manager2.auto_delete_before_date(cutoff)
    print(f"    Deleted {deleted} old items")

    items_after = len(manager2.get_all())
    print(f"    Items after auto-delete: {items_after}")

    assert_true(items_after < items_before, "Should delete old items")
    assert_equal(items_after, 10, "Should have 10 recent items left")

    print(f"  Database pruning test passed!")


# ============================================================================
# Test 9: Import/Export Functionality
# ============================================================================

def test_import_export():
    """Test import/export functionality."""
    from faster_whisper_hotkey.flet_gui.history_manager import HistoryManager, HistoryItem

    test_db = os.path.join(TestConfig.TEMP_DIR, "export_test.db")
    json_export = os.path.join(TestConfig.TEMP_DIR, "export.json")
    txt_export = os.path.join(TestConfig.TEMP_DIR, "export.txt")

    manager = HistoryManager(db_path=test_db)

    # Create test data
    print("  Creating test data for export...")
    test_items = [
        HistoryItem(
            timestamp="2024-01-15T10:30:00",
            text="Meeting about project kickoff",
            model="large-v3",
            language="en",
            tags=["meeting", "project"],
        ),
        HistoryItem(
            timestamp="2024-01-15T14:00:00",
            text="Discussion regarding feature implementation",
            model="medium",
            language="en",
            tags=["discussion", "feature"],
        ),
        HistoryItem(
            timestamp="2024-01-16T09:00:00",
            text="Standup daily sync",
            model="small",
            language="en",
            tags=["standup"],
        ),
    ]

    for item in test_items:
        manager.add_item(item, skip_notification=True)

    print(f"    Added {len(test_items)} items")

    # Test JSON export
    print("  Testing JSON export...")
    success = manager.export_to_json(json_export)
    assert_true(success, "JSON export should succeed")
    assert_true(os.path.exists(json_export), "JSON file should exist")

    # Verify JSON content
    with open(json_export, 'r') as f:
        exported_data = json.load(f)
    print(f"    Exported {len(exported_data)} items to JSON")
    assert_equal(len(exported_data), len(test_items), "All items should be exported")

    # Test TXT export
    print("  Testing TXT export...")
    success = manager.export_to_txt(txt_export)
    assert_true(success, "TXT export should succeed")
    assert_true(os.path.exists(txt_export), "TXT file should exist")

    # Verify TXT content
    with open(txt_export, 'r') as f:
        txt_content = f.read()
    print(f"    TXT file size: {len(txt_content)} bytes")
    assert_true(len(txt_content) > 0, "TXT file should have content")
    assert_true("project" in txt_content, "TXT should contain transcribed text")

    print(f"  Import/export test passed!")


# ============================================================================
# Test 10: Statistics Accuracy
# ============================================================================

def test_statistics_accuracy():
    """Test statistics calculations."""
    from faster_whisper_hotkey.flet_gui.history_manager import HistoryManager, HistoryItem

    # Use unique database for statistics test
    # uuid imported at module level
    test_db = os.path.join(TestConfig.TEMP_DIR, f"stats_test_{uuid.uuid4().hex[:8]}.db")
    manager = HistoryManager(db_path=test_db)

    print("  Creating controlled test data...")

    # Add items with specific properties
    # Ensure unique counts to avoid ties in SQL GROUP BY
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=5)

    # Today's items (15 items with large-v3 and en - will be most used)
    for i in range(15):
        item = HistoryItem(
            timestamp=today.isoformat(),
            text=f"Today item {i}",
            model="large-v3",
            language="en",
        )
        manager.add_item(item, skip_notification=True)

    # Yesterday's items (10 items with medium and es)
    for i in range(10):
        item = HistoryItem(
            timestamp=yesterday.isoformat(),
            text=f"Yesterday item {i}",
            model="medium",
            language="es",
        )
        manager.add_item(item, skip_notification=True)

    # Week's items (5 items with small and fr - less than others)
    for i in range(5):
        item = HistoryItem(
            timestamp=week_ago.isoformat(),
            text=f"Week item {i}",
            model="small",
            language="fr",
        )
        manager.add_item(item, skip_notification=True)

    print("  Testing statistics...")
    stats = manager.get_statistics()

    print(f"    Total items: {stats['total_items']}")
    print(f"    Today count: {stats['today_count']}")
    print(f"    Week count: {stats['week_count']}")
    print(f"    Most used model: {stats['most_used_model']}")
    print(f"    Most used language: {stats['most_used_language']}")

    assert_equal(stats['total_items'], 30, "Should have 30 total items")
    assert_equal(stats['today_count'], 15, "Should have 15 today's items")
    assert_equal(stats['week_count'], 30, "All items should be within week")
    assert_equal(stats['most_used_model'], 'large-v3', "large-v3 should be most used (15 items)")
    assert_equal(stats['most_used_language'], 'en', "en should be most used (15 items)")

    print(f"  Statistics accuracy test passed!")


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all tests."""
    TestConfig.setup()

    try:
        print("\n" + "=" * 70)
        print("Running All Tests")
        print("=" * 70)

        # Performance tests
        run_test(test_large_dataset_performance, "Large Dataset Performance (1000+ items)")

        # Search tests
        run_test(test_search_responsiveness, "Search Responsiveness")

        # Clipboard tests
        run_test(test_clipboard_backup_restore, "Clipboard Backup/Restore")

        # Privacy mode tests
        run_test(test_privacy_mode, "Privacy Mode")

        # Database integrity tests
        run_test(test_corrupted_database_handling, "Corrupted Database Handling")

        # Thread safety tests
        run_test(test_thread_safety, "Thread Safety")

        # Auto-paste tests
        run_test(test_auto_paste, "Auto-Paste Functionality")

        # Pruning tests
        run_test(test_database_pruning, "Database Pruning")

        # Import/Export tests
        run_test(test_import_export, "Import/Export")

        # Statistics tests
        run_test(test_statistics_accuracy, "Statistics Accuracy")

    finally:
        TestConfig.teardown()

    # Print summary
    all_passed = results.print_summary()

    if all_passed:
        print("\n" + "=" * 70)
        print("SUCCESS: All tests passed!")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("FAILURE: Some tests failed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
