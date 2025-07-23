"""
File Selector Widget

Handles input file selection and output directory configuration for Layout A.
Features:
- Multi-file H2K selection with validation
- Output directory selection with smart defaults
- File validation with visual feedback
- Recent files history
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional
import os


class FileSelectorWidget(ctk.CTkFrame):
    """Widget for selecting input files and output directory."""
    
    def __init__(self, parent):
        super().__init__(parent, width=300)
        
        self.selected_files = []
        self.output_path = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the file selector interface."""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # File list should expand
        
        # Header
        self.header_label = ctk.CTkLabel(
            self, 
            text="📁 Input Files", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.header_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # File list frame
        self.file_list_frame = ctk.CTkFrame(self)
        self.file_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.file_list_frame.grid_columnconfigure(0, weight=1)
        self.file_list_frame.grid_rowconfigure(0, weight=1)
        
        # Scrollable file list
        self.file_list = ctk.CTkScrollableFrame(self.file_list_frame, height=200)
        self.file_list.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.file_list.grid_columnconfigure(0, weight=1)
        
        # File list placeholder
        self.placeholder_label = ctk.CTkLabel(
            self.file_list, 
            text="No files selected\\nDrag & drop H2K files here\\nor use Browse button",
            text_color="gray60"
        )
        self.placeholder_label.grid(row=0, column=0, pady=20)
        
        # File action buttons
        self.file_buttons_frame = ctk.CTkFrame(self.file_list_frame)
        self.file_buttons_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.file_buttons_frame.grid_columnconfigure(0, weight=1)
        self.file_buttons_frame.grid_columnconfigure(1, weight=1)
        
        self.browse_button = ctk.CTkButton(
            self.file_buttons_frame,
            text="Browse Files",
            command=self.browse_files
        )
        self.browse_button.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.clear_button = ctk.CTkButton(
            self.file_buttons_frame,
            text="Clear",
            command=self.clear_files
        )
        self.clear_button.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Output directory section
        self.output_label = ctk.CTkLabel(
            self,
            text="📂 Output Directory",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.output_label.grid(row=2, column=0, sticky="w", padx=10, pady=(15, 5))
        
        # Output directory frame
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        self.output_frame.grid_columnconfigure(0, weight=1)
        
        # Output directory entry
        self.output_entry = ctk.CTkEntry(
            self.output_frame,
            placeholder_text="Select output directory..."
        )
        self.output_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.output_browse_button = ctk.CTkButton(
            self.output_frame,
            text="📁",
            width=40,
            command=self.browse_output_directory
        )
        self.output_browse_button.grid(row=0, column=1, padx=5, pady=5)
        
        # File info section
        self.info_label = ctk.CTkLabel(
            self,
            text="ℹ️ File Information",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.info_label.grid(row=4, column=0, sticky="w", padx=10, pady=(15, 5))
        
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        self.info_text = ctk.CTkLabel(
            self.info_frame,
            text="Files selected: 0\\nTotal size: 0 MB",
            justify="left"
        )
        self.info_text.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
    def browse_files(self):
        """Browse and select H2K files."""
        files = filedialog.askopenfilenames(
            title="Select H2K Files",
            filetypes=[
                ("H2K files", "*.h2k"),
                ("All files", "*.*")
            ]
        )
        
        if files:
            self.add_files(files)
            
    def add_files(self, file_paths: List[str]):
        """Add files to the selection list."""
        valid_files = []
        invalid_files = []
        
        for file_path in file_paths:
            if self.validate_h2k_file(file_path):
                if file_path not in self.selected_files:
                    valid_files.append(file_path)
                    self.selected_files.append(file_path)
            else:
                invalid_files.append(file_path)
                
        # Update UI
        if valid_files:
            self.update_file_list()
            self.update_file_info()
            self.event_generate("<<FilesChanged>>")
            
            # Set default output path if not set
            if not self.output_path and valid_files:
                default_output = str(Path(valid_files[0]).parent / "output")
                self.set_output_path(default_output)
                
        # Show warnings for invalid files
        if invalid_files:
            invalid_names = [Path(f).name for f in invalid_files]
            messagebox.showwarning(
                "Invalid Files",
                f"The following files are not valid H2K files:\\n" +
                "\\n".join(invalid_names)
            )
            
    def validate_h2k_file(self, file_path: str) -> bool:
        """Validate that a file is a valid H2K file."""
        try:
            path = Path(file_path)
            
            # Check file exists
            if not path.exists():
                return False
                
            # Check file extension
            if path.suffix.lower() != '.h2k':
                return False
                
            # Check file is readable and not empty
            if path.stat().st_size == 0:
                return False
                
            # Basic content validation (check if it's XML-like)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                if not (first_line.startswith('<?xml') or first_line.startswith('<')):
                    return False
                    
            return True
            
        except Exception:
            return False
            
    def update_file_list(self):
        """Update the visual file list display."""
        # Clear existing file widgets
        for widget in self.file_list.winfo_children():
            if widget != self.placeholder_label:
                widget.destroy()
                
        # Hide placeholder if we have files
        if self.selected_files:
            self.placeholder_label.grid_remove()
            
            # Add file items
            for i, file_path in enumerate(self.selected_files):
                self.add_file_item(i, file_path)
        else:
            # Show placeholder
            self.placeholder_label.grid(row=0, column=0, pady=20)
            
    def add_file_item(self, index: int, file_path: str):
        """Add a file item to the list."""
        file_frame = ctk.CTkFrame(self.file_list)
        file_frame.grid(row=index, column=0, sticky="ew", padx=5, pady=2)
        file_frame.grid_columnconfigure(0, weight=1)
        
        # File info
        path = Path(file_path)
        file_size = path.stat().st_size / (1024 * 1024)  # MB
        
        # File name label
        name_label = ctk.CTkLabel(
            file_frame,
            text=path.name,
            font=ctk.CTkFont(weight="bold")
        )
        name_label.grid(row=0, column=0, sticky="w", padx=10, pady=2)
        
        # File details
        details_label = ctk.CTkLabel(
            file_frame,
            text=f"{file_size:.1f} MB • {path.parent.name}",
            text_color="gray60"
        )
        details_label.grid(row=1, column=0, sticky="w", padx=10, pady=2)
        
        # Remove button
        remove_button = ctk.CTkButton(
            file_frame,
            text="✕",
            width=30,
            height=30,
            command=lambda: self.remove_file(index)
        )
        remove_button.grid(row=0, column=1, rowspan=2, padx=10, pady=5)
        
        # Status indicator (checkmark for valid files)
        status_label = ctk.CTkLabel(
            file_frame,
            text="✓",
            text_color="green",
            font=ctk.CTkFont(size=16)
        )
        status_label.grid(row=0, column=2, rowspan=2, padx=5, pady=5)
        
    def remove_file(self, index: int):
        """Remove a file from the selection."""
        if 0 <= index < len(self.selected_files):
            self.selected_files.pop(index)
            self.update_file_list()
            self.update_file_info()
            self.event_generate("<<FilesChanged>>")
            
    def clear_files(self):
        """Clear all selected files."""
        self.selected_files.clear()
        self.update_file_list()
        self.update_file_info()
        self.event_generate("<<FilesChanged>>")
        
    def browse_output_directory(self):
        """Browse and select output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory"
        )
        
        if directory:
            self.set_output_path(directory)
            
    def set_output_path(self, path: str):
        """Set the output directory path."""
        self.output_path = path
        self.output_entry.delete(0, "end")
        self.output_entry.insert(0, path)
        
    def update_file_info(self):
        """Update file information display."""
        file_count = len(self.selected_files)
        
        if file_count == 0:
            info_text = "Files selected: 0\\nTotal size: 0 MB"
        else:
            # Calculate total size
            total_size = 0
            for file_path in self.selected_files:
                try:
                    total_size += Path(file_path).stat().st_size
                except:
                    pass
                    
            total_size_mb = total_size / (1024 * 1024)
            info_text = f"Files selected: {file_count}\\nTotal size: {total_size_mb:.1f} MB"
            
        self.info_text.configure(text=info_text)
        
    # Public interface methods
    def get_selected_files(self) -> List[str]:
        """Get list of selected file paths."""
        return self.selected_files.copy()
        
    def get_output_path(self) -> str:
        """Get the output directory path."""
        return self.output_entry.get().strip()
        
    def has_files(self) -> bool:
        """Check if any files are selected."""
        return len(self.selected_files) > 0
        
    def has_output_path(self) -> bool:
        """Check if output path is set."""
        return bool(self.get_output_path())