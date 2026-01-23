"""
Shortcuts management panel GUI using tkinter.

This module provides a graphical interface for managing keyboard shortcuts.
It includes dialogs for capturing and editing shortcuts, and a main panel
for organizing shortcuts by groups with conflict detection.

Classes
-------
HotkeyCaptureDialog
    Dialog for capturing a new hotkey combination.

EditShortcutDialog
    Dialog for editing a single shortcut with conflict detection.

ShortcutsPanel
    Main shortcuts management panel with group organization.

Functions
---------
show_shortcuts_panel
    Convenience function to show the shortcuts panel.

Notes
-----
Integrates with shortcuts_manager for persistence and conflict detection.
"""

import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Dict, List, Optional, Tuple

from pynput import keyboard

from .shortcuts_manager import (
    GROUP_NAMES,
    ShortcutsManager,
    get_shortcuts_manager,
)
from .hotkey_dialog import HotkeyDialog

logger = logging.getLogger(__name__)


class HotkeyCaptureDialog:
    """Dialog for capturing a new hotkey combination."""

    def __init__(self, parent, current_hotkey: str = "", exclude_ids: List[str] = None):
        self.parent = parent
        self.result_hotkey = None
        self.current_keys = set()
        self.captured_combo = None
        self.listener = None
        self.exclude_ids = exclude_ids or []

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Capture Hotkey")
        self.dialog.geometry("450x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 250) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self._build_ui(current_hotkey)

    def _build_ui(self, current_hotkey: str):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Instruction
        ttk.Label(
            main_frame,
            text="Press the key combination you want to use",
            font=("", 11)
        ).pack(anchor=tk.W, pady=(0, 10))

        # Current hotkey display
        if current_hotkey:
            ttk.Label(main_frame, text="Current:").pack(anchor=tk.W)
            ttk.Label(
                main_frame,
                text=current_hotkey.upper(),
                font=("Consolas", 12, "bold"),
                foreground="gray"
            ).pack(anchor=tk.W, pady=(0, 15))

        # Capture display
        ttk.Label(main_frame, text="New Hotkey:").pack(anchor=tk.W)

        self.hotkey_display = ttk.Label(
            main_frame,
            text="Press keys now...",
            font=("Consolas", 14),
            foreground="blue"
        )
        self.hotkey_display.pack(anchor=tk.W, pady=(0, 20))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Clear",
            command=self._clear
        ).pack(side=tk.LEFT)

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

        # Start capturing immediately
        self._start_capture()

    def _start_capture(self):
        """Start capturing keyboard input."""
        self.captured_combo = None
        self.current_keys = set()

        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.listener.start()

    def _on_key_press(self, key):
        """Handle key press during capture."""
        self.current_keys.add(key)
        self._update_display()

    def _on_key_release(self, key):
        """Handle key release - finalize capture when non-modifier released."""
        if key in HotkeyDialog.MODIFIER_KEYS and self.current_keys:
            # Still have modifiers held, don't finalize yet
            pass
        elif self.current_keys:
            # Capture complete when all keys released
            self.captured_combo = self._keys_to_string(self.current_keys)
            self._update_display(final=True)

        if key in self.current_keys:
            self.current_keys.discard(key)
            if not self.captured_combo and not self.current_keys:
                self._update_display()

    def _update_display(self, final: bool = False):
        """Update the hotkey display with current keys."""
        if self.captured_combo:
            self.hotkey_display.config(
                text=self.captured_combo.upper(),
                foreground="green" if final else "blue"
            )
        elif self.current_keys:
            display = self._keys_to_string(self.current_keys)
            self.hotkey_display.config(
                text=display.upper(),
                foreground="blue"
            )
        else:
            self.hotkey_display.config(
                text="Press keys now...",
                foreground="blue"
            )

    def _keys_to_string(self, keys: set) -> str:
        """Convert a set of keys to a string representation."""
        modifiers = []
        main_key = None

        for key in keys:
            if key in HotkeyDialog.MODIFIER_KEYS:
                name = HotkeyDialog.KEY_NAMES.get(key, str(key))
                if name not in modifiers:
                    modifiers.append(name)
            else:
                main_key = HotkeyDialog.KEY_NAMES.get(key, None)
                if main_key is None:
                    try:
                        main_key = key.char.upper() if key.char else str(key)
                    except AttributeError:
                        main_key = str(key).replace("Key.", "")

        # Sort modifiers for consistent ordering
        modifier_order = ["Ctrl", "Alt", "Shift", "Win"]
        modifiers.sort(key=lambda m: modifier_order.index(m) if m in modifier_order else 99)

        parts = modifiers + ([main_key] if main_key else [])
        return "+".join(parts).lower() if parts else ""

    def _clear(self):
        """Clear the captured hotkey."""
        self.captured_combo = ""
        self.hotkey_display.config(text="(No hotkey)", foreground="gray")

    def _save(self):
        """Save the hotkey and close."""
        self.result_hotkey = self.captured_combo or ""
        self._cleanup()
        self.dialog.destroy()

    def _cancel(self):
        """Cancel and close."""
        self.result_hotkey = None
        self._cleanup()
        self.dialog.destroy()

    def _cleanup(self):
        """Clean up resources."""
        if self.listener:
            self.listener.stop()
            self.listener = None

    def show(self) -> Optional[str]:
        """Show dialog and return hotkey or None if cancelled."""
        self.dialog.wait_window()
        return self.result_hotkey


class EditShortcutDialog:
    """Dialog for editing a single shortcut."""

    def __init__(
        self,
        parent,
        shortcut_id: str,
        name: str,
        hotkey: str,
        description: str,
        enabled: bool,
        all_shortcuts: Dict[str, Dict],
    ):
        self.parent = parent
        self.shortcut_id = shortcut_id
        self.result = None
        self.conflicting_shortcut_id = None
        self.conflicting_shortcut_name = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Shortcut")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.all_shortcuts = all_shortcuts
        self._build_ui(name, hotkey, description, enabled)

    def _build_ui(self, name: str, hotkey: str, description: str, enabled: bool):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ID (read-only)
        ttk.Label(main_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(
            main_frame,
            text=self.shortcut_id,
            font=("Consolas", 10)
        ).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        # Name
        ttk.Label(main_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=name)
        ttk.Entry(
            main_frame,
            textvariable=self.name_var,
            width=30
        ).grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # Description
        ttk.Label(main_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.desc_var = tk.StringVar(value=description)
        ttk.Entry(
            main_frame,
            textvariable=self.desc_var,
            width=30
        ).grid(row=2, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        # Hotkey
        ttk.Label(main_frame, text="Hotkey:").grid(row=3, column=0, sticky=tk.W, pady=5)

        hotkey_frame = ttk.Frame(main_frame)
        hotkey_frame.grid(row=3, column=1, sticky=tk.EW, padx=(10, 0), pady=5)

        self.hotkey_var = tk.StringVar(value=hotkey.upper() if hotkey else "Not Set")
        self.hotkey_label = ttk.Label(
            hotkey_frame,
            textvariable=self.hotkey_var,
            font=("Consolas", 11)
        )
        self.hotkey_label.pack(side=tk.LEFT)

        ttk.Button(
            hotkey_frame,
            text="Change...",
            command=self._change_hotkey,
            width=10
        ).pack(side=tk.LEFT, padx=(10, 0))

        ttk.Button(
            hotkey_frame,
            text="Clear",
            command=self._clear_hotkey,
            width=6
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Conflict warning frame
        conflict_frame = ttk.Frame(main_frame)
        conflict_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))

        self.conflict_label = ttk.Label(
            conflict_frame,
            text="",
            foreground="red",
            wraplength=350
        )
        self.conflict_label.pack(anchor=tk.W)

        # Resolve conflict button (hidden by default)
        self.resolve_button = ttk.Button(
            conflict_frame,
            text="Disable Conflicting Shortcut",
            command=self._resolve_conflict,
            width=22
        )
        self.resolve_button.pack(anchor=tk.W, pady=(5, 0))

        # Enabled checkbox
        self.enabled_var = tk.BooleanVar(value=enabled)
        ttk.Checkbutton(
            main_frame,
            text="Enable this shortcut",
            variable=self.enabled_var,
            command=self._check_conflict
        ).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=6, column=0, columnspan=2, sticky=tk.EW, pady=15
        )

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, sticky=tk.E)

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

        # Status label (for feedback messages)
        self.status_label = ttk.Label(
            main_frame,
            text="",
            foreground="green",
            wraplength=400
        )
        self.status_label.grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

    def _change_hotkey(self):
        """Open dialog to capture new hotkey."""
        current = self.name_var.get() or ""
        exclude = [sid for sid in self.all_shortcuts.keys() if sid != self.shortcut_id]

        dialog = HotkeyCaptureDialog(
            self.dialog,
            self.hotkey_var.get() if self.hotkey_var.get() != "Not Set" else "",
            exclude
        )
        new_hotkey = dialog.show()

        if new_hotkey is not None:
            self._temp_hotkey = new_hotkey
            self.hotkey_var.set(new_hotkey.upper() if new_hotkey else "Not Set")
            self._check_conflict()

    def _clear_hotkey(self):
        """Clear the hotkey."""
        self._temp_hotkey = ""
        self.hotkey_var.set("Not Set")
        self._clear_conflict_warning()

    def _clear_conflict_warning(self):
        """Clear the conflict warning and hide resolve button."""
        self.conflict_label.config(text="")
        self.resolve_button.pack_forget()
        self.conflicting_shortcut_id = None
        self.conflicting_shortcut_name = None

    def _check_conflict(self):
        """Check for hotkey conflicts and update warning."""
        hotkey = self.hotkey_var.get().lower()
        if hotkey == "not set" or hotkey == "":
            self._clear_conflict_warning()
            return

        # Check against other enabled shortcuts
        self.conflicting_shortcut_id = None
        self.conflicting_shortcut_name = None

        for sid, shortcut_info in self.all_shortcuts.items():
            if sid != self.shortcut_id:
                other_hotkey = shortcut_info.get("hotkey", "").lower()
                other_enabled = shortcut_info.get("enabled", True)
                if other_enabled and other_hotkey == hotkey:
                    self.conflicting_shortcut_id = sid
                    self.conflicting_shortcut_name = shortcut_info.get("name", sid)
                    break

        if self.conflicting_shortcut_id:
            self.conflict_label.config(
                text=f"⚠ Conflict: This hotkey is used by '{self.conflicting_shortcut_name}'"
            )
            self.resolve_button.config(
                text=f"Disable '{self.conflicting_shortcut_name}'"
            )
            self.resolve_button.pack(anchor=tk.W, pady=(5, 0))
        else:
            self._clear_conflict_warning()

    def _resolve_conflict(self):
        """Resolve the conflict by marking the conflicting shortcut to be disabled."""
        if not self.conflicting_shortcut_id:
            return

        # Store the ID of the shortcut to disable in the result
        self._shortcut_to_disable = self.conflicting_shortcut_id
        self._clear_conflict_warning()
        self.status_label.config(
            text=f"✓ '{self.conflicting_shortcut_name}' will be disabled",
            foreground="green"
        )

    def _save(self):
        """Save and close."""
        self._check_conflict()
        if self.conflict_label.cget("text"):
            if not messagebox.askyesno(
                "Conflict Detected",
                f"This hotkey conflicts with '{self.conflicting_shortcut_name}'. Save anyway?"
            ):
                return

        self.result = {
            "name": self.name_var.get(),
            "hotkey": self.hotkey_var.get().lower() if self.hotkey_var.get() != "Not Set" else "",
            "description": self.desc_var.get(),
            "enabled": self.enabled_var.get(),
            "disable_shortcut_id": getattr(self, "_shortcut_to_disable", None),
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


class ShortcutsPanel:
    """Main shortcuts management panel."""

    def __init__(self, parent=None, on_change: Callable = None):
        self.parent = parent or tk.Tk()
        self.on_change = on_change
        self.manager = get_shortcuts_manager()
        self.window = None
        self.tree = None
        self.conflicts_label = None

    def show(self):
        """Show the shortcuts panel window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Keyboard Shortcuts Manager")
        self.window.geometry("700x500")
        self.window.minsize(600, 400)

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
            text="Keyboard Shortcuts",
            font=("", 14, "bold")
        ).pack(side=tk.LEFT)

        # Conflict warning
        self.conflicts_label = ttk.Label(
            header_frame,
            text="",
            foreground="red",
            font=("", 10)
        )
        self.conflicts_label.pack(side=tk.RIGHT)

        # Main content with paned window
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky="nsew")

        # Left side - group list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(
            left_frame,
            text="Groups",
            font=("", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.group_listbox = tk.Listbox(
            left_frame,
            font=("", 10),
            selectmode=tk.SINGLE,
            exportselection=False
        )
        self.group_listbox.pack(fill=tk.BOTH, expand=True)
        self.group_listbox.bind("<<ListboxSelect>>", self._on_group_select)

        # Right side - shortcuts list
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)

        # Toolbar
        toolbar = ttk.Frame(right_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            toolbar,
            text="Edit...",
            command=self._edit_shortcut,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 5))

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
            text="Reset",
            command=self._reset_defaults,
            width=8
        ).pack(side=tk.LEFT)

        # Treeview for shortcuts
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "hotkey", "status")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode=tk.BROWSE
        )

        self.tree.heading("name", text="Name")
        self.tree.heading("hotkey", text="Hotkey")
        self.tree.heading("status", text="Status")

        self.tree.column("name", width=200)
        self.tree.column("hotkey", width=150)
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
            text="Double-click a shortcut to edit it",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, pady=(5, 0))

        # Bind double-click
        self.tree.bind("<Double-1>", lambda e: self._edit_shortcut())
        self.tree.bind("<Return>", lambda e: self._edit_shortcut())

    def _refresh_list(self):
        """Refresh the shortcuts list."""
        if not self.tree or not self.group_listbox:
            return

        # Populate groups
        self.group_listbox.delete(0, tk.END)
        for group_name in self.manager.get_group_names():
            display_name = GROUP_NAMES.get(group_name, group_name.title())
            self.group_listbox.insert(tk.END, display_name)

        # Select first group
        if self.group_listbox.size() > 0:
            self.group_listbox.selection_set(0)
            self._on_group_select(None)

        # Update conflicts display
        self._update_conflicts()

    def _on_group_select(self, event):
        """Handle group selection change."""
        selection = self.group_listbox.curselection()
        if not selection:
            return

        # Get group name from display name
        idx = selection[0]
        group_names = list(self.manager.get_group_names())
        if idx >= len(group_names):
            return

        group_name = group_names[idx]
        shortcuts = self.manager.get_group(group_name)

        # Clear and populate tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        for shortcut in shortcuts:
            hotkey_display = shortcut.hotkey.upper() if shortcut.hotkey else "Not Set"
            status = "✓ Enabled" if shortcut.enabled else "✗ Disabled"

            self.tree.insert("", tk.END, iid=shortcut.id, values=(
                shortcut.name,
                hotkey_display,
                status
            ))

    def _edit_shortcut(self):
        """Edit the selected shortcut."""
        selection = self.tree.selection()
        if not selection:
            self.status_label.config(text="No shortcut selected")
            return

        shortcut_id = selection[0]
        shortcut = self.manager.get(shortcut_id)
        if not shortcut:
            return

        # Get all current shortcuts for conflict checking (full info)
        all_shortcuts = {
            s.id: {
                "hotkey": s.hotkey,
                "name": s.name,
                "enabled": s.enabled,
            }
            for s in self.manager.get_all()
            if s.id != shortcut_id
        }

        dialog = EditShortcutDialog(
            self.window,
            shortcut.id,
            shortcut.name,
            shortcut.hotkey,
            shortcut.description,
            shortcut.enabled,
            all_shortcuts,
        )

        result = dialog.show()
        if result:
            # Update shortcut
            shortcut.name = result["name"]
            shortcut.hotkey = result["hotkey"]
            shortcut.description = result["description"]
            shortcut.enabled = result["enabled"]

            # Handle one-click conflict resolution
            disable_id = result.get("disable_shortcut_id")
            if disable_id:
                conflicting_shortcut = self.manager.get(disable_id)
                if conflicting_shortcut:
                    conflicting_shortcut.enabled = False

            # Save
            self.manager.save()

            # Refresh display
            self._on_group_select(None)
            self._update_conflicts()

            if self.on_change:
                self.on_change()

            status_msg = f"Shortcut '{shortcut.name}' updated"
            if disable_id:
                conflicting = self.manager.get(disable_id)
                if conflicting:
                    status_msg += f"; '{conflicting.name}' disabled"
            self.status_label.config(text=status_msg)

    def _enable_all(self):
        """Enable all shortcuts in current group."""
        selection = self.group_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        group_names = list(self.manager.get_group_names())
        if idx >= len(group_names):
            return

        group_name = group_names[idx]
        shortcuts = self.manager.get_group(group_name)

        for shortcut in shortcuts:
            self.manager.set_enabled(shortcut.id, True)

        self.manager.save()
        self._on_group_select(None)
        self._update_conflicts()

        if self.on_change:
            self.on_change()

        self.status_label.config(text="All shortcuts in group enabled")

    def _disable_all(self):
        """Disable all shortcuts in current group."""
        selection = self.group_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        group_names = list(self.manager.get_group_names())
        if idx >= len(group_names):
            return

        group_name = group_names[idx]
        shortcuts = self.manager.get_group(group_name)

        for shortcut in shortcuts:
            self.manager.set_enabled(shortcut.id, False)

        self.manager.save()
        self._on_group_select(None)
        self._update_conflicts()

        if self.on_change:
            self.on_change()

        self.status_label.config(text="All shortcuts in group disabled")

    def _update_conflicts(self):
        """Update the conflicts display."""
        conflicts = self.manager.detect_all_conflicts()
        if conflicts:
            count = len(conflicts)
            self.conflicts_label.config(text=f"⚠ {count} conflict(s) detected!")
        else:
            self.conflicts_label.config(text="")

    def _import_config(self):
        """Import shortcuts configuration."""
        path = filedialog.askopenfilename(
            title="Import Shortcuts Configuration",
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
            "Do you want to merge with existing shortcuts?\n\n"
            "Yes = Merge with existing shortcuts\n"
            "No = Replace all shortcuts\n"
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
        """Export shortcuts configuration."""
        path = filedialog.asksaveasfilename(
            title="Export Shortcuts Configuration",
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

    def _reset_defaults(self):
        """Reset all shortcuts to defaults."""
        if messagebox.askyesno(
            "Reset Shortcuts",
            "Are you sure you want to reset all shortcuts to default values?\n\n"
            "This will discard all your custom shortcuts."
        ):
            self.manager.reset_to_defaults()
            self._refresh_list()
            if self.on_change:
                self.on_change()
            self.status_label.config(text="Shortcuts reset to defaults")

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


def show_shortcuts_panel(parent=None, on_change: Callable = None) -> ShortcutsPanel:
    """Show the shortcuts panel.

    Args:
        parent: Parent window
        on_change: Callback when shortcuts are changed

    Returns:
        The ShortcutsPanel instance
    """
    panel = ShortcutsPanel(parent, on_change)
    panel.show()
    return panel
