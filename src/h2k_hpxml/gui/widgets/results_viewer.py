"""
Results Viewer Widget

Displays conversion results and simulation outputs with filtering and export capabilities.
Features:
- Real-time result updates during batch conversions
- Success/failure status indicators
- Detailed result information with expand/collapse
- Export functionality for results
- Quick actions for opening output files
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import sys


class ResultsViewerWidget(ctk.CTkFrame):
    """Widget for displaying conversion and simulation results."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.results = []
        self.filtered_results = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the results viewer interface."""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with controls
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="📊 Results",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.header_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Filter and action buttons
        self.controls_frame = ctk.CTkFrame(self.header_frame)
        self.controls_frame.grid(row=0, column=1, sticky="e", padx=10, pady=10)
        
        # Filter dropdown
        self.filter_var = ctk.StringVar(value="All")
        self.filter_menu = ctk.CTkOptionMenu(
            self.controls_frame,
            variable=self.filter_var,
            values=["All", "Success", "Failed", "In Progress"],
            command=self.filter_results
        )
        self.filter_menu.pack(side="left", padx=5)
        
        # Clear results button
        self.clear_btn = ctk.CTkButton(
            self.controls_frame,
            text="Clear",
            width=80,
            command=self.clear_results
        )
        self.clear_btn.pack(side="left", padx=5)
        
        # Export results button
        self.export_btn = ctk.CTkButton(
            self.controls_frame,
            text="Export",
            width=80,
            command=self.export_results
        )
        self.export_btn.pack(side="left", padx=5)
        
        # Results list frame
        self.results_frame = ctk.CTkFrame(self)
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(0, weight=1)
        
        # Scrollable results list
        self.results_list = ctk.CTkScrollableFrame(self.results_frame, height=200)
        self.results_list.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.results_list.grid_columnconfigure(0, weight=1)
        
        # Empty state
        self.empty_label = ctk.CTkLabel(
            self.results_list,
            text="No results yet\nConversion results will appear here",
            text_color="gray60"
        )
        self.empty_label.grid(row=0, column=0, pady=40)
        
    def add_result(self, result: Dict[str, Any]):
        """Add a conversion result to the display."""
        self.results.append(result)
        self.filtered_results = self.results.copy()
        self.update_results_display()
        
    def update_result(self, file_path: str, updates: Dict[str, Any]):
        """Update an existing result."""
        for result in self.results:
            if result.get('file') == file_path or result.get('input_path') == file_path:
                result.update(updates)
                break
        self.update_results_display()
        
    def clear_results(self):
        """Clear all results."""
        self.results.clear()
        self.filtered_results.clear()
        self.update_results_display()
        
    def filter_results(self, filter_type: str = None):
        """Filter results by status."""
        if filter_type is None:
            filter_type = self.filter_var.get()
            
        if filter_type == "All":
            self.filtered_results = self.results.copy()
        else:
            status_map = {
                "Success": ["success", "completed"],
                "Failed": ["error", "failed"],
                "In Progress": ["in_progress", "processing"]
            }
            target_statuses = status_map.get(filter_type, [])
            self.filtered_results = [
                r for r in self.results 
                if r.get('status', '').lower() in target_statuses
            ]
            
        self.update_results_display()
        
    def update_results_display(self):
        """Update the visual display of results."""
        # Clear existing result widgets
        for widget in self.results_list.winfo_children():
            if widget != self.empty_label:
                widget.destroy()
                
        # Show empty state if no results
        if not self.filtered_results:
            self.empty_label.grid(row=0, column=0, pady=40)
            return
        else:
            self.empty_label.grid_remove()
            
        # Add result items
        for i, result in enumerate(self.filtered_results):
            self.add_result_item(i, result)
            
    def add_result_item(self, index: int, result: Dict[str, Any]):
        """Add a result item to the display."""
        # Main result frame
        result_frame = ctk.CTkFrame(self.results_list)
        result_frame.grid(row=index, column=0, sticky="ew", padx=5, pady=3)
        result_frame.grid_columnconfigure(1, weight=1)
        
        # Status indicator
        status = result.get('status', 'unknown').lower()
        status_colors = {
            'success': 'green',
            'completed': 'green',
            'error': 'red',
            'failed': 'red',
            'in_progress': 'orange',
            'processing': 'orange'
        }
        status_icons = {
            'success': '✓',
            'completed': '✓',
            'error': '✗',
            'failed': '✗',
            'in_progress': '⏳',
            'processing': '⏳'
        }
        
        status_color = status_colors.get(status, 'gray')
        status_icon = status_icons.get(status, '?')
        
        status_label = ctk.CTkLabel(
            result_frame,
            text=status_icon,
            text_color=status_color,
            font=ctk.CTkFont(size=16, weight="bold"),
            width=30
        )
        status_label.grid(row=0, column=0, padx=10, pady=10)
        
        # File information
        info_frame = ctk.CTkFrame(result_frame)
        info_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # File name
        file_name = result.get('file', result.get('input_path', 'Unknown'))
        if isinstance(file_name, str):
            file_name = Path(file_name).name
            
        name_label = ctk.CTkLabel(
            info_frame,
            text=file_name,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_label.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 2))
        
        # Status message
        message = result.get('message', result.get('error', 'No message'))
        message_label = ctk.CTkLabel(
            info_frame,
            text=message,
            text_color="gray60"
        )
        message_label.grid(row=1, column=0, sticky="w", padx=10, pady=(2, 5))
        
        # Output path (if available)
        output_path = result.get('output_path')
        if output_path:
            output_label = ctk.CTkLabel(
                info_frame,
                text=f"Output: {Path(output_path).name}",
                text_color="gray50",
                font=ctk.CTkFont(size=12)
            )
            output_label.grid(row=2, column=0, sticky="w", padx=10, pady=(2, 5))
        
        # Action buttons
        if status in ['success', 'completed'] and output_path:
            actions_frame = ctk.CTkFrame(result_frame)
            actions_frame.grid(row=0, column=2, padx=10, pady=5)
            
            # Open output folder button
            open_folder_btn = ctk.CTkButton(
                actions_frame,
                text="📁",
                width=35,
                height=30,
                command=lambda p=output_path: self.open_output_folder(p)
            )
            open_folder_btn.pack(side="top", pady=2)
            
            # View details button
            details_btn = ctk.CTkButton(
                actions_frame,
                text="📄",
                width=35,
                height=30,
                command=lambda r=result: self.show_result_details(r)
            )
            details_btn.pack(side="top", pady=2)
            
    def open_output_folder(self, output_path: str):
        """Open the output folder in file explorer."""
        try:
            path = Path(output_path)
            if path.is_file():
                path = path.parent
                
            if sys.platform == "win32":
                subprocess.run(["explorer", str(path)])
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)])
            else:
                subprocess.run(["xdg-open", str(path)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")
            
    def show_result_details(self, result: Dict[str, Any]):
        """Show detailed result information in a popup."""
        details_window = ctk.CTkToplevel(self)
        details_window.title("Result Details")
        details_window.geometry("600x400")
        details_window.transient(self)
        details_window.grab_set()
        
        # Scrollable text widget for details
        text_frame = ctk.CTkFrame(details_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        details_text = ctk.CTkTextbox(text_frame)
        details_text.pack(fill="both", expand=True)
        
        # Format result details
        details = []
        details.append(f"File: {result.get('file', 'Unknown')}")
        details.append(f"Status: {result.get('status', 'Unknown')}")
        details.append(f"Message: {result.get('message', 'No message')}")
        
        if result.get('output_path'):
            details.append(f"Output Path: {result.get('output_path')}")
        if result.get('processing_time'):
            details.append(f"Processing Time: {result.get('processing_time'):.2f}s")
        if result.get('file_size'):
            details.append(f"File Size: {result.get('file_size')} bytes")
            
        # Add any additional details
        for key, value in result.items():
            if key not in ['file', 'status', 'message', 'output_path', 'processing_time', 'file_size']:
                details.append(f"{key.replace('_', ' ').title()}: {value}")
                
        details_text.insert("1.0", "\n".join(details))
        details_text.configure(state="disabled")
        
        # Close button
        close_btn = ctk.CTkButton(
            details_window,
            text="Close",
            command=details_window.destroy
        )
        close_btn.pack(pady=10)
        
    def export_results(self):
        """Export results to a file."""
        if not self.filtered_results:
            messagebox.showwarning("No Results", "No results to export.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("Text files", "*.txt")
            ]
        )
        
        if not file_path:
            return
            
        try:
            if file_path.endswith('.csv'):
                self._export_csv(file_path)
            elif file_path.endswith('.json'):
                self._export_json(file_path)
            else:
                self._export_text(file_path)
                
            messagebox.showinfo("Export Complete", f"Results exported to {Path(file_path).name}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")
            
    def _export_csv(self, file_path: str):
        """Export results as CSV."""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if not self.filtered_results:
                return
                
            # Get all unique keys from results
            all_keys = set()
            for result in self.filtered_results:
                all_keys.update(result.keys())
                
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(self.filtered_results)
            
    def _export_json(self, file_path: str):
        """Export results as JSON."""
        import json
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.filtered_results, f, indent=2, default=str)
            
    def _export_text(self, file_path: str):
        """Export results as text."""
        with open(file_path, 'w', encoding='utf-8') as f:
            for i, result in enumerate(self.filtered_results):
                f.write(f"Result {i + 1}:\n")
                for key, value in result.items():
                    f.write(f"  {key.replace('_', ' ').title()}: {value}\n")
                f.write("\n")
                
    def get_results_summary(self) -> Dict[str, int]:
        """Get summary statistics of results."""
        summary = {
            'total': len(self.results),
            'success': 0,
            'failed': 0,
            'in_progress': 0
        }
        
        for result in self.results:
            status = result.get('status', '').lower()
            if status in ['success', 'completed']:
                summary['success'] += 1
            elif status in ['error', 'failed']:
                summary['failed'] += 1
            elif status in ['in_progress', 'processing']:
                summary['in_progress'] += 1
                
        return summary