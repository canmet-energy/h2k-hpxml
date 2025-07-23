"""
Conversion Options Widget

Provides comprehensive control over conversion and simulation settings.
Features:
- Basic/Advanced view toggle
- All CLI options accessible through GUI
- Settings presets (Quick, Standard, Advanced)
- Real-time validation of option combinations
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any
import json
from pathlib import Path


class ConversionOptionsWidget(ctk.CTkFrame):
    """Widget for configuring conversion and simulation options."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Default options based on CLI defaults
        self.options = {
            # Simulation options
            'run_simulation': True,
            'add_component_loads': True,
            'debug_mode': False,
            
            # Output options
            'timestep_all': False,
            'timestep_total': True,
            'timestep_fuels': True,
            'timestep_end_uses': False,
            'timestep_emissions': False,
            'timestep_hot_water': False,
            'timestep_loads': False,
            'timestep_component_loads': False,
            'timestep_unmets': False,
            'timestep_temperatures': False,
            
            'daily_all': False,
            'daily_total': False,
            'daily_fuels': False,
            'daily_end_uses': False,
            'daily_emissions': False,
            'daily_hot_water': False,
            'daily_loads': False,
            'daily_component_loads': False,
            'daily_unmets': False,
            'daily_temperatures': False,
            
            'hourly_all': False,
            'hourly_total': False,
            'hourly_fuels': False,
            'hourly_end_uses': False,
            'hourly_emissions': False,
            'hourly_hot_water': False,
            'hourly_loads': False,
            'hourly_component_loads': False,
            'hourly_unmets': False,
            'hourly_temperatures': False,
            
            'monthly_all': False,
            'monthly_total': False,
            'monthly_fuels': False,
            'monthly_end_uses': False,
            'monthly_emissions': False,
            'monthly_hot_water': False,
            'monthly_loads': False,
            'monthly_component_loads': False,
            'monthly_unmets': False,
            'monthly_temperatures': False,
            
            # Validation options
            'skip_validation': False,
            
            # Performance options
            'max_parallel': 4
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the conversion options interface."""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with preset buttons
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.header_frame.grid_columnconfigure(3, weight=1)
        
        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="⚙️ Conversion Options",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.header_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Preset buttons
        self.quick_preset_btn = ctk.CTkButton(
            self.header_frame,
            text="Quick",
            width=80,
            command=lambda: self.apply_preset("quick")
        )
        self.quick_preset_btn.grid(row=0, column=1, padx=5, pady=10)
        
        self.standard_preset_btn = ctk.CTkButton(
            self.header_frame,
            text="Standard", 
            width=80,
            command=lambda: self.apply_preset("standard")
        )
        self.standard_preset_btn.grid(row=0, column=2, padx=5, pady=10)
        
        self.advanced_preset_btn = ctk.CTkButton(
            self.header_frame,
            text="Advanced",
            width=80,
            command=lambda: self.apply_preset("advanced")
        )
        self.advanced_preset_btn.grid(row=0, column=3, padx=5, pady=10)
        
        # Main options frame with tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create tabs
        self.basic_tab = self.tabview.add("Basic")
        self.output_tab = self.tabview.add("Output")
        self.advanced_tab = self.tabview.add("Advanced")
        
        # Setup tab contents
        self.setup_basic_tab()
        self.setup_output_tab()
        self.setup_advanced_tab()
        
        # Select basic tab by default
        self.tabview.set("Basic")
        
    def setup_basic_tab(self):
        """Setup basic simulation options."""
        # Simulation settings
        sim_frame = ctk.CTkFrame(self.basic_tab)
        sim_frame.pack(fill="x", padx=10, pady=10)
        
        sim_label = ctk.CTkLabel(
            sim_frame,
            text="Simulation Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        sim_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Run simulation checkbox
        self.run_simulation_var = ctk.BooleanVar(value=self.options['run_simulation'])
        self.run_simulation_cb = ctk.CTkCheckBox(
            sim_frame,
            text="Run OpenStudio Simulation",
            variable=self.run_simulation_var,
            command=self.on_option_changed
        )
        self.run_simulation_cb.pack(anchor="w", padx=20, pady=2)
        
        # Add component loads checkbox
        self.component_loads_var = ctk.BooleanVar(value=self.options['add_component_loads'])
        self.component_loads_cb = ctk.CTkCheckBox(
            sim_frame,
            text="Add Component Loads",
            variable=self.component_loads_var,
            command=self.on_option_changed
        )
        self.component_loads_cb.pack(anchor="w", padx=20, pady=2)
        
        # Debug mode checkbox
        self.debug_mode_var = ctk.BooleanVar(value=self.options['debug_mode'])
        self.debug_mode_cb = ctk.CTkCheckBox(
            sim_frame,
            text="Debug Mode (Keep intermediate files)",
            variable=self.debug_mode_var,
            command=self.on_option_changed
        )
        self.debug_mode_cb.pack(anchor="w", padx=20, pady=(2, 10))
        
        # Quick output settings
        output_frame = ctk.CTkFrame(self.basic_tab)
        output_frame.pack(fill="x", padx=10, pady=10)
        
        output_label = ctk.CTkLabel(
            output_frame,
            text="Quick Output Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        output_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Timestep outputs
        timestep_frame = ctk.CTkFrame(output_frame)
        timestep_frame.pack(fill="x", padx=10, pady=5)
        
        timestep_label = ctk.CTkLabel(timestep_frame, text="Timestep Outputs:")
        timestep_label.pack(anchor="w", padx=10, pady=5)
        
        timestep_buttons_frame = ctk.CTkFrame(timestep_frame)
        timestep_buttons_frame.pack(fill="x", padx=10, pady=5)
        
        self.timestep_total_var = ctk.BooleanVar(value=self.options['timestep_total'])
        self.timestep_total_cb = ctk.CTkCheckBox(
            timestep_buttons_frame,
            text="Total",
            variable=self.timestep_total_var,
            command=self.on_option_changed
        )
        self.timestep_total_cb.pack(side="left", padx=10)
        
        self.timestep_fuels_var = ctk.BooleanVar(value=self.options['timestep_fuels'])
        self.timestep_fuels_cb = ctk.CTkCheckBox(
            timestep_buttons_frame,
            text="Fuels",
            variable=self.timestep_fuels_var,
            command=self.on_option_changed
        )
        self.timestep_fuels_cb.pack(side="left", padx=10)
        
        self.timestep_all_var = ctk.BooleanVar(value=self.options['timestep_all'])
        self.timestep_all_cb = ctk.CTkCheckBox(
            timestep_buttons_frame,
            text="All",
            variable=self.timestep_all_var,
            command=self.on_timestep_all_changed
        )
        self.timestep_all_cb.pack(side="left", padx=10)
        
        # Validation settings
        validation_frame = ctk.CTkFrame(self.basic_tab)
        validation_frame.pack(fill="x", padx=10, pady=10)
        
        validation_label = ctk.CTkLabel(
            validation_frame,
            text="Validation Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        validation_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.skip_validation_var = ctk.BooleanVar(value=self.options['skip_validation'])
        self.skip_validation_cb = ctk.CTkCheckBox(
            validation_frame,
            text="Skip HPXML Validation (faster but less safe)",
            variable=self.skip_validation_var,
            command=self.on_option_changed
        )
        self.skip_validation_cb.pack(anchor="w", padx=20, pady=(2, 10))
        
    def setup_output_tab(self):
        """Setup detailed output options."""
        # Create scrollable frame for output options
        scrollable_frame = ctk.CTkScrollableFrame(self.output_tab)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Output frequency sections
        frequencies = [
            ("Timestep", "timestep"),
            ("Daily", "daily"), 
            ("Hourly", "hourly"),
            ("Monthly", "monthly")
        ]
        
        output_types = [
            ("Total", "total"),
            ("Fuels", "fuels"),
            ("End Uses", "end_uses"),
            ("Emissions", "emissions"),
            ("Hot Water", "hot_water"),
            ("Loads", "loads"),
            ("Component Loads", "component_loads"),
            ("Unmet Hours", "unmets"),
            ("Temperatures", "temperatures")
        ]
        
        for freq_display, freq_key in frequencies:
            # Frequency section
            freq_frame = ctk.CTkFrame(scrollable_frame)
            freq_frame.pack(fill="x", padx=5, pady=5)
            
            freq_label = ctk.CTkLabel(
                freq_frame,
                text=f"{freq_display} Outputs",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            freq_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            # All checkbox
            all_var_name = f"{freq_key}_all_var"
            all_var = ctk.BooleanVar(value=self.options[f'{freq_key}_all'])
            setattr(self, all_var_name, all_var)
            
            all_cb = ctk.CTkCheckBox(
                freq_frame,
                text="All",
                variable=all_var,
                command=lambda f=freq_key: self.on_frequency_all_changed(f)
            )
            all_cb.pack(anchor="w", padx=20, pady=2)
            
            # Individual output types
            types_frame = ctk.CTkFrame(freq_frame)
            types_frame.pack(fill="x", padx=20, pady=(5, 10))
            
            # Create 3 columns of checkboxes
            for i, (type_display, type_key) in enumerate(output_types):
                row = i // 3
                col = i % 3
                
                var_name = f"{freq_key}_{type_key}_var"
                var = ctk.BooleanVar(value=self.options[f'{freq_key}_{type_key}'])
                setattr(self, var_name, var)
                
                cb = ctk.CTkCheckBox(
                    types_frame,
                    text=type_display,
                    variable=var,
                    command=self.on_option_changed
                )
                cb.grid(row=row, column=col, sticky="w", padx=10, pady=2)
                
    def setup_advanced_tab(self):
        """Setup advanced options."""
        # Performance settings
        perf_frame = ctk.CTkFrame(self.advanced_tab)
        perf_frame.pack(fill="x", padx=10, pady=10)
        
        perf_label = ctk.CTkLabel(
            perf_frame,
            text="Performance Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        perf_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Max parallel conversions
        parallel_frame = ctk.CTkFrame(perf_frame)
        parallel_frame.pack(fill="x", padx=10, pady=5)
        
        parallel_label = ctk.CTkLabel(parallel_frame, text="Max Parallel Conversions:")
        parallel_label.pack(side="left", padx=10, pady=10)
        
        self.max_parallel_var = ctk.StringVar(value=str(self.options['max_parallel']))
        self.max_parallel_entry = ctk.CTkEntry(
            parallel_frame,
            textvariable=self.max_parallel_var,
            width=80
        )
        self.max_parallel_entry.pack(side="left", padx=10, pady=10)
        self.max_parallel_entry.bind('<KeyRelease>', self.on_option_changed)
        
        # Memory management
        memory_frame = ctk.CTkFrame(self.advanced_tab)
        memory_frame.pack(fill="x", padx=10, pady=10)
        
        memory_label = ctk.CTkLabel(
            memory_frame,
            text="Memory Management",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        memory_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        memory_info = ctk.CTkLabel(
            memory_frame,
            text="Automatic memory management based on system resources",
            text_color="gray60"
        )
        memory_info.pack(anchor="w", padx=20, pady=(2, 10))
        
    def apply_preset(self, preset_name: str):
        """Apply a predefined preset configuration."""
        presets = {
            "quick": {
                'run_simulation': False,
                'add_component_loads': False,
                'debug_mode': False,
                'timestep_all': False,
                'timestep_total': True,
                'timestep_fuels': False,
                'skip_validation': True,
                'max_parallel': 8
            },
            "standard": {
                'run_simulation': True,
                'add_component_loads': True,
                'debug_mode': False,
                'timestep_all': False,
                'timestep_total': True,
                'timestep_fuels': True,
                'hourly_total': True,
                'hourly_fuels': True,
                'skip_validation': False,
                'max_parallel': 4
            },
            "advanced": {
                'run_simulation': True,
                'add_component_loads': True,
                'debug_mode': True,
                'timestep_all': True,
                'hourly_all': True,
                'monthly_all': True,
                'skip_validation': False,
                'max_parallel': 2
            }
        }
        
        if preset_name in presets:
            # Clear all current options first
            for key in self.options:
                if key.endswith('_all') or key.endswith('_total') or key.endswith('_fuels') or key.endswith('_end_uses') or key.endswith('_emissions') or key.endswith('_hot_water') or key.endswith('_loads') or key.endswith('_component_loads') or key.endswith('_unmets') or key.endswith('_temperatures'):
                    self.options[key] = False
                    
            # Apply preset
            self.options.update(presets[preset_name])
            
            # Update UI
            self.update_ui_from_options()
            
            # Show confirmation
            messagebox.showinfo("Preset Applied", f"{preset_name.title()} preset has been applied.")
            
    def update_ui_from_options(self):
        """Update UI elements to match current options."""
        # Basic tab
        self.run_simulation_var.set(self.options['run_simulation'])
        self.component_loads_var.set(self.options['add_component_loads'])
        self.debug_mode_var.set(self.options['debug_mode'])
        self.timestep_total_var.set(self.options['timestep_total'])
        self.timestep_fuels_var.set(self.options['timestep_fuels'])
        self.timestep_all_var.set(self.options['timestep_all'])
        self.skip_validation_var.set(self.options['skip_validation'])
        
        # Advanced tab
        self.max_parallel_var.set(str(self.options['max_parallel']))
        
        # Output tab - update all frequency/type combinations
        frequencies = ["timestep", "daily", "hourly", "monthly"]
        types = ["all", "total", "fuels", "end_uses", "emissions", "hot_water", 
                "loads", "component_loads", "unmets", "temperatures"]
        
        for freq in frequencies:
            for type_key in types:
                var_name = f"{freq}_{type_key}_var"
                if hasattr(self, var_name):
                    var = getattr(self, var_name)
                    var.set(self.options[f'{freq}_{type_key}'])
                    
    def on_option_changed(self, event=None):
        """Handle option change events."""
        # Update options from UI
        self.options['run_simulation'] = self.run_simulation_var.get()
        self.options['add_component_loads'] = self.component_loads_var.get()
        self.options['debug_mode'] = self.debug_mode_var.get()
        self.options['timestep_total'] = self.timestep_total_var.get()
        self.options['timestep_fuels'] = self.timestep_fuels_var.get()
        self.options['timestep_all'] = self.timestep_all_var.get()
        self.options['skip_validation'] = self.skip_validation_var.get()
        
        try:
            self.options['max_parallel'] = int(self.max_parallel_var.get())
        except ValueError:
            self.options['max_parallel'] = 4
            
        # Update output options from all frequency/type combinations
        frequencies = ["timestep", "daily", "hourly", "monthly"]
        types = ["all", "total", "fuels", "end_uses", "emissions", "hot_water",
                "loads", "component_loads", "unmets", "temperatures"]
        
        for freq in frequencies:
            for type_key in types:
                var_name = f"{freq}_{type_key}_var"
                if hasattr(self, var_name):
                    var = getattr(self, var_name)
                    self.options[f'{freq}_{type_key}'] = var.get()
                    
    def on_timestep_all_changed(self):
        """Handle timestep 'All' checkbox change."""
        if self.timestep_all_var.get():
            # If All is checked, uncheck individual options
            self.timestep_total_var.set(False)
            self.timestep_fuels_var.set(False)
        self.on_option_changed()
        
    def on_frequency_all_changed(self, frequency: str):
        """Handle frequency 'All' checkbox change."""
        all_var = getattr(self, f"{frequency}_all_var")
        
        if all_var.get():
            # If All is checked, uncheck individual options for this frequency
            types = ["total", "fuels", "end_uses", "emissions", "hot_water",
                    "loads", "component_loads", "unmets", "temperatures"]
            for type_key in types:
                var_name = f"{frequency}_{type_key}_var"
                if hasattr(self, var_name):
                    var = getattr(self, var_name)
                    var.set(False)
                    
        self.on_option_changed()
        
    def reset_to_defaults(self):
        """Reset all options to default values."""
        # Reset to standard preset
        self.apply_preset("standard")
        
    def get_options(self) -> Dict[str, Any]:
        """Get current options as dictionary."""
        # Update options from UI first
        self.on_option_changed()
        return self.options.copy()
        
    def validate_options(self) -> bool:
        """Validate current option combination."""
        # Check if max_parallel is valid
        try:
            max_parallel = int(self.max_parallel_var.get())
            if max_parallel < 1 or max_parallel > 32:
                messagebox.showerror(
                    "Invalid Option",
                    "Max parallel conversions must be between 1 and 32."
                )
                return False
        except ValueError:
            messagebox.showerror(
                "Invalid Option", 
                "Max parallel conversions must be a valid number."
            )
            return False
            
        return True