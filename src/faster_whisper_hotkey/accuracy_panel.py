"""
Accuracy dashboard panel for tracking transcription accuracy over time.

This module provides a modern GUI window for viewing and managing
accuracy tracking data. It features:
- Overall accuracy statistics
- Accuracy trend visualization over time
- Problem words list with one-click dictionary add
- Correction statistics by type

Classes
-------
AccuracyPanel
    Modern accuracy dashboard with theme support.

Notes
-----
Accuracy data is loaded from the accuracy tracking system and
displayed with interactive visualizations.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .settings import load_settings
from .theme import ThemeManager, create_styled_frame, create_styled_label, create_styled_button
from .icons import IconFactory
from .accuracy_tracker import AccuracyTracker, ProblemWord, load_accuracy_tracker
from .dictionary import load_dictionary


class AccuracyPanel:
    """Modern accuracy dashboard with charts and problem words."""

    def __init__(self, theme_manager: ThemeManager, on_close=None):
        """Initialize the accuracy panel.

        Args:
            theme_manager: ThemeManager instance for styling
            on_close: Callback when panel is closed
        """
        self.theme_manager = theme_manager
        self.on_close = on_close
        self.accuracy_tracker = load_accuracy_tracker()
        self.dictionary = load_dictionary()
        self.window = None
        self.icon_factory = IconFactory(theme_manager)
        self.problem_words: List[ProblemWord] = []
        self.selected_days = 30

    def show(self):
        """Show the accuracy panel window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel()
        self.window.title("Accuracy Dashboard")
        self.window.geometry("900x700")
        self.window.minsize(700, 500)

        # Apply theme to window
        self.theme_manager.style.apply_to_widget(self.window)

        # Configure grid with 8px padding
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        # Main container
        main_frame = create_styled_frame(
            self.window,
            self.theme_manager,
            card_style=False
        )
        main_frame.grid(row=0, column=0, sticky="nsew", padx=self.theme_manager.get_spacing("md"),
                       pady=self.theme_manager.get_spacing("md"))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Header section
        self._create_header(main_frame)

        # Time range selector
        self._create_time_range_selector(main_frame)

        # Content section with tabs
        self._create_content(main_frame)

        # Load data
        self._refresh_data()

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Center on screen
        self._center_window()

    def _create_header(self, parent):
        """Create the header section."""
        header_frame = create_styled_frame(parent, self.theme_manager, card_style=False)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, self.theme_manager.get_spacing("sm")))
        header_frame.columnconfigure(1, weight=1)

        # Icon + title
        title_frame = ttk.Frame(header_frame)
        title_frame.grid(row=0, column=0, sticky="w")

        # Chart icon
        icon = self.icon_factory.create(title_frame, "chart", size=28,
                                       color=self.theme_manager.get_color("primary"))
        icon.grid(row=0, column=0, padx=(0, self.theme_manager.get_spacing("sm")), pady="4")

        # Title
        title = create_styled_label(
            title_frame,
            self.theme_manager,
            variant="subtitle",
            text="Accuracy Dashboard"
        )
        title.grid(row=0, column=1)

    def _create_time_range_selector(self, parent):
        """Create the time range selector."""
        selector_frame = create_styled_frame(parent, self.theme_manager, card_style=True)
        selector_frame.grid(row=1, column=0, sticky="ew", pady=(0, self.theme_manager.get_spacing("sm")))

        label = create_styled_label(
            selector_frame,
            self.theme_manager,
            variant="body",
            text="Time Range:"
        )
        label.pack(side=tk.LEFT, padx=(self.theme_manager.get_spacing("sm"), self.theme_manager.get_spacing("xs")))

        # Time range buttons
        ranges = [(7, "7 Days"), (30, "30 Days"), (90, "90 Days")]

        self.range_var = tk.IntVar(value=30)
        self.range_buttons = {}

        for days, text in ranges:
            rb = ttk.Radiobutton(
                selector_frame,
                text=text,
                variable=self.range_var,
                value=days,
                command=lambda d=days: self._on_range_change(d)
            )
            rb.pack(side=tk.LEFT, padx=self.theme_manager.get_spacing("xs"))
            self.range_buttons[days] = rb

    def _create_content(self, parent):
        """Create the main content area with tabs."""
        content_frame = create_styled_frame(parent, self.theme_manager, card_style=True)
        content_frame.grid(row=2, column=0, sticky="nsew")
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Statistics tab
        self._create_stats_tab(self.notebook)

        # Problem words tab
        self._create_problem_words_tab(self.notebook)

    def _create_stats_tab(self, parent):
        """Create the statistics tab."""
        stats_frame = ttk.Frame(parent)
        parent.add(stats_frame, text="Statistics")
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(1, weight=1)

        # Overall stats section
        overall_frame = create_styled_frame(stats_frame, self.theme_manager, card_style=True)
        overall_frame.grid(row=0, column=0, sticky="ew", padx=self.theme_manager.get_spacing("sm"),
                          pady=self.theme_manager.get_spacing("sm"))
        overall_frame.columnconfigure(0, weight=1)

        # Stats header
        stats_header = create_styled_label(
            overall_frame,
            self.theme_manager,
            variant="section",
            text="Overall Statistics"
        )
        stats_header.grid(row=0, column=0, sticky="w", padx=self.theme_manager.get_spacing("sm"),
                         pady=(self.theme_manager.get_spacing("sm"), 0))

        # Stats container with cards
        stats_container = ttk.Frame(overall_frame)
        stats_container.grid(row=1, column=0, sticky="ew", padx=self.theme_manager.get_spacing("sm"),
                            pady=self.theme_manager.get_spacing("sm"))
        stats_container.columnconfigure((0, 1, 2, 3), weight=1)

        # Accuracy card
        self.accuracy_card = self._create_stat_card(
            stats_container,
            "Accuracy",
            "0%",
            0,
            "primary"
        )

        # Total words card
        self.words_card = self._create_stat_card(
            stats_container,
            "Total Words",
            "0",
            1,
            "success"
        )

        # Corrections card
        self.corrections_card = self._create_stat_card(
            stats_container,
            "Corrections",
            "0",
            2,
            "warning"
        )

        # Manual edits card
        self.manual_card = self._create_stat_card(
            stats_container,
            "Manual Edits",
            "0%",
            3,
            "error"
        )

        # Trend chart section
        trend_frame = create_styled_frame(stats_frame, self.theme_manager, card_style=True)
        trend_frame.grid(row=1, column=0, sticky="nsew", padx=self.theme_manager.get_spacing("sm"),
                        pady=(0, self.theme_manager.get_spacing("sm")))
        trend_frame.columnconfigure(0, weight=1)
        trend_frame.rowconfigure(1, weight=1)

        # Trend header
        trend_header = create_styled_label(
            trend_frame,
            self.theme_manager,
            variant="section",
            text="Accuracy Trend"
        )
        trend_header.grid(row=0, column=0, sticky="w", padx=self.theme_manager.get_spacing("sm"),
                         pady=(self.theme_manager.get_spacing("sm"), 0))

        # Canvas for trend chart
        self.trend_canvas = tk.Canvas(
            trend_frame,
            bg=self.theme_manager.get_color("bg_card"),
            highlightthickness=0
        )
        self.trend_canvas.grid(row=1, column=0, sticky="nsew", padx=self.theme_manager.get_spacing("sm"),
                               pady=self.theme_manager.get_spacing("sm"))

        # Correction stats section
        correction_frame = create_styled_frame(stats_frame, self.theme_manager, card_style=True)
        correction_frame.grid(row=2, column=0, sticky="nsew", padx=self.theme_manager.get_spacing("sm"),
                             pady=(0, self.theme_manager.get_spacing("sm")))
        correction_frame.columnconfigure(0, weight=1)
        correction_frame.rowconfigure(1, weight=1)

        # Correction stats header
        corr_header = create_styled_label(
            correction_frame,
            self.theme_manager,
            variant="section",
            text="Corrections by Type"
        )
        corr_header.grid(row=0, column=0, sticky="w", padx=self.theme_manager.get_spacing("sm"),
                        pady=(self.theme_manager.get_spacing("sm"), 0))

        # Correction stats listbox
        list_container = ttk.Frame(correction_frame)
        list_container.grid(row=1, column=0, sticky="nsew", padx=self.theme_manager.get_spacing("sm"),
                           pady=self.theme_manager.get_spacing("sm"))
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)

        self.correction_listbox = tk.Listbox(
            list_container,
            font=self.theme_manager.get_font("base"),
            selectmode=tk.SINGLE,
            highlightthickness=0,
            borderwidth=0,
            relief="flat"
        )
        c = self.theme_manager.colors
        self.correction_listbox.configure(
            bg=c["bg_main"],
            fg=c["fg_primary"],
            selectbackground=c["primary_light"],
            selectforeground=c["fg_primary"]
        )
        self.correction_listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.correction_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.correction_listbox.configure(yscrollcommand=scrollbar.set)

    def _create_problem_words_tab(self, parent):
        """Create the problem words tab."""
        pw_frame = ttk.Frame(parent)
        parent.add(pw_frame, text="Problem Words")
        pw_frame.columnconfigure(0, weight=1)
        pw_frame.rowconfigure(1, weight=1)

        # Header
        header_frame = create_styled_frame(pw_frame, self.theme_manager, card_style=True)
        header_frame.grid(row=0, column=0, sticky="ew", padx=self.theme_manager.get_spacing("sm"),
                         pady=self.theme_manager.get_spacing("sm"))

        header_text = create_styled_label(
            header_frame,
            self.theme_manager,
            variant="section",
            text="Problem Words - Frequently Mis-transcribed"
        )
        header_text.pack(anchor=tk.W, padx=self.theme_manager.get_spacing("sm"),
                        pady=(self.theme_manager.get_spacing("sm"), self.theme_manager.get_spacing("xs")))

        hint_text = create_styled_label(
            header_frame,
            self.theme_manager,
            variant="hint",
            text="Click 'Add to Dictionary' to add common corrections to your personal dictionary"
        )
        hint_text.pack(anchor=tk.W, padx=self.theme_manager.get_spacing("sm"),
                      pady=(0, self.theme_manager.get_spacing("sm")))

        # Problem words list
        list_frame = create_styled_frame(pw_frame, self.theme_manager, card_style=True)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=self.theme_manager.get_spacing("sm"),
                       pady=(0, self.theme_manager.get_spacing("sm")))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Create treeview for problem words
        columns = ("word", "frequency", "corrections", "status")
        self.pw_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode=tk.BROWSE)

        self.pw_tree.heading("word", text="Word/Phrase")
        self.pw_tree.heading("frequency", text="Frequency")
        self.pw_tree.heading("corrections", text="Corrections")
        self.pw_tree.heading("status", text="Status")

        self.pw_tree.column("word", width=200)
        self.pw_tree.column("frequency", width=100)
        self.pw_tree.column("corrections", width=100)
        self.pw_tree.column("status", width=100)

        c = self.theme_manager.colors
        self.pw_tree.tag_configure("in_dict", background=c["success_light"])
        self.pw_tree.tag_configure("not_in_dict", background=c["bg_main"])

        self.pw_tree.grid(row=0, column=0, sticky="nsew", padx=self.theme_manager.get_spacing("sm"),
                         pady=self.theme_manager.get_spacing("sm"))

        pw_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.pw_tree.yview)
        pw_scrollbar.grid(row=0, column=1, sticky="ns")
        self.pw_tree.configure(yscrollcommand=pw_scrollbar.set)

        # Action buttons
        button_frame = create_styled_frame(pw_frame, self.theme_manager, card_style=False)
        button_frame.grid(row=2, column=0, sticky="ew", padx=self.theme_manager.get_spacing("sm"),
                         pady=(0, self.theme_manager.get_spacing("sm")))

        self.add_dict_btn = create_styled_button(
            button_frame,
            self.theme_manager,
            variant="primary",
            text="Add to Dictionary",
            command=self._add_to_dictionary,
            state=tk.DISABLED
        )
        self.add_dict_btn.pack(side=tk.LEFT, padx=(self.theme_manager.get_spacing("sm"), 0))

        refresh_btn = create_styled_button(
            button_frame,
            self.theme_manager,
            variant="secondary",
            text="Refresh",
            command=self._refresh_data
        )
        refresh_btn.pack(side=tk.LEFT, padx=self.theme_manager.get_spacing("xs"))

        # Status label
        self.pw_status = create_styled_label(
            button_frame,
            self.theme_manager,
            variant="hint",
            text="Select a word to add to dictionary"
        )
        self.pw_status.pack(side=tk.LEFT, padx=self.theme_manager.get_spacing("sm"))

        # Bind selection event
        self.pw_tree.bind("<<TreeviewSelect>>", self._on_pw_select)

    def _create_stat_card(self, parent, title: str, value: str, col: int, color_variant: str):
        """Create a statistics card."""
        card_frame = tk.Frame(
            parent,
            bg=self.theme_manager.get_color("bg_card"),
            highlightbackground=self.theme_manager.get_color("border"),
            highlightthickness=1
        )
        card_frame.grid(row=0, column=col, sticky="ew", padx=self.theme_manager.get_spacing("xs"),
                       pady=self.theme_manager.get_spacing("xs"))

        # Title
        title_label = tk.Label(
            card_frame,
            text=title,
            fg=self.theme_manager.get_color("fg_hint"),
            bg=self.theme_manager.get_color("bg_card"),
            font=self.theme_manager.get_font("sm")
        )
        title_label.pack(anchor=tk.W, padx=self.theme_manager.get_spacing("sm"),
                        pady=(self.theme_manager.get_spacing("sm"), 0))

        # Value
        value_color = self.theme_manager.get_color(color_variant)
        value_label = tk.Label(
            card_frame,
            text=value,
            fg=value_color,
            bg=self.theme_manager.get_color("bg_card"),
            font=self.theme_manager.get_font("xl", bold=True)
        )
        value_label.pack(anchor=tk.W, padx=self.theme_manager.get_spacing("sm"),
                        pady=(self.theme_manager.get_spacing("xs"), self.theme_manager.get_spacing("sm")))

        return value_label

    def _refresh_data(self):
        """Refresh all data from the accuracy tracker."""
        # Get overall stats
        overall = self.accuracy_tracker.get_overall_accuracy(days=self.selected_days)

        # Update stat cards
        self.accuracy_card.configure(text=f"{overall['accuracy']:.1f}%")
        self.words_card.configure(text=str(overall['total_words']))
        self.corrections_card.configure(text=str(overall['total_corrections']))
        self.manual_card.configure(text=f"{overall['manual_edit_rate']:.1f}%")

        # Update trend chart
        self._update_trend_chart()

        # Update correction stats
        self._update_correction_stats()

        # Update problem words
        self._update_problem_words()

    def _update_trend_chart(self):
        """Update the accuracy trend chart."""
        self.trend_canvas.delete("all")

        data = self.accuracy_tracker.get_accuracy_over_time(days=self.selected_days)
        if not data:
            # Show no data message
            self.trend_canvas.create_text(
                200, 100,
                text="No data available for this time range",
                fill=self.theme_manager.get_color("fg_hint"),
                font=self.theme_manager.get_font("base")
            )
            return

        # Get canvas dimensions
        self.trend_canvas.update_idletasks()
        width = self.trend_canvas.winfo_width()
        height = self.trend_canvas.winfo_height()

        if width < 100 or height < 50:
            # Schedule update for later
            self.trend_canvas.after(100, self._update_trend_chart)
            return

        # Chart margins
        margin_left = 50
        margin_right = 20
        margin_top = 20
        margin_bottom = 40

        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        # Find min/max accuracy
        accuracies = [d["accuracy"] for d in data]
        if not accuracies:
            return

        min_acc = max(0, min(accuracies) - 5)
        max_acc = min(100, max(accuracies) + 5)

        # Draw grid lines
        for i in range(5):
            y = margin_top + (chart_height * i / 4)
            value = max_acc - (max_acc - min_acc) * i / 4

            # Grid line
            self.trend_canvas.create_line(
                margin_left, y, width - margin_right, y,
                fill=self.theme_manager.get_color("border"),
                dash=(2, 2)
            )

            # Y-axis label
            self.trend_canvas.create_text(
                margin_left - 10, y,
                text=f"{value:.0f}%",
                fill=self.theme_manager.get_color("fg_hint"),
                font=self.theme_manager.get_font("sm"),
                anchor=tk.E
            )

        # Draw data line
        if len(data) > 1:
            points = []
            for i, d in enumerate(data):
                x = margin_left + (chart_width * i / (len(data) - 1))
                y = margin_top + chart_height - (chart_height * (d["accuracy"] - min_acc) / (max_acc - min_acc))
                points.append((x, y))

            # Draw line
            for i in range(len(points) - 1):
                self.trend_canvas.create_line(
                    points[i][0], points[i][1],
                    points[i + 1][0], points[i + 1][1],
                    fill=self.theme_manager.get_color("primary"),
                    width=2
                )

            # Draw points
            for x, y in points:
                self.trend_canvas.create_oval(
                    x - 4, y - 4, x + 4, y + 4,
                    fill=self.theme_manager.get_color("primary"),
                    outline=self.theme_manager.get_color("bg_card"),
                    width=2
                )

        # Draw X-axis labels (dates)
        if len(data) <= 10:
            # Show all dates
            for i, d in enumerate(data):
                x = margin_left + (chart_width * i / max(1, len(data) - 1))
                date_str = datetime.fromisoformat(d["date"]).strftime("%m/%d")
                self.trend_canvas.create_text(
                    x, height - margin_bottom + 15,
                    text=date_str,
                    fill=self.theme_manager.get_color("fg_hint"),
                    font=self.theme_manager.get_font("sm"),
                    anchor=tk.CENTER
                )
        else:
            # Show first, middle, last
            positions = [0, len(data) // 2, len(data) - 1]
            for i in positions:
                x = margin_left + (chart_width * i / (len(data) - 1))
                date_str = datetime.fromisoformat(data[i]["date"]).strftime("%m/%d")
                self.trend_canvas.create_text(
                    x, height - margin_bottom + 15,
                    text=date_str,
                    fill=self.theme_manager.get_color("fg_hint"),
                    font=self.theme_manager.get_font("sm"),
                    anchor=tk.CENTER
                )

    def _update_correction_stats(self):
        """Update the correction statistics list."""
        self.correction_listbox.delete(0, tk.END)

        stats = self.accuracy_tracker.get_correction_statistics(days=self.selected_days)

        # By type
        by_type = stats.get("by_type", {})
        if by_type:
            self.correction_listbox.insert(tk.END, "--- Corrections by Type ---")
            for corr_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
                self.correction_listbox.insert(tk.END, f"  {corr_type}: {count}")

        # By processor
        by_processor = stats.get("by_processor", {})
        if by_processor:
            self.correction_listbox.insert(tk.END, "")
            self.correction_listbox.insert(tk.END, "--- Corrections by Processor ---")
            for processor, count in sorted(by_processor.items(), key=lambda x: x[1], reverse=True):
                self.correction_listbox.insert(tk.END, f"  {processor}: {count}")

        if not by_type and not by_processor:
            self.correction_listbox.insert(tk.END, "No correction data available")

    def _update_problem_words(self):
        """Update the problem words list."""
        # Clear existing items
        for item in self.pw_tree.get_children():
            self.pw_tree.delete(item)

        # Get problem words
        self.problem_words = self.accuracy_tracker.get_problem_words(limit=100)

        # Check which are in dictionary
        for pw in self.problem_words:
            # Check if word is already in dictionary
            pw.in_dictionary = self.dictionary._is_in_dictionary(pw.word)

            # Determine status tag
            tag = "in_dict" if pw.in_dictionary else "not_in_dict"

            # Format suggested corrections
            suggestions = ", ".join(pw.suggested_corrections[:3]) if pw.suggested_corrections else "None"

            self.pw_tree.insert("", tk.END, values=(
                pw.word,
                f"{pw.correction_frequency:.1%}",
                f"{pw.correction_count}/{pw.occurrence_count}",
                "In Dictionary" if pw.in_dictionary else suggestions
            ), tags=(tag,))

    def _on_range_change(self, days: int):
        """Handle time range change."""
        self.selected_days = days
        self._refresh_data()

    def _on_pw_select(self, event=None):
        """Handle problem word selection."""
        selection = self.pw_tree.selection()
        if selection:
            item = selection[0]
            index = self.pw_tree.index(item)
            if 0 <= index < len(self.problem_words):
                pw = self.problem_words[index]
                if not pw.in_dictionary:
                    self.add_dict_btn.configure(state=tk.NORMAL)
                    self.pw_status.configure(text=f"Selected: '{pw.word}'")
                else:
                    self.add_dict_btn.configure(state=tk.DISABLED)
                    self.pw_status.configure(text=f"'{pw.word}' is already in dictionary")
        else:
            self.add_dict_btn.configure(state=tk.DISABLED)
            self.pw_status.configure(text="Select a word to add to dictionary")

    def _add_to_dictionary(self):
        """Add selected word to dictionary."""
        selection = self.pw_tree.selection()
        if not selection:
            return

        item = selection[0]
        index = self.pw_tree.index(item)
        if 0 <= index < len(self.problem_words):
            pw = self.problem_words[index]

            # Use first suggested correction as the correct spelling
            if pw.suggested_corrections:
                correct = pw.suggested_corrections[0]

                # Add to dictionary
                self.dictionary.add_entry(pw.word, correct)

                # Update UI
                pw.in_dictionary = True
                self._update_problem_words()
                self.add_dict_btn.configure(state=tk.DISABLED)
                self.pw_status.configure(
                    text=f"Added '{pw.word}' -> '{correct}' to dictionary!",
                    foreground=self.theme_manager.get_color("success")
                )

                # Reload dictionary in text processor
                from .text_processor import TextProcessor
                # Note: The actual text processor instance will need to be reloaded
                # This is typically done by the main application

    def _center_window(self):
        """Center the window on screen."""
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - self.window.winfo_width()) // 2
        y = (screen_height - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")

    def _on_window_close(self):
        """Handle window close."""
        if self.on_close:
            self.on_close()
        self.window.destroy()
        self.window = None

    def close(self):
        """Close the window if open."""
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None
