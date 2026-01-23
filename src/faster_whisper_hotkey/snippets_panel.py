"""
Snippets management panel GUI using tkinter.

This module provides a graphical interface for managing text snippets
that can be triggered by voice commands. Includes dialogs for creating
and editing snippets, with variable substitution support.

Classes
-------
EditSnippetDialog
    Dialog for creating/editing a single snippet.

SnippetsPanel
    Main snippets management panel with category organization.

Functions
---------
show_snippets_panel
    Convenience function to show the snippets panel.

Notes
-----
Integrates with snippets_manager for persistence and expansion.
"""

import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Callable, Dict, List, Optional
from datetime import datetime

from .snippets_manager import (
    Snippet,
    SnippetCategory,
    SnippetsManager,
    get_snippets_manager,
)

logger = logging.getLogger(__name__)


class EditSnippetDialog:
    """Dialog for creating or editing a snippet."""

    def __init__(
        self,
        parent,
        snippet_id: str = None,
        name: str = "",
        trigger: str = "",
        content: str = "",
        description: str = "",
        category: str = "general",
        enabled: bool = True,
        all_triggers: List[str] = None,
    ):
        self.parent = parent
        self.snippet_id = snippet_id
        self.all_triggers = all_triggers or []
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Snippet" if snippet_id else "New Snippet")
        self.dialog.geometry("600x550")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 550) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.categories = self._load_categories()
        self._build_ui(name, trigger, content, description, category, enabled)

    def _load_categories(self) -> List[SnippetCategory]:
        """Load available categories."""
        manager = get_snippets_manager()
        return manager.get_categories()

    def _build_ui(self, name, trigger, content, description, category, enabled):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ID (read-only, only for editing)
        if self.snippet_id:
            ttk.Label(main_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
            ttk.Label(
                main_frame,
                text=self.snippet_id,
                font=("Consolas", 10)
            ).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        row_offset = 1 if self.snippet_id else 0

        # Name
        ttk.Label(main_frame, text="Name:").grid(row=row_offset, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=name)
        ttk.Entry(
            main_frame,
            textvariable=self.name_var,
            width=50
        ).grid(row=row_offset, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # Trigger
        ttk.Label(main_frame, text="Trigger:").grid(row=row_offset + 1, column=0, sticky=tk.W, pady=5)
        trigger_frame = ttk.Frame(main_frame)
        trigger_frame.grid(row=row_offset + 1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        self.trigger_var = tk.StringVar(value=trigger)
        self.trigger_entry = ttk.Entry(
            trigger_frame,
            textvariable=self.trigger_var,
            width=40
        )
        self.trigger_entry.pack(side=tk.LEFT)

        # Test button
        ttk.Button(
            trigger_frame,
            text="Test",
            command=self._test_trigger,
            width=6
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Content
        ttk.Label(main_frame, text="Content:").grid(row=row_offset + 2, column=0, sticky=tk.NW, pady=5)
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=row_offset + 2, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        self.content_text = scrolledtext.ScrolledText(
            content_frame,
            width=50,
            height=8,
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.content_text.pack(fill=tk.BOTH, expand=True)
        self.content_text.insert("1.0", content)

        # Variable helper
        var_frame = ttk.Frame(content_frame)
        var_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(
            var_frame,
            text="Use {variable_name} for placeholders",
            font=("", 8),
            foreground="gray"
        ).pack(side=tk.LEFT)

        # Description
        ttk.Label(main_frame, text="Description:").grid(row=row_offset + 3, column=0, sticky=tk.W, pady=5)
        self.desc_var = tk.StringVar(value=description)
        ttk.Entry(
            main_frame,
            textvariable=self.desc_var,
            width=50
        ).grid(row=row_offset + 3, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # Category
        ttk.Label(main_frame, text="Category:").grid(row=row_offset + 4, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar(value=category)
        category_combo = ttk.Combobox(
            main_frame,
            textvariable=self.category_var,
            values=[cat.name for cat in self.categories],
            state="readonly",
            width=20
        )
        category_combo.grid(row=row_offset + 4, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        # Enabled checkbox
        self.enabled_var = tk.BooleanVar(value=enabled)
        ttk.Checkbutton(
            main_frame,
            text="Enable this snippet",
            variable=self.enabled_var,
        ).grid(row=row_offset + 5, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Warning label
        self.warning_label = ttk.Label(
            main_frame,
            text="",
            foreground="red",
            wraplength=500
        )
        self.warning_label.grid(row=row_offset + 6, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=row_offset + 7, column=0, columnspan=2, sticky=tk.EW, pady=10
        )

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row_offset + 8, column=0, columnspan=2, sticky=tk.E)

        ttk.Button(
            button_frame,
            text="Save",
            command=self._save
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel
        ).pack(side=tk.RIGHT)

        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)

        main_frame.columnconfigure(1, weight=1)

        # Check for conflicts
        self.trigger_var.trace_add("write", self._check_trigger)

    def _test_trigger(self):
        """Test the trigger phrase."""
        trigger = self.trigger_var.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        if not trigger:
            messagebox.showinfo("Test Trigger", "Please enter a trigger phrase first.")
            return

        if not content:
            messagebox.showinfo("Test Trigger", "Please enter content first.")
            return

        messagebox.showinfo(
            "Test Trigger",
            f"When you say '{trigger}',\n\nit will expand to:\n\n{content}"
        )

    def _check_trigger(self, *args):
        """Check if trigger already exists."""
        trigger = self.trigger_var.get().strip().lower()
        self.warning_label.config(text="")

        if not trigger or not self.snippet_id:
            return

        # Check against other triggers (exclude current)
        for existing_trigger in self.all_triggers:
            if existing_trigger.lower() == trigger and existing_trigger != self.all_triggers.get(self.snippet_id, ""):
                self.warning_label.config(
                    text=f"⚠ Warning: This trigger is already in use"
                )
                break

    def _save(self):
        """Save and close."""
        name = self.name_var.get().strip()
        trigger = self.trigger_var.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()
        description = self.desc_var.get().strip()

        if not name:
            messagebox.showerror("Validation Error", "Please enter a name for the snippet.")
            return

        if not trigger:
            messagebox.showerror("Validation Error", "Please enter a trigger phrase.")
            return

        if not content:
            messagebox.showerror("Validation Error", "Please enter the snippet content.")
            return

        # Check for trigger conflict
        trigger_lower = trigger.lower()
        for existing_trigger in self.all_triggers:
            if existing_trigger.lower() == trigger_lower:
                if not self.snippet_id or existing_trigger != self.all_triggers.get(self.snippet_id, ""):
                    if not messagebox.askyesno(
                        "Duplicate Trigger",
                        f"The trigger '{trigger}' is already in use. Use it anyway?"
                    ):
                        return

        self.result = {
            "name": name,
            "trigger": trigger,
            "content": content,
            "description": description,
            "category": self.category_var.get(),
            "enabled": self.enabled_var.get(),
        }
        self.dialog.destroy()

    def _cancel(self):
        """Cancel and close."""
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[Dict]:
        """Show dialog and return result or None if cancelled."""
        self.dialog.wait_window()
        return self.result


class SnippetsPanel:
    """Main snippets management panel."""

    def __init__(self, parent=None, on_change: Callable = None):
        self.parent = parent or tk.Tk()
        self.on_change = on_change
        self.manager = get_snippets_manager()
        self.window = None
        self.tree = None
        self.current_category = "all"

    def show(self):
        """Show the snippets panel window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Text Snippets Manager")
        self.window.geometry("800x550")
        self.window.minsize(700, 450)

        # Configure grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        self._build_ui()
        self._refresh_list()

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _build_ui(self):
        """Build the UI components."""
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(
            header_frame,
            text="Voice-Activated Text Snippets",
            font=("", 14, "bold")
        ).pack(side=tk.LEFT)

        # Search box
        search_frame = ttk.Frame(header_frame)
        search_frame.pack(side=tk.RIGHT)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=20
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Main content with paned window
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky="nsew")

        # Left side - category list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(
            left_frame,
            text="Categories",
            font=("", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        # Category listbox
        self.category_listbox = tk.Listbox(
            left_frame,
            font=("", 10),
            selectmode=tk.SINGLE,
            exportselection=False
        )
        self.category_listbox.pack(fill=tk.BOTH, expand=True)
        self.category_listbox.bind("<<ListboxSelect>>", self._on_category_select)

        # Right side - snippets list
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)

        # Toolbar
        toolbar = ttk.Frame(right_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            toolbar,
            text="New...",
            command=self._new_snippet,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Edit...",
            command=self._edit_snippet,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Delete",
            command=self._delete_snippet,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        ttk.Button(
            toolbar,
            text="Enable All",
            command=self._enable_all,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Disable All",
            command=self._disable_all,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        ttk.Button(
            toolbar,
            text="Import...",
            command=self._import_config,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Export...",
            command=self._export_config,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Stats",
            command=self._show_stats,
            width=8
        ).pack(side=tk.LEFT)

        # Treeview for snippets
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "trigger", "category", "status")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode=tk.BROWSE
        )

        self.tree.heading("name", text="Name")
        self.tree.heading("trigger", text="Trigger")
        self.tree.heading("category", text="Category")
        self.tree.heading("status", text="Status")

        self.tree.column("name", width=150)
        self.tree.column("trigger", width=150)
        self.tree.column("category", width=100)
        self.tree.column("status", width=80)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Status bar
        self.status_label = ttk.Label(
            right_frame,
            text="Double-click a snippet to edit it",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, pady=(5, 0))

        # Bind double-click
        self.tree.bind("<Double-1>", lambda e: self._edit_snippet())
        self.tree.bind("<Return>", lambda e: self._edit_snippet())

    def _refresh_list(self):
        """Refresh the snippets list."""
        if not self.tree or not self.category_listbox:
            return

        # Populate categories
        self.category_listbox.delete(0, tk.END)
        self.category_listbox.insert(tk.END, "All Snippets")

        for category in self.manager.get_categories():
            self.category_listbox.insert(tk.END, category.name)

        # Select first category
        self.category_listbox.selection_set(0)
        self._on_category_select(None)

    def _on_category_select(self, event):
        """Handle category selection change."""
        selection = self.category_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx == 0:
            # All snippets
            snippets = self.manager.get_all()
        else:
            # Specific category
            categories = list(self.manager.get_categories())
            if idx - 1 >= len(categories):
                return
            category = categories[idx - 1]
            snippets = self.manager.get_by_category(category.id)

        self._populate_tree(snippets)

    def _populate_tree(self, snippets: List[Snippet]):
        """Populate tree with snippets."""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        for snippet in snippets:
            status = "✓ Enabled" if snippet.enabled else "✗ Disabled"

            # Get category name
            category_obj = next(
                (c for c in self.manager.get_categories() if c.id == snippet.category),
                None
            )
            category_name = category_obj.name if category_obj else snippet.category

            self.tree.insert("", tk.END, iid=snippet.id, values=(
                snippet.name,
                snippet.trigger,
                category_name,
                status
            ))

    def _on_search(self, *args):
        """Handle search input."""
        query = self.search_var.get().strip()

        if not query:
            # Show all in current category
            self._on_category_select(None)
            return

        # Search across all snippets
        results = self.manager.search_snippets(query)
        self._populate_tree(results)

    def _new_snippet(self):
        """Create a new snippet."""
        # Get all existing triggers
        all_triggers = {s.id: s.trigger for s in self.manager.get_all()}

        dialog = EditSnippetDialog(
            self.window,
            all_triggers=all_triggers,
        )

        result = dialog.show()
        if result:
            # Generate ID from name
            import re
            base_id = re.sub(r'[^a-z0-9]+', '-', result["name"].lower()).strip('-')
            snippet_id = base_id
            counter = 1
            while self.manager.get(snippet_id):
                snippet_id = f"{base_id}-{counter}"
                counter += 1

            snippet = Snippet(
                id=snippet_id,
                name=result["name"],
                trigger=result["trigger"],
                content=result["content"],
                description=result["description"],
                category=result["category"],
                enabled=result["enabled"],
            )

            success, error = self.manager.add_snippet(snippet)
            if success:
                self._on_category_select(None)
                if self.on_change:
                    self.on_change()
                self.status_label.config(text=f"Snippet '{snippet.name}' created")
            else:
                messagebox.showerror("Error", error)

    def _edit_snippet(self):
        """Edit the selected snippet."""
        selection = self.tree.selection()
        if not selection:
            self.status_label.config(text="No snippet selected")
            return

        snippet_id = selection[0]
        snippet = self.manager.get(snippet_id)
        if not snippet:
            return

        # Get all existing triggers (for conflict checking)
        all_triggers = {s.id: s.trigger for s in self.manager.get_all() if s.id != snippet_id}

        dialog = EditSnippetDialog(
            self.window,
            snippet_id=snippet.id,
            name=snippet.name,
            trigger=snippet.trigger,
            content=snippet.content,
            description=snippet.description,
            category=snippet.category,
            enabled=snippet.enabled,
            all_triggers=list(all_triggers.values()),
        )

        result = dialog.show()
        if result:
            success, error = self.manager.update_snippet(
                snippet_id,
                **result
            )

            if success:
                self._on_category_select(None)
                if self.on_change:
                    self.on_change()
                self.status_label.config(text=f"Snippet '{snippet.name}' updated")
            else:
                messagebox.showerror("Error", error)

    def _delete_snippet(self):
        """Delete the selected snippet."""
        selection = self.tree.selection()
        if not selection:
            self.status_label.config(text="No snippet selected")
            return

        snippet_id = selection[0]
        snippet = self.manager.get(snippet_id)
        if not snippet:
            return

        if messagebox.askyesno(
            "Delete Snippet",
            f"Are you sure you want to delete '{snippet.name}'?"
        ):
            if self.manager.remove_snippet(snippet_id):
                self._on_category_select(None)
                if self.on_change:
                    self.on_change()
                self.status_label.config(text=f"Snippet '{snippet.name}' deleted")

    def _enable_all(self):
        """Enable all snippets in current view."""
        for item_id in self.tree.get_children():
            snippet = self.manager.get(item_id)
            if snippet:
                self.manager.update_snippet(item_id, enabled=True)

        self._on_category_select(None)
        if self.on_change:
            self.on_change()
        self.status_label.config(text="All snippets enabled")

    def _disable_all(self):
        """Disable all snippets in current view."""
        for item_id in self.tree.get_children():
            snippet = self.manager.get(item_id)
            if snippet:
                self.manager.update_snippet(item_id, enabled=False)

        self._on_category_select(None)
        if self.on_change:
            self.on_change()
        self.status_label.config(text="All snippets disabled")

    def _import_config(self):
        """Import snippets configuration."""
        path = filedialog.askopenfilename(
            title="Import Snippets Configuration",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        # Ask whether to merge or replace
        response = messagebox.askyesnocancel(
            "Import Options",
            "Do you want to merge with existing snippets?\n\n"
            "Yes = Merge with existing snippets\n"
            "No = Replace all snippets\n"
            "Cancel = Don't import"
        )

        if response is None:  # Cancel
            return

        merge = response
        success, message = self.manager.import_config(path, merge=merge)

        if success:
            self._refresh_list()
            if self.on_change:
                self.on_change()
            messagebox.showinfo("Import Successful", message)
        else:
            messagebox.showerror("Import Failed", message)

    def _export_config(self):
        """Export snippets configuration."""
        path = filedialog.asksaveasfilename(
            title="Export Snippets Configuration",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        success, message = self.manager.export_config(path)

        if success:
            messagebox.showinfo("Export Successful", message)
        else:
            messagebox.showerror("Export Failed", message)

    def _show_stats(self):
        """Show usage statistics."""
        stats = self.manager.get_usage_stats()

        stats_window = tk.Toplevel(self.window)
        stats_window.title("Snippet Statistics")
        stats_window.geometry("400x350")
        stats_window.transient(self.window)
        stats_window.grab_set()

        frame = ttk.Frame(stats_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="Snippet Statistics", font=("", 12, "bold")).grid(
            row=row, column=0, columnspan=2, pady=(0, 15)
        )
        row += 1

        ttk.Label(frame, text=f"Total snippets:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Label(frame, text=f"{stats['total_snippets']}").grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        ttk.Label(frame, text=f"Enabled snippets:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Label(frame, text=f"{stats['enabled_snippets']}").grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        ttk.Label(frame, text=f"Total expansions:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Label(frame, text=f"{stats['total_usage']}").grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=tk.EW, pady=15
        )
        row += 1

        if stats['most_used']:
            ttk.Label(frame, text="Most Used:", font=("", 10, "bold")).grid(
                row=row, column=0, columnspan=2, sticky=tk.W
            )
            row += 1
            for item in stats['most_used'][:5]:
                ttk.Label(frame, text=f"  • {item['name']}:").grid(
                    row=row, column=0, sticky=tk.W, pady=2
                )
                ttk.Label(frame, text=f"{item['count']} times").grid(
                    row=row, column=1, sticky=tk.W, pady=2
                )
                row += 1

        # Close button
        ttk.Button(
            frame,
            text="Close",
            command=stats_window.destroy
        ).grid(row=row, column=0, columnspan=2, pady=(15, 0))

        # Center on parent
        stats_window.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 400) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 350) // 2
        stats_window.geometry(f"+{x}+{y}")

    def _on_window_close(self):
        """Handle window close."""
        if self.window:
            self.window.destroy()
            self.window = None

    def close(self):
        """Close the window if open."""
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None


def show_snippets_panel(parent=None, on_change: Callable = None) -> SnippetsPanel:
    """Show the snippets panel.

    Args:
        parent: Parent window
        on_change: Callback when snippets are changed

    Returns:
        The SnippetsPanel instance
    """
    panel = SnippetsPanel(parent, on_change)
    panel.show()
    return panel
