"""
Application rules panel for managing per-application settings.

This module provides a modern GUI panel for creating, editing, and managing
per-application configuration rules.

Classes
-------
AppRulesPanel
    Main panel for managing app-specific rules.

AppRuleEditor
    Dialog for creating/editing individual rules.

Functions
---------
show_app_rules_panel
    Show the app rules management panel.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, Callable, List, Dict, Any

from .theme import ThemeManager, create_styled_frame, create_styled_label, create_styled_button
from .icons import IconFactory
from .app_rules_manager import get_app_rules_manager, AppRule
from .app_detector import AppMatcher, MatchType, get_active_window_info, WindowInfo

logger = logging.getLogger(__name__)


class AppRuleEditor:
    """Dialog for creating/editing app rules."""

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager,
                 rule: Optional[AppRule] = None,
                 on_save: Optional[Callable] = None):
        """Initialize the rule editor.

        Args:
            parent: Parent window
            theme_manager: ThemeManager instance
            rule: Existing rule to edit (None for new rule)
            on_save: Callback when rule is saved
        """
        self.parent = parent
        self.theme_manager = theme_manager
        self.rule = rule
        self.on_save = on_save
        self.dialog = None
        self.icon_factory = IconFactory(theme_manager)

        # Form fields
        self.name_var = tk.StringVar()
        self.priority_var = tk.IntVar(value=10)
        self.enabled_var = tk.BooleanVar(value=True)
        self.notes_var = tk.StringVar()

        # Settings overrides
        self.hotkey_var = tk.StringVar()
        self.model_type_var = tk.StringVar()
        self.model_name_var = tk.StringVar()
        self.language_var = tk.StringVar()
        self.device_var = tk.StringVar()
        self.compute_type_var = tk.StringVar()

        # Matchers list
        self.matchers: List[AppMatcher] = []

        # UI components
        self.matchers_listbox = None
        self.matcher_type_var = tk.StringVar()
        self.matcher_pattern_var = tk.StringVar()
        self.matcher_case_var = tk.BooleanVar(value=False)

        if rule:
            self._load_rule_data()

    def _load_rule_data(self):
        """Load existing rule data into form."""
        if not self.rule:
            return

        self.name_var.set(self.rule.name)
        self.priority_var.set(self.rule.priority)
        self.enabled_var.set(self.rule.enabled)
        self.notes_var.set(self.rule.notes)

        self.hotkey_var.set(self.rule.hotkey or "")
        self.model_type_var.set(self.rule.model_type or "")
        self.model_name_var.set(self.rule.model_name or "")
        self.language_var.set(self.rule.language or "")
        self.device_var.set(self.rule.device or "")
        self.compute_type_var.set(self.rule.compute_type or "")

        self.matchers = self.rule.matchers.copy()

    def show(self):
        """Show the editor dialog."""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.lift()
            self.dialog.focus_force()
            return

        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Edit Rule" if self.rule else "New App Rule")
        self.dialog.geometry("700x650")
        self.dialog.resizable(False, False)

        self.theme_manager.style.apply_to_widget(self.dialog)
        self._build_ui()
        self._center_dialog()

    def _center_dialog(self):
        """Center dialog on parent."""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _build_ui(self):
        """Build the editor UI."""
        main_frame = create_styled_frame(
            self.dialog,
            self.theme_manager,
            card_style=False
        )
        main_frame.pack(fill=tk.BOTH, expand=True,
                       padx=self.theme_manager.get_spacing("md"),
                       pady=self.theme_manager.get_spacing("md"))

        # Header
        self._create_header(main_frame)

        # Scrollable content
        canvas = tk.Canvas(main_frame, highlightthickness=0,
                          bg=self.theme_manager.get_color("bg_main"))
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Sections
        self._create_basic_info_section(scrollable)
        self._create_matchers_section(scrollable)
        self._create_settings_section(scrollable)

        # Footer buttons
        footer = ttk.Frame(main_frame)
        footer.pack(fill=tk.X, pady=(self.theme_manager.get_spacing("md"), 0))

        cancel_btn = create_styled_button(
            footer,
            self.theme_manager,
            variant="secondary",
            text="Cancel",
            command=self.dialog.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=self.theme_manager.get_spacing("xs"))

        save_btn = create_styled_button(
            footer,
            self.theme_manager,
            variant="primary",
            text="Save Rule",
            command=self._save_rule
        )
        save_btn.pack(side=tk.RIGHT)

    def _create_header(self, parent):
        """Create header section."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, self.theme_manager.get_spacing("sm")))

        icon = self.icon_factory.create(
            header_frame, "settings",
            size=28,
            color=self.theme_manager.get_color("primary")
        )
        icon.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("sm")))

        title_text = "Edit Application Rule" if self.rule else "Create Application Rule"
        title = create_styled_label(
            header_frame,
            self.theme_manager,
            variant="title",
            text=title_text
        )
        title.pack(side=tk.LEFT)

    def _create_basic_info_section(self, parent):
        """Create basic info section."""
        card = create_styled_frame(parent, self.theme_manager, card_style=True)
        card.pack(fill=tk.X, padx=self.theme_manager.get_spacing("md"),
                  pady=(self.theme_manager.get_spacing("md"), self.theme_manager.get_spacing("sm")))

        # Header
        header = create_styled_label(
            card,
            self.theme_manager,
            variant="subtitle",
            text="Basic Information"
        )
        header.pack(anchor=tk.W, padx=self.theme_manager.get_spacing("sm"),
                   pady=(self.theme_manager.get_spacing("sm"), self.theme_manager.get_spacing("xs")))

        ttk.Separator(card, orient=tk.HORIZONTAL).pack(
            fill=tk.X, padx=self.theme_manager.get_spacing("sm"))

        content = ttk.Frame(card)
        content.pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"),
                     pady=self.theme_manager.get_spacing("sm"))

        # Rule name
        name_row = ttk.Frame(content)
        name_row.pack(fill=tk.X, pady=(0, self.theme_manager.get_spacing("xs")))

        create_styled_label(
            name_row,
            self.theme_manager,
            text="Rule Name:"
        ).pack(side=tk.LEFT)

        name_entry = ttk.Entry(name_row, textvariable=self.name_var, width=40)
        name_entry.pack(side=tk.RIGHT, padx=(self.theme_manager.get_spacing("sm"), 0))

        # Priority and Enabled
        priority_row = ttk.Frame(content)
        priority_row.pack(fill=tk.X, pady=(self.theme_manager.get_spacing("xs"), 0))

        create_styled_label(
            priority_row,
            self.theme_manager,
            text="Priority:"
        ).pack(side=tk.LEFT)

        priority_spin = ttk.Spinbox(
            priority_row,
            from_=0,
            to=1000,
            textvariable=self.priority_var,
            width=10
        )
        priority_spin.pack(side=tk.LEFT, padx=(self.theme_manager.get_spacing("sm"), 0))

        create_styled_label(
            priority_row,
            self.theme_manager,
            variant="caption",
            text="(higher = checked first)"
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Enabled checkbox
        enabled_check = ttk.Checkbutton(
            priority_row,
            text="Enabled",
            variable=self.enabled_var
        )
        enabled_check.pack(side=tk.RIGHT)

        # Notes
        notes_row = ttk.Frame(content)
        notes_row.pack(fill=tk.X, pady=(self.theme_manager.get_spacing("sm"), 0))

        create_styled_label(
            notes_row,
            self.theme_manager,
            text="Notes:"
        ).pack(anchor=tk.W)

        notes_entry = ttk.Entry(notes_row, textvariable=self.notes_var)
        notes_entry.pack(fill=tk.X, pady=(self.theme_manager.get_spacing("xs"), 0))

    def _create_matchers_section(self, parent):
        """Create matchers section."""
        card = create_styled_frame(parent, self.theme_manager, card_style=True)
        card.pack(fill=tk.X, padx=self.theme_manager.get_spacing("md"),
                  pady=(0, self.theme_manager.get_spacing("sm")))

        # Header
        header_frame = ttk.Frame(card)
        header_frame.pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"),
                         pady=(self.theme_manager.get_spacing("sm"), self.theme_manager.get_spacing("xs")))

        create_styled_label(
            header_frame,
            self.theme_manager,
            variant="subtitle",
            text="Application Matchers"
        ).pack(side=tk.LEFT)

        detect_btn = create_styled_button(
            header_frame,
            self.theme_manager,
            variant="tertiary",
            text="Detect Current App",
            command=self._detect_current_app,
            width=15
        )
        detect_btn.pack(side=tk.RIGHT)

        ttk.Separator(card, orient=tk.HORIZONTAL).pack(
            fill=tk.X, padx=self.theme_manager.get_spacing("sm"))

        content = ttk.Frame(card)
        content.pack(fill=tk.BOTH, expand=True,
                     padx=self.theme_manager.get_spacing("sm"),
                     pady=self.theme_manager.get_spacing("sm"))

        # Matchers list
        list_frame = create_styled_frame(content, self.theme_manager, card_style=False)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.matchers_listbox = tk.Listbox(
            list_frame,
            height=5,
            bg=self.theme_manager.get_color("bg_card"),
            fg=self.theme_manager.get_color("fg_primary"),
            font=self.theme_manager.get_font("sm"),
            relief=tk.FLAT,
            borderwidth=0
        )
        self.matchers_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        list_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                     command=self.matchers_listbox.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.matchers_listbox.configure(yscrollcommand=list_scroll.set)

        self._refresh_matchers_list()

        # Add matcher form
        add_frame = ttk.Frame(content)
        add_frame.pack(fill=tk.X, pady=(self.theme_manager.get_spacing("sm"), 0))

        # Type dropdown
        type_frame = ttk.Frame(add_frame)
        type_frame.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("xs")))

        create_styled_label(
            type_frame,
            self.theme_manager,
            text="Type:"
        ).pack(anchor=tk.W)

        self.matcher_type_var.set(MatchType.WINDOW_CLASS.value)
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.matcher_type_var,
            values=[m.value for m in MatchType],
            state="readonly",
            width=15
        )
        type_combo.pack(pady=(2, 0))

        # Pattern entry
        pattern_frame = ttk.Frame(add_frame)
        pattern_frame.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("xs")))

        create_styled_label(
            pattern_frame,
            self.theme_manager,
            text="Pattern:"
        ).pack(anchor=tk.W)

        pattern_entry = ttk.Entry(
            pattern_frame,
            textvariable=self.matcher_pattern_var,
            width=25
        )
        pattern_entry.pack(pady=(2, 0))

        # Case sensitive and Add button
        options_frame = ttk.Frame(add_frame)
        options_frame.pack(side=tk.LEFT)

        case_check = ttk.Checkbutton(
            options_frame,
            text="Case Sensitive",
            variable=self.matcher_case_var
        )
        case_check.pack(anchor=tk.W)

        add_btn = create_styled_button(
            options_frame,
            self.theme_manager,
            variant="secondary",
            text="+ Add",
            command=self._add_matcher,
            width=8
        )
        add_btn.pack(pady=(2, 0))

        # Remove button
        remove_btn = create_styled_button(
            add_frame,
            self.theme_manager,
            variant="tertiary",
            text="- Remove",
            command=self._remove_matcher,
            width=8
        )
        remove_btn.pack(side=tk.LEFT, padx=(self.theme_manager.get_spacing("xs"), 0))

    def _create_settings_section(self, parent):
        """Create settings overrides section."""
        card = create_styled_frame(parent, self.theme_manager, card_style=True)
        card.pack(fill=tk.X, padx=self.theme_manager.get_spacing("md"),
                  pady=(0, self.theme_manager.get_spacing("md")))

        # Header
        header = create_styled_label(
            card,
            self.theme_manager,
            variant="subtitle",
            text="Settings Overrides (Optional)"
        )
        header.pack(anchor=tk.W, padx=self.theme_manager.get_spacing("sm"),
                   pady=(self.theme_manager.get_spacing("sm"), self.theme_manager.get_spacing("xs")))

        ttk.Separator(card, orient=tk.HORIZONTAL).pack(
            fill=tk.X, padx=self.theme_manager.get_spacing("sm"))

        content = ttk.Frame(card)
        content.pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"),
                     pady=self.theme_manager.get_spacing("sm"))

        # Grid layout for settings
        for i, (label, var) in enumerate([
            ("Hotkey:", self.hotkey_var),
            ("Model Type:", self.model_type_var),
            ("Model Name:", self.model_name_var),
            ("Language:", self.language_var),
            ("Device:", self.device_var),
            ("Compute Type:", self.compute_type_var),
        ]):
            row_frame = ttk.Frame(content)
            row_frame.pack(fill=tk.X, pady=(0 if i == 0 else self.theme_manager.get_spacing("xs"), 0))

            create_styled_label(
                row_frame,
                self.theme_manager,
                text=label,
                width=15
            ).pack(side=tk.LEFT)

            entry = ttk.Entry(row_frame, textvariable=var)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Help text
        help_text = (
            "Leave fields empty to use global defaults.\n"
            "For example, set Model Type to 'parakeet' for games\n"
            "to use a lighter, faster model."
        )
        help_label = create_styled_label(
            content,
            self.theme_manager,
            variant="caption",
            text=help_text
        )
        help_label.pack(anchor=tk.W, pady=(self.theme_manager.get_spacing("sm"), 0))

    def _detect_current_app(self):
        """Detect current active window and create matcher."""
        window_info = get_active_window_info()

        # Create matchers based on available info
        matchers_to_add = []
        if window_info.window_class:
            matchers_to_add.append(
                AppMatcher(MatchType.WINDOW_CLASS, window_info.window_class)
            )
        if window_info.window_title:
            matchers_to_add.append(
                AppMatcher(MatchType.WINDOW_TITLE, window_info.window_title[:50])
            )

        if matchers_to_add:
            self.matchers.extend(matchers_to_add)
            self._refresh_matchers_list()

            # Update name if empty
            if not self.name_var.get():
                name = window_info.window_class or window_info.window_title or "Detected App"
                self.name_var.set(name[:50])

            messagebox.showinfo(
                "App Detected",
                f"Window Class: {window_info.window_class or 'N/A'}\n"
                f"Window Title: {window_info.window_title or 'N/A'}\n"
                f"Process: {window_info.process_name or 'N/A'}"
            )
        else:
            messagebox.showwarning(
                "Detection Failed",
                "Could not detect active window information."
            )

    def _add_matcher(self):
        """Add a matcher from form."""
        match_type_str = self.matcher_type_var.get()
        pattern = self.matcher_pattern_var.get().strip()
        case_sensitive = self.matcher_case_var.get()

        if not pattern:
            messagebox.showwarning("Invalid Input", "Please enter a pattern.")
            return

        try:
            match_type = MatchType(match_type_str)
            matcher = AppMatcher(match_type, pattern, case_sensitive)
            self.matchers.append(matcher)
            self._refresh_matchers_list()
            self.matcher_pattern_var.set("")
        except ValueError:
            messagebox.showerror("Error", "Invalid matcher type")

    def _remove_matcher(self):
        """Remove selected matcher."""
        selection = self.matchers_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        del self.matchers[index]
        self._refresh_matchers_list()

    def _refresh_matchers_list(self):
        """Refresh the matchers listbox."""
        self.matchers_listbox.delete(0, tk.END)
        for i, matcher in enumerate(self.matchers):
            text = f"{i+1}. {matcher.match_type.value}: {matcher.pattern}"
            if matcher.case_sensitive:
                text += " [Case]"
            self.matchers_listbox.insert(tk.END, text)

    def _save_rule(self):
        """Save the rule."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Please enter a rule name.")
            return

        if not self.matchers:
            messagebox.showwarning("Validation Error",
                                   "Please add at least one matcher.")
            return

        priority = self.priority_var.get()
        enabled = self.enabled_var.get()
        notes = self.notes_var.get().strip()

        # Get settings overrides (only if set)
        hotkey = self.hotkey_var.get().strip() or None
        model_type = self.model_type_var.get().strip() or None
        model_name = self.model_name_var.get().strip() or None
        language = self.language_var.get().strip() or None
        device = self.device_var.get().strip() or None
        compute_type = self.compute_type_var.get().strip() or None

        if self.rule:
            # Update existing
            updated_rule = AppRule(
                id=self.rule.id,
                name=name,
                matchers=self.matchers,
                priority=priority,
                hotkey=hotkey,
                model_type=model_type,
                model_name=model_name,
                compute_type=compute_type,
                device=device,
                language=language,
                enabled=enabled,
                created_at=self.rule.created_at,
                notes=notes
            )
            get_app_rules_manager().update_rule(self.rule.id, updated_rule)
        else:
            # Create new
            get_app_rules_manager().create_rule(
                name=name,
                matchers=self.matchers,
                priority=priority,
                hotkey=hotkey,
                model_type=model_type,
                model_name=model_name,
                compute_type=compute_type,
                device=device,
                language=language,
                enabled=enabled,
                notes=notes
            )

        if self.on_save:
            self.on_save()

        self.dialog.destroy()


class AppRulesPanel:
    """Panel for managing app-specific rules."""

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager,
                 on_change: Optional[Callable] = None):
        """Initialize the panel.

        Args:
            parent: Parent window
            theme_manager: ThemeManager instance
            on_change: Callback when rules are changed
        """
        self.parent = parent
        self.theme_manager = theme_manager
        self.on_change = on_change
        self.window = None
        self.icon_factory = IconFactory(theme_manager)
        self.rules_manager = get_app_rules_manager()

        # UI components
        self.rules_tree = None
        self.currently_matching_label = None

    def show(self):
        """Show the panel."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Application-Specific Settings")
        self.window.geometry("800x600")
        self.window.resizable(True, True)

        self.theme_manager.style.apply_to_widget(self.window)
        self._build_ui()
        self._refresh_rules_list()
        self._update_current_match()

    def _build_ui(self):
        """Build the panel UI."""
        main_frame = create_styled_frame(
            self.window,
            self.theme_manager,
            card_style=False
        )
        main_frame.pack(fill=tk.BOTH, expand=True,
                       padx=self.theme_manager.get_spacing("md"),
                       pady=self.theme_manager.get_spacing("md"))

        # Header
        self._create_header(main_frame)

        # Content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True,
                          pady=(self.theme_manager.get_spacing("md"), 0))

        # Rules list
        self._create_rules_list(content_frame)

        # Buttons
        self._create_buttons(main_frame)

    def _create_header(self, parent):
        """Create header section."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, self.theme_manager.get_spacing("sm")))

        icon = self.icon_factory.create(
            header_frame, "settings",
            size=28,
            color=self.theme_manager.get_color("primary")
        )
        icon.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("sm")))

        title = create_styled_label(
            header_frame,
            self.theme_manager,
            variant="title",
            text="Application-Specific Settings"
        )
        title.pack(side=tk.LEFT)

        # Current match indicator
        self.currently_matching_label = create_styled_label(
            header_frame,
            self.theme_manager,
            variant="caption",
            text=""
        )
        self.currently_matching_label.pack(side=tk.RIGHT)

    def _create_rules_list(self, parent):
        """Create rules list."""
        card = create_styled_frame(parent, self.theme_manager, card_style=True)
        card.pack(fill=tk.BOTH, expand=True)

        # Treeview with scrollbar
        tree_frame = ttk.Frame(card)
        tree_frame.pack(fill=tk.BOTH, expand=True,
                       padx=self.theme_manager.get_spacing("sm"),
                       pady=self.theme_manager.get_spacing("sm"))

        # Treeview columns
        columns = ("name", "priority", "matchers", "settings", "enabled")

        self.rules_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=10
        )

        self.rules_tree.heading("name", text="Rule Name")
        self.rules_tree.heading("priority", text="Priority")
        self.rules_tree.heading("matchers", text="Matchers")
        self.rules_tree.heading("settings", text="Overrides")
        self.rules_tree.heading("enabled", text="Enabled")

        self.rules_tree.column("name", width=200)
        self.rules_tree.column("priority", width=70)
        self.rules_tree.column("matchers", width=250)
        self.rules_tree.column("settings", width=200)
        self.rules_tree.column("enabled", width=70)

        tree_scroll = ttk.Scrollbar(
            tree_frame,
            orient=tk.VERTICAL,
            command=self.rules_tree.yview
        )
        self.rules_tree.configure(yscrollcommand=tree_scroll.set)

        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Double-click to edit
        self.rules_tree.bind("<Double-1>", self._on_double_click)

    def _create_buttons(self, parent):
        """Create button row."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(self.theme_manager.get_spacing("md"), 0))

        # Left side: Add/Edit/Delete
        left_frame = ttk.Frame(button_frame)
        left_frame.pack(side=tk.LEFT)

        add_btn = create_styled_button(
            left_frame,
            self.theme_manager,
            variant="primary",
            text="+ New Rule",
            command=self._new_rule,
            width=12
        )
        add_btn.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("xs")))

        edit_btn = create_styled_button(
            left_frame,
            self.theme_manager,
            variant="secondary",
            text="Edit",
            command=self._edit_rule,
            width=10
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("xs")))

        delete_btn = create_styled_button(
            left_frame,
            self.theme_manager,
            variant="secondary",
            text="Delete",
            command=self._delete_rule,
            width=10
        )
        delete_btn.pack(side=tk.LEFT)

        # Right side: Close
        close_btn = create_styled_button(
            button_frame,
            self.theme_manager,
            variant="secondary",
            text="Close",
            command=self.window.destroy,
            width=10
        )
        close_btn.pack(side=tk.RIGHT)

    def _refresh_rules_list(self):
        """Refresh the rules list."""
        # Clear existing items
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)

        # Add rules (sorted by priority)
        rules = self.rules_manager.get_all_rules()
        for rule in rules:
            # Format matchers
            matchers_str = ", ".join(
                f"{m.match_type.value}={m.pattern}"
                for m in rule.matchers
            )
            if len(matchers_str) > 40:
                matchers_str = matchers_str[:37] + "..."

            # Format settings overrides
            settings_parts = []
            if rule.hotkey:
                settings_parts.append(f"hotkey:{rule.hotkey}")
            if rule.model_name:
                settings_parts.append(f"model:{rule.model_name}")
            if rule.language:
                settings_parts.append(f"lang:{rule.language}")
            settings_str = ", ".join(settings_parts) if settings_parts else "-"

            self.rules_tree.insert(
                "",
                tk.END,
                values=(
                    rule.name,
                    rule.priority,
                    matchers_str,
                    settings_str,
                    "Yes" if rule.enabled else "No"
                )
            )

    def _update_current_match(self):
        """Update the currently matching rule display."""
        matched_rule = self.rules_manager.match_active_window()
        if matched_rule:
            text = f"Currently Active: {matched_rule.name}"
            color = self.theme_manager.get_color("success")
        else:
            text = "Using Global Settings"
            color = self.theme_manager.get_color("fg_secondary")

        self.currently_matching_label.configure(text=text, fg=color)

    def _new_rule(self):
        """Create a new rule."""
        editor = AppRuleEditor(
            self.window,
            self.theme_manager,
            on_save=self._on_rule_changed
        )
        editor.show()

    def _edit_rule(self):
        """Edit selected rule."""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a rule to edit.")
            return

        item = selection[0]
        index = self.rules_tree.index(item)
        rules = self.rules_manager.get_all_rules()
        rule = rules[index]

        editor = AppRuleEditor(
            self.window,
            self.theme_manager,
            rule=rule,
            on_save=self._on_rule_changed
        )
        editor.show()

    def _delete_rule(self):
        """Delete selected rule."""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a rule to delete.")
            return

        if not messagebox.askyesno("Confirm Delete",
                                    "Are you sure you want to delete this rule?"):
            return

        item = selection[0]
        index = self.rules_tree.index(item)
        rules = self.rules_manager.get_all_rules()
        rule = rules[index]

        self.rules_manager.delete_rule(rule.id)
        self._on_rule_changed()

    def _on_double_click(self, event):
        """Handle double-click on rule."""
        self._edit_rule()

    def _on_rule_changed(self):
        """Handle rule change."""
        self._refresh_rules_list()
        self._update_current_match()
        if self.on_change:
            self.on_change()


def show_app_rules_panel(parent: tk.Tk,
                         theme_manager: ThemeManager,
                         on_change: Optional[Callable] = None) -> AppRulesPanel:
    """Show the app rules management panel.

    Args:
        parent: Parent window
        theme_manager: ThemeManager instance
        on_change: Callback when rules are changed

    Returns:
        AppRulesPanel instance
    """
    panel = AppRulesPanel(parent, theme_manager, on_change)
    panel.show()
    return panel
