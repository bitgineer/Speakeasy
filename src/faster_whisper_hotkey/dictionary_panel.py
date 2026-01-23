"""
Dictionary management panel using tkinter.

This module provides a GUI window for managing the personal dictionary.
Users can add, edit, remove, and view dictionary entries, as well as
export/import the dictionary.

Classes
-------
DictionaryPanel
    A window showing and managing dictionary entries.

Notes
-----
Changes made in this panel are immediately saved to disk.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import logging

from .dictionary import PersonalDictionary, DictionaryEntry, load_dictionary, DICTIONARY_FILE

logger = logging.getLogger(__name__)


class DictionaryPanel:
    """A window for managing the personal dictionary."""

    def __init__(self, on_close=None):
        self.on_close = on_close
        self.dictionary = load_dictionary()
        self.window = None
        self.entry_listbox = None
        self.search_var = None
        self.current_entries = []  # Currently displayed entries

    def show(self):
        """Show the dictionary panel window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel()
        self.window.title("Personal Dictionary")
        self.window.geometry("800x500")
        self.window.minsize(600, 400)

        # Configure grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        # Main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Header with stats
        self._create_header(main_frame)

        # Search bar
        self._create_search_bar(main_frame)

        # List frame with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Treeview for entries
        columns = ("incorrect", "correct", "usage", "context")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode=tk.BROWSE
        )

        self.tree.heading("incorrect", text="Incorrect")
        self.tree.heading("correct", text="Correct")
        self.tree.heading("usage", text="Used")
        self.tree.heading("context", text="Context")

        self.tree.column("incorrect", width=200)
        self.tree.column("correct", width=200)
        self.tree.column("usage", width=60)
        self.tree.column("context", width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)
        self.tree.bind("<Double-1>", self._on_double_click)

        # Detail panel
        self._create_detail_panel(main_frame)

        # Buttons frame
        self._create_buttons(main_frame)

        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text=f"Dictionary: {len(self.dictionary.entries)} entries",
            font=("", 9)
        )
        self.status_label.grid(row=5, column=0, sticky="w", pady=(5, 0))

        # Populate list
        self._refresh_list()

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _create_header(self, parent):
        """Create header with statistics."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(
            header_frame,
            text="Personal Dictionary",
            font=("", 14, "bold")
        ).pack(side=tk.LEFT)

        # Stats button
        ttk.Button(
            header_frame,
            text="Statistics",
            command=self._show_statistics
        ).pack(side=tk.RIGHT)

    def _create_search_bar(self, parent):
        """Create search bar."""
        search_frame = ttk.Frame(parent)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Clear button
        ttk.Button(
            search_frame,
            text="Clear",
            width=6,
            command=self._clear_search
        ).pack(side=tk.LEFT, padx=(5, 0))

    def _create_detail_panel(self, parent):
        """Create detail panel for selected entry."""
        detail_frame = ttk.LabelFrame(parent, text="Entry Details", padding=10)
        detail_frame.grid(row=3, column=0, sticky="ew", pady=(10, 10))

        # Grid layout for details
        for i in range(4):
            detail_frame.columnconfigure(i, weight=1)

        # Incorrect
        ttk.Label(detail_frame, text="Incorrect:").grid(row=0, column=0, sticky=tk.W)
        self.detail_incorrect = ttk.Label(detail_frame, text="", font=("Consolas", 10))
        self.detail_incorrect.grid(row=0, column=1, sticky=tk.W, padx=(5, 10))

        # Correct
        ttk.Label(detail_frame, text="Correct:").grid(row=0, column=2, sticky=tk.W)
        self.detail_correct = ttk.Label(detail_frame, text="", font=("Consolas", 10))
        self.detail_correct.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))

        # Case sensitive
        ttk.Label(detail_frame, text="Case Sensitive:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.detail_case_sensitive = ttk.Label(detail_frame, text="")
        self.detail_case_sensitive.grid(row=1, column=1, sticky=tk.W, padx=(5, 10), pady=(5, 0))

        # Context
        ttk.Label(detail_frame, text="Context:").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        self.detail_context = ttk.Label(detail_frame, text="")
        self.detail_context.grid(row=1, column=3, sticky=tk.W, padx=(5, 0), pady=(5, 0))

        # Pronunciation
        ttk.Label(detail_frame, text="Pronunciation:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.detail_pronunciation = ttk.Label(detail_frame, text="")
        self.detail_pronunciation.grid(row=1, column=1, sticky=tk.W, padx=(5, 10), pady=(5, 0))

        # Notes
        ttk.Label(detail_frame, text="Notes:").grid(row=2, column=2, sticky=tk.W, pady=(5, 0))
        self.detail_notes = ttk.Label(detail_frame, text="")
        self.detail_notes.grid(row=2, column=3, sticky=tk.W, padx=(5, 0), pady=(5, 0))

    def _create_buttons(self, parent):
        """Create action buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, sticky="ew")

        buttons = [
            ("Add New...", self._add_entry),
            ("Edit...", self._edit_entry),
            ("Remove", self._remove_entry),
            (None, None),  # Separator
            ("Export...", self._export_dictionary),
            ("Import...", self._import_dictionary),
            (None, None),  # Separator
            ("Clear All", self._clear_all),
        ]

        for i, (text, command) in enumerate(buttons):
            if text is None:
                ttk.Separator(button_frame, orient=tk.VERTICAL).grid(row=0, column=i, padx=5, sticky="ns")
            else:
                btn = ttk.Button(button_frame, text=text, command=command)
                btn.grid(row=0, column=i, padx=2)

    def _refresh_list(self, search_term: str = ""):
        """Refresh the entry list."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filter entries based on search
        search_lower = search_term.lower()
        filtered = []
        for entry in self.dictionary.entries:
            if not search_term:
                filtered.append(entry)
            else:
                # Search in incorrect, correct, context, notes
                if (
                    search_term in entry.incorrect.lower() or
                    search_term in entry.correct.lower() or
                    (entry.context and search_term in entry.context.lower()) or
                    (entry.notes and search_term in entry.notes.lower())
                ):
                    filtered.append(entry)

        self.current_entries = filtered

        # Populate tree
        for entry in filtered:
            values = (
                entry.incorrect,
                entry.correct,
                str(entry.usage_count),
                entry.context or ""
            )
            self.tree.insert("", tk.END, values=values)

        # Update status
        self.status_label.config(
            text=f"Dictionary: {len(self.dictionary.entries)} entries "
            f"({len(filtered)} shown)"
        )

    def _on_search(self, *args):
        """Handle search input."""
        self._refresh_list(self.search_var.get())

    def _clear_search(self):
        """Clear search."""
        self.search_var.set("")

    def _on_selection_change(self, event=None):
        """Handle selection change."""
        selection = self.tree.selection()
        if not selection:
            self._clear_details()
            return

        # Get the selected entry
        item = selection[0]
        idx = self.tree.index(item)
        if 0 <= idx < len(self.current_entries):
            entry = self.current_entries[idx]
            self._show_details(entry)

    def _on_double_click(self, event=None):
        """Handle double-click - edit entry."""
        self._edit_entry()

    def _show_details(self, entry: DictionaryEntry):
        """Show entry details."""
        self.detail_incorrect.config(text=entry.incorrect)
        self.detail_correct.config(text=entry.correct)
        self.detail_case_sensitive.config(text="Yes" if entry.case_sensitive else "No")
        self.detail_context.config(text=entry.context or "None")
        self.detail_pronunciation.config(text=entry.pronunciation_hint or "None")
        self.detail_notes.config(text=entry.notes or "None")

    def _clear_details(self):
        """Clear entry details."""
        self.detail_incorrect.config(text="")
        self.detail_correct.config(text="")
        self.detail_case_sensitive.config(text="")
        self.detail_context.config(text="")
        self.detail_pronunciation.config(text="")
        self.detail_notes.config(text="")

    def _add_entry(self):
        """Add a new entry."""
        self._show_entry_dialog()

    def _edit_entry(self):
        """Edit the selected entry."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an entry to edit.")
            return

        item = selection[0]
        idx = self.tree.index(item)
        if 0 <= idx < len(self.current_entries):
            entry = self.current_entries[idx]
            self._show_entry_dialog(entry)

    def _remove_entry(self):
        """Remove the selected entry."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an entry to remove.")
            return

        item = selection[0]
        idx = self.tree.index(item)
        if 0 <= idx < len(self.current_entries):
            entry = self.current_entries[idx]

            if messagebox.askyesno(
                "Confirm Remove",
                f"Remove entry '{entry.incorrect}' -> '{entry.correct}'?"
            ):
                self.dictionary.remove_entry(entry.incorrect, entry.correct)
                self._refresh_list(self.search_var.get())
                self._clear_details()

    def _show_entry_dialog(self, entry: DictionaryEntry = None):
        """Show dialog to add/edit an entry."""
        is_edit = entry is not None

        dialog = tk.Toplevel(self.window)
        dialog.title("Edit Entry" if is_edit else "Add Entry")
        dialog.geometry("500x350")
        dialog.transient(self.window)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # Incorrect
        ttk.Label(main_frame, text="Incorrect:").grid(row=row, column=0, sticky=tk.W, pady=5)
        incorrect_var = tk.StringVar(value=entry.incorrect if entry else "")
        ttk.Entry(main_frame, textvariable=incorrect_var, width=40).grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        # Correct
        ttk.Label(main_frame, text="Correct:").grid(row=row, column=0, sticky=tk.W, pady=5)
        correct_var = tk.StringVar(value=entry.correct if entry else "")
        ttk.Entry(main_frame, textvariable=correct_var, width=40).grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        # Case sensitive
        case_var = tk.BooleanVar(value=entry.case_sensitive if entry else False)
        ttk.Checkbutton(
            main_frame,
            text="Case sensitive",
            variable=case_var
        ).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        # Context
        ttk.Label(main_frame, text="Context:").grid(row=row, column=0, sticky=tk.W, pady=5)
        context_var = tk.StringVar(value=entry.context if entry else "")
        ttk.Entry(main_frame, textvariable=context_var, width=40).grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        # Pronunciation hint
        ttk.Label(main_frame, text="Pronunciation:").grid(row=row, column=0, sticky=tk.W, pady=5)
        pron_var = tk.StringVar(value=entry.pronunciation_hint if entry else "")
        ttk.Entry(main_frame, textvariable=pron_var, width=40).grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        # Notes
        ttk.Label(main_frame, text="Notes:").grid(row=row, column=0, sticky=tk.W, pady=5)
        notes_text = tk.Text(main_frame, width=40, height=4)
        notes_text.grid(row=row, column=1, sticky="ew", pady=5)
        if entry and entry.notes:
            notes_text.insert("1.0", entry.notes)
        row += 1

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(10, 0))

        def save():
            incorrect = incorrect_var.get().strip()
            correct = correct_var.get().strip()

            if not incorrect or not correct:
                messagebox.showerror("Error", "Both 'Incorrect' and 'Correct' fields are required.")
                return

            context = context_var.get().strip() or None
            pronunciation = pron_var.get().strip() or None
            notes = notes_text.get("1.0", tk.END).strip() or None

            if is_edit:
                # Remove old entry and add new one
                self.dictionary.remove_entry(entry.incorrect, entry.correct)
                self.dictionary.add_entry(
                    incorrect=incorrect,
                    correct=correct,
                    case_sensitive=case_var.get(),
                    pronunciation_hint=pronunciation,
                    context=context,
                    notes=notes
                )
            else:
                self.dictionary.add_entry(
                    incorrect=incorrect,
                    correct=correct,
                    case_sensitive=case_var.get(),
                    pronunciation_hint=pronunciation,
                    context=context,
                    notes=notes
                )

            self._refresh_list(self.search_var.get())
            dialog.destroy()

        def cancel():
            dialog.destroy()

        ttk.Button(button_frame, text="Save", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)

    def _export_dictionary(self):
        """Export dictionary to file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Dictionary"
        )

        if filepath:
            if self.dictionary.export_to_json(filepath):
                messagebox.showinfo("Export Successful", f"Dictionary exported to:\n{filepath}")
            else:
                messagebox.showerror("Export Failed", "Failed to export dictionary.")

    def _import_dictionary(self):
        """Import dictionary from file."""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Dictionary"
        )

        if filepath:
            # Ask merge or replace
            result = messagebox.askyesnocancel(
                "Import Dictionary",
                "Import options:\n\nYes - Merge with existing dictionary\nNo - Replace existing dictionary\nCancel - Cancel import"
            )

            if result is None:  # Cancel
                return

            merge = result  # Yes = merge, No = replace
            count = self.dictionary.import_from_json(filepath, merge=merge)

            if count > 0:
                self._refresh_list(self.search_var.get())
                messagebox.showinfo("Import Successful", f"Dictionary now has {count} entries.")
            else:
                messagebox.showerror("Import Failed", "Failed to import dictionary.")

    def _clear_all(self):
        """Clear all dictionary entries."""
        if messagebox.askyesno(
            "Confirm Clear",
            "Are you sure you want to clear all dictionary entries? This cannot be undone."
        ):
            self.dictionary.clear()
            self._refresh_list(self.search_var.get())
            self._clear_details()

    def _show_statistics(self):
        """Show dictionary statistics."""
        stats = self.dictionary.get_statistics()

        stats_text = f"""Dictionary Statistics

Total Entries: {stats['total_entries']}
Total Corrections Applied: {stats['total_corrections_applied']}
Case-Sensitive Entries: {stats['case_sensitive_entries']}
Entries with Pronunciation: {stats['entries_with_pronunciation']}
Unique Contexts: {stats['unique_contexts']}

Top Used Entries:
"""

        for i, entry in enumerate(stats['most_used_entries'][:5], 1):
            stats_text += f"{i}. {entry.incorrect} -> {entry.correct} ({entry.usage_count} uses)\n"

        messagebox.showinfo("Dictionary Statistics", stats_text)

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


def show_dictionary_panel(parent=None, on_close=None) -> DictionaryPanel:
    """
    Show the dictionary panel.

    Parameters
    ----------
    parent : tk.Tk or tk.Toplevel, optional
        Parent window.
    on_close : callable, optional
        Callback when panel is closed.

    Returns
    -------
    DictionaryPanel
        The dictionary panel instance.
    """
    panel = DictionaryPanel(on_close=on_close)
    panel.show()
    return panel
