"""
Analytics dashboard panel for faster-whisper-hotkey.

This module provides a comprehensive dashboard showing usage statistics including:
- Words transcribed today/week/month
- Estimated time saved vs typing
- Most-used applications
- Transcription accuracy
- Peak usage hours
- Charts and heatmaps

Classes
-------
AnalyticsPanel
    Main analytics dashboard window with charts and visualizations.

Notes
-----
Uses matplotlib for charting. Falls back gracefully if not available.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import logging

from .analytics import get_analytics_tracker, UsageStatistics
from .theme import ThemeManager

logger = logging.getLogger(__name__)

# Try to import matplotlib for charts
try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available - charts will be disabled")


class AnalyticsPanel:
    """Analytics dashboard showing usage statistics and visualizations."""

    def __init__(self, theme_manager: ThemeManager, on_close=None):
        """Initialize the analytics panel.

        Args:
            theme_manager: ThemeManager instance for styling
            on_close: Callback when panel is closed
        """
        self.theme_manager = theme_manager
        self.on_close = on_close
        self.window = None
        self.tracker = get_analytics_tracker()
        self.stats = None

    def show(self):
        """Show the analytics panel window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel()
        self.window.title("Usage Statistics Dashboard")
        self.window.geometry("900x700")
        self.window.minsize(700, 500)

        # Apply theme
        self._apply_theme()

        # Configure grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        # Main container with scroll
        main_container = ttk.Frame(self.window)
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(0, weight=1)

        # Canvas for scrolling
        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Mouse wheel binding
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Header
        header = ttk.Label(
            scrollable_frame,
            text="Usage Statistics Dashboard",
            font=("", 16, "bold")
        )
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        # Last updated label
        self.updated_label = ttk.Label(
            scrollable_frame,
            text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            font=("", 9),
            foreground="#666666"
        )
        self.updated_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        # Load and display statistics
        self._build_dashboard(scrollable_frame)

        # Refresh button
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=100, column=0, sticky="ew", padx=20, pady=(20, 10))

        ttk.Button(
            button_frame,
            text="Refresh Data",
            command=self._refresh_dashboard
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Clear All Analytics Data",
            command=self._clear_data
        ).pack(side=tk.LEFT)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _apply_theme(self):
        """Apply current theme to the window."""
        mode = self.theme_manager.current_mode
        if mode == "dark":
            bg_color = "#1e1e1e"
            fg_color = "#ffffff"
            self.window.configure(bg=bg_color)
            ttk.Style().theme_use('clam')
        else:
            bg_color = "#ffffff"
            fg_color = "#000000"
            self.window.configure(bg=bg_color)

    def _refresh_dashboard(self):
        """Refresh the dashboard with latest data."""
        if not self.window or not self.window.winfo_exists():
            return

        # Clear existing widgets
        for widget in self.window.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.destroy()

        # Rebuild dashboard
        self._build_dashboard(self.window)

        # Update timestamp
        self.updated_label.config(
            text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def _build_dashboard(self, parent):
        """Build the dashboard UI.

        Args:
            parent: Parent widget to build in
        """
        self.stats = self.tracker.get_statistics()
        summary = self.stats.get_summary_stats()

        row_idx = 2

        # Summary Stats Cards
        row_idx = self._build_summary_cards(parent, summary, row_idx)

        # Charts section
        if MATPLOTLIB_AVAILABLE:
            row_idx = self._build_charts_section(parent, row_idx)

        # App Usage Breakdown
        row_idx = self._build_app_usage(parent, row_idx)

        # Peak Hours
        row_idx = self._build_peak_hours(parent, row_idx)

    def _build_summary_cards(self, parent, summary, start_row):
        """Build summary statistics cards.

        Args:
            parent: Parent widget
            summary: Summary statistics dict
            start_row: Starting row index

        Returns:
            Next row index
        """
        # Cards frame
        cards_frame = ttk.Frame(parent)
        cards_frame.grid(row=start_row, column=0, sticky="ew", padx=20, pady=(0, 20))
        cards_frame.columnconfigure((0, 1, 2), weight=1)

        cards = [
            ("Words Today", f"{summary['words_today']:,}", "#4CAF50"),
            ("Words This Week", f"{summary['words_this_week']:,}", "#2196F3"),
            ("Words This Month", f"{summary['words_this_month']:,}", "#9C27B0"),
            ("Time Saved", f"{summary['time_saved_minutes']:.1f} min", "#FF9800"),
            ("Accuracy", f"{summary['accuracy_rate']:.1f}%", "#00BCD4"),
            ("All Time Words", f"{summary['words_all_time']:,}", "#607D8B"),
        ]

        for i, (title, value, color) in enumerate(cards):
            card = tk.Frame(cards_frame, bg=color, relief="flat", bd=0)
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=5, pady=5)

            tk.Label(
                card,
                text=title,
                bg=color,
                fg="white",
                font=("", 9)
            ).pack(pady=(8, 4))

            tk.Label(
                card,
                text=value,
                bg=color,
                fg="white",
                font=("", 18, "bold")
            ).pack(pady=(0, 8))

        return start_row + 2

    def _build_charts_section(self, parent, start_row):
        """Build charts section.

        Args:
            parent: Parent widget
            start_row: Starting row index

        Returns:
            Next row index
        """
        # Section header
        ttk.Label(
            parent,
            text="Words Per Day (Last 30 Days)",
            font=("", 12, "bold")
        ).grid(row=start_row, column=0, sticky="w", padx=20, pady=(20, 10))

        # Create chart
        chart_frame = ttk.Frame(parent)
        chart_frame.grid(row=start_row + 1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        self._create_words_per_day_chart(chart_frame)

        # Heatmap
        ttk.Label(
            parent,
            text="Usage by Hour (Last 7 Days)",
            font=("", 12, "bold")
        ).grid(row=start_row + 2, column=0, sticky="w", padx=20, pady=(20, 10))

        heatmap_frame = ttk.Frame(parent)
        heatmap_frame.grid(row=start_row + 3, column=0, sticky="nsew", padx=20, pady=(0, 20))

        self._create_hourly_heatmap(heatmap_frame)

        return start_row + 4

    def _create_words_per_day_chart(self, parent):
        """Create words per day chart.

        Args:
            parent: Parent widget
        """
        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(parent, text="Charts require matplotlib").pack()
            return

        data = self.stats.get_words_per_day(30)
        if not data:
            ttk.Label(parent, text="No data available yet").pack()
            return

        dates = [datetime.fromisoformat(d).date() for d, _ in data]
        counts = [c for _, c in data]

        fig = Figure(figsize=(8, 2.5), dpi=100)
        ax = fig.add_subplot(111)

        ax.plot(dates, counts, marker='o', linewidth=2, markersize=4, color='#2196F3')
        ax.fill_between(dates, counts, alpha=0.3, color='#2196F3')

        ax.set_xlabel("Date", fontsize=9)
        ax.set_ylabel("Words", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=8)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        fig.autofmt_xdate()

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_hourly_heatmap(self, parent):
        """Create hourly usage heatmap.

        Args:
            parent: Parent widget
        """
        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(parent, text="Charts require matplotlib").pack()
            return

        data = self.stats.get_hourly_heatmap_data(7)

        fig = Figure(figsize=(8, 2), dpi=100)
        ax = fig.add_subplot(111)

        hours = list(range(24))
        counts = [data[hour] for hour in hours]

        # Create bar chart
        if counts and max(counts) > 0:
            colors = plt.cm.YlGnBu([c / max(counts) for c in counts])
        else:
            colors = plt.cm.YlGnBu([0 for _ in counts])
        ax.bar(hours, counts, color=colors)

        ax.set_xlabel("Hour of Day", fontsize=9)
        ax.set_ylabel("Transcriptions", fontsize=9)
        ax.set_xticks(hours[::3])  # Show every 3rd hour
        ax.grid(True, alpha=0.3, axis='y')
        ax.tick_params(labelsize=8)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _build_app_usage(self, parent, start_row):
        """Build app usage breakdown section.

        Args:
            parent: Parent widget
            start_row: Starting row index

        Returns:
            Next row index
        """
        ttk.Label(
            parent,
            text="Most Used Applications",
            font=("", 12, "bold")
        ).grid(row=start_row, column=0, sticky="w", padx=20, pady=(20, 10))

        apps_frame = ttk.Frame(parent)
        apps_frame.grid(row=start_row + 1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        apps_frame.columnconfigure(0, weight=1)

        apps = self.stats.get_most_used_apps(10)
        if not apps:
            ttk.Label(apps_frame, text="No app usage data yet").pack()
        else:
            for i, (app_name, count) in enumerate(apps):
                # Progress bar with label
                row = ttk.Frame(apps_frame)
                row.grid(row=i, column=0, sticky="ew", pady=2)

                # Name and count
                label_text = f"{app_name}: {count} transcriptions"
                ttk.Label(row, text=label_text, font=("", 10)).pack(side=tk.LEFT)

                # Progress bar
                max_count = apps[0][1] if apps else 1
                progress = ttk.Progressbar(
                    row,
                    length=200,
                    mode='determinate',
                    maximum=max_count
                )
                progress.pack(side=tk.RIGHT, padx=(10, 0))
                progress['value'] = count

        return start_row + 2

    def _build_peak_hours(self, parent, start_row):
        """Build peak usage hours section.

        Args:
            parent: Parent widget
            start_row: Starting row index

        Returns:
            Next row index
        """
        ttk.Label(
            parent,
            text="Peak Usage Hours",
            font=("", 12, "bold")
        ).grid(row=start_row, column=0, sticky="w", padx=20, pady=(20, 10))

        hours_frame = ttk.Frame(parent)
        hours_frame.grid(row=start_row + 1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        peak_hours = self.stats.get_peak_usage_hours(5)
        if not peak_hours:
            ttk.Label(hours_frame, text="No usage data yet").pack()
        else:
            for hour, count in peak_hours:
                # Format hour as HH:00
                hour_str = f"{hour:02d}:00"
                ttk.Label(
                    hours_frame,
                    text=f"{hour_str} - {count} transcriptions",
                    font=("", 10)
                ).pack(anchor=tk.W, pady=2)

        return start_row + 2

    def _clear_data(self):
        """Clear all analytics data after confirmation."""
        from tkinter import messagebox

        response = messagebox.askyesno(
            "Clear Analytics Data",
            "Are you sure you want to clear all analytics data? This cannot be undone."
        )

        if response:
            self.tracker.clear_all_data()
            self._refresh_dashboard()
            messagebox.showinfo("Data Cleared", "All analytics data has been cleared.")

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


def show_analytics_panel(parent, theme_manager, on_close=None):
    """Show the analytics panel.

    Args:
        parent: Parent window
        theme_manager: ThemeManager instance
        on_close: Callback when panel is closed

    Returns:
        AnalyticsPanel instance
    """
    panel = AnalyticsPanel(theme_manager, on_close)
    panel.show()
    return panel
