# Implementation Guides: High-Priority Features

## Guide 1: Recording Indicator Overlay

### Overview
Create a floating, minimalist overlay that appears when recording starts and shows visual feedback.

### Design Spec
```
┌─────────────────────────┐
│   ● Recording...        │  ← Pulsing red circle
│   ━━━━━━               │  ← Audio waveform
│   00:03                │  ← Duration counter
└─────────────────────────┘
   ↑
   Draggable, always on top
```

### Technical Implementation

#### File: `src/faster_whisper_hotkey/recording_indicator.py`

```python
import tkinter as tk
from tkinter import ttk
import time
import threading

class RecordingIndicator:
    """Floating overlay window for recording feedback."""

    def __init__(self, parent=None):
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.withdraw()
        self.window.overrideredirect(True)  # No window decorations
        self.window.attributes('-topmost', True)  # Always on top
        self.window.attributes('-alpha', 0.95)  # Slight transparency

        # Position: Center of screen, offset from top
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = 100
        self.window.geometry(f"300x120+{x}+{y}")

        # Make draggable
        self._make_draggable()

        # Build UI
        self._build_ui()

        # Animation state
        self.is_recording = False
        self.start_time = None
        self.pulse_phase = 0

    def _make_draggable(self):
        """Make the window draggable."""
        self.window.bind('<Button-1>', self._start_drag)
        self.window.bind('<B1-Motion>', self._do_drag)

    def _start_drag(self, event):
        self.window._drag_x = event.x
        self.window._drag_y = event.y

    def _do_drag(self, event):
        x = self.window.winfo_x() + event.x - self.window._drag_x
        y = self.window.winfo_y() + event.y - self.window._drag_y
        self.window.geometry(f"+{x}+{y}")

    def _build_ui(self):
        """Build the UI components."""
        # Dark background
        self.window.configure(bg='#1E1E1E')

        # Container frame
        frame = tk.Frame(self.window, bg='#1E1E1E')
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Status row
        status_frame = tk.Frame(frame, bg='#1E1E1E')
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Pulsing circle canvas
        self.canvas = tk.Canvas(
            status_frame,
            width=20,
            height=20,
            bg='#1E1E1E',
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, padx=(0, 10))

        # Status text
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            fg='#FFFFFF',
            bg='#1E1E1E',
            font=('', 10, 'bold')
        )
        self.status_label.pack(side=tk.LEFT)

        # Waveform canvas
        self.waveform = tk.Canvas(
            frame,
            width=270,
            height=40,
            bg='#2D2D2D',
            highlightthickness=0
        )
        self.waveform.pack(pady=(0, 10))

        # Duration label
        self.duration_label = tk.Label(
            frame,
            text="00:00",
            fg='#AAAAAA',
            bg='#1E1E1E',
            font=('', 9)
        )
        self.duration_label.pack()

    def show(self):
        """Show the indicator."""
        self.window.deiconify()

    def hide(self):
        """Hide the indicator."""
        self.window.withdraw()

    def set_recording(self, is_recording: bool):
        """Set recording state and start animation."""
        self.is_recording = is_recording
        self.start_time = time.time() if is_recording else None

        if is_recording:
            self.status_label.config(text="Recording...", fg='#F44336')
            self._start_animation()
        else:
            self.status_label.config(text="Processing...", fg='#FF9800')

    def _start_animation(self):
        """Start the animation loop."""
        if self.is_recording:
            self._animate()
            # Update duration
            if self.start_time:
                elapsed = int(time.time() - self.start_time)
                minutes = elapsed // 60
                seconds = elapsed % 60
                self.duration_label.config(
                    text=f"{minutes:02d}:{seconds:02d}"
                )
            # Schedule next frame (30 FPS)
            self.window.after(33, self._start_animation)

    def _animate(self):
        """Animate one frame."""
        # Pulsing circle
        self.pulse_phase = (self.pulse_phase + 0.1) % (2 * 3.14159)
        radius = 8 + 2 * (self.pulse_phase / 3.14159)
        alpha = int(255 * (1 - self.pulse_phase / (2 * 3.14159)))

        self.canvas.delete('all')
        self.canvas.create_oval(
            10 - radius, 10 - radius,
            10 + radius, 10 + radius,
            fill='#F44336',
            outline='#FFFFFF'
        )

        # Waveform (simulated)
        self.waveform.delete('all')
        import random
        for i in range(20):
            x = i * 14
            height = random.randint(5, 35)
            color = '#F44336' if height > 20 else '#2196F3'
            self.waveform.create_rectangle(
                x, 20 - height // 2,
                x + 10, 20 + height // 2,
                fill=color,
                outline=''
            )
```

### Integration

#### In `transcriber.py`:

```python
from .recording_indicator import RecordingIndicator

class MicrophoneTranscriber:
    def __init__(self, settings, on_state_change=None, on_transcription=None):
        # ... existing code ...

        # Add recording indicator
        self.recording_indicator = RecordingIndicator()

    def on_press(self):
        """Called when hotkey is pressed."""
        self.recording_indicator.show()
        self.recording_indicator.set_recording(True)
        # ... existing code ...

    def on_release(self):
        """Called when hotkey is released."""
        self.recording_indicator.set_recording(False)
        # ... existing code ...

        # Hide after processing
        def hide_indicator():
            self.recording_indicator.hide()

        # Schedule hide after transcription completes
        threading.Timer(1.0, hide_indicator).start()
```

---

## Guide 2: Dark Mode Styling

### Overview
Implement modern dark mode with system-aware theme detection.

### Color Palette

```python
THEMES = {
    'dark': {
        'bg': '#1E1E1E',           # Background
        'fg': '#E0E0E0',           # Foreground (text)
        'surface': '#2D2D2D',      # Surface (panels, cards)
        'surface_variant': '#3D3D3D',  # Surface variant
        'primary': '#64B5F6',      # Primary (accent)
        'primary_dark': '#42A5F5', # Primary dark
        'secondary': '#9C27B0',    # Secondary
        'error': '#F44336',        # Error
        'warning': '#FF9800',      # Warning
        'success': '#4CAF50',      # Success
        'border': '#424242',       # Border
        'disabled': '#757575',     # Disabled text
    },
    'light': {
        'bg': '#FFFFFF',
        'fg': '#212121',
        'surface': '#F5F5F5',
        'surface_variant': '#EEEEEE',
        'primary': '#2196F3',
        'primary_dark': '#1976D2',
        'secondary': '#9C27B0',
        'error': '#F44336',
        'warning': '#FF9800',
        'success': '#4CAF50',
        'border': '#E0E0E0',
        'disabled': '#BDBDBD',
    }
}
```

### Implementation

#### File: `src/faster_whisper_hotkey/theme.py`

```python
import tkinter as tk
from tkinter import ttk
import json
import os

class ThemeManager:
    """Manage application theming."""

    def __init__(self):
        self.current_theme = self._load_theme_preference()
        self.colors = THEMES[self.current_theme]

    def _load_theme_preference(self) -> str:
        """Load theme preference from settings."""
        # Try to load from settings
        settings_file = os.path.expanduser(
            "~/.config/faster_whisper_hotkey/transcriber_settings.json"
        )
        try:
            with open(settings_file, 'r') as f:
                data = json.load(f)
                return data.get('theme', 'dark')
        except:
            # Detect system theme
            # For now, default to dark
            return 'dark'

    def save_theme_preference(self, theme: str):
        """Save theme preference to settings."""
        settings_file = os.path.expanduser(
            "~/.config/faster_whisper_hotkey/transcriber_settings.json"
        )
        try:
            with open(settings_file, 'r') as f:
                data = json.load(f)
        except:
            data = {}

        data['theme'] = theme

        with open(settings_file, 'w') as f:
            json.dump(data, f, indent=2)

        self.current_theme = theme
        self.colors = THEMES[theme]

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        new_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.save_theme_preference(new_theme)
        return new_theme

    def get_color(self, name: str) -> str:
        """Get a color by name."""
        return self.colors.get(name, '#000000')

    def apply_style(self, root: tk.Tk):
        """Apply theme styles to a root window."""
        style = ttk.Style(root)

        # Use clam as base (more customizable)
        style.theme_use('clam')

        # Configure colors
        bg = self.get_color('bg')
        fg = self.get_color('fg')
        surface = self.get_color('surface')
        primary = self.get_color('primary')
        border = self.get_color('border')

        # Root configuration
        root.configure(bg=bg)

        # Frame
        style.configure(
            'TFrame',
            background=bg,
            bordercolor=border,
        )

        # Label
        style.configure(
            'TLabel',
            background=bg,
            foreground=fg,
            font=('', 10)
        )

        # Button
        style.configure(
            'TButton',
            background=surface,
            foreground=fg,
            bordercolor=border,
            lightcolor=surface,
            darkcolor=surface,
            padding=10,
            relief='flat',
        )
        style.map(
            'TButton',
            background=[('active', primary)],
            foreground=[('active', '#FFFFFF')]
        )

        # Entry
        style.configure(
            'TEntry',
            fieldbackground=surface,
            foreground=fg,
            bordercolor=border,
            padding=8,
        )

        # Checkbutton
        style.configure(
            'TCheckbutton',
            background=bg,
            foreground=fg,
        )

        # Radiobutton
        style.configure(
            'TRadiobutton',
            background=bg,
            foreground=fg,
        )

        # Combobox
        style.configure(
            'TCombobox',
            fieldbackground=surface,
            foreground=fg,
            bordercolor=border,
            padding=8,
        )

        # Notebook (tabs)
        style.configure(
            'TNotebook',
            background=bg,
            bordercolor=border,
        )
        style.configure(
            'TNotebook.Tab',
            background=surface,
            foreground=fg,
            padding=[20, 10],
            bordercolor=border,
        )
        style.map(
            'TNotebook.Tab',
            background=[('selected', primary)],
            foreground=[('selected', '#FFFFFF')]
        )

        # Progress bar
        style.configure(
            'TProgressbar',
            background=primary,
            troughcolor=surface,
            bordercolor=border,
            lightcolor=primary,
            darkcolor=primary,
        )

        # Separator
        style.configure(
            'TSeparator',
            background=border,
        )

        # Scrollbar
        style.configure(
            'TScrollbar',
            background=surface,
            troughcolor=bg,
            bordercolor=border,
            arrowsize=20,
        )

        return style
```

### Usage Example

#### In `gui.py`:

```python
from .theme import ThemeManager

class WhisperHotkeyGUI:
    def __init__(self):
        self.theme = ThemeManager()

        # Create root
        self.root = tk.Tk()
        self.root.withdraw()

        # Apply theme
        self.style = self.theme.apply_style(self.root)

    def _create_settings_window(self):
        """Create settings window with theme support."""
        window = tk.Toplevel(self.root)
        window.title("Settings")

        # Apply theme to this window
        self.style = self.theme.apply_style(window)

        # Theme toggle button
        theme_btn = ttk.Button(
            window,
            text=f"Toggle Theme (Currently: {self.theme.current_theme})",
            command=self._toggle_theme
        )
        theme_btn.pack(pady=10)

    def _toggle_theme(self):
        """Toggle between light and dark theme."""
        new_theme = self.theme.toggle_theme()

        # Refresh all windows
        self.style = self.theme.apply_style(self.root)

        # Refresh settings window if open
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.destroy()
            self._create_settings_window()
```

---

## Guide 3: Personal Dictionary

### Overview
Auto-learn user-specific vocabulary from manual corrections.

### Data Structure

```json
{
  "dictionary": {
    "user_added": {
      "Deque": {
        "variants": ["deque", "dequeue", "d-queue"],
        "context": "Python data structure",
        "usage_count": 5
      },
      "PyScript": {
        "variants": ["pyscript", "pi-script"],
        "context": "Python in browser",
        "usage_count": 3
      }
    },
    "auto_learned": {
      "faster-whisper": {
        "variants": ["faster whisper", "fasterwhisper"],
        "context": null,
        "usage_count": 12
      }
    }
  }
}
```

### Implementation

#### File: `src/faster_whisper_hotkey/dictionary.py`

```python
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
import re
from difflib import SequenceMatcher

@dataclass
class DictionaryEntry:
    """A dictionary entry."""
    canonical: str
    variants: List[str]
    context: Optional[str]
    usage_count: int

class PersonalDictionary:
    """Manage user-specific vocabulary."""

    def __init__(self):
        self.dictionary_file = os.path.expanduser(
            "~/.config/faster_whisper_hotkey/personal_dictionary.json"
        )
        self.entries = self._load()

    def _load(self) -> Dict[str, DictionaryEntry]:
        """Load dictionary from disk."""
        if not os.path.exists(self.dictionary_file):
            return {}

        try:
            with open(self.dictionary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                word: DictionaryEntry(
                    canonical=word,
                    variants=entry.get('variants', []),
                    context=entry.get('context'),
                    usage_count=entry.get('usage_count', 0)
                )
                for word, entry in data.items()
            }
        except:
            return {}

    def save(self):
        """Save dictionary to disk."""
        data = {
            word: {
                'variants': entry.variants,
                'context': entry.context,
                'usage_count': entry.usage_count
            }
            for word, entry in self.entries.items()
        }

        os.makedirs(os.path.dirname(self.dictionary_file), exist_ok=True)
        with open(self.dictionary_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def add_word(
        self,
        word: str,
        variants: Optional[List[str]] = None,
        context: Optional[str] = None,
        auto_learned: bool = False
    ):
        """Add a word to the dictionary."""
        if word in self.entries:
            # Update existing entry
            self.entries[word].usage_count += 1
            if variants:
                self.entries[word].variants.extend(variants)
            if context:
                self.entries[word].context = context
        else:
            # Create new entry
            self.entries[word] = DictionaryEntry(
                canonical=word,
                variants=variants or [],
                context=context,
                usage_count=1
            )

        self.save()

    def remove_word(self, word: str):
        """Remove a word from the dictionary."""
        if word in self.entries:
            del self.entries[word]
            self.save()

    def find_match(self, word: str, threshold: float = 0.8) -> Optional[str]:
        """Find a dictionary word that matches the given word."""
        # Direct match
        if word in self.entries:
            return word

        # Check variants
        for entry_word, entry in self.entries.items():
            if word.lower() in [v.lower() for v in entry.variants]:
                return entry_word

        # Fuzzy match
        for entry_word, entry in self.entries.items():
            similarity = SequenceMatcher(None, word.lower(), entry_word.lower()).ratio()
            if similarity >= threshold:
                return entry_word

        return None

    def correct_text(self, text: str) -> str:
        """Apply dictionary corrections to text."""
        words = text.split()
        corrected = []

        for word in words:
            # Preserve punctuation
            stripped = word.strip('.,!?;:')
            punctuation = word[len(stripped):]

            # Check for match
            match = self.find_match(stripped)
            if match:
                corrected.append(match + punctuation)
                # Increment usage
                self.entries[match].usage_count += 1
            else:
                corrected.append(stripped + punctuation)

        result = ' '.join(corrected)
        self.save()

        return result

    def suggest_from_correction(self, original: str, corrected: str):
        """Suggest dictionary entry from manual correction."""
        # If correction is substantially different, suggest adding
        similarity = SequenceMatcher(None, original.lower(), corrected.lower()).ratio()

        if similarity < 0.8:  # Significant change
            # Suggest adding corrected word with original as variant
            self.add_word(
                word=corrected,
                variants=[original],
                context="Auto-learned from correction",
                auto_learned=True
            )

    def get_statistics(self) -> Dict:
        """Get dictionary statistics."""
        return {
            'total_words': len(self.entries),
            'auto_learned': sum(1 for e in self.entries.values() if e.context and 'auto-learned' in e.context),
            'most_used': sorted(
                [(w, e.usage_count) for w, e in self.entries.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
```

### Integration with History Panel

#### In `history_panel.py`:

```python
from .dictionary import PersonalDictionary

class HistoryPanel:
    def __init__(self, max_items=50):
        # ... existing code ...
        self.dictionary = PersonalDictionary()

    def add_edit_functionality(self):
        """Add edit and learn functionality."""
        # Add "Learn from correction" button
        learn_btn = ttk.Button(
            self,
            text="Learn from Corrections",
            command=self._learn_from_corrections
        )
        learn_btn.pack(pady=5)

    def _learn_from_corrections(self):
        """Analyze manual edits and add to dictionary."""
        if not self.history:
            return

        # Compare transcriptions with edits
        for item in self.history:
            original = item.get('text', '')
            edited = item.get('edited_text', '')

            if edited and edited != original:
                # Suggest dictionary entry
                # (This would require tracking edits per-item)
                pass
```

---

## Guide 4: Snippet Library

### Overview
Voice shortcuts that expand to predefined text.

### Data Structure

```json
{
  "snippets": {
    "calendar": {
      "name": "Calendar Link",
      "trigger": "calendar",
      "content": "You can book a 30-minute call with me here: calendly.com/yourname",
      "category": "contact",
      "usage_count": 15
    },
    "intro": {
      "name": "Email Introduction",
      "trigger": "introduction",
      "content": "Hi, I'm {name}, a {role} working on {project}.",
      "variables": ["name", "role", "project"],
      "category": "templates",
      "usage_count": 8
    }
  },
  "categories": ["contact", "templates", "code", "responses"]
}
```

### Implementation

#### File: `src/faster_whisper_hotkey/snippets.py`

```python
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

@dataclass
class Snippet:
    """A text snippet."""
    name: str
    trigger: str
    content: str
    variables: Optional[List[str]] = None
    category: str = "general"
    usage_count: int = 0

class SnippetLibrary:
    """Manage text snippets for voice shortcuts."""

    def __init__(self):
        self.snippets_file = os.path.expanduser(
            "~/.config/faster_whisper_hotkey/snippets.json"
        )
        self.snippets = self._load()

    def _load(self) -> Dict[str, Snippet]:
        """Load snippets from disk."""
        if not os.path.exists(self.snippets_file):
            # Create default snippets
            defaults = self._get_defaults()
            self._save_dict(defaults)
            return defaults

        try:
            with open(self.snippets_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                trigger: Snippet(
                    name=entry['name'],
                    trigger=trigger,
                    content=entry['content'],
                    variables=entry.get('variables'),
                    category=entry.get('category', 'general'),
                    usage_count=entry.get('usage_count', 0)
                )
                for trigger, entry in data.get('snippets', {}).items()
            }
        except:
            return self._get_defaults()

    def _get_defaults(self) -> Dict[str, Snippet]:
        """Get default snippets."""
        return {
            "calendar": Snippet(
                name="Calendar Link",
                trigger="calendar",
                content="You can book a 30-minute call with me here: calendly.com/yourname",
                category="contact"
            ),
            "email": Snippet(
                name="Email Signature",
                trigger="email signature",
                content="Best regards,\n[Your Name]",
                category="contact"
            ),
            "address": Snippet(
                name="Address",
                trigger="my address",
                content="[Your Full Address]",
                category="personal"
            )
        }

    def _save_dict(self, snippets: Dict[str, Snippet]):
        """Save snippets to disk."""
        data = {
            'snippets': {
                trigger: {
                    'name': snippet.name,
                    'content': snippet.content,
                    'variables': snippet.variables,
                    'category': snippet.category,
                    'usage_count': snippet.usage_count
                }
                for trigger, snippet in snippets.items()
            }
        }

        os.makedirs(os.path.dirname(self.snippets_file), exist_ok=True)
        with open(self.snippets_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def save(self):
        """Save snippets to disk."""
        self._save_dict(self.snippets)

    def add_snippet(
        self,
        trigger: str,
        content: str,
        name: Optional[str] = None,
        category: str = "general"
    ):
        """Add a new snippet."""
        # Extract variables from content
        variables = re.findall(r'\{(\w+)\}', content)

        snippet = Snippet(
            name=name or trigger.title(),
            trigger=trigger,
            content=content,
            variables=variables if variables else None,
            category=category
        )

        self.snippets[trigger] = snippet
        self.save()

    def remove_snippet(self, trigger: str):
        """Remove a snippet."""
        if trigger in self.snippets:
            del self.snippets[trigger]
            self.save()

    def find_snippet(self, text: str) -> Optional[Snippet]:
        """Find a snippet triggered by the given text."""
        # Check for exact trigger match
        if text.lower().strip() in self.snippets:
            snippet = self.snippets[text.lower().strip()]
            snippet.usage_count += 1
            self.save()
            return snippet

        # Check for partial match (fuzzy)
        for trigger, snippet in self.snippets.items():
            if trigger in text.lower():
                snippet.usage_count += 1
                self.save()
                return snippet

        return None

    def expand_snippet(self, snippet: Snippet, variables: Optional[Dict] = None) -> str:
        """Expand a snippet with optional variable substitution."""
        content = snippet.content

        if snippet.variables and variables:
            for var in snippet.variables:
                placeholder = '{' + var + '}'
                value = variables.get(var, f'[{var.title()}]')
                content = content.replace(placeholder, value)

        return content

    def get_all_triggers(self) -> List[str]:
        """Get all snippet triggers."""
        return list(self.snippets.keys())

    def get_by_category(self, category: str) -> List[Snippet]:
        """Get all snippets in a category."""
        return [
            snippet for snippet in self.snippets.values()
            if snippet.category == category
        ]
```

### Integration with Transcription

#### In `transcriber.py`:

```python
from .snippets import SnippetLibrary

class MicrophoneTranscriber:
    def __init__(self, settings, on_state_change=None, on_transcription=None):
        # ... existing code ...
        self.snippets = SnippetLibrary()

    def process_transcription(self, text: str) -> str:
        """Process transcription and expand snippets."""
        # Check if text is a snippet trigger
        snippet = self.snippets.find_snippet(text)

        if snippet:
            # Expand snippet
            expanded = self.snippets.expand_snippet(snippet)
            # Optional: Show notification
            logger.info(f"Expanded snippet '{snippet.trigger}'")
            return expanded

        return text
```

### GUI for Snippet Management

#### File: `src/faster_whisper_hotkey/snippets_panel.py`

```python
import tkinter as tk
from tkinter import ttk, messagebox
from .snippets import SnippetLibrary

class SnippetsPanel:
    """Panel for managing text snippets."""

    def __init__(self, parent, on_change=None):
        self.on_change = on_change
        self.library = SnippetLibrary()

        self.window = tk.Toplevel(parent)
        self.window.title("Snippet Library")
        self.window.geometry("600x400")

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        """Build the UI."""
        # Main container
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(
            header_frame,
            text="Snippet Library",
            font=('', 14, 'bold')
        ).pack(side=tk.LEFT)

        ttk.Button(
            header_frame,
            text="+ Add Snippet",
            command=self._add_snippet
        ).pack(side=tk.RIGHT)

        # Search
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Snippet list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview
        columns = ('trigger', 'name', 'category', 'usage')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')

        self.tree.heading('trigger', text='Trigger')
        self.tree.heading('name', text='Name')
        self.tree.heading('category', text='Category')
        self.tree.heading('usage', text='Uses')

        self.tree.column('trigger', width=120)
        self.tree.column('name', width=200)
        self.tree.column('category', width=100)
        self.tree.column('usage', width=60)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="Edit", command=self._edit_snippet).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Delete", command=self._delete_snippet).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT)

    def _refresh_list(self, search: str = ''):
        """Refresh the snippet list."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add snippets
        for snippet in self.library.snippets.values():
            if search and search.lower() not in snippet.trigger.lower():
                continue

            self.tree.insert(
                '',
                'end',
                values=(
                    snippet.trigger,
                    snippet.name,
                    snippet.category,
                    snippet.usage_count
                )
            )

    def _on_search(self, *args):
        """Handle search input."""
        self._refresh_list(self.search_var.get())

    def _add_snippet(self):
        """Add a new snippet."""
        # Open add snippet dialog
        dialog = SnippetDialog(self.window, self.library)
        self.window.wait_window(dialog.window)

        if dialog.result:
            self.library.add_snippet(**dialog.result)
            self._refresh_list()
            if self.on_change:
                self.on_change()

    def _edit_snippet(self):
        """Edit selected snippet."""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        trigger = item['values'][0]

        snippet = self.library.snippets.get(trigger)
        if not snippet:
            return

        # Open edit dialog
        dialog = SnippetDialog(self.window, self.library, snippet)
        self.window.wait_window(dialog.window)

        if dialog.result:
            # Remove old, add new
            self.library.remove_snippet(trigger)
            self.library.add_snippet(**dialog.result)
            self._refresh_list()
            if self.on_change:
                self.on_change()

    def _delete_snippet(self):
        """Delete selected snippet."""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        trigger = item['values'][0]

        if messagebox.askyesno("Confirm Delete", f"Delete snippet '{trigger}'?"):
            self.library.remove_snippet(trigger)
            self._refresh_list()
            if self.on_change:
                self.on_change()

class SnippetDialog:
    """Dialog for adding/editing snippets."""

    def __init__(self, parent, library, snippet=None):
        self.library = library
        self.snippet = snippet
        self.result = None

        self.window = tk.Toplevel(parent)
        self.window.title("Edit Snippet" if snippet else "Add Snippet")
        self.window.geometry("400x300")
        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self):
        """Build the UI."""
        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Trigger
        ttk.Label(frame, text="Voice Trigger:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.trigger_var = tk.StringVar(value=self.snippet.trigger if self.snippet else '')
        ttk.Entry(frame, textvariable=self.trigger_var).grid(row=0, column=1, sticky=tk.EW, pady=5)

        # Name
        ttk.Label(frame, text="Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=self.snippet.name if self.snippet else '')
        ttk.Entry(frame, textvariable=self.name_var).grid(row=1, column=1, sticky=tk.EW, pady=5)

        # Category
        ttk.Label(frame, text="Category:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar(value=self.snippet.category if self.snippet else 'general')
        category_combo = ttk.Combobox(
            frame,
            textvariable=self.category_var,
            values=['general', 'contact', 'code', 'templates', 'personal']
        )
        category_combo.grid(row=2, column=1, sticky=tk.EW, pady=5)

        # Content
        ttk.Label(frame, text="Content:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.content_text = tk.Text(frame, height=8, width=40)
        self.content_text.grid(row=3, column=1, sticky=tk.EW, pady=5)

        if self.snippet:
            self.content_text.insert('1.0', self.snippet.content)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=15)

        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT)

        frame.columnconfigure(1, weight=1)

    def _save(self):
        """Save the snippet."""
        trigger = self.trigger_var.get().strip()
        name = self.name_var.get().strip()
        category = self.category_var.get().strip()
        content = self.content_text.get('1.0', tk.END).strip()

        if not trigger or not content:
            messagebox.showerror("Error", "Trigger and content are required")
            return

        self.result = {
            'trigger': trigger,
            'name': name or trigger.title(),
            'category': category,
            'content': content
        }

        self.window.destroy()
```

---

## Testing Checklist

For each feature, test:

### Recording Indicator
- [ ] Appears on hotkey press
- [ ] Shows pulsing animation
- [ ] Displays waveform
- [ ] Updates duration counter
- [ ] Draggable to reposition
- [ ] Disappears after transcription
- [ ] Works on multi-monitor setups

### Dark Mode
- [ ] Toggle switches themes
- [ ] All windows update
- [ ] Text remains readable
- [ ] Colors follow accessibility guidelines
- [ ] Theme preference persists across restarts

### Personal Dictionary
- [ ] Add new words
- [ ] Remove words
- [ ] Fuzzy matching works
- [ ] Auto-learn from corrections
- [ ] Statistics accurate
- [ ] Export/import functionality

### Snippet Library
- [ ] Add new snippets
- [ ] Edit existing snippets
- [ ] Delete snippets
- [ ] Voice triggers work
- [ ] Variable substitution works
- [ ] Categories organize snippets
- [ ] Search/filter functionality

---

## Next Steps

1. **Pick One Feature**: Start with the recording indicator (highest visual impact)
2. **Create Branch**: `feature/recording-indicator`
3. **Implement**: Follow the guide
4. **Test**: Use the checklist
5. **Iterate**: Refine based on testing
6. **Document**: Update user guide

**Let's build something amazing!** 🚀
