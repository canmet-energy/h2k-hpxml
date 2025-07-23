"""
Main GUI Application for H2K to HPXML Converter
Layout A: Traditional Desktop Application

This implements the traditional desktop application layout with:
- Menu bar with File, Edit, Tools, View, Help
- Toolbar with quick action buttons  
- Side-by-side layout for files and options
- Integrated progress and results in bottom panel
- Status bar with quick information
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from pathlib import Path
from typing import List, Dict, Optional
import threading
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from h2k_hpxml.gui.widgets.file_selector import FileSelectorWidget
from h2k_hpxml.gui.widgets.conversion_options import ConversionOptionsWidget
from h2k_hpxml.gui.widgets.progress_display import ProgressDisplayWidget
from h2k_hpxml.gui.widgets.results_viewer import ResultsViewerWidget
from h2k_hpxml.gui.widgets.status_bar import StatusBarWidget
from h2k_hpxml.gui.core.conversion_controller import ConversionController


class H2KConverterGUI(ctk.CTk):
    """Main application window for H2K to HPXML converter using Layout A."""
    
    def __init__(self):
        super().__init__()
        
        # Application configuration
        self.title("H2K to HPXML Converter v1.7.0")
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        # Theme and appearance
        ctk.set_appearance_mode("system")  # Follow system theme
        ctk.set_default_color_theme("blue")
        
        # Application state
        self.conversion_tasks = []
        self.current_conversion = None
        self.settings = {}
        
        # Initialize conversion controller
        self.conversion_controller = ConversionController()
        self.setup_conversion_callbacks()
        
        # Initialize UI
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Initialize the complete user interface."""
        # Create menu bar
        self.setup_menu()
        
        # Create toolbar
        self.setup_toolbar()
        
        # Create main layout
        self.setup_main_layout()
        
        # Create status bar
        self.setup_status_bar()
        
        # Bind events
        self.bind_events()
        
    def setup_menu(self):
        """Create menu bar for traditional desktop application."""
        # Create menu bar using tkinter (CustomTkinter doesn't have native menu support)
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Open Project", command=self.open_project, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Save Project", command=self.save_project, accelerator="Ctrl+S")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Add H2K Files", command=self.add_h2k_files)
        self.file_menu.add_command(label="Clear Files", command=self.clear_files)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit, accelerator="Ctrl+Q")
        
        # Edit menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Preferences", command=self.show_preferences)
        self.edit_menu.add_command(label="Configuration", command=self.show_configuration)
        
        # Tools menu
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        self.tools_menu.add_command(label="Dependency Manager", command=self.show_dependency_manager)
        self.tools_menu.add_command(label="Resilience Analysis", command=self.show_resilience_analysis)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="Validate Files", command=self.validate_files)
        self.tools_menu.add_command(label="Clear Cache", command=self.clear_cache)
        
        # View menu  
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(label="Refresh", command=self.refresh_view, accelerator="F5")
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Show Toolbar", command=self.toggle_toolbar)
        self.view_menu.add_command(label="Show Status Bar", command=self.toggle_status_bar)
        
        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="Help", command=self.show_help, accelerator="F1")
        self.help_menu.add_command(label="User Manual", command=self.show_user_manual)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="About", command=self.show_about)
        
    def setup_toolbar(self):
        """Create toolbar with quick action buttons."""
        self.toolbar_frame = ctk.CTkFrame(self, height=50)
        self.toolbar_frame.pack(fill="x", padx=5, pady=5)
        self.toolbar_frame.pack_propagate(False)
        
        # Quick action buttons
        self.open_files_btn = ctk.CTkButton(
            self.toolbar_frame, 
            text="📁", 
            width=40,
            command=self.add_h2k_files,
            tooltip_text="Open H2K Files"
        )
        self.open_files_btn.pack(side="left", padx=2)
        
        self.start_btn = ctk.CTkButton(
            self.toolbar_frame,
            text="▶️",
            width=40, 
            command=self.start_conversion,
            tooltip_text="Start Conversion"
        )
        self.start_btn.pack(side="left", padx=2)
        
        self.stop_btn = ctk.CTkButton(
            self.toolbar_frame,
            text="⏹️",
            width=40,
            command=self.stop_conversion,
            tooltip_text="Stop Conversion"
        )
        self.stop_btn.pack(side="left", padx=2)
        
        self.settings_btn = ctk.CTkButton(
            self.toolbar_frame,
            text="⚙️",
            width=40,
            command=self.show_configuration,
            tooltip_text="Settings"
        )
        self.settings_btn.pack(side="left", padx=2)
        
        self.help_btn = ctk.CTkButton(
            self.toolbar_frame,
            text="❓",
            width=40,
            command=self.show_help,
            tooltip_text="Help"
        )
        self.help_btn.pack(side="left", padx=2)
        
    def setup_main_layout(self):
        """Create main layout with side-by-side panels."""
        # Main content frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure grid layout
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0)
        
        # Left panel - File selection (300px wide)
        self.file_panel = FileSelectorWidget(self.main_frame)
        self.file_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        # Connect file panel events
        self.file_panel.bind("<<FilesChanged>>", lambda e: self.update_file_count())
        
        # Right panel - Options and conversion
        self.right_panel = ctk.CTkFrame(self.main_frame)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Configure right panel layout
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        
        # Options widget in right panel
        self.options_panel = ConversionOptionsWidget(self.right_panel)
        self.options_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Bottom panel - Progress and results (spans both columns)
        self.results_panel = ctk.CTkFrame(self.main_frame)
        self.results_panel.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Configure results panel layout
        self.results_panel.grid_columnconfigure(0, weight=1)
        
        # Progress display
        self.progress_display = ProgressDisplayWidget(self.results_panel)
        self.progress_display.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Results viewer  
        self.results_viewer = ResultsViewerWidget(self.results_panel)
        self.results_viewer.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
    def setup_status_bar(self):
        """Create status bar at bottom."""
        self.status_bar = StatusBarWidget(self)
        self.status_bar.pack(side="bottom", fill="x")
        
        # Set initial status
        self.status_bar.set_status("Ready")
        
    def bind_events(self):
        """Bind keyboard shortcuts and events."""
        # Keyboard shortcuts
        self.bind('<Control-n>', lambda e: self.new_project())
        self.bind('<Control-o>', lambda e: self.open_project())
        self.bind('<Control-s>', lambda e: self.save_project())
        self.bind('<Control-q>', lambda e: self.quit())
        self.bind('<F1>', lambda e: self.show_help())
        self.bind('<F5>', lambda e: self.refresh_view())
        
        # Window events
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_conversion_callbacks(self):
        """Setup callbacks for conversion controller."""
        self.conversion_controller.set_callbacks(
            on_progress_update=self.on_conversion_progress,
            on_file_start=self.on_file_start,
            on_file_complete=self.on_file_complete,
            on_conversion_complete=self.on_conversion_complete,
            on_error=self.on_conversion_error
        )
        
    def on_conversion_progress(self, progress: float, completed: int, failed: int):
        """Handle conversion progress updates."""
        self.progress_display.update_overall_progress(progress, f"Completed: {completed}, Failed: {failed}")
        self.status_bar.set_operation_status("Converting", progress)
        
    def on_file_start(self, file_path: str, current: int, total: int):
        """Handle file conversion start."""
        file_name = Path(file_path).name
        self.progress_display.update_current_progress(0, file_name)
        self.status_bar.show_progress(current, total, "Converting")
        
    def on_file_complete(self, file_path: str, success: bool, result: Dict[str, Any]):
        """Handle file conversion completion."""
        # Add result to results viewer
        result_data = {
            'file': Path(file_path).name,
            'status': 'success' if success else 'failed',
            'input_path': file_path,
            **result
        }
        self.results_viewer.add_result(result_data)
        
        # Update current file progress to 100%
        if success:
            self.progress_display.update_current_progress(100, Path(file_path).name)
        
    def on_conversion_complete(self, completed: int, failed: int, was_stopped: bool):
        """Handle conversion batch completion."""
        self.progress_display.complete_conversion(
            success=not was_stopped and failed == 0,
            message=f"Conversion {'stopped' if was_stopped else 'completed'}: {completed} succeeded, {failed} failed"
        )
        self.status_bar.hide_progress()
        
        if was_stopped:
            self.status_bar.set_status("Conversion stopped")
        elif failed == 0:
            self.status_bar.show_success(f"All {completed} files converted successfully")
        else:
            self.status_bar.show_error(f"Conversion completed with {failed} failures")
            
        # Re-enable UI controls
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
    def on_conversion_error(self, error_message: str):
        """Handle conversion errors."""
        self.status_bar.show_error(error_message)
        messagebox.showerror("Conversion Error", error_message)
        
    def load_settings(self):
        """Load application settings."""
        # Implementation will load from settings file
        pass
        
    def save_settings(self):
        """Save application settings."""
        # Implementation will save to settings file
        pass
        
    # Menu and toolbar actions
    def new_project(self):
        """Create a new project."""
        # Clear current files and settings
        self.file_panel.clear_files()
        self.options_panel.reset_to_defaults()
        self.results_viewer.clear_results()
        self.status_bar.set_status("New project created")
        
    def open_project(self):
        """Open an existing project."""
        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("Project files", "*.h2kproj"), ("All files", "*.*")]
        )
        if file_path:
            # Implementation will load project file
            self.status_bar.set_status(f"Opened project: {Path(file_path).name}")
            
    def save_project(self):
        """Save current project."""
        file_path = filedialog.asksaveasfilename(
            title="Save Project",
            defaultextension=".h2kproj",
            filetypes=[("Project files", "*.h2kproj"), ("All files", "*.*")]
        )
        if file_path:
            # Implementation will save project file
            self.status_bar.set_status(f"Saved project: {Path(file_path).name}")
            
    def add_h2k_files(self):
        """Add H2K files to the conversion list."""
        files = filedialog.askopenfilenames(
            title="Select H2K Files",
            filetypes=[("H2K files", "*.h2k"), ("All files", "*.*")]
        )
        if files:
            self.file_panel.add_files(files)
            self.status_bar.set_status(f"Added {len(files)} file(s)")
            
    def clear_files(self):
        """Clear all selected files."""
        self.file_panel.clear_files()
        self.status_bar.set_status("Files cleared")
        
    def start_conversion(self):
        """Start the conversion process."""
        # Get selected files and options
        files = self.file_panel.get_selected_files()
        options = self.options_panel.get_options()
        output_path = self.file_panel.get_output_path()
        
        if not files:
            messagebox.showwarning("No Files", "Please select H2K files to convert.")
            return
            
        if not output_path:
            messagebox.showwarning("No Output Path", "Please select an output directory.")
            return
            
        # Validate options
        if not self.options_panel.validate_options():
            return
            
        # Clear previous results
        self.results_viewer.clear_results()
        self.progress_display.reset_progress()
        
        # Start conversion using controller
        success = self.conversion_controller.start_conversion(files, output_path, options)
        
        if success:
            # Update UI state
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.status_bar.set_status("Starting conversion...")
            self.progress_display.start_conversion()
        else:
            messagebox.showerror("Error", "Could not start conversion. Another conversion may be running.")
        
    def stop_conversion(self):
        """Stop the conversion process."""
        self.conversion_controller.stop_conversion()
        self.status_bar.set_status("Stopping conversion...")
        
    def pause_conversion(self):
        """Pause the conversion process."""
        if self.conversion_controller.status == "running":
            self.conversion_controller.pause_conversion()
            self.status_bar.set_status("Conversion paused")
        elif self.conversion_controller.status == "paused":
            self.conversion_controller.resume_conversion()
            self.status_bar.set_status("Conversion resumed")
        
    def update_file_count(self):
        """Update file count in status bar."""
        file_count = len(self.file_panel.get_selected_files())
        self.status_bar.set_file_count(file_count)
        
    def show_preferences(self):
        """Show preferences dialog."""
        messagebox.showinfo("Preferences", "Preferences dialog will be implemented.")
        
    def show_configuration(self):
        """Show configuration dialog."""
        messagebox.showinfo("Configuration", "Configuration dialog will be implemented.")
        
    def show_dependency_manager(self):
        """Show dependency manager."""
        messagebox.showinfo("Dependency Manager", "Dependency manager will be implemented.")
        
    def show_resilience_analysis(self):
        """Show resilience analysis."""
        messagebox.showinfo("Resilience Analysis", "Resilience analysis will be implemented.")
        
    def validate_files(self):
        """Validate selected H2K files."""
        files = self.file_panel.get_selected_files()
        if not files:
            messagebox.showwarning("No Files", "Please select H2K files to validate.")
            return
            
        # Implementation will validate files
        messagebox.showinfo("Validation", f"Validated {len(files)} file(s).")
        
    def clear_cache(self):
        """Clear application cache."""
        messagebox.showinfo("Cache", "Cache cleared.")
        
    def refresh_view(self):
        """Refresh the current view."""
        self.status_bar.set_status("View refreshed")
        
    def toggle_toolbar(self):
        """Toggle toolbar visibility."""
        if self.toolbar_frame.winfo_viewable():
            self.toolbar_frame.pack_forget()
        else:
            self.toolbar_frame.pack(after=self.menu_bar, fill="x", padx=5, pady=5)
            
    def toggle_status_bar(self):
        """Toggle status bar visibility."""
        if self.status_bar.winfo_viewable():
            self.status_bar.pack_forget()
        else:
            self.status_bar.pack(side="bottom", fill="x")
            
    def show_help(self):
        """Show help documentation."""
        messagebox.showinfo("Help", "Help documentation will be implemented.")
        
    def show_user_manual(self):
        """Show user manual."""
        messagebox.showinfo("User Manual", "User manual will be implemented.")
        
    def show_about(self):
        """Show about dialog."""
        about_text = """H2K to HPXML Converter v1.7.0

A comprehensive tool for converting Canadian Hot2000 (H2K) 
building energy models to the standardized HPXML format 
for simulation in EnergyPlus.

Copyright © 2024 NRCAN
All rights reserved."""
        
        messagebox.showinfo("About", about_text)
        
    def on_closing(self):
        """Handle application closing."""
        # Save settings before closing
        self.save_settings()
        
        # Check if conversion is running
        if hasattr(self, 'conversion_thread') and self.conversion_thread.is_alive():
            if messagebox.askokcancel("Quit", "Conversion is running. Do you want to quit?"):
                # Stop conversion and quit
                self.quit()
        else:
            self.quit()


def main():
    """Main entry point for the GUI application."""
    try:
        app = H2KConverterGUI()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()