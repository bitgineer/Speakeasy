"""
Text processing settings panel for faster-whisper-hotkey.

This module provides a GUI panel for configuring the text processing pipeline
with live preview of before/after text processing.

Classes
-------
TextProcessingPanel
    Main settings panel for text processing configuration.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import logging

from .text_processor import (
    TextProcessor,
    TextProcessorConfig,
    FillerWordProcessor,
    CapitalizationProcessor,
    PunctuationProcessor,
    NumberFormattingProcessor,
    AcronymExpansionProcessor,
    ToneStyleProcessor,
)

logger = logging.getLogger(__name__)


# Sample text for preview
SAMPLE_TEXTS = [
    "um hello world this is a test of the transcription system",
    "so i was thinking about the project and uh i think we should do it",
    "what do you think about the new ai features",
    "there are 5000 people coming to the event and we need to prepare",
    "the ui is great but the ux needs work",
]


class TextProcessingPanel:
    """
    Settings panel for text processing configuration.

    Provides checkboxes for toggling processors, sliders for sensitivity
    settings, and a live preview panel showing before/after text.
    """

    def __init__(self, parent, settings, on_save=None):
        """
        Initialize the text processing panel.

        Parameters
        ----------
        parent : tk.Widget
            Parent window
        settings : Settings
            Application settings object
        on_save : callable, optional
            Callback when settings are saved
        """
        self.parent = parent
        self.settings = settings
        self.on_save = on_save
        self.window = None

        # Get current text processing settings
        self.tp_settings = settings.get_text_processing_settings()

        # Create processor for preview
        self.processor = TextProcessor(self.tp_settings)

        # Current sample text index
        self.sample_index = 0

    def show(self):
        """Show the text processing panel window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self._create_window()

    def _create_window(self):
        """Create the main window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Text Processing Settings")
        self.window.geometry("800x700")
        self.window.resizable(True, True)

        # Create main container with notebook
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        processors_frame = ttk.Frame(notebook, padding=15)
        preview_frame = ttk.Frame(notebook, padding=15)
        advanced_frame = ttk.Frame(notebook, padding=15)
        tone_frame = ttk.Frame(notebook, padding=15)

        notebook.add(processors_frame, text="Processors")
        notebook.add(preview_frame, text="Preview")
        notebook.add(advanced_frame, text="Advanced")
        notebook.add(tone_frame, text="Tone Style")

        # Build each tab
        self._build_processors_tab(processors_frame)
        self._build_preview_tab(preview_frame)
        self._build_advanced_tab(advanced_frame)
        self._build_tone_tab(tone_frame)

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(
            button_frame,
            text="Save & Close",
            command=self._save_and_close
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.window.destroy
        ).pack(side=tk.RIGHT)

        # Initial preview update
        self._update_preview()

    def _build_processors_tab(self, parent):
        """Build the processors configuration tab."""
        # Title
        ttk.Label(
            parent,
            text="Enable/disable text processing features",
            font=("", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 15))

        # Scrollable frame for processor options
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Processor options
        self._create_processor_option(
            scrollable_frame,
            "Remove Filler Words",
            "Remove common filler words like 'um', 'uh', 'like'",
            "remove_filler_words",
            0
        )

        self._create_processor_option(
            scrollable_frame,
            "Auto-Capitalize",
            "Capitalize first letters and proper nouns",
            "auto_capitalize",
            1
        )

        self._create_processor_option(
            scrollable_frame,
            "Auto-Punctuate",
            "Add punctuation to transcriptions",
            "auto_punctuate",
            2
        )

        self._create_processor_option(
            scrollable_frame,
            "Format Numbers",
            "Add thousand separators to large numbers",
            "format_numbers",
            3
        )

        self._create_processor_option(
            scrollable_frame,
            "Expand Acronyms",
            "Expand common acronyms (AI, API, etc.) on first use",
            "expand_acronyms",
            4
        )

        self._create_processor_option(
            scrollable_frame,
            "Use Personal Dictionary",
            "Apply custom word corrections from your dictionary",
            "use_dictionary",
            5
        )

        # Bind mouse wheel for scrolling
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _create_processor_option(self, parent, title, description, setting_key, row):
        """Create a single processor option row."""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky="ew", pady=10)
        parent.columnconfigure(0, weight=1)

        # Checkbox
        var = tk.BooleanVar(value=getattr(self.tp_settings, setting_key))
        setattr(self, f"{setting_key}_var", var)

        check = ttk.Checkbutton(
            frame,
            text=title,
            variable=var,
            command=self._update_preview
        )
        check.pack(anchor=tk.W)

        # Description
        desc_label = ttk.Label(frame, text=description, foreground="gray", font=("", 9))
        desc_label.pack(anchor=tk.W, padx=20)

    def _build_preview_tab(self, parent):
        """Build the live preview tab."""
        # Title
        ttk.Label(
            parent,
            text="Live preview of text processing",
            font=("", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 15))

        # Sample selector
        sample_frame = ttk.Frame(parent)
        sample_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(sample_frame, text="Sample text:").pack(side=tk.LEFT)
        self.sample_var = tk.StringVar(value=SAMPLE_TEXTS[0])
        self.sample_combo = ttk.Combobox(
            sample_frame,
            textvariable=self.sample_var,
            values=SAMPLE_TEXTS,
            width=50,
            state="readonly"
        )
        self.sample_combo.pack(side=tk.LEFT, padx=10)
        self.sample_combo.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

        ttk.Button(
            sample_frame,
            text="Try Custom Text",
            command=self._show_custom_text_dialog
        ).pack(side=tk.LEFT)

        # Paned window for before/after
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Before panel
        before_frame = ttk.Frame(paned)
        paned.add(before_frame, weight=1)

        ttk.Label(before_frame, text="Before", font=("", 9, "bold")).pack(anchor=tk.W)
        self.before_text = scrolledtext.ScrolledText(
            before_frame,
            height=15,
            wrap=tk.WORD,
            font=("Consolas", 10)
        )
        self.before_text.pack(fill=tk.BOTH, expand=True)

        # After panel
        after_frame = ttk.Frame(paned)
        paned.add(after_frame, weight=1)

        ttk.Label(after_frame, text="After", font=("", 9, "bold")).pack(anchor=tk.W)
        self.after_text = scrolledtext.ScrolledText(
            after_frame,
            height=15,
            wrap=tk.WORD,
            font=("Consolas", 10)
        )
        self.after_text.pack(fill=tk.BOTH, expand=True)

        # Processing steps display
        steps_frame = ttk.LabelFrame(parent, text="Processing Steps", padding=10)
        steps_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        self.steps_text = scrolledtext.ScrolledText(
            steps_frame,
            height=8,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state="disabled"
        )
        self.steps_text.pack(fill=tk.BOTH, expand=True)

    def _build_advanced_tab(self, parent):
        """Build the advanced settings tab."""
        # Title
        ttk.Label(
            parent,
            text="Advanced configuration",
            font=("", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 15))

        # Filler aggressiveness
        filler_frame = ttk.LabelFrame(parent, text="Filler Word Removal", padding=10)
        filler_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filler_frame, text="Aggressiveness:").pack(anchor=tk.W)
        self.aggressiveness_var = tk.DoubleVar(value=self.tp_settings.filler_aggressiveness)
        aggressiveness_scale = ttk.Scale(
            filler_frame,
            from_=0.0,
            to=1.0,
            variable=self.aggressiveness_var,
            orient=tk.HORIZONTAL,
            command=lambda v: self._update_preview()
        )
        aggressiveness_scale.pack(fill=tk.X, pady=5)

        aggressiveness_desc = ttk.Label(
            filler_frame,
            text="Low: Only remove 'um', 'uh' | Medium: Standard removal | High: Aggressive removal",
            foreground="gray",
            font=("", 8)
        )
        aggressiveness_desc.pack(anchor=tk.W)

        # Capitalization style
        cap_frame = ttk.LabelFrame(parent, text="Capitalization Style", padding=10)
        cap_frame.pack(fill=tk.X, pady=(0, 10))

        self.cap_style_var = tk.StringVar(value=self.tp_settings.capitalization_style)
        ttk.Radiobutton(
            cap_frame,
            text="Sentence case (First letter of sentences)",
            variable=self.cap_style_var,
            value="sentence",
            command=self._update_preview
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            cap_frame,
            text="Title case (First letter of each word)",
            variable=self.cap_style_var,
            value="title",
            command=self._update_preview
        ).pack(anchor=tk.W)

        # Punctuation style
        punct_frame = ttk.LabelFrame(parent, text="Punctuation Style", padding=10)
        punct_frame.pack(fill=tk.X, pady=(0, 10))

        self.punct_style_var = tk.StringVar(value=self.tp_settings.punctuation_style)
        ttk.Radiobutton(
            punct_frame,
            text="Minimal (Only end punctuation)",
            variable=self.punct_style_var,
            value="minimal",
            command=self._update_preview
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            punct_frame,
            text="Full (Add commas, periods, question marks)",
            variable=self.punct_style_var,
            value="full",
            command=self._update_preview
        ).pack(anchor=tk.W)

        # Number formatting style
        num_frame = ttk.LabelFrame(parent, text="Number Formatting", padding=10)
        num_frame.pack(fill=tk.X, pady=(0, 10))

        self.num_style_var = tk.StringVar(value=self.tp_settings.number_style)
        ttk.Radiobutton(
            num_frame,
            text="Commas (1,000, 5,000,000)",
            variable=self.num_style_var,
            value="commas",
            command=self._update_preview
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            num_frame,
            text="Words (one thousand)",
            variable=self.num_style_var,
            value="words",
            command=self._update_preview
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            num_frame,
            text="Both (1,000 with word in parentheses)",
            variable=self.num_style_var,
            value="both",
            command=self._update_preview
        ).pack(anchor=tk.W)

    def _build_tone_tab(self, parent):
        """Build the tone style preset tab."""
        # Title
        ttk.Label(
            parent,
            text="Adjust writing style with tone presets",
            font=("", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 15))

        # Enable tone style processing
        enable_frame = ttk.Frame(parent)
        enable_frame.pack(fill=tk.X, pady=(0, 15))

        self.tone_preset_enabled_var = tk.BooleanVar(
            value=getattr(self.tp_settings, 'tone_preset_enabled', False)
        )
        ttk.Checkbutton(
            enable_frame,
            text="Enable Tone Style Processing",
            variable=self.tone_preset_enabled_var,
            command=self._update_preview
        ).pack(side=tk.LEFT)

        # Tone preset selection
        tone_frame = ttk.LabelFrame(parent, text="Select Tone Preset", padding=10)
        tone_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Get current tone preset
        current_tone = getattr(self.tp_settings, 'tone_preset', 'neutral')

        # Description
        desc_label = ttk.Label(
            tone_frame,
            text="Choose a tone preset to automatically adjust your transcriptions:",
            foreground="gray",
            font=("", 9)
        )
        desc_label.pack(anchor=tk.W, pady=(0, 10))

        # Create radio buttons for each preset
        self.tone_preset_var = tk.StringVar(value=current_tone)

        # Get tone presets from the processor
        presets = ToneStyleProcessor.TONE_PRESETS

        # Group presets by category for better organization
        basic_presets = ["neutral", "professional", "casual"]
        advanced_presets = ["technical", "concise", "creative"]

        # Basic presets section
        ttk.Label(
            tone_frame,
            text="Basic Styles",
            font=("", 9, "bold")
        ).pack(anchor=tk.W, pady=(10, 5))

        for preset_key in basic_presets:
            preset = presets[preset_key]
            self._create_tone_preset_option(tone_frame, preset_key, preset)

        # Advanced presets section
        ttk.Label(
            tone_frame,
            text="Advanced Styles",
            font=("", 9, "bold")
        ).pack(anchor=tk.W, pady=(15, 5))

        for preset_key in advanced_presets:
            preset = presets[preset_key]
            self._create_tone_preset_option(tone_frame, preset_key, preset)

        # Description panel
        desc_frame = ttk.LabelFrame(parent, text="Tone Details", padding=10)
        desc_frame.pack(fill=tk.BOTH, expand=True)

        self.tone_description_text = scrolledtext.ScrolledText(
            desc_frame,
            height=6,
            wrap=tk.WORD,
            font=("", 9),
            state="disabled",
            background="#f5f5f5"
        )
        self.tone_description_text.pack(fill=tk.BOTH, expand=True)

        # Update description on selection change
        self.tone_preset_var.trace_add('write', lambda *args: self._update_tone_description())
        self._update_tone_description()

        # Example transformations
        example_frame = ttk.LabelFrame(parent, text="Example Transformations", padding=10)
        example_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        self.tone_example_text = scrolledtext.ScrolledText(
            example_frame,
            height=5,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state="disabled",
            background="#f5f5f5"
        )
        self.tone_example_text.pack(fill=tk.BOTH, expand=True)

        # Update examples on selection change
        self.tone_preset_var.trace_add('write', lambda *args: self._update_tone_examples())

    def _create_tone_preset_option(self, parent, preset_key, preset):
        """Create a single tone preset option row."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)

        # Radio button
        radio = ttk.Radiobutton(
            frame,
            text=preset["name"],
            variable=self.tone_preset_var,
            value=preset_key,
            command=self._update_preview
        )
        radio.pack(side=tk.LEFT)

        # Description
        desc = ttk.Label(
            frame,
            text=f" — {preset['description']}",
            foreground="gray",
            font=("", 8)
        )
        desc.pack(side=tk.LEFT, padx=(5, 0))

    def _update_tone_description(self):
        """Update the tone description panel."""
        preset_key = self.tone_preset_var.get()
        preset = ToneStyleProcessor.TONE_PRESETS.get(preset_key, {})

        description = f"Tone: {preset.get('name', 'Unknown')}\n\n"
        description += f"{preset.get('description', 'No description available.')}\n\n"

        # Add details about what this tone does
        if preset_key == "neutral":
            description += "This preset applies no modifications to the text. Transcriptions appear exactly as processed by other text processors."
        elif preset_key == "professional":
            description += "Transformations:\n• Removes contractions (can't → cannot)\n• Removes informal words (gonna, wanna, etc.)\n• Ensures complete sentences with proper endings"
        elif preset_key == "casual":
            description += "Transformations:\n• Allows conversational language\n• Permits abbreviations and contractions\n• Maintains relaxed tone (future: contextual emoticons)"
        elif preset_key == "technical":
            description += "Transformations:\n• Preserves technical jargon and terminology\n• Allows technical abbreviations\n• Maintains precise language accuracy"
        elif preset_key == "concise":
            description += "Transformations:\n• Removes filler phrases (I think, basically, etc.)\n• Shortens wordy expressions\n• Removes repetitive words and phrases"
        elif preset_key == "creative":
            description += "Transformations:\n• Adds descriptive elements (future LLM integration)\n• Varied vocabulary enhancements\n• Engaging and elaborate style"

        self.tone_description_text.config(state="normal")
        self.tone_description_text.delete("1.0", tk.END)
        self.tone_description_text.insert("1.0", description)
        self.tone_description_text.config(state="disabled")

    def _update_tone_examples(self):
        """Update the tone example transformations."""
        preset_key = self.tone_preset_var.get()

        # Example input/output pairs for each tone
        examples = {
            "neutral": (
                "Input:  i'm gonna go to the store and get some stuff\n"
                "Output: I'm gonna go to the store and get some stuff"
            ),
            "professional": (
                "Input:  i'm gonna go to the meeting and discuss the project\n"
                "Output: I am going to attend the meeting and discuss the project."
            ),
            "casual": (
                "Input:  i will attend the meeting and discuss the project\n"
                "Output: I'll attend the meeting and discuss the project"
            ),
            "technical": (
                "Input:  the api uses rest and returns json data\n"
                "Output: The API uses REST and returns JSON data"
            ),
            "concise": (
                "Input:  i think that we should basically try to do it\n"
                "Output: We should try to do it."
            ),
            "creative": (
                "Input:  the sunset was beautiful\n"
                "Output: The sunset was beautiful (future: will add elaborate descriptions)"
            ),
        }

        example = examples.get(preset_key, examples["neutral"])

        self.tone_example_text.config(state="normal")
        self.tone_example_text.delete("1.0", tk.END)
        self.tone_example_text.insert("1.0", example)
        self.tone_example_text.config(state="disabled")

    def _show_custom_text_dialog(self):
        """Show dialog for entering custom text."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Custom Text")
        dialog.geometry("500x150")
        dialog.transient(self.window)
        dialog.grab_set()

        ttk.Label(dialog, text="Enter text to preview:").pack(anchor=tk.W, padx=10, pady=10)

        text_var = tk.StringVar(value=self.sample_var.get())
        entry = ttk.Entry(dialog, textvariable=text_var)
        entry.pack(fill=tk.X, padx=10, pady=5)
        entry.select_range(0, tk.END)
        entry.focus()

        def apply():
            self.sample_var.set(text_var.get())
            self._update_preview()
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Preview", command=apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _update_preview(self):
        """Update the preview with current settings."""
        # Update processor config from current UI values
        config = TextProcessorConfig(
            remove_filler_words=self.remove_filler_words_var.get(),
            auto_capitalize=self.auto_capitalize_var.get(),
            auto_punctuate=self.auto_punctuate_var.get(),
            format_numbers=self.format_numbers_var.get(),
            expand_acronyms=self.expand_acronyms_var.get(),
            use_dictionary=getattr(self, 'use_dictionary_var', tk.BooleanVar(value=True)).get(),
            filler_aggressiveness=self.aggressiveness_var.get(),
            capitalization_style=self.cap_style_var.get(),
            punctuation_style=self.punct_style_var.get(),
            number_style=self.num_style_var.get(),
            dictionary_fuzzy_matching=getattr(self.tp_settings, 'dictionary_fuzzy_matching', True),
            tone_preset=getattr(self, 'tone_preset_var', tk.StringVar(value='neutral')).get(),
            tone_preset_enabled=getattr(self, 'tone_preset_enabled_var', tk.BooleanVar(value=False)).get(),
        )

        # Get sample text
        sample = self.sample_var.get()

        # Process and get preview steps
        self.processor = TextProcessor(config)
        preview = self.processor.preview(sample)

        # Update before text
        self.before_text.delete("1.0", tk.END)
        self.before_text.insert("1.0", preview["original"])

        # Update after text
        self.after_text.delete("1.0", tk.END)
        self.after_text.insert("1.0", preview["final"])

        # Update steps display
        self.steps_text.config(state="normal")
        self.steps_text.delete("1.0", tk.END)

        for step, text in preview.items():
            if step != "original" and step != "final":
                # Format step name nicely
                step_name = step.replace("Processor", "")
                self.steps_text.insert(tk.END, f"[{step_name}]\n", "header")
                self.steps_text.insert(tk.END, f"{text}\n\n", "text")

        self.steps_text.tag_config("header", font=("", 9, "bold"))
        self.steps_text.config(state="disabled")

    def _save_and_close(self):
        """Save settings and close window."""
        # Build settings dict from UI values
        text_processing = {
            "remove_filler_words": self.remove_filler_words_var.get(),
            "auto_capitalize": self.auto_capitalize_var.get(),
            "auto_punctuate": self.auto_punctuate_var.get(),
            "format_numbers": self.format_numbers_var.get(),
            "expand_acronyms": self.expand_acronyms_var.get(),
            "use_dictionary": getattr(self, 'use_dictionary_var', tk.BooleanVar(value=True)).get(),
            "filler_aggressiveness": self.aggressiveness_var.get(),
            "capitalization_style": self.cap_style_var.get(),
            "punctuation_style": self.punct_style_var.get(),
            "number_style": self.num_style_var.get(),
            "dictionary_fuzzy_matching": getattr(self.tp_settings, 'dictionary_fuzzy_matching', True),
            "tone_preset": getattr(self, 'tone_preset_var', tk.StringVar(value='neutral')).get(),
            "tone_preset_enabled": getattr(self, 'tone_preset_enabled_var', tk.BooleanVar(value=False)).get(),
        }

        # Save to settings file
        try:
            import json
            from .settings import SETTINGS_FILE, save_settings
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            data["text_processing"] = text_processing
            save_settings(data)

            # Update local settings
            self.settings.text_processing = text_processing
            self.tp_settings = self.settings.get_text_processing_settings()

            if self.on_save:
                self.on_save(text_processing)

            self.window.destroy()
            logger.info("Text processing settings saved")

        except Exception as e:
            logger.error(f"Failed to save text processing settings: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to save settings: {e}")


def show_text_processing_panel(parent, settings, on_save=None):
    """
    Show the text processing settings panel.

    Parameters
    ----------
    parent : tk.Widget
        Parent window
    settings : Settings
        Application settings object
    on_save : callable, optional
        Callback when settings are saved

    Returns
    -------
    TextProcessingPanel
        The panel instance
    """
    panel = TextProcessingPanel(parent, settings, on_save)
    panel.show()
    return panel
