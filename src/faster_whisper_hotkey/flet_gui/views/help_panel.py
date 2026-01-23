"""
Help panel view for the Flet GUI.

This module provides a comprehensive help and documentation interface with:
- FAQ section with common questions
- Keyboard shortcuts reference
- Troubleshooting guide
- Interactive tutorial for first-time users
- Link to online documentation

Classes
-------
HelpSection
    Enum for help section identifiers.

HelpPanel
    Comprehensive help interface with FAQ, shortcuts, and troubleshooting.

InteractiveTutorial
    Step-by-step interactive tutorial for new users.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Callable

import flet as ft

from ..theme import get_theme_manager, SPACING, BORDER_RADIUS, TYPOGRAPHY
from ..components import Card
from ..accessibility import get_accessibility_manager

logger = logging.getLogger(__name__)


class HelpSection(Enum):
    """Help section identifiers."""
    OVERVIEW = "overview"
    FAQ = "faq"
    SHORTCUTS = "shortcuts"
    TROUBLESHOOTING = "troubleshooting"
    TUTORIAL = "tutorial"


@dataclass
class FAQItem:
    """
    Frequently Asked Question item.

    Attributes
    ----------
    question
        The question text.
    answer
        The answer text.
    category
        Optional category for grouping.
    keywords
        Search keywords.
    """
    question: str
    answer: str
    category: str = "General"
    keywords: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class ShortcutItem:
    """
    Keyboard shortcut item.

    Attributes
    ----------
    keys
        The keyboard combination (e.g., "Ctrl+Shift+H").
    description
        What the shortcut does.
    category
        Category for grouping.
    """
    keys: str
    description: str
    category: str = "General"


@dataclass
class TroubleshootingItem:
    """
    Troubleshooting item.

    Attributes
    ----------
    problem
        The problem description.
    solution
        The solution steps.
    severity
        Problem severity (info, warning, error).
    """
    problem: str
    solution: str
    severity: str = "info"


class FAQCard(ft.Container):
    """
    Expandable FAQ card with question and answer.

    Parameters
    ----------
    faq
        The FAQ item to display.
    **kwargs
        Additional Container properties.
    """

    def __init__(self, faq: FAQItem, **kwargs):
        self._theme = get_theme_manager()
        self._faq = faq
        self._expanded = False

        # Create the expandable content
        self._icon = ft.Icon(
            ft.icons.EXPAND_MORE,
            size=20,
            color=self._theme.colors.on_surface_variant,
        )

        self._answer_text = ft.Text(
            self._faq.answer,
            size=TYPOGRAPHY.body_medium,
            color=self._theme.colors.on_surface_variant,
            visible=False,
        )

        content = ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                self._faq.question,
                                size=TYPOGRAPHY.body_large,
                                weight=ft.FontWeight.MEDIUM,
                                color=self._theme.colors.on_surface,
                                expand=True,
                            ),
                            self._icon,
                        ],
                        spacing=SPACING.sm,
                    ),
                    padding=ft.padding.symmetric(horizontal=SPACING.md, vertical=SPACING.sm),
                    on_click=self._toggle_expand,
                    ink=True,
                    border_radius=BORDER_RADIUS.md,
                ),
                ft.Container(
                    content=self._answer_text,
                    padding=ft.padding.only(
                        left=SPACING.md,
                        right=SPACING.md,
                        bottom=SPACING.md,
                    ),
                ),
            ],
            spacing=SPACING.none,
        )

        super().__init__(
            content=content,
            bgcolor=self._theme.colors.surface_container_low,
            border_radius=BORDER_RADIUS.md,
            **kwargs,
        )

    def _toggle_expand(self, e):
        """Toggle the expanded state of the FAQ card."""
        self._expanded = not self._expanded
        self._answer_text.visible = self._expanded
        self._icon.name = ft.icons.EXPAND_LESS if self._expanded else ft.icons.EXPAND_MORE

        if self.page:
            self.page.update()


class ShortcutRow(ft.Container):
    """
    Row displaying a keyboard shortcut.

    Parameters
    ----------
    shortcut
        The shortcut item to display.
    **kwargs
        Additional Container properties.
    """

    def __init__(self, shortcut: ShortcutItem, **kwargs):
        self._theme = get_theme_manager()
        self._shortcut = shortcut

        # Create key badges
        keys = self._shortcut.keys.split("+")
        key_badges = []
        for i, key in enumerate(keys):
            key_badges.append(
                ft.Container(
                    content=ft.Text(
                        key.upper(),
                        size=TYPOGRAPHY.label_medium,
                        weight=ft.FontWeight.MEDIUM,
                        color=self._theme.colors.on_surface,
                    ),
                    padding=ft.padding.symmetric(horizontal=SPACING.sm, vertical=SPACING.xs),
                    bgcolor=self._theme.colors.surface_container,
                    border_radius=BORDER_RADIUS.sm,
                    border=ft.border.all(1, self._theme.colors.outline),
                )
            )
            if i < len(keys) - 1:
                key_badges.append(ft.Text(" + ", size=TYPOGRAPHY.body_small))

        content = ft.Row(
            [
                ft.Text(
                    self._shortcut.description,
                    size=TYPOGRAPHY.body_medium,
                    color=self._theme.colors.on_surface,
                    expand=True,
                ),
                ft.Row(
                    key_badges,
                    spacing=SPACING.xs,
                ),
            ],
            spacing=SPACING.md,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        super().__init__(
            content=content,
            padding=ft.padding.symmetric(horizontal=SPACING.md, vertical=SPACING.sm),
            **kwargs,
        )


class TroubleshootingCard(ft.Container):
    """
    Card displaying a troubleshooting issue.

    Parameters
    ----------
    item
        The troubleshooting item to display.
    **kwargs
        Additional Container properties.
    """

    def __init__(self, item: TroubleshootingItem, **kwargs):
        self._theme = get_theme_manager()
        self._item = item

        # Severity icon and color
        severity_config = {
            "info": (ft.icons.INFO_OUTLINED, self._theme.colors.info),
            "warning": (ft.icons.WARNING_OUTLINED, self._theme.colors.warning),
            "error": (ft.icons.ERROR_OUTLINE, self._theme.colors.error),
        }

        icon_name, icon_color = severity_config.get(
            item.severity,
            severity_config["info"]
        )

        # Parse solution as steps
        solution_lines = item.solution.strip().split("\n")
        solution_steps = []
        for line in solution_lines:
            line = line.strip()
            if line.startswith("- "):
                line = line[2:]
            elif line.startswith("* "):
                line = line[2:]

            solution_steps.append(
                ft.Row(
                    [
                        ft.Container(
                            width=6,
                            height=6,
                            border_radius=3,
                            bgcolor=self._theme.colors.primary,
                            margin=ft.margin.only(top=6),
                        ),
                        ft.Text(
                            line,
                            size=TYPOGRAPHY.body_medium,
                            color=self._theme.colors.on_surface_variant,
                        ),
                    ],
                    spacing=SPACING.sm,
                )
            )

        content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(icon_name, size=20, color=icon_color),
                        ft.Text(
                            self._item.problem,
                            size=TYPOGRAPHY.body_large,
                            weight=ft.FontWeight.MEDIUM,
                            color=self._theme.colors.on_surface,
                        ),
                    ],
                    spacing=SPACING.sm,
                ),
                ft.Container(
                    content=ft.Column(
                        solution_steps,
                        spacing=SPACING.xs,
                    ),
                    padding=ft.padding.only(left=SPACING.md),
                ),
            ],
            spacing=SPACING.sm,
        )

        super().__init__(
            content=content,
            padding=SPACING.md,
            bgcolor=self._theme.colors.surface_container_low,
            border_radius=BORDER_RADIUS.md,
            border=ft.border.only(left=ft.BorderSide(4, icon_color)),
            **kwargs,
        )


class TutorialStep:
    """
    A single step in the interactive tutorial.

    Attributes
    ----------
    title
        Step title.
    description
        Step description.
    icon
        Icon to display for this step.
    action_text
        Text describing what the user should do.
    """
    title: str
    description: str
    icon: str
    action_text: str

    def __init__(self, title: str, description: str, icon: str, action_text: str = ""):
        self.title = title
        self.description = description
        self.icon = icon
        self.action_text = action_text


class InteractiveTutorial(ft.Container):
    """
    Interactive step-by-step tutorial for new users.

    The tutorial guides users through the main features of the application
    with interactive steps and visual highlights.

    Parameters
    ----------
    on_complete
        Callback when tutorial is completed.
    on_skip
        Callback when tutorial is skipped.
    hotkey
        The configured hotkey for transcription.
    **kwargs
        Additional Container properties.
    """

    def __init__(
        self,
        on_complete: Optional[Callable[[], None]] = None,
        on_skip: Optional[Callable[[], None]] = None,
        hotkey: str = "pause",
        **kwargs,
    ):
        self._theme = get_theme_manager()
        self._on_complete = on_complete
        self._on_skip = on_skip
        self._hotkey = hotkey
        self._current_step = 0

        # Define tutorial steps
        self._steps = [
            TutorialStep(
                "Welcome to faster-whisper-hotkey!",
                "This tutorial will guide you through the main features of the application.",
                ft.icons.ROCKET_LAUNCH,
                "Press 'Next' to get started",
            ),
            TutorialStep(
                "Push-to-Talk Transcription",
                "The fastest way to transcribe audio. Hold your hotkey to record, release to transcribe.",
                ft.icons.MIC,
                f"Press and hold '{self._hotkey.upper()}' to start recording",
            ),
            TutorialStep(
                "Recording State",
                "When recording, you'll see a pulsing indicator and your audio level in real-time.",
                ft.icons.FAVORITE,
                "Try pressing the hotkey briefly to see the recording indicator",
            ),
            TutorialStep(
                "Transcription Result",
                "Your transcribed text appears in the main window. You can copy or paste it anywhere.",
                ft.icons.TEXT_FIELDS,
                "Click the copy button or paste directly to other apps",
            ),
            TutorialStep(
                "History Access",
                "All your transcriptions are saved. Access them from the history panel.",
                ft.icons.HISTORY,
                "Click the history icon to see past transcriptions",
            ),
            TutorialStep(
                "Settings Customization",
                "Customize models, hotkeys, audio devices, and more in the settings panel.",
                ft.icons.SETTINGS,
                "Click the settings icon to explore options",
            ),
            TutorialStep(
                "Practice Session",
                "Let's practice! Record a short phrase and see it transcribed.",
                ft.icons.RECORD_VOICE_OVER,
                "Press the hotkey, speak, then release",
            ),
            TutorialStep(
                "You're Ready!",
                "You now know the basics. Check the Help panel for more tips and tricks.",
                ft.icons.CHECK_CIRCLE,
                "Enjoy using faster-whisper-hotkey!",
            ),
        ]

        content = self._build_current_step()

        super().__init__(
            content=content,
            padding=SPACING.lg,
            **kwargs,
        )

    def _build_current_step(self) -> ft.Control:
        """Build the current tutorial step."""
        step = self._steps[self._current_step]

        # Progress dots
        progress_dots = []
        for i in range(len(self._steps)):
            is_active = i == self._current_step
            is_completed = i < self._current_step

            dot_color = (
                self._theme.colors.primary if is_active else
                (self._theme.colors.success if is_completed else self._theme.colors.outline_variant)
            )

            progress_dots.append(
                ft.Container(
                    width=12 if is_active else 8,
                    height=8,
                    border_radius=4 if is_active else 4,
                    bgcolor=dot_color,
                )
            )

        # Step icon
        icon = ft.Icon(
            step.icon,
            size=48,
            color=self._theme.colors.primary,
        )

        # Step content
        title = ft.Text(
            step.title,
            size=TYPOGRAPHY.headline_small,
            weight=ft.FontWeight.BOLD,
            color=self._theme.colors.on_surface,
            text_align=ft.TextAlign.CENTER,
        )

        description = ft.Text(
            step.description,
            size=TYPOGRAPHY.body_medium,
            color=self._theme.colors.on_surface_variant,
            text_align=ft.TextAlign.CENTER,
        )

        action = ft.Container(
            content=ft.Text(
                step.action_text,
                size=TYPOGRAPHY.body_small,
                color=self._theme.colors.primary,
                weight=ft.FontWeight.MEDIUM,
                text_align=ft.TextAlign.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=SPACING.md, vertical=SPACING.sm),
            bgcolor=self._theme.colors.primary_container,
            border_radius=BORDER_RADIUS.md,
        )

        # Navigation buttons
        self._back_button = ft.TextButton(
            "Back",
            on_click=self._on_back,
            visible=self._current_step > 0,
        )

        self._skip_button = ft.TextButton(
            "Skip Tutorial",
            on_click=self._on_skip_click,
        )

        self._next_button = ft.ElevatedButton(
            "Finish" if self._current_step == len(self._steps) - 1 else "Next",
            on_click=self._on_next,
            icon=ft.icons.CHECK if self._current_step == len(self._steps) - 1 else ft.icons.ARROW_FORWARD,
            style=ft.ButtonStyle(
                bgcolor=self._theme.colors.primary,
                color=self._theme.colors.on_primary,
            ),
        )

        nav_row = ft.Row(
            [self._back_button, ft.Container(expand=True), self._skip_button, self._next_button],
            alignment=ft.MainAxisAlignment.END,
        )

        return ft.Column(
            [
                ft.Row(progress_dots, spacing=SPACING.sm, alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=SPACING.lg),
                icon,
                ft.Container(height=SPACING.md),
                title,
                ft.Container(height=SPACING.sm),
                description,
                ft.Container(height=SPACING.md),
                action,
                ft.Container(expand=True),
                nav_row,
            ],
            spacing=SPACING.none,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _on_next(self, e):
        """Handle next button."""
        if self._current_step < len(self._steps) - 1:
            self._current_step += 1
            self.content = self._build_current_step()
            if self.page:
                self.page.update()
        else:
            if self._on_complete:
                self._on_complete()

    def _on_back(self, e):
        """Handle back button."""
        if self._current_step > 0:
            self._current_step -= 1
            self.content = self._build_current_step()
            if self.page:
                self.page.update()

    def _on_skip_click(self, e):
        """Handle skip button."""
        if self._on_skip:
            self._on_skip()

    def reset(self):
        """Reset the tutorial to the first step."""
        self._current_step = 0
        self.content = self._build_current_step()
        if self.page:
            self.page.update()


class HelpPanel:
    """
    Comprehensive help panel with FAQ, shortcuts, and troubleshooting.

    The panel provides:
    - Overview of the application
    - FAQ section with expandable answers
    - Keyboard shortcuts reference
    - Troubleshooting guide
    - Interactive tutorial access
    - Links to online documentation

    Parameters
    ----------
    on_close
        Callback when help panel is closed.
    hotkey
        The configured hotkey for transcription (for tutorial display).
    history_hotkey
        The configured history hotkey.
    """

    # FAQ data
    FAQ_ITEMS = [
        FAQItem(
            "How do I start transcribing?",
            "Press and hold your configured hotkey (default: PAUSE) to start recording. Speak clearly, then release the key to transcribe.",
            "Getting Started",
            ["record", "start", "begin", "how to"],
        ),
        FAQItem(
            "Can I use a different hotkey?",
            "Yes! Go to Settings > Recording to change your hotkey. You can set any key combination you prefer.",
            "Settings",
            ["hotkey", "change", "custom", "key"],
        ),
        FAQItem(
            "What's the difference between Hold and Toggle mode?",
            "Hold mode: Hold the key to record, release to transcribe.\nToggle mode: Press once to start, press again to stop.",
            "Settings",
            ["mode", "hold", "toggle", "activation"],
        ),
        FAQItem(
            "How accurate is the transcription?",
            "Accuracy depends on the model, audio quality, and speaking clarity. Larger models (like large-v3) provide higher accuracy but are slower.",
            "Models",
            ["accuracy", "quality", "model", "precision"],
        ),
        FAQItem(
            "Which model should I use?",
            "For most users: medium or small models provide good balance of speed and accuracy.\nFor best accuracy: large-v3 (requires more resources).\nFor fastest speed: tiny or base.",
            "Models",
            ["model", "which", "recommend", "best"],
        ),
        FAQItem(
            "Does it work offline?",
            "Yes! Once the model is downloaded, all transcription happens locally on your computer. No internet connection required.",
            "General",
            ["offline", "internet", "connection", "network"],
        ),
        FAQItem(
            "How do I access past transcriptions?",
            "Click the History icon in the bottom toolbar, or press your history hotkey (default: Ctrl+Shift+H).",
            "Features",
            ["history", "past", "previous", "access"],
        ),
        FAQItem(
            "Can I use transcription in other applications?",
            "Yes! Use the paste button to automatically paste the transcription into your active application window.",
            "Features",
            ["paste", "other apps", "applications", "export"],
        ),
        FAQItem(
            "What languages are supported?",
            "faster-whisper supports 90+ languages including English, Spanish, French, German, Chinese, Japanese, and many more.",
            "General",
            ["languages", "language", "supported", "multilingual"],
        ),
        FAQItem(
            "How do I improve audio quality?",
            "Use a good microphone, speak clearly, minimize background noise, and position the microphone close to your mouth.",
            "Tips",
            ["quality", "audio", "microphone", "improve"],
        ),
        FAQItem(
            "Why is transcription slow?",
            "This depends on your hardware and model size. Consider using a smaller model, enabling GPU acceleration, or a faster computer.",
            "Performance",
            ["slow", "speed", "performance", "lag"],
        ),
        FAQItem(
            "Can I minimize to tray?",
            "Yes! Click the minimize button to minimize to system tray. The app continues running and hotkeys still work.",
            "Features",
            ["tray", "minimize", "background", "system tray"],
        ),
    ]

    # Troubleshooting data
    TROUBLESHOOTING_ITEMS = [
        TroubleshootingItem(
            "No audio is being detected",
            "- Check your microphone is connected and not muted\n- Verify the correct audio device is selected in Settings\n- Test your microphone in Windows Sound settings\n- Try restarting the application",
            "warning",
        ),
        TroubleshootingItem(
            "Transcription results are empty or incorrect",
            "- Speak more clearly and closer to the microphone\n- Reduce background noise\n- Check the correct language is selected in Settings\n- Try a larger model for better accuracy",
            "warning",
        ),
        TroubleshootingItem(
            "Hotkey not working",
            "- Check if another application is using the same hotkey\n- Verify the hotkey is correctly set in Settings\n- Try running the application as administrator\n- Make sure the app window is not completely closed (minimized to tray is OK)",
            "error",
        ),
        TroubleshootingItem(
            "Model download fails",
            "- Check your internet connection\n- Try a different network if available\n- Disable VPN or proxy temporarily\n- Clear the model cache and retry download\n- Check if your firewall is blocking the download",
            "error",
        ),
        TroubleshootingItem(
            "Application crashes on startup",
            "- Update to the latest version\n- Try deleting the settings file and restarting\n- Check if your antivirus is blocking the app\n- Run the application from terminal to see error messages",
            "error",
        ),
        TroubleshootingItem(
            "High CPU or memory usage",
            "- This is normal during transcription, especially with large models\n- Consider using a smaller model (base or tiny)\n- Enable GPU acceleration if you have a compatible GPU\n- Close other applications to free up resources",
            "info",
        ),
        TroubleshootingItem(
            "Paste to other applications doesn't work",
            "- Some applications may block programmatic paste\n- Try using copy + manual paste (Ctrl+V)\n- Run the application as administrator\n- Check if the target application is running with elevated privileges",
            "info",
        ),
    ]

    def __init__(
        self,
        on_close: Optional[Callable[[], None]] = None,
        hotkey: str = "pause",
        history_hotkey: str = "ctrl+shift+h",
    ):
        self._on_close = on_close
        self._hotkey = hotkey
        self._history_hotkey = history_hotkey
        self._theme = get_theme_manager()
        self._accessibility_manager = get_accessibility_manager()

        # UI components
        self._current_section = HelpSection.OVERVIEW
        self._content_column: Optional[ft.Column] = None
        self._search_field: Optional[ft.TextField] = None

        # Keyboard shortcuts
        self._shortcuts = [
            ShortcutItem(hotkey, "Start/Stop Recording", "Recording"),
            ShortcutItem(history_hotkey, "Open History Panel", "Navigation"),
            ShortcutItem("Ctrl+C", "Copy Transcription", "General"),
            ShortcutItem("Ctrl+V", "Paste Transcription", "General"),
            ShortcutItem("Escape", "Close Current Panel", "Navigation"),
            ShortcutItem("F1", "Open Help Panel", "General"),
        ]

    def build(self) -> ft.Control:
        """Build the help panel UI."""
        # Navigation sidebar
        nav_items = [
            self._build_nav_item("Overview", HelpSection.OVERVIEW, ft.icons.HOME_OUTLINED),
            self._build_nav_item("FAQ", HelpSection.FAQ, ft.icons.HELP_OUTLINE),
            self._build_nav_item("Shortcuts", HelpSection.SHORTCUTS, ft.icons.KEYBOARD_OUTLINED),
            self._build_nav_item("Troubleshooting", HelpSection.TROUBLESHOOTING, ft.icons.BUILD_OUTLINED),
            self._build_nav_item("Tutorial", HelpSection.TUTORIAL, ft.icons.SCHOOL_OUTLINED),
        ]

        nav_column = ft.Column(
            nav_items,
            spacing=SPACING.none,
        )

        # Search field
        self._search_field = ft.TextField(
            hint_text="Search help...",
            prefix_icon=ft.icons.SEARCH,
            border_radius=BORDER_RADIUS.md,
            on_change=self._on_search,
        )

        # Main content
        self._content_column = ft.Column(
            [self._build_overview_content()],
            spacing=SPACING.md,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Row(
            [
                # Sidebar
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Help",
                                size=TYPOGRAPHY.title_large,
                                weight=ft.FontWeight.BOLD,
                                color=self._theme.colors.on_surface,
                            ),
                            ft.Container(height=SPACING.md),
                            self._search_field,
                            ft.Container(height=SPACING.md),
                            ft.Container(
                                content=nav_column,
                                padding=ft.padding.symmetric(vertical=SPACING.sm),
                            ),
                        ],
                        spacing=SPACING.sm,
                    ),
                    width=200,
                    padding=SPACING.md,
                    bgcolor=self._theme.colors.surface_container_low,
                    border_radius=ft.BorderRadius(0, BORDER_RADIUS.lg, BORDER_RADIUS.lg, 0),
                ),
                # Main content
                ft.Container(
                    content=self._content_column,
                    expand=True,
                    padding=SPACING.lg,
                    bgcolor=self._theme.colors.surface,
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _build_nav_item(self, label: str, section: HelpSection, icon: str) -> ft.Container:
        """Build a navigation item for the sidebar."""
        is_active = self._current_section == section

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        icon,
                        size=20,
                        color=self._theme.colors.primary if is_active else self._theme.colors.on_surface_variant,
                    ),
                    ft.Text(
                        label,
                        size=TYPOGRAPHY.body_medium,
                        weight=ft.FontWeight.MEDIUM if is_active else ft.FontWeight.NORMAL,
                        color=self._theme.colors.primary if is_active else self._theme.colors.on_surface,
                    ),
                ],
                spacing=SPACING.sm,
            ),
            padding=ft.padding.symmetric(horizontal=SPACING.md, vertical=SPACING.sm),
            border_radius=BORDER_RADIUS.md,
            bgcolor=self._theme.colors.primary_container if is_active else None,
            on_click=lambda _, s=section: self._navigate_to_section(s),
            ink=True,
        )

    def _navigate_to_section(self, section: HelpSection):
        """Navigate to a help section."""
        self._current_section = section

        # Update content
        if section == HelpSection.OVERVIEW:
            self._content_column.controls = [self._build_overview_content()]
        elif section == HelpSection.FAQ:
            self._content_column.controls = [self._build_faq_content()]
        elif section == HelpSection.SHORTCUTS:
            self._content_column.controls = [self._build_shortcuts_content()]
        elif section == HelpSection.TROUBLESHOOTING:
            self._content_column.controls = [self._build_troubleshooting_content()]
        elif section == HelpSection.TUTORIAL:
            self._content_column.controls = [self._build_tutorial_content()]

        # Rebuild nav to update active state
        if self.page:
            self.update(self.build())
            self.page.update()

    def _build_overview_content(self) -> ft.Control:
        """Build the overview section content."""
        return ft.Column(
            [
                ft.Text(
                    "Welcome to faster-whisper-hotkey",
                    size=TYPOGRAPHY.headline_medium,
                    weight=ft.FontWeight.BOLD,
                    color=self._theme.colors.on_surface,
                ),
                ft.Text(
                    "Your local AI-powered transcription assistant",
                    size=TYPOGRAPHY.body_large,
                    color=self._theme.colors.on_surface_variant,
                ),
                ft.Divider(height=SPACING.lg),
                self._build_feature_card(
                    "Push-to-Talk",
                    "Instant voice transcription with a customizable hotkey",
                    ft.icons.MIC,
                ),
                self._build_feature_card(
                    "Local Processing",
                    "All processing happens on your device - no data leaves your computer",
                    ft.icons.SECURITY,
                ),
                self._build_feature_card(
                    "History",
                    "Access all your past transcriptions anytime",
                    ft.icons.HISTORY,
                ),
                self._build_feature_card(
                    "Multi-Language",
                    "Support for 90+ languages with automatic detection",
                    ft.icons.TRANSLATE,
                ),
                ft.Divider(height=SPACING.lg),
                ft.Text(
                    "Quick Start",
                    size=TYPOGRAPHY.title_large,
                    weight=ft.FontWeight.BOLD,
                    color=self._theme.colors.on_surface,
                ),
                ft.Text(
                    f"1. Press {self._hotkey.upper()} and start speaking\n"
                    f"2. Release to transcribe\n"
                    f"3. Copy or paste your text anywhere",
                    size=TYPOGRAPHY.body_medium,
                    color=self._theme.colors.on_surface_variant,
                ),
                ft.Divider(height=SPACING.md),
                ft.ElevatedButton(
                    "Start Interactive Tutorial",
                    icon=ft.icons.PLAY_ARROW,
                    on_click=lambda _: self._navigate_to_section(HelpSection.TUTORIAL),
                    style=ft.ButtonStyle(
                        bgcolor=self._theme.colors.primary,
                        color=self._theme.colors.on_primary,
                    ),
                ),
            ],
            spacing=SPACING.sm,
        )

    def _build_feature_card(self, title: str, description: str, icon: str) -> ft.Container:
        """Build a feature overview card."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=24, color=self._theme.colors.primary),
                        width=48,
                        height=48,
                        border_radius=BORDER_RADIUS.md,
                        bgcolor=self._theme.colors.primary_container,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                title,
                                size=TYPOGRAPHY.body_large,
                                weight=ft.FontWeight.MEDIUM,
                                color=self._theme.colors.on_surface,
                            ),
                            ft.Text(
                                description,
                                size=TYPOGRAPHY.body_small,
                                color=self._theme.colors.on_surface_variant,
                            ),
                        ],
                        spacing=SPACING.xs,
                    ),
                ],
                spacing=SPACING.md,
            ),
            padding=SPACING.md,
            bgcolor=self._theme.colors.surface_container_low,
            border_radius=BORDER_RADIUS.md,
        )

    def _build_faq_content(self) -> ft.Control:
        """Build the FAQ section content."""
        faq_cards = [FAQCard(faq) for faq in self.FAQ_ITEMS]

        return ft.Column(
            [
                ft.Text(
                    "Frequently Asked Questions",
                    size=TYPOGRAPHY.headline_medium,
                    weight=ft.FontWeight.BOLD,
                    color=self._theme.colors.on_surface,
                ),
                ft.Text(
                    "Click on any question to expand the answer",
                    size=TYPOGRAPHY.body_medium,
                    color=self._theme.colors.on_surface_variant,
                ),
                ft.Divider(height=SPACING.md),
                *faq_cards,
            ],
            spacing=SPACING.sm,
        )

    def _build_shortcuts_content(self) -> ft.Control:
        """Build the keyboard shortcuts section content."""
        # Group shortcuts by category
        categories = {}
        for shortcut in self._shortcuts:
            if shortcut.category not in categories:
                categories[shortcut.category] = []
            categories[shortcut.category].append(shortcut)

        # Build category sections
        category_sections = []
        for category, shortcuts in categories.items():
            shortcut_rows = [ShortcutRow(s) for s in shortcuts]

            category_sections.append(
                ft.Column(
                    [
                        ft.Text(
                            category,
                            size=TYPOGRAPHY.title_medium,
                            weight=ft.FontWeight.BOLD,
                            color=self._theme.colors.primary,
                        ),
                        ft.Container(height=SPACING.sm),
                        ft.Container(
                            content=ft.Column(shortcut_rows, spacing=SPACING.xs),
                            padding=SPACING.md,
                            bgcolor=self._theme.colors.surface_container_low,
                            border_radius=BORDER_RADIUS.md,
                        ),
                    ],
                    spacing=SPACING.sm,
                )
            )

        return ft.Column(
            [
                ft.Text(
                    "Keyboard Shortcuts",
                    size=TYPOGRAPHY.headline_medium,
                    weight=ft.FontWeight.BOLD,
                    color=self._theme.colors.on_surface,
                ),
                ft.Divider(height=SPACING.md),
                *category_sections,
            ],
            spacing=SPACING.md,
        )

    def _build_troubleshooting_content(self) -> ft.Control:
        """Build the troubleshooting section content."""
        trouble_cards = [TroubleshootingCard(item) for item in self.TROUBLESHOOTING_ITEMS]

        return ft.Column(
            [
                ft.Text(
                    "Troubleshooting",
                    size=TYPOGRAPHY.headline_medium,
                    weight=ft.FontWeight.BOLD,
                    color=self._theme.colors.on_surface,
                ),
                ft.Text(
                    "Common issues and their solutions",
                    size=TYPOGRAPHY.body_medium,
                    color=self._theme.colors.on_surface_variant,
                ),
                ft.Divider(height=SPACING.md),
                *trouble_cards,
            ],
            spacing=SPACING.sm,
        )

    def _build_tutorial_content(self) -> ft.Control:
        """Build the interactive tutorial section."""
        tutorial = InteractiveTutorial(
            on_complete=lambda: self._on_tutorial_complete(),
            on_skip=lambda: self._on_tutorial_skip(),
            hotkey=self._hotkey,
        )

        return ft.Column(
            [
                ft.Text(
                    "Interactive Tutorial",
                    size=TYPOGRAPHY.headline_medium,
                    weight=ft.FontWeight.BOLD,
                    color=self._theme.colors.on_surface,
                ),
                ft.Divider(height=SPACING.md),
                tutorial,
            ],
            spacing=SPACING.sm,
        )

    def _on_tutorial_complete(self):
        """Handle tutorial completion."""
        # Announce completion
        self._accessibility_manager.announce("Tutorial completed! You're ready to use faster-whisper-hotkey.")

        # Navigate to overview
        self._navigate_to_section(HelpSection.OVERVIEW)

    def _on_tutorial_skip(self):
        """Handle tutorial skip."""
        self._accessibility_manager.announce("Tutorial skipped. Explore the help panel for more information.")

        # Navigate to overview
        self._navigate_to_section(HelpSection.OVERVIEW)

    def _on_search(self, e):
        """Handle search input."""
        query = e.data.lower().strip()

        if not query:
            return

        # Search FAQ items
        results = []
        for faq in self.FAQ_ITEMS:
            if (
                query in faq.question.lower() or
                query in faq.answer.lower() or
                any(query in kw.lower() for kw in faq.keywords)
            ):
                results.append(faq)

        # Show results
        if results:
            self._content_column.controls = [
                ft.Text(
                    f"Search Results for '{e.data}'",
                    size=TYPOGRAPHY.title_large,
                    weight=ft.FontWeight.BOLD,
                    color=self._theme.colors.on_surface,
                ),
                ft.Text(
                    f"Found {len(results)} result(s)",
                    size=TYPOGRAPHY.body_small,
                    color=self._theme.colors.on_surface_variant,
                ),
                ft.Divider(height=SPACING.md),
                *[FAQCard(faq) for faq in results],
            ]
        else:
            self._content_column.controls = [
                ft.Text(
                    f"No results for '{e.data}'",
                    size=TYPOGRAPHY.title_large,
                    weight=ft.FontWeight.BOLD,
                    color=self._theme.colors.on_surface,
                ),
                ft.Text(
                    "Try different keywords or browse the categories below",
                    size=TYPOGRAPHY.body_medium,
                    color=self._theme.colors.on_surface_variant,
                ),
                ft.Divider(height=SPACING.md),
                ft.ElevatedButton(
                    "Browse All FAQ",
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda _: self._navigate_to_section(HelpSection.FAQ),
                ),
            ]

        if self.page:
            self.page.update()
