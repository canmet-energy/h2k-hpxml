"""
Status Bar Widget

Provides real-time status information and system monitoring at the bottom of the application.
Features:
- Current operation status
- File count and progress indicators
- Memory and CPU usage monitoring
- Connection status for dependencies
- Quick access to settings and help
"""

import customtkinter as ctk
import threading
import time
import psutil
from typing import Optional


class StatusBarWidget(ctk.CTkFrame):
    """Status bar widget for showing application status and system information."""
    
    def __init__(self, parent):
        super().__init__(parent, height=30)
        
        self.pack_propagate(False)
        self.current_status = "Ready"
        self.monitoring_enabled = True
        
        self.setup_ui()
        self.start_monitoring()
        
    def setup_ui(self):
        """Setup the status bar interface."""
        # Main status label
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Separator
        separator1 = ctk.CTkLabel(self, text="|", text_color="gray50")
        separator1.pack(side="left", padx=5)
        
        # File count indicator
        self.file_count_label = ctk.CTkLabel(
            self,
            text="Files: 0",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        self.file_count_label.pack(side="left", padx=5)
        
        # Progress indicator (hidden by default)
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        # Don't pack initially - will be shown during operations
        
        # Right side elements
        
        # Memory usage
        self.memory_label = ctk.CTkLabel(
            self,
            text="Memory: --",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        self.memory_label.pack(side="right", padx=5)
        
        # CPU usage
        self.cpu_label = ctk.CTkLabel(
            self,
            text="CPU: --%",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        self.cpu_label.pack(side="right", padx=5)
        
        # Separator
        separator2 = ctk.CTkLabel(self, text="|", text_color="gray50")
        separator2.pack(side="right", padx=5)
        
        # Dependency status indicator
        self.deps_status = ctk.CTkLabel(
            self,
            text="🔴",  # Red circle for unknown status
            font=ctk.CTkFont(size=12)
        )
        self.deps_status.pack(side="right", padx=5)
        
        # Create tooltip for dependency status
        self.create_tooltip(self.deps_status, "Dependency Status: Click to check")
        self.deps_status.bind("<Button-1>", self.check_dependencies)
        
    def create_tooltip(self, widget, text):
        """Create a simple tooltip for a widget."""
        def on_enter(event):
            tooltip = ctk.CTkToplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ctk.CTkLabel(tooltip, text=text, font=ctk.CTkFont(size=10))
            label.pack()
            
            def on_leave():
                tooltip.destroy()
                
            widget.bind("<Leave>", lambda e: on_leave())
            tooltip.after(3000, on_leave)  # Auto-hide after 3 seconds
            
        widget.bind("<Enter>", on_enter)
        
    def set_status(self, status: str, temporary: bool = False):
        """Set the main status text."""
        self.current_status = status
        self.status_label.configure(text=status)
        
        # If temporary, reset after 3 seconds
        if temporary:
            self.after(3000, lambda: self.set_status("Ready"))
            
    def set_file_count(self, count: int):
        """Update the file count display."""
        self.file_count_label.configure(text=f"Files: {count}")
        
    def show_progress(self, current: int, total: int, operation: str = "Processing"):
        """Show progress indicator."""
        progress_text = f"{operation}: {current}/{total} ({current/total*100:.0f}%)"
        self.progress_label.configure(text=progress_text)
        
        if not self.progress_label.winfo_viewable():
            self.progress_label.pack(side="left", padx=5, after=self.file_count_label)
            
    def hide_progress(self):
        """Hide progress indicator."""
        if self.progress_label.winfo_viewable():
            self.progress_label.pack_forget()
            
    def start_monitoring(self):
        """Start system monitoring in background thread."""
        def monitor():
            while self.monitoring_enabled:
                try:
                    # Update CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.after(0, lambda: self.cpu_label.configure(text=f"CPU: {cpu_percent:.0f}%"))
                    
                    # Update memory usage
                    memory = psutil.virtual_memory()
                    memory_mb = memory.used / (1024 * 1024)
                    memory_text = f"Memory: {memory_mb:.0f}MB"
                    self.after(0, lambda: self.memory_label.configure(text=memory_text))
                    
                    # Check if memory usage is high (>80%)
                    if memory.percent > 80:
                        self.after(0, lambda: self.memory_label.configure(text_color="orange"))
                    elif memory.percent > 90:
                        self.after(0, lambda: self.memory_label.configure(text_color="red"))
                    else:
                        self.after(0, lambda: self.memory_label.configure(text_color="gray60"))
                        
                except Exception:
                    # If monitoring fails, just continue
                    time.sleep(2)
                    
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring_enabled = False
        
    def check_dependencies(self, event=None):
        """Check dependency status and update indicator."""
        def check_deps():
            try:
                # This would integrate with the dependency manager
                # For now, simulate the check
                from pathlib import Path
                
                # Check for OpenStudio-HPXML
                hpxml_path = Path("/OpenStudio-HPXML/")
                hpxml_ok = hpxml_path.exists()
                
                # Check for OpenStudio Python bindings
                try:
                    import openstudio
                    os_ok = True
                except ImportError:
                    os_ok = False
                    
                # Update status indicator
                if hpxml_ok and os_ok:
                    status = "🟢"  # Green - all good
                    tooltip_text = "Dependencies: All OK"
                elif hpxml_ok or os_ok:
                    status = "🟡"  # Yellow - partial
                    tooltip_text = "Dependencies: Partial (some missing)"
                else:
                    status = "🔴"  # Red - missing
                    tooltip_text = "Dependencies: Missing (click to install)"
                    
                self.after(0, lambda: self.update_deps_status(status, tooltip_text))
                
            except Exception as e:
                self.after(0, lambda: self.update_deps_status("🔴", f"Dependencies: Error checking ({str(e)})"))
                
        # Run check in background
        check_thread = threading.Thread(target=check_deps, daemon=True)
        check_thread.start()
        
    def update_deps_status(self, status: str, tooltip_text: str):
        """Update dependency status indicator."""
        self.deps_status.configure(text=status)
        
        # Update tooltip
        # Remove old bindings
        self.deps_status.unbind("<Enter>")
        self.deps_status.unbind("<Button-1>")
        
        # Create new tooltip and click handler
        self.create_tooltip(self.deps_status, tooltip_text)
        self.deps_status.bind("<Button-1>", self.check_dependencies)
        
    def set_operation_status(self, operation: str, progress: Optional[float] = None):
        """Set status for long-running operations."""
        if progress is not None:
            status_text = f"{operation} ({progress:.0f}%)"
        else:
            status_text = operation
            
        self.set_status(status_text)
        
    def flash_status(self, message: str, color: str = "orange"):
        """Flash a temporary status message."""
        original_color = self.status_label.cget("text_color")
        
        self.status_label.configure(text=message, text_color=color)
        self.after(2000, lambda: self.status_label.configure(
            text=self.current_status, 
            text_color=original_color
        ))
        
    def show_error(self, error_message: str):
        """Show an error status."""
        self.set_status(f"Error: {error_message}")
        self.status_label.configure(text_color="red")
        self.after(5000, lambda: self.status_label.configure(text_color="gray90"))
        
    def show_success(self, success_message: str):
        """Show a success status."""
        self.set_status(success_message)
        self.status_label.configure(text_color="green")
        self.after(3000, lambda: self.status_label.configure(text_color="gray90"))
        
    def destroy(self):
        """Clean up monitoring thread before destroying."""
        self.stop_monitoring()
        super().destroy()