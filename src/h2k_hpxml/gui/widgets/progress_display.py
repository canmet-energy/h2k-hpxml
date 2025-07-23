"""
Progress Display Widget

Real-time feedback during conversion operations.
Features:
- Overall progress bar for batch operations
- Individual file progress tracking
- Current operation status display
- Cancel operation capability
"""

import customtkinter as ctk
from typing import Optional


class ProgressDisplayWidget(ctk.CTkFrame):
    """Widget for displaying conversion progress."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the progress display interface."""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        self.header_label = ctk.CTkLabel(
            self,
            text="📊 Progress",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.header_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Overall progress section
        self.overall_frame = ctk.CTkFrame(self)
        self.overall_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.overall_frame.grid_columnconfigure(1, weight=1)
        
        self.overall_label = ctk.CTkLabel(self.overall_frame, text="Overall:")
        self.overall_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.overall_progress = ctk.CTkProgressBar(self.overall_frame)
        self.overall_progress.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        self.overall_progress.set(0)
        
        self.overall_text = ctk.CTkLabel(self.overall_frame, text="0%")
        self.overall_text.grid(row=0, column=2, padx=10, pady=5)
        
        # Current file progress section
        self.current_frame = ctk.CTkFrame(self)
        self.current_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.current_frame.grid_columnconfigure(1, weight=1)
        
        self.current_label = ctk.CTkLabel(self.current_frame, text="Current:")
        self.current_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.current_progress = ctk.CTkProgressBar(self.current_frame)
        self.current_progress.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        self.current_progress.set(0)
        
        self.current_text = ctk.CTkLabel(self.current_frame, text="Ready")
        self.current_text.grid(row=0, column=2, padx=10, pady=5)
        
        # Status and control section
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        # Status message
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready to start conversion",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Control buttons
        self.control_frame = ctk.CTkFrame(self.status_frame)
        self.control_frame.grid(row=0, column=1, padx=10, pady=5)
        
        self.pause_button = ctk.CTkButton(
            self.control_frame,
            text="⏸️",
            width=40,
            command=self.pause_conversion,
            state="disabled"
        )
        self.pause_button.pack(side="left", padx=2)
        
        self.cancel_button = ctk.CTkButton(
            self.control_frame,
            text="⏹️",
            width=40,
            command=self.cancel_conversion,
            state="disabled"
        )
        self.cancel_button.pack(side="left", padx=2)
        
    def start_conversion(self):
        """Start conversion progress tracking."""
        self.overall_progress.set(0)
        self.current_progress.set(0)
        self.overall_text.configure(text="0%")
        self.current_text.configure(text="Starting...")
        self.status_label.configure(text="Initializing conversion...")
        
        # Enable control buttons
        self.pause_button.configure(state="normal")
        self.cancel_button.configure(state="normal")
        
    def update_overall_progress(self, percent: float, message: Optional[str] = None):
        """Update overall progress."""
        # Clamp percentage between 0 and 100
        percent = max(0, min(100, percent))
        
        # Update progress bar
        self.overall_progress.set(percent / 100)
        self.overall_text.configure(text=f"{percent:.0f}%")
        
        # Update message if provided
        if message:
            self.status_label.configure(text=message)
            
    def update_current_progress(self, percent: float, filename: Optional[str] = None):
        """Update current file progress."""
        # Clamp percentage between 0 and 100
        percent = max(0, min(100, percent))
        
        # Update progress bar
        self.current_progress.set(percent / 100)
        
        # Update filename display
        if filename:
            self.current_text.configure(text=f"{filename} ({percent:.0f}%)")
        else:
            self.current_text.configure(text=f"{percent:.0f}%")
            
    def set_status_message(self, message: str):
        """Set the status message."""
        self.status_label.configure(text=message)
        
    def complete_conversion(self, success: bool = True, message: Optional[str] = None):
        """Complete the conversion process."""
        if success:
            self.overall_progress.set(1.0)
            self.current_progress.set(1.0)
            self.overall_text.configure(text="100%")
            self.current_text.configure(text="Complete")
            self.status_label.configure(text=message or "Conversion completed successfully")
        else:
            self.status_label.configure(text=message or "Conversion failed")
            
        # Disable control buttons
        self.pause_button.configure(state="disabled")
        self.cancel_button.configure(state="disabled")
        
    def pause_conversion(self):
        """Handle pause button click."""
        # This will be connected to the main conversion controller
        if hasattr(self.master, 'pause_conversion'):
            self.master.pause_conversion()
        self.status_label.configure(text="Conversion paused")
        
    def cancel_conversion(self):
        """Handle cancel button click."""
        # This will be connected to the main conversion controller
        if hasattr(self.master, 'cancel_conversion'):
            self.master.cancel_conversion()
        self.status_label.configure(text="Cancelling conversion...")
        
    def reset_progress(self):
        """Reset progress display to initial state."""
        self.overall_progress.set(0)
        self.current_progress.set(0)
        self.overall_text.configure(text="0%")
        self.current_text.configure(text="Ready")
        self.status_label.configure(text="Ready to start conversion")
        
        # Disable control buttons
        self.pause_button.configure(state="disabled")
        self.cancel_button.configure(state="disabled")