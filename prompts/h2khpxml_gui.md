# H2K to HPXML GUI Implementation Plan

## Overview
This document outlines a comprehensive plan for implementing a modern GUI for the H2K to HPXML conversion tool using CustomTKinter. The GUI will provide an intuitive interface for both novice and advanced users while maintaining all the functionality of the existing CLI tool.

## Project Structure

```
src/h2k_hpxml/gui/
├── __init__.py                 # Package initialization
├── app.py                      # Main application class
├── constants.py                # GUI constants and configurations
├── models/
│   ├── __init__.py
│   ├── conversion_task.py      # Data model for conversion tasks
│   ├── settings.py             # Application settings model
│   └── energy_data.py          # Energy analysis data models
├── widgets/
│   ├── __init__.py
│   ├── file_selector.py        # File input/output selection widget
│   ├── conversion_options.py   # Conversion settings widget
│   ├── progress_display.py     # Real-time progress tracking
│   ├── results_viewer.py       # Results display and management
│   ├── log_viewer.py           # Log output display
│   ├── status_bar.py           # Application status bar
│   ├── reports_page.py         # Energy analysis and reporting
│   ├── energy_charts.py        # Chart widgets for energy visualization
│   └── export_tools.py         # Export and comparison tools
├── dialogs/
│   ├── __init__.py
│   ├── about_dialog.py         # About information dialog
│   ├── settings_dialog.py      # Application preferences
│   ├── help_dialog.py          # User help and documentation
│   └── chart_settings.py       # Chart customization dialog
├── utils/
│   ├── __init__.py
│   ├── gui_helpers.py          # GUI utility functions
│   ├── file_operations.py      # File handling utilities
│   ├── validation.py           # Input validation utilities
│   ├── threading_helpers.py    # Background task management
│   ├── energy_analysis.py      # Energy data analysis utilities
│   └── chart_helpers.py        # Chart creation and styling utilities
└── resources/
    ├── __init__.py
    ├── icons/                  # Application icons and images
    └── themes/                 # Custom theme configurations
```

## GUI Design Mockups

This section presents three different design approaches for the H2K to HPXML converter GUI. Each design caters to different user preferences and workflow patterns.

### Design Option A: Traditional Desktop Application Layout

**Philosophy:** Familiar desktop application with menu bar, toolbar, and docked panels

**Layout Description:**
```
┌─────────────────────────────────────────────────────────────┐
│ File  Edit  Tools  View  Help                    [- □ ×]    │
├─────────────────────────────────────────────────────────────┤
│ [📁] [▶️] [⏹️] [⚙️] [❓]                                      │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────────────────────────┐ │
│ │   File List     │ │        Conversion Options           │ │
│ │                 │ │                                     │ │
│ │ □ file1.h2k     │ │ □ Run Simulation                    │ │
│ │ □ file2.h2k     │ │ □ Add Component Loads               │ │
│ │ □ file3.h2k     │ │ □ Debug Mode                        │ │
│ │                 │ │                                     │ │
│ │ [Browse] [Clear]│ │ Output Format: [Dropdown ▼]        │ │
│ │                 │ │                                     │ │
│ │ Output Dir:     │ │ Timestep: □ All □ Total □ Fuels    │ │
│ │ [___________]   │ │ Daily:    □ All □ Total □ Fuels    │ │
│ │          [...]  │ │ Hourly:   □ All □ Total □ Fuels    │ │
│ └─────────────────┘ │ Monthly:  □ All □ Total □ Fuels    │ │
│                     │                                     │ │
│                     │ [Advanced Settings...]              │ │
│                     └─────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Progress & Results                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Overall: [████████████████████████░░░░░] 85%            │ │
│ │ Current: Processing file2.h2k [██████░░░░] 60%          │ │
│ │                                          [Cancel] [⏸️]   │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ Results Table:                                          │ │
│ │ File       │ Status  │ Output Path        │ Actions     │ │
│ │ file1.h2k  │ ✅ Done │ /output/file1/     │ [Open] [📋] │ │
│ │ file2.h2k  │ 🔄 Proc │ /output/file2/     │ [View]      │ │
│ │ file3.h2k  │ ⏳ Wait │                    │             │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Ready | 3 files selected | Output: /home/user/output       │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Traditional Windows/Linux desktop application feel
- Familiar menu structure with File, Edit, Tools, etc.
- Quick action toolbar with common operations
- Side-by-side layout for files and options
- Integrated progress and results in bottom panel
- Status bar with quick information

**Target Users:** Power users, engineers familiar with traditional CAD/engineering software

**Advantages:**
- Familiar interface for professional users
- Efficient use of screen space
- All information visible at once
- Professional appearance

**Implementation Notes:**
```python
class TraditionalLayoutGUI(ctk.CTk):
    def setup_ui(self):
        # Menu bar (using tkinter.Menu)
        self.setup_menu_bar()
        
        # Toolbar frame
        self.toolbar_frame = ctk.CTkFrame(self, height=40)
        
        # Main content area with three panels
        self.main_frame = ctk.CTkFrame(self)
        
        # Left panel - File selection
        self.file_panel = ctk.CTkFrame(self.main_frame, width=300)
        
        # Right panel - Options
        self.options_panel = ctk.CTkFrame(self.main_frame)
        
        # Bottom panel - Progress and results
        self.results_panel = ctk.CTkFrame(self.main_frame, height=250)
        
        # Status bar
        self.status_bar = ctk.CTkFrame(self, height=25)
```

---

### Design Option B: Modern Wizard-Style Interface

**Philosophy:** Step-by-step guided workflow with clean, modern aesthetics

**Layout Description:**
```
┌─────────────────────────────────────────────────────────────┐
│              H2K to HPXML Converter                [- □ ×]   │
│                                                             │
│    Step 1: Select Files → Step 2: Configure → Step 3: Run  │
│       ● ────────────────────○────────────────────○         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │              📁 Select H2K Files                      │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │                                                 │  │  │
│  │  │        Drag & Drop H2K Files Here              │  │  │
│  │  │                    or                          │  │  │
│  │  │               [Browse Files]                    │  │  │
│  │  │                                                 │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  Selected Files:                                      │  │
│  │  ✓ WizardHouse.h2k                     [Remove]      │  │
│  │  ✓ ERS-EX-10000.h2k                   [Remove]      │  │
│  │                                                       │  │
│  │  Output Directory:                                    │  │
│  │  [/home/user/h2k_output                    ] [📁]     │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│                                      [Back]    [Next →]    │
└─────────────────────────────────────────────────────────────┘
```

**Step 2 - Configure Options:**
```
┌─────────────────────────────────────────────────────────────┐
│              H2K to HPXML Converter                [- □ ×]   │
│                                                             │
│    Step 1: Select Files → Step 2: Configure → Step 3: Run  │
│       ○ ────────────────────●────────────────────○         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │               ⚙️ Conversion Options                    │  │
│  │                                                       │  │
│  │  ┌─ Simulation Settings ─────────────────────────────┐ │  │
│  │  │                                                  │ │  │
│  │  │ ☑ Run OpenStudio Simulation                      │ │  │
│  │  │ ☑ Add Component Loads                            │ │  │
│  │  │ ☐ Debug Mode (Advanced)                          │ │  │
│  │  │                                                  │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │                                                       │  │
│  │  ┌─ Output Reports ───────────────────────────────────┐ │  │
│  │  │                                                   │ │  │
│  │  │ Frequency:  ○ Monthly  ○ Hourly  ○ Timestep     │ │  │
│  │  │ Types:      ☑ Total    ☑ Fuels   ☐ End Uses    │ │  │
│  │  │             ☐ Loads    ☐ Temperatures            │ │  │
│  │  │                                                   │ │  │
│  │  └───────────────────────────────────────────────────┘ │  │
│  │                                                       │  │
│  │              [🔧 Advanced Settings...]                 │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│                                     [← Back]    [Next →]   │
└─────────────────────────────────────────────────────────────┘
```

**Step 3 - Run Conversion:**
```
┌─────────────────────────────────────────────────────────────┐
│              H2K to HPXML Converter                [- □ ×]   │
│                                                             │
│    Step 1: Select Files → Step 2: Configure → Step 3: Run  │
│       ○ ────────────────────○────────────────────●         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │                🚀 Running Conversion                   │  │
│  │                                                       │  │
│  │  Overall Progress:                                    │  │
│  │  [████████████████████████████████░░░] 85% (2/3)     │  │
│  │                                                       │  │
│  │  Current File: ERS-EX-10000.h2k                      │  │
│  │  [██████████████░░░░░░░░░░░░░░░░░░░░] 45%             │  │
│  │  Status: Running OpenStudio simulation...             │  │
│  │                                                       │  │
│  │  ┌─ Log Output ─────────────────────────────────────┐ │  │
│  │  │ Processing file: ERS-EX-10000.h2k                │ │  │
│  │  │ Converting H2K to HPXML...                       │ │  │
│  │  │ HPXML file created: /output/ERS-EX-10000/        │ │  │
│  │  │ Starting simulation...                           │ │  │
│  │  │ ▼                                                │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │                                                       │  │
│  │                         [⏸️ Pause] [⏹️ Cancel]         │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│                                     [← Back]    [Finish]   │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Guided step-by-step workflow
- Clean, uncluttered interface at each step
- Large drag-drop area for files
- Progress indicator showing current step
- Context-appropriate controls for each step
- Modern card-based layout

**Target Users:** New users, occasional users, non-technical users

**Advantages:**
- Intuitive for beginners
- Prevents user errors by guiding workflow
- Clean, modern appearance
- Less overwhelming than showing all options at once

**Implementation Notes:**
```python
class WizardStyleGUI(ctk.CTk):
    def __init__(self):
        self.current_step = 1
        self.steps = ["Select Files", "Configure", "Run"]
        
    def setup_ui(self):
        # Progress indicator
        self.progress_frame = ctk.CTkFrame(self, height=80)
        
        # Main content area (changes based on step)
        self.content_frame = ctk.CTkFrame(self)
        
        # Navigation buttons
        self.nav_frame = ctk.CTkFrame(self, height=60)
        
    def show_step(self, step_number):
        # Clear content and show appropriate step
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        if step_number == 1:
            self.show_file_selection_step()
        elif step_number == 2:
            self.show_options_step()
        elif step_number == 3:
            self.show_conversion_step()
```

---

### Design Option C: Dashboard-Style Interface

**Philosophy:** Information-dense dashboard with cards and panels for power users

**Layout Description:**
```
┌─────────────────────────────────────────────────────────────┐
│  H2K to HPXML Converter Dashboard            🌙 ⚙️ ❓ [×]   │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────────────────┐ │
│ │    📁 Input Files    │ │        📊 Quick Stats           │ │
│ │ ┌─────────────────┐ │ │ Files Selected:      3          │ │
│ │ │                 │ │ │ Total Size:         12.4 MB     │ │
│ │ │  Drop files     │ │ │ Est. Time:          ~5 min      │ │
│ │ │      here       │ │ │ Output Size:        ~45 MB      │ │
│ │ │                 │ │ │                                 │ │
│ │ └─────────────────┘ │ │ [📈 View Details]                │ │
│ │ [+ Add] [🗑️ Clear]  │ └─────────────────────────────────┘ │
│ └─────────────────────┘ ┌─────────────────────────────────┐ │
│ ┌─────────────────────┐ │       ⚙️ Quick Settings         │ │
│ │  📂 Recent Files     │ │                                 │ │
│ │ • WizardHouse.h2k   │ │ Profile: [Standard    ▼]        │ │
│ │ • ERS-EX-10000.h2k  │ │          ○ Quick                │ │
│ │ • TestHouse.h2k     │ │          ● Standard             │ │
│ │ • Building1.h2k     │ │          ○ Detailed             │ │
│ │                     │ │          ○ Custom               │ │
│ │ [📋 Load Set]       │ │                                 │ │
│ └─────────────────────┘ │ 🚀 [START CONVERSION]            │ │
│ ┌─────────────────────┐ └─────────────────────────────────┘ │
│ │   📁 Output Path     │ ┌─────────────────────────────────┐ │
│ │                     │ │      📋 Recent Results          │ │
│ │ [/home/user/output] │ │                                 │ │
│ │              [...]  │ │ ✅ WizardHouse.h2k              │ │
│ │                     │ │    → /output/WizardHouse/       │ │
│ │ ☑ Open when done    │ │                                 │ │
│ │ ☑ Archive originals │ │ ❌ TestBuilding.h2k              │ │
│ └─────────────────────┘ │    → Error: Invalid format     │ │
├─────────────────────────┼─────────────────────────────────┤
│     🔄 Active Operations                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Current: Converting ERS-EX-10000.h2k            [⏸️][⏹️]│ │
│ │ [████████████████████████████████████░░░] 89%           │ │
│ │                                                         │ │
│ │ Queue: WizardHouse.h2k, TestHouse.h2k          2 files │ │
│ │ Completed: BuildingA.h2k                       1 files │ │
│ │ Failed: None                                   0 files │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─ 📝 Activity Log ─┐ ┌─ 📊 Performance ─┐ ┌─ 🔧 Tools ─┐ │
│ │ 14:23 Started     │ │ CPU: ████░░ 67%  │ │ [⚡ Batch] │ │
│ │ 14:24 HPXML OK    │ │ RAM: ██░░░░ 34%  │ │ [📋 Template] │ │
│ │ 14:25 Simulation  │ │ Disk: █░░░░ 12%  │ │ [📁 Manager] │ │
│ │ 14:27 Complete    │ │                  │ │ [⚙️ Settings] │ │
│ └───────────────────┘ └──────────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Card-based layout with modular panels
- Information-rich dashboard view
- Real-time statistics and performance monitoring
- Quick access to recent files and results
- Multiple operation queues visible
- Customizable panel arrangement
- Dark/light theme toggle

**Target Users:** Power users, batch processing users, system administrators

**Advantages:**
- Maximum information density
- Efficient for frequent users
- Multiple operations visible at once
- Professional monitoring feel
- Highly customizable

**Implementation Notes:**
```python
class DashboardStyleGUI(ctk.CTk):
    def setup_ui(self):
        # Grid-based layout with resizable panels
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        
        # Left column panels
        self.left_column = ctk.CTkFrame(self)
        self.input_card = InputFilesCard(self.left_column)
        self.recent_card = RecentFilesCard(self.left_column)
        self.output_card = OutputPathCard(self.left_column)
        
        # Right column panels  
        self.right_column = ctk.CTkFrame(self)
        self.stats_card = QuickStatsCard(self.right_column)
        self.settings_card = QuickSettingsCard(self.right_column)
        self.results_card = RecentResultsCard(self.right_column)
        
        # Bottom operations panel (spans both columns)
        self.operations_panel = ActiveOperationsPanel(self)
        
        # Bottom info panels
        self.bottom_panels = ctk.CTkFrame(self)
        self.log_panel = ActivityLogPanel(self.bottom_panels)
        self.perf_panel = PerformancePanel(self.bottom_panels)
        self.tools_panel = ToolsPanel(self.bottom_panels)
```

---

## Design Comparison Summary

| Feature | Traditional (A) | Wizard (B) | Dashboard (C) | Reports Page |
|---------|----------------|------------|---------------|--------------|
| **Learning Curve** | Medium | Low | High | Low |
| **Information Density** | High | Low | Very High | High |
| **Beginner Friendly** | Medium | High | Low | High |
| **Power User Efficiency** | High | Medium | Very High | High |
| **Visual Appeal** | Professional | Modern | Information-rich | Analytical |
| **Screen Space Usage** | Efficient | Generous | Maximum | Optimized |
| **Error Prevention** | Medium | High | Medium | N/A |
| **Customization** | Medium | Low | High | High |
| **Analysis Capabilities** | Basic | Basic | Medium | Comprehensive |
| **Export Options** | Limited | Limited | Medium | Extensive |

**Reports Page Features:**
- **Energy Analysis**: Comprehensive breakdown of energy consumption by end-use
- **Peak Usage Analysis**: Identification of peak electric demand with timing
- **Seasonal Analysis**: Detailed charts for hottest and coldest weeks
- **Visual Charts**: Interactive matplotlib-based charts with zoom/pan
- **Export Capabilities**: PDF reports, Excel data, CSV tables, PNG charts
- **Comparison Tools**: Side-by-side building analysis
- **Data Integration**: Direct reading from EnergyPlus SQL output files

---

### Design Addition: Comprehensive Reports Page

**Philosophy:** Dedicated analysis and visualization interface for post-conversion energy analysis

**Purpose:** Provide detailed energy analysis, visualization, and reporting capabilities for completed conversions

**Layout Description:**
```
┌─────────────────────────────────────────────────────────────┐
│  H2K to HPXML Converter - Reports            📊 📋 🖨️ [×]  │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────────────────┐ │
│ │   📁 Select File     │ │       📊 Energy Summary         │ │
│ │                     │ │                                 │ │
│ │ Recent Conversions: │ │ Annual Total:      125,890 kWh  │ │
│ │ • WizardHouse.h2k   │ │ Peak Electric:     12.5 kW      │ │
│ │ • ERS-EX-10000.h2k  │ │ Peak Time:         Jul 15 3:00PM│ │
│ │ • TestBuilding.h2k  │ │                                 │ │
│ │                     │ │ End Use Breakdown:              │ │
│ │ [📁 Browse Others]   │ │ • Heating:    45,320 kWh (36%) │ │
│ │                     │ │ • Cooling:    28,150 kWh (22%) │ │
│ │ Selected:           │ │ • Hot Water:  18,900 kWh (15%) │ │
│ │ WizardHouse.h2k     │ │ • Lighting:   12,650 kWh (10%) │ │
│ │ Status: ✅ Complete  │ │ • Appliances: 20,870 kWh (17%) │ │
│ │                     │ │                                 │ │
│ │ [🔄 Refresh Results]│ │ [📋 Detailed Report]            │ │
│ └─────────────────────┘ └─────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    📈 Energy Usage Analysis                 │ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Tabs: [Monthly] [Hottest Week] [Coldest Week] [Peak]   │ │
│ │                                                         │ │
│ │        Hottest Week Energy Usage (Jul 10-16)           │ │
│ │ kWh                                                     │ │
│ │  50 ┤                                                   │ │
│ │  40 ┤     ██                    ██                      │ │
│ │  30 ┤   ████  ██              ████                      │ │
│ │  20 ┤ ██████████████        ████████                    │ │
│ │  10 ┤████████████████      ████████████                │ │
│ │   0 └──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬─ │ │
│ │        Mon Tue Wed Thu Fri Sat Sun                     │ │
│ │                                                         │ │
│ │ Legend: ■ Cooling ■ Heating ■ Hot Water ■ Other       │ │
│ │                                                         │ │
│ │ Peak Usage: 12.5 kW at July 15, 3:00 PM               │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ ┌─ 📋 Export Options ──┐ ┌─ 📊 Comparison ──┐ ┌─ ⚙️ Tools ─┐ │
│ │ Format:              │ │ Compare With:     │ │ [📈 Trends]│ │
│ │ ○ PDF Report         │ │ [Dropdown ▼]     │ │ [🎯 Goals] │ │
│ │ ○ Excel Data         │ │                   │ │ [📐 Calc]  │ │
│ │ ○ CSV Tables         │ │ [Add Comparison]  │ │ [🔍 Detail]│ │
│ │ ○ PNG Charts         │ │                   │ │            │ │
│ │ [💾 Export]          │ │ [📊 Show Chart]   │ │ [❓ Help]  │ │
│ └──────────────────────┘ └───────────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- **File Selection Panel**: Browse and select from completed conversions
- **Energy Summary**: Quick overview of total consumption and peak usage
- **Interactive Charts**: 
  - Monthly energy usage patterns
  - Hottest/coldest week detailed analysis
  - Peak usage identification and timing
  - End-use breakdowns with visual representations
- **Export Capabilities**: Multiple format options for reports and data
- **Comparison Tools**: Side-by-side analysis of different files
- **Analysis Tools**: Trend analysis, goal setting, detailed calculations

**Target Users:** All user types - essential for understanding conversion results

**Chart Types:**
1. **Monthly Overview**: Bar chart showing total monthly consumption
2. **Hottest Week**: Hourly/daily breakdown during peak cooling period
3. **Coldest Week**: Hourly/daily breakdown during peak heating period  
4. **Peak Analysis**: Timeline view showing when and how peak usage occurred
5. **End-Use Pie Chart**: Visual breakdown of energy consumption by category

**Implementation Notes:**
```python
class ReportsPageWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # File selection panel
        self.file_selector = ResultFileSelector(self)
        
        # Summary panel  
        self.summary_panel = EnergySummaryPanel(self)
        
        # Chart display with tabs
        self.chart_tabview = ctk.CTkTabview(self)
        self.monthly_tab = self.chart_tabview.add("Monthly")
        self.hot_week_tab = self.chart_tabview.add("Hottest Week") 
        self.cold_week_tab = self.chart_tabview.add("Coldest Week")
        self.peak_tab = self.chart_tabview.add("Peak Analysis")
        
        # Analysis tools panel
        self.tools_panel = AnalysisToolsPanel(self)
        
        # Setup chart widgets
        self.setup_charts()
        
    def setup_charts(self):
        """Initialize chart widgets using matplotlib with tkinter backend"""
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkinter
        
        # Monthly chart
        self.monthly_figure = plt.Figure(figsize=(10, 6))
        self.monthly_canvas = FigureCanvasTkinter(self.monthly_figure, self.monthly_tab)
        
        # Weekly charts  
        self.weekly_figure = plt.Figure(figsize=(10, 6))
        self.weekly_canvas = FigureCanvasTkinter(self.weekly_figure, self.hot_week_tab)
        
        # Peak analysis chart
        self.peak_figure = plt.Figure(figsize=(10, 6))
        self.peak_canvas = FigureCanvasTkinter(self.peak_figure, self.peak_tab)
```

## Recommended Implementation Approach

1. **Start with Design B (Wizard)** for initial implementation - easiest to implement and most user-friendly
2. **Add Design A (Traditional)** as an "Advanced Mode" toggle for power users  
3. **Include Reports Page** as a dedicated tab/window accessible from all designs
4. **Consider Design C (Dashboard)** for future versions based on user feedback

## Main Application Architecture

### 1. Core Application Class (`app.py`)

```python
import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
import json

class H2KConverterGUI(ctk.CTk):
    """Main application window for H2K to HPXML converter."""
    
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
        
        # Initialize UI
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Initialize the complete user interface."""
        # Create menu bar
        self.setup_menu()
        
        # Create main layout
        self.setup_main_layout()
        
        # Create status bar
        self.setup_status_bar()
        
        # Bind events
        self.bind_events()
```

### 2. File Selector Widget (`widgets/file_selector.py`)

**Purpose:** Handle input file selection and output directory configuration

**Features:**
- Multi-file H2K selection with drag-and-drop support
- Output directory selection with smart defaults
- File validation with visual feedback
- Recent files history
- File preview capabilities

**Key Components:**
```python
class FileSelectorWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Input section
        self.input_frame = ctk.CTkFrame(self)
        self.input_label = ctk.CTkLabel(self.input_frame, text="H2K Files:")
        self.input_listbox = ctk.CTkScrollableFrame(self.input_frame)
        self.browse_button = ctk.CTkButton(self.input_frame, text="Browse Files", command=self.browse_files)
        self.clear_button = ctk.CTkButton(self.input_frame, text="Clear", command=self.clear_files)
        
        # Output section
        self.output_frame = ctk.CTkFrame(self)
        self.output_label = ctk.CTkLabel(self.output_frame, text="Output Directory:")
        self.output_entry = ctk.CTkEntry(self.output_frame)
        self.output_browse_button = ctk.CTkButton(self.output_frame, text="Browse", command=self.browse_output)
        
        # Drag and drop support
        self.setup_drag_drop()
        
    def setup_drag_drop(self):
        """Enable drag and drop for H2K files."""
        # Implementation for drag-drop functionality
        pass
        
    def validate_files(self):
        """Validate selected H2K files."""
        # Check file existence, format, readability
        pass
```

### 3. Conversion Options Widget (`widgets/conversion_options.py`)

**Purpose:** Provide comprehensive control over conversion and simulation settings

**Features:**
- Basic/Advanced view toggle
- All CLI options accessible through GUI
- Settings presets (Beginner, Standard, Advanced)
- Real-time validation of option combinations
- Tooltips and help text for complex options

**Key Options Sections:**
1. **Output Settings**
   - Output format selection
   - File naming conventions
   - Directory structure options

2. **Simulation Controls**
   - Enable/disable simulation
   - Timestep output options (ALL, total, fuels, etc.)
   - Daily, hourly, monthly reporting
   - Component loads inclusion

3. **Performance Settings**
   - Thread count for parallel processing
   - Memory usage limits
   - Validation skip options

4. **Debug and Validation**
   - Debug mode toggle
   - Schema validation controls
   - Error handling preferences

```python
class ConversionOptionsWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Create tabbed interface for organization
        self.tabview = ctk.CTkTabview(self)
        
        # Basic options tab
        self.basic_tab = self.tabview.add("Basic")
        self.setup_basic_options()
        
        # Advanced options tab
        self.advanced_tab = self.tabview.add("Advanced")
        self.setup_advanced_options()
        
        # Output options tab
        self.output_tab = self.tabview.add("Output")
        self.setup_output_options()
        
    def setup_basic_options(self):
        """Setup basic conversion options."""
        # Simulation enable/disable
        self.simulate_var = ctk.BooleanVar(value=True)
        self.simulate_checkbox = ctk.CTkCheckBox(
            self.basic_tab, 
            text="Run OpenStudio Simulation",
            variable=self.simulate_var
        )
        
        # Component loads
        self.component_loads_var = ctk.BooleanVar(value=True)
        self.component_loads_checkbox = ctk.CTkCheckBox(
            self.basic_tab,
            text="Add Component Loads",
            variable=self.component_loads_var
        )
```

### 4. Progress Display Widget (`widgets/progress_display.py`)

**Purpose:** Real-time feedback during conversion operations

**Features:**
- Overall progress bar for batch operations
- Individual file progress tracking
- Current operation status display
- Estimated time remaining
- Cancel operation capability
- Live log output with filtering

```python
class ProgressDisplayWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Overall progress
        self.overall_progress_label = ctk.CTkLabel(self, text="Overall Progress:")
        self.overall_progress_bar = ctk.CTkProgressBar(self)
        self.overall_progress_text = ctk.CTkLabel(self, text="Ready")
        
        # Current file progress
        self.current_file_label = ctk.CTkLabel(self, text="Current File:")
        self.current_file_progress = ctk.CTkProgressBar(self)
        self.current_file_text = ctk.CTkLabel(self, text="")
        
        # Control buttons
        self.cancel_button = ctk.CTkButton(self, text="Cancel", command=self.cancel_operation)
        self.pause_button = ctk.CTkButton(self, text="Pause", command=self.pause_operation)
        
        # Log display
        self.log_frame = ctk.CTkFrame(self)
        self.log_textbox = ctk.CTkTextbox(self.log_frame, height=200)
        self.log_scrollbar = ctk.CTkScrollbar(self.log_frame)
        
    def update_progress(self, overall_percent, current_file, current_percent, message):
        """Update progress displays."""
        self.overall_progress_bar.set(overall_percent / 100)
        self.current_file_progress.set(current_percent / 100)
        self.current_file_text.configure(text=current_file)
        self.add_log_message(message)
```

### 5. Results Viewer Widget (`widgets/results_viewer.py`)

**Purpose:** Display and manage conversion results

**Features:**
- Tabular display of conversion results
- Success/failure status indicators
- Quick access to generated files
- Error details for failed conversions
- Export results summary
- Open output folders

```python
class ResultsViewerWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Results table (using CTkScrollableFrame)
        self.results_frame = ctk.CTkScrollableFrame(self)
        self.results_headers = ["File", "Status", "Output", "Actions"]
        
        # Action buttons
        self.actions_frame = ctk.CTkFrame(self)
        self.open_output_button = ctk.CTkButton(self.actions_frame, text="Open Output Folder")
        self.export_report_button = ctk.CTkButton(self.actions_frame, text="Export Report")
        self.clear_results_button = ctk.CTkButton(self.actions_frame, text="Clear Results")
        
    def add_result(self, filename, status, output_path, error_message=None):
        """Add a conversion result to the display."""
        # Create result row with appropriate styling based on status
        pass
```

### 6. Reports Page Widget (`widgets/reports_page.py`)

**Purpose:** Comprehensive energy analysis and visualization for completed conversions

**Features:**
- File selection from completed conversions with status validation
- Energy summary dashboard with key metrics
- Interactive charts for different analysis periods
- Peak usage identification and timing analysis
- End-use breakdown with visual representations
- Export capabilities for reports and raw data
- Comparison tools for multiple buildings

**Key Components:**

#### Energy Data Integration
```python
class EnergyDataManager:
    """Manages loading and processing of energy simulation results."""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.sql', '.xml']
        self.data_cache = {}
        
    def load_simulation_results(self, output_path):
        """Load energy results from OpenStudio simulation output."""
        # Look for eplusout.sql, results.csv, or other output files
        sql_path = Path(output_path) / "run" / "eplusout.sql"
        csv_path = Path(output_path) / "run" / "results.csv"
        
        if sql_path.exists():
            return self._load_from_sql(sql_path)
        elif csv_path.exists():
            return self._load_from_csv(csv_path)
        else:
            raise FileNotFoundError("No supported energy results found")
            
    def _load_from_sql(self, sql_path):
        """Extract energy data from EnergyPlus SQL output."""
        import sqlite3
        import pandas as pd
        
        conn = sqlite3.connect(sql_path)
        
        # Get hourly energy consumption data
        hourly_query = """
        SELECT 
            rd.Name,
            rd.KeyValue,
            t.Month, t.Day, t.Hour,
            rd.Value
        FROM ReportData rd
        JOIN Time t ON rd.TimeIndex = t.TimeIndex
        WHERE rd.ReportingFrequency = 'Hourly'
        AND rd.Name LIKE '%Energy%'
        ORDER BY t.Month, t.Day, t.Hour
        """
        
        hourly_data = pd.read_sql_query(hourly_query, conn)
        
        # Get monthly summary data
        monthly_query = """
        SELECT 
            rd.Name,
            rd.KeyValue,
            t.Month,
            SUM(rd.Value) as MonthlyTotal
        FROM ReportData rd
        JOIN Time t ON rd.TimeIndex = t.TimeIndex
        WHERE rd.ReportingFrequency = 'Hourly'
        AND rd.Name LIKE '%Energy%'
        GROUP BY rd.Name, rd.KeyValue, t.Month
        ORDER BY t.Month
        """
        
        monthly_data = pd.read_sql_query(monthly_query, conn)
        conn.close()
        
        return {
            'hourly': hourly_data,
            'monthly': monthly_data,
            'building_name': Path(sql_path).parent.parent.name
        }
```

#### Reports Page Implementation
```python
class ReportsPageWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.energy_manager = EnergyDataManager()
        self.current_data = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the reports page layout."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # File selection panel (left side)
        self.file_panel = self.create_file_selection_panel()
        self.file_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        
        # Energy summary panel (top right)
        self.summary_panel = self.create_energy_summary_panel()
        self.summary_panel.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        # Chart display panel (bottom right)
        self.chart_panel = self.create_chart_panel()
        self.chart_panel.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        # Export and tools panel (bottom)
        self.tools_panel = self.create_tools_panel()
        self.tools_panel.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
    def create_file_selection_panel(self):
        """Create file selection and status panel."""
        panel = ctk.CTkFrame(self, width=250)
        
        # Header
        header = ctk.CTkLabel(panel, text="📁 Select Results File", font=("Arial", 16, "bold"))
        header.pack(pady=(10, 5))
        
        # Recent conversions list
        recent_label = ctk.CTkLabel(panel, text="Recent Conversions:")
        recent_label.pack(anchor="w", padx=10)
        
        self.recent_listbox = ctk.CTkScrollableFrame(panel, height=200)
        self.recent_listbox.pack(fill="x", padx=10, pady=5)
        
        # Browse button
        browse_btn = ctk.CTkButton(panel, text="📁 Browse Others", command=self.browse_results)
        browse_btn.pack(pady=5)
        
        # Selected file info
        selected_label = ctk.CTkLabel(panel, text="Selected:")
        selected_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.selected_file_label = ctk.CTkLabel(panel, text="None", wraplength=200)
        self.selected_file_label.pack(anchor="w", padx=10)
        
        self.status_label = ctk.CTkLabel(panel, text="")
        self.status_label.pack(anchor="w", padx=10)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(panel, text="🔄 Refresh Results", command=self.refresh_results)
        refresh_btn.pack(pady=10)
        
        return panel
        
    def create_energy_summary_panel(self):
        """Create energy summary dashboard."""
        panel = ctk.CTkFrame(self)
        
        # Header
        header = ctk.CTkLabel(panel, text="📊 Energy Summary", font=("Arial", 16, "bold"))
        header.pack(pady=10)
        
        # Summary metrics
        self.summary_frame = ctk.CTkFrame(panel)
        self.summary_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Annual total
        self.annual_label = ctk.CTkLabel(self.summary_frame, text="Annual Total: --")
        self.annual_label.pack(anchor="w", padx=10, pady=2)
        
        # Peak electric
        self.peak_label = ctk.CTkLabel(self.summary_frame, text="Peak Electric: --")
        self.peak_label.pack(anchor="w", padx=10, pady=2)
        
        # Peak time
        self.peak_time_label = ctk.CTkLabel(self.summary_frame, text="Peak Time: --")
        self.peak_time_label.pack(anchor="w", padx=10, pady=2)
        
        # End use breakdown
        breakdown_label = ctk.CTkLabel(self.summary_frame, text="End Use Breakdown:")
        breakdown_label.pack(anchor="w", padx=10, pady=(10, 2))
        
        self.breakdown_frame = ctk.CTkFrame(self.summary_frame)
        self.breakdown_frame.pack(fill="x", padx=10, pady=5)
        
        # Detailed report button
        detail_btn = ctk.CTkButton(panel, text="📋 Detailed Report", command=self.show_detailed_report)
        detail_btn.pack(pady=10)
        
        return panel
        
    def create_chart_panel(self):
        """Create chart display with tabs."""
        panel = ctk.CTkFrame(self)
        
        # Header
        header = ctk.CTkLabel(panel, text="📈 Energy Usage Analysis", font=("Arial", 16, "bold"))
        header.pack(pady=10)
        
        # Tabbed chart view
        self.chart_tabview = ctk.CTkTabview(panel)
        self.chart_tabview.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add tabs
        self.monthly_tab = self.chart_tabview.add("Monthly")
        self.hot_week_tab = self.chart_tabview.add("Hottest Week")
        self.cold_week_tab = self.chart_tabview.add("Coldest Week") 
        self.peak_tab = self.chart_tabview.add("Peak Analysis")
        
        # Initialize charts
        self.setup_charts()
        
        return panel
        
    def setup_charts(self):
        """Initialize matplotlib charts in each tab."""
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkinter
        from matplotlib.figure import Figure
        
        # Set up matplotlib for dark theme compatibility
        plt.style.use('default')
        
        # Monthly chart
        self.monthly_fig = Figure(figsize=(10, 6), dpi=100)
        self.monthly_canvas = FigureCanvasTkinter(self.monthly_fig, self.monthly_tab)
        self.monthly_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Hottest week chart
        self.hot_week_fig = Figure(figsize=(10, 6), dpi=100)
        self.hot_week_canvas = FigureCanvasTkinter(self.hot_week_fig, self.hot_week_tab)
        self.hot_week_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Coldest week chart
        self.cold_week_fig = Figure(figsize=(10, 6), dpi=100)
        self.cold_week_canvas = FigureCanvasTkinter(self.cold_week_fig, self.cold_week_tab)
        self.cold_week_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Peak analysis chart
        self.peak_fig = Figure(figsize=(10, 6), dpi=100)
        self.peak_canvas = FigureCanvasTkinter(self.peak_fig, self.peak_tab)
        self.peak_canvas.get_tk_widget().pack(fill="both", expand=True)
```

#### Chart Generation Methods
```python
    def update_monthly_chart(self, data):
        """Generate monthly energy usage bar chart."""
        self.monthly_fig.clear()
        ax = self.monthly_fig.add_subplot(111)
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Process data for different end uses
        heating_data = data['monthly'][data['monthly']['Name'].str.contains('Heating')].groupby('Month')['MonthlyTotal'].sum()
        cooling_data = data['monthly'][data['monthly']['Name'].str.contains('Cooling')].groupby('Month')['MonthlyTotal'].sum()
        
        # Create stacked bar chart
        ax.bar(months, heating_data, label='Heating', color='#FF6B6B')
        ax.bar(months, cooling_data, bottom=heating_data, label='Cooling', color='#4ECDC4')
        
        ax.set_title('Monthly Energy Consumption')
        ax.set_ylabel('Energy (kWh)')
        ax.legend()
        ax.tick_params(axis='x', rotation=45)
        
        self.monthly_fig.tight_layout()
        self.monthly_canvas.draw()
        
    def update_peak_week_chart(self, data, week_type='hot'):
        """Generate hottest or coldest week analysis."""
        fig = self.hot_week_fig if week_type == 'hot' else self.cold_week_fig
        canvas = self.hot_week_canvas if week_type == 'hot' else self.cold_week_canvas
        
        fig.clear()
        ax = fig.add_subplot(111)
        
        # Find hottest/coldest week based on cooling/heating load
        if week_type == 'hot':
            # Find week with highest cooling demand
            week_data = self._find_peak_cooling_week(data)
            title = f"Hottest Week Energy Usage ({week_data['date_range']})"
        else:
            # Find week with highest heating demand  
            week_data = self._find_peak_heating_week(data)
            title = f"Coldest Week Energy Usage ({week_data['date_range']})"
        
        # Create hourly usage chart for the week
        hours = range(len(week_data['hourly_usage']))
        ax.plot(hours, week_data['hourly_usage'], linewidth=2)
        ax.fill_between(hours, week_data['hourly_usage'], alpha=0.3)
        
        ax.set_title(title)
        ax.set_xlabel('Hour of Week')
        ax.set_ylabel('Energy Usage (kWh)')
        
        # Add day separators
        for day in range(1, 8):
            ax.axvline(x=day*24, color='gray', linestyle='--', alpha=0.5)
            
        fig.tight_layout()
        canvas.draw()
        
    def update_peak_analysis_chart(self, data):
        """Generate peak usage analysis chart."""
        self.peak_fig.clear()
        ax = self.peak_fig.add_subplot(111)
        
        # Find peak usage day
        peak_info = self._find_peak_usage(data)
        peak_day_data = peak_info['day_data']
        
        hours = range(24)
        ax.plot(hours, peak_day_data, marker='o', linewidth=2, markersize=4)
        
        # Highlight peak hour
        peak_hour = peak_info['peak_hour']
        peak_value = peak_info['peak_value']
        ax.scatter([peak_hour], [peak_value], color='red', s=100, zorder=5)
        ax.annotate(f'Peak: {peak_value:.1f} kW\nat {peak_hour}:00', 
                   xy=(peak_hour, peak_value), 
                   xytext=(peak_hour+2, peak_value+1),
                   arrowprops=dict(arrowstyle='->', color='red'))
        
        ax.set_title(f"Peak Usage Day: {peak_info['date']}")
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Power (kW)')
        ax.grid(True, alpha=0.3)
        
        self.peak_fig.tight_layout()
        self.peak_canvas.draw()
```

### 7. Export and Analysis Tools (`widgets/export_tools.py`)

**Purpose:** Provide comprehensive export and comparison capabilities

**Features:**
- Multiple export formats (PDF, Excel, CSV, PNG)
- Building comparison tools
- Custom report generation
- Energy benchmark analysis
- Goal setting and tracking

```python
class ExportToolsWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.setup_export_options()
        self.setup_comparison_tools()
        self.setup_analysis_tools()
        
    def export_pdf_report(self, energy_data, charts):
        """Generate comprehensive PDF report."""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet
        
        # Create PDF with energy summary, charts, and analysis
        pass
        
    def export_excel_data(self, energy_data):
        """Export detailed energy data to Excel workbook."""
        import pandas as pd
        
        with pd.ExcelWriter('energy_analysis.xlsx') as writer:
            energy_data['hourly'].to_excel(writer, sheet_name='Hourly Data')
            energy_data['monthly'].to_excel(writer, sheet_name='Monthly Summary')
            # Add more sheets as needed
```

## Background Processing Integration

### Threading Strategy
```python
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
import asyncio

class ConversionManager:
    def __init__(self, gui_callback):
        self.gui_callback = gui_callback
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.progress_queue = queue.Queue()
        self.cancel_event = threading.Event()
        
    def start_conversion(self, h2k_files, output_path, options):
        """Start conversion process in background thread."""
        conversion_thread = threading.Thread(
            target=self._run_conversion,
            args=(h2k_files, output_path, options)
        )
        conversion_thread.daemon = True
        conversion_thread.start()
        
        # Start progress monitoring
        self._monitor_progress()
        
    def _run_conversion(self, h2k_files, output_path, options):
        """Execute the actual conversion process."""
        # Integrate with existing CLI conversion logic
        # from h2k_hpxml.cli.convert import process_file
        pass
```

## Integration with Existing CLI Code

### Wrapper Classes
```python
from h2k_hpxml.cli.convert import (
    _convert_h2k_to_hpxml,
    _run_simulation,
    _build_simulation_flags,
    _handle_processing_error
)

class ConversionWrapper:
    """Wrapper around CLI conversion functionality for GUI integration."""
    
    def __init__(self, progress_callback=None, log_callback=None):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        
    def convert_single_file(self, h2k_path, output_path, options):
        """Convert a single H2K file with GUI progress updates."""
        try:
            # Update progress
            if self.progress_callback:
                self.progress_callback("Starting conversion...", 0)
                
            # Convert H2K to HPXML
            hpxml_path = _convert_h2k_to_hpxml(h2k_path, output_path)
            
            if self.progress_callback:
                self.progress_callback("HPXML generated", 50)
            
            # Run simulation if enabled
            if options.get('simulate', True):
                simulation_result = self._run_simulation_wrapped(hpxml_path, options)
                
            if self.progress_callback:
                self.progress_callback("Conversion complete", 100)
                
            return {"status": "success", "output_path": hpxml_path}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
```

## User Experience Enhancements

### 1. Drag and Drop Support
- Native drag-drop for H2K files
- Visual feedback during drag operations
- Automatic file validation on drop

### 2. Settings Persistence
```python
import json
from pathlib import Path

class SettingsManager:
    def __init__(self):
        self.settings_file = Path.home() / ".h2k_converter" / "settings.json"
        self.default_settings = {
            "recent_files": [],
            "default_output_path": "",
            "conversion_options": {},
            "window_geometry": "1200x800",
            "theme": "system"
        }
        
    def save_settings(self, settings):
        """Save current settings to file."""
        self.settings_file.parent.mkdir(exist_ok=True)
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
            
    def load_settings(self):
        """Load settings from file."""
        if self.settings_file.exists():
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        return self.default_settings.copy()
```

### 3. Help and Documentation
- Integrated help system with tooltips
- Context-sensitive help panels
- Quick start wizard for new users
- Link to external documentation

### 4. Error Handling and Validation
- Real-time input validation
- Clear error messages with suggestions
- Automatic recovery from common errors
- Detailed error logging

## Advanced Features

### 1. Batch Operation Templates
- Save common conversion configurations
- Quick apply of saved templates
- Import/export template configurations

### 2. File Preview
- Quick preview of H2K file contents
- Validation status display
- File metadata information

### 3. Performance Monitoring
- Real-time CPU and memory usage
- Conversion speed metrics
- Performance optimization suggestions

### 4. Integration Features
- Command-line argument import
- Export GUI settings as CLI commands
- Batch script generation

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Basic application window and layout
- [ ] File selection widget with validation
- [ ] Basic conversion options interface
- [ ] Integration with existing CLI conversion logic

### Phase 2: Progress and Results (Week 3)
- [ ] Progress tracking system
- [ ] Background processing implementation
- [ ] Results display and management
- [ ] Error handling and reporting

### Phase 3: Reports and Analysis (Week 4)
- [ ] Reports page with file selection
- [ ] Energy data loading from simulation results
- [ ] Basic charts (monthly, peak analysis)
- [ ] Energy summary calculations
- [ ] Export functionality (PDF, Excel, CSV)

### Phase 4: Advanced Analysis (Week 5)
- [ ] Hottest/coldest week analysis
- [ ] Interactive chart features
- [ ] Building comparison tools
- [ ] Advanced export options

### Phase 5: Polish and Advanced Features (Week 6)
- [ ] Drag and drop functionality
- [ ] Settings persistence
- [ ] Help system and documentation
- [ ] UI/UX refinements and testing

### Phase 6: Testing and Documentation (Week 7)
- [ ] Comprehensive testing (unit, integration, user acceptance)
- [ ] Performance optimization
- [ ] Documentation completion
- [ ] Final polish and bug fixes

## Key Reports Page Capabilities

### Energy Data Processing
- **SQL Integration**: Direct reading from `eplusout.sql` files generated by EnergyPlus
- **Data Validation**: Automatic checking of data completeness and quality
- **Caching**: Efficient data storage for quick re-analysis

### Chart Types and Analysis
1. **Monthly Overview**: Bar chart showing energy consumption by month with end-use breakdown
2. **Hottest Week Analysis**: Hourly energy profile during peak cooling period
3. **Coldest Week Analysis**: Hourly energy profile during peak heating period
4. **Peak Usage Identification**: Timeline analysis showing when and how peak electric demand occurs
5. **End-Use Breakdown**: Pie charts and bar charts showing heating, cooling, hot water, lighting, and appliance usage

### Export and Reporting
- **PDF Reports**: Professional formatted reports with charts, summary data, and analysis
- **Excel Workbooks**: Detailed data tables with multiple sheets for different time periods
- **CSV Data**: Raw data export for further analysis in other tools
- **PNG Charts**: High-quality chart images for presentations

### Advanced Features
- **Building Comparison**: Side-by-side analysis of multiple building simulations
- **Benchmark Analysis**: Compare against typical buildings or energy codes
- **Goal Tracking**: Set and monitor energy performance targets
- **Trend Analysis**: Multi-year comparison and trend identification

## Dependencies

### New Dependencies to Add
```toml
[project.optional-dependencies]
gui = [
    "customtkinter>=5.2.0",
    "pillow>=9.0.0",          # For image handling and icons
    "tkinterdnd2>=0.3.0",     # For drag-and-drop functionality
    "psutil>=5.8.0",          # For system resource monitoring
    "matplotlib>=3.7.0",     # For energy usage charts and graphs
    "pandas>=2.0.0",          # For energy data analysis and processing
    "numpy>=1.24.0",          # For numerical computations
    "sqlite3",                # For reading EnergyPlus SQL output (built-in)
    "openpyxl>=3.1.0",        # For Excel export functionality
    "reportlab>=4.0.0",       # For PDF report generation
]
```

### Entry Point Configuration
```toml
[project.scripts]
h2k-converter-gui = "h2k_hpxml.gui.app:main"
```

## Testing Strategy

### Unit Tests
- Individual widget functionality
- Settings management
- File validation logic
- Conversion wrapper functions

### Integration Tests
- End-to-end conversion workflows
- GUI-CLI integration
- Error handling scenarios
- Performance under load

### User Acceptance Tests
- Usability testing with target users
- Accessibility compliance
- Cross-platform compatibility
- Performance benchmarking

## Documentation Requirements

### User Documentation
- Installation and setup guide
- User manual with screenshots
- Tutorial videos
- FAQ and troubleshooting

### Developer Documentation
- Architecture overview
- API documentation
- Contribution guidelines
- Build and deployment instructions

## Additional Features and Enhancements

### 1. Complete CLI Integration

#### Resilience Analysis Integration (`widgets/resilience_widget.py`)

**Purpose:** Full integration of the `h2k-resilience` CLI tool with GUI interface

**Features:**
- Scenario selection interface (4 scenarios: power outage + normal/extreme weather, thermal autonomy + normal/extreme weather)
- Clothing factor configuration with presets
- HVAC scenario management
- Weather file selection (CWEC vs EWY)
- Results visualization and comparison

```python
class ResilienceAnalysisWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Scenario selection
        self.scenario_frame = ctk.CTkFrame(self)
        self.scenario_label = ctk.CTkLabel(self.scenario_frame, text="Analysis Scenarios:")
        
        # Power outage scenarios
        self.power_normal_var = ctk.BooleanVar(value=True)
        self.power_extreme_var = ctk.BooleanVar(value=True)
        self.power_normal_cb = ctk.CTkCheckBox(self.scenario_frame, text="Power Outage + Normal Weather", variable=self.power_normal_var)
        self.power_extreme_cb = ctk.CTkCheckBox(self.scenario_frame, text="Power Outage + Extreme Weather", variable=self.power_extreme_var)
        
        # Thermal autonomy scenarios
        self.thermal_normal_var = ctk.BooleanVar(value=True)
        self.thermal_extreme_var = ctk.BooleanVar(value=True)
        self.thermal_normal_cb = ctk.CTkCheckBox(self.scenario_frame, text="Thermal Autonomy + Normal Weather", variable=self.thermal_normal_var)
        self.thermal_extreme_cb = ctk.CTkCheckBox(self.scenario_frame, text="Thermal Autonomy + Extreme Weather", variable=self.thermal_extreme_var)
        
        # Clothing factor settings
        self.clothing_frame = ctk.CTkFrame(self)
        self.clothing_label = ctk.CTkLabel(self.clothing_frame, text="Clothing Factors:")
        self.summer_clothing = ctk.CTkEntry(self.clothing_frame, placeholder_text="Summer (default: 0.5)")
        self.winter_clothing = ctk.CTkEntry(self.clothing_frame, placeholder_text="Winter (default: 1.0)")
        
        # Weather file selection
        self.weather_frame = ctk.CTkFrame(self)
        self.weather_type = ctk.CTkSegmentedButton(self.weather_frame, values=["CWEC (Typical)", "EWY (Extreme)"])
        self.weather_type.set("CWEC (Typical)")
        
        # Results display
        self.results_tabview = ctk.CTkTabview(self)
        self.setup_resilience_results_tabs()
        
    def setup_resilience_results_tabs(self):
        """Setup tabs for different resilience analysis results."""
        self.temp_tab = self.results_tabview.add("Temperature Analysis")
        self.comfort_tab = self.results_tabview.add("Comfort Analysis") 
        self.duration_tab = self.results_tabview.add("Outage Duration")
        self.comparison_tab = self.results_tabview.add("Scenario Comparison")
        
    def run_resilience_analysis(self, h2k_file, output_path):
        """Execute resilience analysis using CLI backend."""
        from h2k_hpxml.cli.resilience import run_resilience_analysis
        
        # Build scenario list based on user selections
        scenarios = []
        if self.power_normal_var.get():
            scenarios.append("power_outage_normal")
        if self.power_extreme_var.get():
            scenarios.append("power_outage_extreme")
        if self.thermal_normal_var.get():
            scenarios.append("thermal_autonomy_normal")
        if self.thermal_extreme_var.get():
            scenarios.append("thermal_autonomy_extreme")
            
        # Execute analysis
        results = run_resilience_analysis(
            h2k_file=h2k_file,
            scenarios=scenarios,
            summer_clothing=float(self.summer_clothing.get() or "0.5"),
            winter_clothing=float(self.winter_clothing.get() or "1.0"),
            weather_type=self.weather_type.get().split()[0].lower(),
            output_path=output_path
        )
        
        self.display_resilience_results(results)
```

#### Dependency Management Integration (`widgets/dependency_manager.py`)

**Purpose:** GUI interface for the `h2k-deps` dependency management tool

**Features:**
- Visual dependency status checking
- One-click installation/uninstall
- Version management and updates
- Installation progress tracking

```python
class DependencyManagerWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Dependency status display
        self.status_frame = ctk.CTkFrame(self)
        self.openstudio_status = self.create_dependency_status("OpenStudio", "checking...")
        self.hpxml_status = self.create_dependency_status("OpenStudio-HPXML", "checking...")
        
        # Action buttons
        self.actions_frame = ctk.CTkFrame(self)
        self.check_button = ctk.CTkButton(self.actions_frame, text="🔍 Check Status", command=self.check_dependencies)
        self.install_button = ctk.CTkButton(self.actions_frame, text="📦 Auto Install", command=self.auto_install)
        self.uninstall_button = ctk.CTkButton(self.actions_frame, text="🗑️ Uninstall All", command=self.uninstall_all)
        
        # Installation progress
        self.progress_frame = ctk.CTkFrame(self)
        self.install_progress = ctk.CTkProgressBar(self.progress_frame)
        self.install_status = ctk.CTkLabel(self.progress_frame, text="")
        
        self.check_dependencies()  # Check on startup
        
    def create_dependency_status(self, name, status):
        """Create status display for a dependency."""
        frame = ctk.CTkFrame(self.status_frame)
        name_label = ctk.CTkLabel(frame, text=name, font=("Arial", 14, "bold"))
        status_label = ctk.CTkLabel(frame, text=status)
        version_label = ctk.CTkLabel(frame, text="")
        
        name_label.pack(anchor="w", padx=10, pady=2)
        status_label.pack(anchor="w", padx=10)
        version_label.pack(anchor="w", padx=10)
        
        return {
            "frame": frame,
            "status": status_label,
            "version": version_label
        }
        
    def check_dependencies(self):
        """Check dependency status using CLI backend."""
        from h2k_hpxml.utils.dependencies import DependencyManager
        
        dep_manager = DependencyManager()
        
        # Check OpenStudio
        os_status = dep_manager.check_openstudio()
        self.update_dependency_status("openstudio", os_status)
        
        # Check OpenStudio-HPXML
        hpxml_status = dep_manager.check_openstudio_hpxml()
        self.update_dependency_status("hpxml", hpxml_status)
        
    def update_dependency_status(self, dep_type, status):
        """Update dependency status display."""
        if dep_type == "openstudio":
            widget = self.openstudio_status
        else:
            widget = self.hpxml_status
            
        if status["installed"]:
            widget["status"].configure(text="✅ Installed", text_color="green")
            widget["version"].configure(text=f"Version: {status['version']}")
        else:
            widget["status"].configure(text="❌ Not Found", text_color="red")
            widget["version"].configure(text="")
```

### 2. Error Recovery & User Feedback System

#### Notification System (`utils/notifications.py`)

**Purpose:** Toast notifications and user feedback for all GUI operations

**Features:**
- Non-blocking toast notifications for status updates
- Progress notifications for long-running operations
- Error alerts with suggested actions
- Success confirmations with quick actions

```python
import tkinter as tk
from typing import Literal, Optional, Callable
import threading
import time

class NotificationManager:
    """Manages toast notifications and user feedback."""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.active_notifications = []
        
    def show_toast(self, 
                   message: str, 
                   notification_type: Literal["info", "success", "warning", "error"] = "info",
                   duration: int = 3000,
                   action_text: Optional[str] = None,
                   action_callback: Optional[Callable] = None):
        """Show a toast notification."""
        
        toast = ToastNotification(
            parent=self.parent,
            message=message,
            notification_type=notification_type,
            duration=duration,
            action_text=action_text,
            action_callback=action_callback
        )
        
        self.active_notifications.append(toast)
        toast.show()
        
    def show_progress_notification(self, title: str, initial_message: str = "Starting..."):
        """Show a persistent progress notification."""
        progress_toast = ProgressNotification(self.parent, title, initial_message)
        self.active_notifications.append(progress_toast)
        return progress_toast
        
    def clear_all(self):
        """Clear all active notifications."""
        for notification in self.active_notifications:
            notification.hide()
        self.active_notifications.clear()

class ToastNotification:
    """Individual toast notification widget."""
    
    def __init__(self, parent, message, notification_type, duration, action_text=None, action_callback=None):
        self.parent = parent
        self.message = message
        self.type = notification_type
        self.duration = duration
        self.action_text = action_text
        self.action_callback = action_callback
        
        # Create notification window
        self.window = tk.Toplevel(parent)
        self.window.withdraw()  # Hide initially
        self.setup_window()
        
    def setup_window(self):
        """Setup the toast notification window."""
        self.window.overrideredirect(True)  # Remove window decorations
        self.window.configure(bg=self.get_bg_color())
        
        # Main frame
        main_frame = tk.Frame(self.window, bg=self.get_bg_color(), padx=15, pady=10)
        main_frame.pack(fill="both", expand=True)
        
        # Icon and message
        content_frame = tk.Frame(main_frame, bg=self.get_bg_color())
        content_frame.pack(side="left", fill="both", expand=True)
        
        icon_label = tk.Label(content_frame, text=self.get_icon(), 
                             font=("Arial", 14), bg=self.get_bg_color(), fg="white")
        icon_label.pack(side="left", padx=(0, 10))
        
        message_label = tk.Label(content_frame, text=self.message,
                               font=("Arial", 10), bg=self.get_bg_color(), fg="white",
                               wraplength=300)
        message_label.pack(side="left", fill="both", expand=True)
        
        # Action button if provided
        if self.action_text and self.action_callback:
            action_btn = tk.Button(main_frame, text=self.action_text,
                                 command=self.action_callback,
                                 font=("Arial", 9), relief="flat",
                                 bg="white", fg=self.get_bg_color())
            action_btn.pack(side="right", padx=(10, 0))
            
    def get_bg_color(self):
        """Get background color based on notification type."""
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50", 
            "warning": "#FF9800",
            "error": "#F44336"
        }
        return colors.get(self.type, "#2196F3")
        
    def get_icon(self):
        """Get icon based on notification type."""
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️", 
            "error": "❌"
        }
        return icons.get(self.type, "ℹ️")
        
    def show(self):
        """Show the toast notification."""
        # Position at top-right of parent window
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        
        self.window.update_idletasks()
        toast_width = self.window.winfo_reqwidth()
        
        x = parent_x + parent_width - toast_width - 20
        y = parent_y + 20
        
        self.window.geometry(f"+{x}+{y}")
        self.window.deiconify()
        
        # Auto-hide after duration
        if self.duration > 0:
            self.window.after(self.duration, self.hide)
            
    def hide(self):
        """Hide and destroy the toast notification."""
        self.window.destroy()

class ProgressNotification:
    """Persistent progress notification for long operations."""
    
    def __init__(self, parent, title, initial_message):
        self.parent = parent
        self.title = title
        self.window = tk.Toplevel(parent)
        self.setup_window()
        self.update_message(initial_message)
        
    def setup_window(self):
        """Setup progress notification window."""
        self.window.title(self.title)
        self.window.geometry("400x120")
        self.window.resizable(False, False)
        
        # Center on parent
        self.window.transient(self.parent)
        self.window.grab_set()
        
        main_frame = tk.Frame(self.window, padx=20, pady=15)
        main_frame.pack(fill="both", expand=True)
        
        self.message_label = tk.Label(main_frame, text="", font=("Arial", 10))
        self.message_label.pack(anchor="w", pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = tk.ttk.Progressbar(main_frame, variable=self.progress_var, 
                                              mode="determinate", length=360)
        self.progress_bar.pack(fill="x", pady=(0, 10))
        
        self.cancel_button = tk.Button(main_frame, text="Cancel", command=self.cancel)
        self.cancel_button.pack(anchor="e")
        
    def update_message(self, message):
        """Update progress message."""
        self.message_label.configure(text=message)
        
    def update_progress(self, percent):
        """Update progress bar."""
        self.progress_var.set(percent)
        
    def cancel(self):
        """Handle cancel button."""
        # Implementation depends on the operation being cancelled
        pass
        
    def complete(self, success=True, final_message=""):
        """Complete the progress notification."""
        if success:
            self.message_label.configure(text=final_message or "Completed successfully!")
            self.progress_var.set(100)
            self.cancel_button.configure(text="Close")
        else:
            self.message_label.configure(text=final_message or "Operation failed!")
            self.cancel_button.configure(text="Close")
```

#### Error Recovery System (`utils/error_recovery.py`)

**Purpose:** Automatic error recovery and user-guided problem resolution

**Features:**
- Automatic retry with exponential backoff
- User-guided error resolution workflows
- Error categorization and suggested fixes
- Recovery state persistence

```python
import time
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class ErrorCategory(Enum):
    FILE_ACCESS = "file_access"
    DEPENDENCY_MISSING = "dependency_missing"
    CONVERSION_FAILED = "conversion_failed"
    SIMULATION_FAILED = "simulation_failed"
    NETWORK_ERROR = "network_error"
    PERMISSION_ERROR = "permission_error"
    VALIDATION_ERROR = "validation_error"

@dataclass
class ErrorInfo:
    category: ErrorCategory
    message: str
    original_exception: Exception
    file_path: Optional[str] = None
    suggested_actions: List[str] = None
    auto_recoverable: bool = False
    recovery_function: Optional[Callable] = None

class ErrorRecoveryManager:
    """Manages error recovery workflows and retry logic."""
    
    def __init__(self, notification_manager):
        self.notifications = notification_manager
        self.recovery_state_file = Path.home() / ".h2k_converter" / "recovery_state.json"
        self.recovery_state = self.load_recovery_state()
        
    def categorize_error(self, exception: Exception, context: Dict) -> ErrorInfo:
        """Categorize an error and provide recovery suggestions."""
        
        error_message = str(exception)
        
        # File access errors
        if isinstance(exception, (FileNotFoundError, PermissionError)):
            if isinstance(exception, PermissionError):
                return ErrorInfo(
                    category=ErrorCategory.PERMISSION_ERROR,
                    message=f"Permission denied: {error_message}",
                    original_exception=exception,
                    file_path=context.get("file_path"),
                    suggested_actions=[
                        "Check file permissions",
                        "Run as administrator",
                        "Move files to a different location",
                        "Close any programs using the files"
                    ],
                    auto_recoverable=False
                )
            else:
                return ErrorInfo(
                    category=ErrorCategory.FILE_ACCESS,
                    message=f"File not found: {error_message}",
                    original_exception=exception,
                    file_path=context.get("file_path"),
                    suggested_actions=[
                        "Check if the file path is correct",
                        "Verify the file hasn't been moved or deleted",
                        "Select a different file"
                    ],
                    auto_recoverable=False
                )
        
        # Dependency errors
        if "openstudio" in error_message.lower() or "hpxml" in error_message.lower():
            return ErrorInfo(
                category=ErrorCategory.DEPENDENCY_MISSING,
                message="Missing or corrupted dependencies",
                original_exception=exception,
                suggested_actions=[
                    "Install OpenStudio and OpenStudio-HPXML using the dependency manager",
                    "Check system PATH configuration",
                    "Reinstall dependencies"
                ],
                auto_recoverable=True,
                recovery_function=self.recover_dependencies
            )
        
        # Network errors (for weather file downloads)
        if "network" in error_message.lower() or "connection" in error_message.lower():
            return ErrorInfo(
                category=ErrorCategory.NETWORK_ERROR,
                message="Network connection failed",
                original_exception=exception,
                suggested_actions=[
                    "Check internet connection",
                    "Try again in a few moments",
                    "Use cached weather files if available"
                ],
                auto_recoverable=True,
                recovery_function=self.recover_network_error
            )
        
        # Default categorization
        return ErrorInfo(
            category=ErrorCategory.CONVERSION_FAILED,
            message=error_message,
            original_exception=exception,
            suggested_actions=[
                "Check the H2K file for corruption",
                "Try with a different H2K file",
                "Contact support with error details"
            ],
            auto_recoverable=False
        )
    
    def handle_error(self, exception: Exception, context: Dict, auto_retry: bool = True) -> bool:
        """Handle an error with recovery options."""
        
        error_info = self.categorize_error(exception, context)
        
        # Try automatic recovery first
        if auto_retry and error_info.auto_recoverable and error_info.recovery_function:
            success = self.attempt_auto_recovery(error_info, context)
            if success:
                return True
        
        # Show error to user with recovery options
        self.show_error_dialog(error_info, context)
        return False
        
    def attempt_auto_recovery(self, error_info: ErrorInfo, context: Dict, max_retries: int = 3) -> bool:
        """Attempt automatic error recovery with exponential backoff."""
        
        operation_id = context.get("operation_id", "unknown")
        retry_count = self.recovery_state.get(operation_id, {}).get("retry_count", 0)
        
        if retry_count >= max_retries:
            return False
            
        # Update retry count
        if operation_id not in self.recovery_state:
            self.recovery_state[operation_id] = {}
        self.recovery_state[operation_id]["retry_count"] = retry_count + 1
        self.save_recovery_state()
        
        # Show progress notification
        progress = self.notifications.show_progress_notification(
            "Error Recovery", 
            f"Attempting automatic recovery (attempt {retry_count + 1}/{max_retries})..."
        )
        
        try:
            # Wait with exponential backoff
            wait_time = 2 ** retry_count
            time.sleep(wait_time)
            
            # Call recovery function
            success = error_info.recovery_function(error_info, context)
            
            if success:
                progress.complete(True, "Recovery successful!")
                # Reset retry count on success
                self.recovery_state[operation_id]["retry_count"] = 0
                self.save_recovery_state()
                return True
            else:
                progress.complete(False, "Automatic recovery failed")
                return False
                
        except Exception as e:
            progress.complete(False, f"Recovery failed: {str(e)}")
            return False
    
    def show_error_dialog(self, error_info: ErrorInfo, context: Dict):
        """Show error dialog with recovery options."""
        
        # Create custom error dialog
        dialog = ErrorRecoveryDialog(
            parent=self.notifications.parent,
            error_info=error_info,
            context=context,
            recovery_manager=self
        )
        dialog.show()
    
    def recover_dependencies(self, error_info: ErrorInfo, context: Dict) -> bool:
        """Attempt to recover from dependency errors."""
        try:
            from h2k_hpxml.utils.dependencies import DependencyManager
            
            dep_manager = DependencyManager()
            success = dep_manager.auto_install()
            return success
        except Exception:
            return False
    
    def recover_network_error(self, error_info: ErrorInfo, context: Dict) -> bool:
        """Attempt to recover from network errors."""
        try:
            # Try to use cached files or alternative sources
            # Implementation depends on specific network operation
            return True
        except Exception:
            return False
    
    def load_recovery_state(self) -> Dict:
        """Load recovery state from file."""
        if self.recovery_state_file.exists():
            try:
                with open(self.recovery_state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def save_recovery_state(self):
        """Save recovery state to file."""
        self.recovery_state_file.parent.mkdir(exist_ok=True)
        with open(self.recovery_state_file, 'w') as f:
            json.dump(self.recovery_state, f, indent=2)

class ErrorRecoveryDialog:
    """Dialog for user-guided error recovery."""
    
    def __init__(self, parent, error_info: ErrorInfo, context: Dict, recovery_manager):
        self.parent = parent
        self.error_info = error_info
        self.context = context
        self.recovery_manager = recovery_manager
        
    def show(self):
        """Show the error recovery dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Error Recovery")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self.setup_dialog()
        
    def setup_dialog(self):
        """Setup the error recovery dialog UI."""
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Error icon and title
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 15))
        
        error_icon = tk.Label(header_frame, text="❌", font=("Arial", 24))
        error_icon.pack(side="left")
        
        title_label = tk.Label(header_frame, text="Operation Failed", 
                              font=("Arial", 14, "bold"))
        title_label.pack(side="left", padx=(10, 0))
        
        # Error message
        message_frame = tk.Frame(main_frame)
        message_frame.pack(fill="x", pady=(0, 15))
        
        message_label = tk.Label(message_frame, text=self.error_info.message,
                               wraplength=450, justify="left")
        message_label.pack(anchor="w")
        
        # Suggested actions
        if self.error_info.suggested_actions:
            actions_label = tk.Label(main_frame, text="Suggested Actions:",
                                   font=("Arial", 11, "bold"))
            actions_label.pack(anchor="w", pady=(0, 5))
            
            for i, action in enumerate(self.error_info.suggested_actions, 1):
                action_label = tk.Label(main_frame, text=f"{i}. {action}",
                                      wraplength=450, justify="left")
                action_label.pack(anchor="w", padx=(10, 0))
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        if self.error_info.auto_recoverable:
            retry_btn = tk.Button(button_frame, text="Retry",
                                command=self.retry_operation)
            retry_btn.pack(side="right", padx=(5, 0))
        
        skip_btn = tk.Button(button_frame, text="Skip",
                           command=self.skip_operation)
        skip_btn.pack(side="right", padx=(5, 0))
        
        cancel_btn = tk.Button(button_frame, text="Cancel All",
                             command=self.cancel_all)
        cancel_btn.pack(side="right")
        
    def retry_operation(self):
        """Retry the failed operation."""
        self.dialog.destroy()
        # Trigger retry through recovery manager
        self.recovery_manager.attempt_auto_recovery(self.error_info, self.context)
        
    def skip_operation(self):
        """Skip the current operation and continue with next."""
        self.dialog.destroy()
        # Signal to continue with next operation
        
    def cancel_all(self):
        """Cancel all pending operations."""
        self.dialog.destroy()
        # Signal to cancel all operations
```

### 3. Configuration Management System

#### Configuration Editor Widget (`widgets/config_editor.py`)

**Purpose:** GUI interface for editing conversionconfig.ini and other configuration files

**Features:**
- Visual editing of all configuration parameters
- Real-time validation of settings
- Configuration presets and templates
- Import/export configurations
- Weather file management

```python
class ConfigurationEditorWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.config_file = Path("conversionconfig.ini")
        self.config = self.load_config()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup configuration editor interface."""
        # Header with load/save buttons
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(header_frame, text="⚙️ Configuration Editor", 
                                  font=("Arial", 16, "bold"))
        title_label.pack(side="left", padx=10)
        
        buttons_frame = ctk.CTkFrame(header_frame)
        buttons_frame.pack(side="right", padx=10)
        
        load_btn = ctk.CTkButton(buttons_frame, text="📁 Load Config", command=self.load_config_file)
        load_btn.pack(side="left", padx=5)
        
        save_btn = ctk.CTkButton(buttons_frame, text="💾 Save Config", command=self.save_config_file)
        save_btn.pack(side="left", padx=5)
        
        reset_btn = ctk.CTkButton(buttons_frame, text="🔄 Reset to Default", command=self.reset_to_default)
        reset_btn.pack(side="left", padx=5)
        
        # Tabbed configuration sections
        self.config_tabview = ctk.CTkTabview(self)
        self.config_tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs for different config sections
        self.paths_tab = self.config_tabview.add("Paths & Files")
        self.simulation_tab = self.config_tabview.add("Simulation")
        self.weather_tab = self.config_tabview.add("Weather")
        self.output_tab = self.config_tabview.add("Output")
        self.advanced_tab = self.config_tabview.add("Advanced")
        
        self.setup_config_tabs()
        
    def setup_config_tabs(self):
        """Setup individual configuration tabs."""
        self.setup_paths_tab()
        self.setup_simulation_tab()
        self.setup_weather_tab()
        self.setup_output_tab()
        self.setup_advanced_tab()
        
    def setup_paths_tab(self):
        """Setup paths and files configuration."""
        # H2K input directory
        input_frame = ctk.CTkFrame(self.paths_tab)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        input_label = ctk.CTkLabel(input_frame, text="H2K Input Directory:")
        input_label.pack(anchor="w", padx=10, pady=5)
        
        input_path_frame = ctk.CTkFrame(input_frame)
        input_path_frame.pack(fill="x", padx=10, pady=5)
        
        self.input_path_var = ctk.StringVar(value=self.config.get("paths", {}).get("h2k_input", ""))
        self.input_path_entry = ctk.CTkEntry(input_path_frame, textvariable=self.input_path_var)
        self.input_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        input_browse_btn = ctk.CTkButton(input_path_frame, text="📁", width=40, 
                                        command=lambda: self.browse_directory(self.input_path_var))
        input_browse_btn.pack(side="right")
        
        # Output directory
        output_frame = ctk.CTkFrame(self.paths_tab)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        output_label = ctk.CTkLabel(output_frame, text="Output Directory:")
        output_label.pack(anchor="w", padx=10, pady=5)
        
        output_path_frame = ctk.CTkFrame(output_frame)
        output_path_frame.pack(fill="x", padx=10, pady=5)
        
        self.output_path_var = ctk.StringVar(value=self.config.get("paths", {}).get("output", ""))
        self.output_path_entry = ctk.CTkEntry(output_path_frame, textvariable=self.output_path_var)
        self.output_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        output_browse_btn = ctk.CTkButton(output_path_frame, text="📁", width=40,
                                         command=lambda: self.browse_directory(self.output_path_var))
        output_browse_btn.pack(side="right")
        
        # OpenStudio-HPXML path
        hpxml_frame = ctk.CTkFrame(self.paths_tab)
        hpxml_frame.pack(fill="x", padx=10, pady=5)
        
        hpxml_label = ctk.CTkLabel(hpxml_frame, text="OpenStudio-HPXML Path:")
        hpxml_label.pack(anchor="w", padx=10, pady=5)
        
        hpxml_path_frame = ctk.CTkFrame(hpxml_frame)
        hpxml_path_frame.pack(fill="x", padx=10, pady=5)
        
        self.hpxml_path_var = ctk.StringVar(value=self.config.get("paths", {}).get("openstudio_hpxml", "/OpenStudio-HPXML"))
        self.hpxml_path_entry = ctk.CTkEntry(hpxml_path_frame, textvariable=self.hpxml_path_var)
        self.hpxml_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        hpxml_browse_btn = ctk.CTkButton(hpxml_path_frame, text="📁", width=40,
                                        command=lambda: self.browse_directory(self.hpxml_path_var))
        hpxml_browse_btn.pack(side="right")
        
    def setup_simulation_tab(self):
        """Setup simulation configuration options."""
        # Simulation settings
        sim_frame = ctk.CTkFrame(self.simulation_tab)
        sim_frame.pack(fill="x", padx=10, pady=10)
        
        sim_label = ctk.CTkLabel(sim_frame, text="Simulation Settings", font=("Arial", 14, "bold"))
        sim_label.pack(anchor="w", padx=10, pady=5)
        
        # Run simulation checkbox
        self.run_simulation_var = ctk.BooleanVar(value=self.config.get("simulation", {}).get("run", True))
        run_sim_cb = ctk.CTkCheckBox(sim_frame, text="Run OpenStudio Simulation", 
                                    variable=self.run_simulation_var)
        run_sim_cb.pack(anchor="w", padx=10, pady=2)
        
        # Add component loads
        self.component_loads_var = ctk.BooleanVar(value=self.config.get("simulation", {}).get("component_loads", True))
        comp_loads_cb = ctk.CTkCheckBox(sim_frame, text="Add Component Loads",
                                       variable=self.component_loads_var)
        comp_loads_cb.pack(anchor="w", padx=10, pady=2)
        
        # Debug mode
        self.debug_mode_var = ctk.BooleanVar(value=self.config.get("simulation", {}).get("debug", False))
        debug_cb = ctk.CTkCheckBox(sim_frame, text="Debug Mode",
                                  variable=self.debug_mode_var)
        debug_cb.pack(anchor="w", padx=10, pady=2)
        
        # Validation settings
        validation_frame = ctk.CTkFrame(self.simulation_tab)
        validation_frame.pack(fill="x", padx=10, pady=10)
        
        validation_label = ctk.CTkLabel(validation_frame, text="Validation Settings", font=("Arial", 14, "bold"))
        validation_label.pack(anchor="w", padx=10, pady=5)
        
        self.skip_validation_var = ctk.BooleanVar(value=self.config.get("validation", {}).get("skip", False))
        skip_val_cb = ctk.CTkCheckBox(validation_frame, text="Skip HPXML Validation (faster but less safe)",
                                     variable=self.skip_validation_var)
        skip_val_cb.pack(anchor="w", padx=10, pady=2)
        
    def setup_weather_tab(self):
        """Setup weather configuration options."""
        weather_frame = ctk.CTkFrame(self.weather_tab)
        weather_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        weather_label = ctk.CTkLabel(weather_frame, text="Weather Configuration", font=("Arial", 14, "bold"))
        weather_label.pack(anchor="w", padx=10, pady=5)
        
        # Weather file source
        source_frame = ctk.CTkFrame(weather_frame)
        source_frame.pack(fill="x", padx=10, pady=5)
        
        source_label = ctk.CTkLabel(source_frame, text="Weather File Source:")
        source_label.pack(anchor="w", padx=10, pady=5)
        
        self.weather_source_var = ctk.StringVar(value=self.config.get("weather", {}).get("source", "auto"))
        weather_source_menu = ctk.CTkOptionMenu(source_frame, 
                                               values=["auto", "local", "download"],
                                               variable=self.weather_source_var)
        weather_source_menu.pack(anchor="w", padx=10, pady=5)
        
        # Weather type preference
        type_frame = ctk.CTkFrame(weather_frame)
        type_frame.pack(fill="x", padx=10, pady=5)
        
        type_label = ctk.CTkLabel(type_frame, text="Preferred Weather Type:")
        type_label.pack(anchor="w", padx=10, pady=5)
        
        self.weather_type_var = ctk.StringVar(value=self.config.get("weather", {}).get("type", "CWEC"))
        weather_type_menu = ctk.CTkOptionMenu(type_frame,
                                             values=["CWEC (Typical)", "EWY (Extreme)", "Both"],
                                             variable=self.weather_type_var)
        weather_type_menu.pack(anchor="w", padx=10, pady=5)
        
        # Weather files management
        files_frame = ctk.CTkFrame(weather_frame)
        files_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        files_label = ctk.CTkLabel(files_frame, text="Weather Files Management:")
        files_label.pack(anchor="w", padx=10, pady=5)
        
        # Weather files list
        self.weather_files_list = ctk.CTkScrollableFrame(files_frame, height=200)
        self.weather_files_list.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Weather management buttons
        weather_buttons_frame = ctk.CTkFrame(files_frame)
        weather_buttons_frame.pack(fill="x", padx=10, pady=5)
        
        refresh_weather_btn = ctk.CTkButton(weather_buttons_frame, text="🔄 Refresh List", 
                                           command=self.refresh_weather_files)
        refresh_weather_btn.pack(side="left", padx=5)
        
        download_weather_btn = ctk.CTkButton(weather_buttons_frame, text="📥 Download Missing",
                                            command=self.download_missing_weather)
        download_weather_btn.pack(side="left", padx=5)
        
        clear_cache_btn = ctk.CTkButton(weather_buttons_frame, text="🗑️ Clear Cache",
                                       command=self.clear_weather_cache)
        clear_cache_btn.pack(side="left", padx=5)
        
        self.refresh_weather_files()
        
    def setup_output_tab(self):
        """Setup output configuration options."""
        output_frame = ctk.CTkFrame(self.output_tab)
        output_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Output frequency settings
        freq_frame = ctk.CTkFrame(output_frame)
        freq_frame.pack(fill="x", padx=10, pady=5)
        
        freq_label = ctk.CTkLabel(freq_frame, text="Output Frequency", font=("Arial", 14, "bold"))
        freq_label.pack(anchor="w", padx=10, pady=5)
        
        # Timestep outputs
        timestep_frame = ctk.CTkFrame(freq_frame)
        timestep_frame.pack(fill="x", padx=10, pady=5)
        
        timestep_label = ctk.CTkLabel(timestep_frame, text="Timestep Outputs:")
        timestep_label.pack(anchor="w", padx=10, pady=2)
        
        self.timestep_all_var = ctk.BooleanVar(value=self.config.get("output", {}).get("timestep_all", False))
        timestep_all_cb = ctk.CTkCheckBox(timestep_frame, text="All", variable=self.timestep_all_var)
        timestep_all_cb.pack(side="left", padx=10)
        
        self.timestep_total_var = ctk.BooleanVar(value=self.config.get("output", {}).get("timestep_total", True))
        timestep_total_cb = ctk.CTkCheckBox(timestep_frame, text="Total", variable=self.timestep_total_var)
        timestep_total_cb.pack(side="left", padx=10)
        
        self.timestep_fuels_var = ctk.BooleanVar(value=self.config.get("output", {}).get("timestep_fuels", True))
        timestep_fuels_cb = ctk.CTkCheckBox(timestep_frame, text="Fuels", variable=self.timestep_fuels_var)
        timestep_fuels_cb.pack(side="left", padx=10)
        
        # Similar for daily, hourly, monthly...
        
    def setup_advanced_tab(self):
        """Setup advanced configuration options."""
        advanced_frame = ctk.CTkFrame(self.advanced_tab)
        advanced_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Performance settings
        perf_frame = ctk.CTkFrame(advanced_frame)
        perf_frame.pack(fill="x", padx=10, pady=5)
        
        perf_label = ctk.CTkLabel(perf_frame, text="Performance Settings", font=("Arial", 14, "bold"))
        perf_label.pack(anchor="w", padx=10, pady=5)
        
        # Thread count
        thread_frame = ctk.CTkFrame(perf_frame)
        thread_frame.pack(fill="x", padx=10, pady=5)
        
        thread_label = ctk.CTkLabel(thread_frame, text="Max Concurrent Conversions:")
        thread_label.pack(side="left", padx=10, pady=5)
        
        self.thread_count_var = ctk.StringVar(value=str(self.config.get("performance", {}).get("max_threads", 4)))
        thread_spinbox = ctk.CTkEntry(thread_frame, textvariable=self.thread_count_var, width=80)
        thread_spinbox.pack(side="left", padx=10)
        
        # Memory limit
        memory_frame = ctk.CTkFrame(perf_frame)
        memory_frame.pack(fill="x", padx=10, pady=5)
        
        memory_label = ctk.CTkLabel(memory_frame, text="Memory Limit (MB):")
        memory_label.pack(side="left", padx=10, pady=5)
        
        self.memory_limit_var = ctk.StringVar(value=str(self.config.get("performance", {}).get("memory_limit", 2048)))
        memory_entry = ctk.CTkEntry(memory_frame, textvariable=self.memory_limit_var, width=80)
        memory_entry.pack(side="left", padx=10)
        
    def load_config(self):
        """Load configuration from file."""
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(self.config_file)
            
            # Convert to dict for easier handling
            config_dict = {}
            for section in config.sections():
                config_dict[section] = dict(config[section])
                
            return config_dict
        except Exception:
            return {}
            
    def save_config_file(self):
        """Save configuration to file."""
        try:
            import configparser
            config = configparser.ConfigParser()
            
            # Build config from UI values
            self.update_config_from_ui()
            
            # Write sections
            for section_name, section_data in self.config.items():
                config.add_section(section_name)
                for key, value in section_data.items():
                    config.set(section_name, key, str(value))
                    
            with open(self.config_file, 'w') as f:
                config.write(f)
                
            self.show_success_message("Configuration saved successfully!")
            
        except Exception as e:
            self.show_error_message(f"Failed to save configuration: {str(e)}")
            
    def update_config_from_ui(self):
        """Update config dict from UI values."""
        # Update paths
        if "paths" not in self.config:
            self.config["paths"] = {}
        self.config["paths"]["h2k_input"] = self.input_path_var.get()
        self.config["paths"]["output"] = self.output_path_var.get()
        self.config["paths"]["openstudio_hpxml"] = self.hpxml_path_var.get()
        
        # Update simulation settings
        if "simulation" not in self.config:
            self.config["simulation"] = {}
        self.config["simulation"]["run"] = str(self.run_simulation_var.get())
        self.config["simulation"]["component_loads"] = str(self.component_loads_var.get())
        self.config["simulation"]["debug"] = str(self.debug_mode_var.get())
        
        # Continue for other sections...
        
    def browse_directory(self, string_var):
        """Browse for directory and update string variable."""
        from tkinter import filedialog
        directory = filedialog.askdirectory()
        if directory:
            string_var.set(directory)
            
    def refresh_weather_files(self):
        """Refresh the weather files list."""
        # Clear existing list
        for widget in self.weather_files_list.winfo_children():
            widget.destroy()
            
        # Get weather files from utils directory
        weather_dir = Path("src/h2k_hpxml/utils")
        if weather_dir.exists():
            weather_files = list(weather_dir.glob("*.epw"))
            
            for weather_file in weather_files:
                file_frame = ctk.CTkFrame(self.weather_files_list)
                file_frame.pack(fill="x", padx=5, pady=2)
                
                file_label = ctk.CTkLabel(file_frame, text=weather_file.name)
                file_label.pack(side="left", padx=10, pady=5)
                
                size_label = ctk.CTkLabel(file_frame, text=f"{weather_file.stat().st_size // 1024} KB")
                size_label.pack(side="right", padx=10, pady=5)
                
    def download_missing_weather(self):
        """Download missing weather files."""
        # Implementation for downloading weather files
        pass
        
    def clear_weather_cache(self):
        """Clear weather file cache."""
        # Implementation for clearing cache
        pass
```

#### Project Workspace Manager (`widgets/workspace_manager.py`)

**Purpose:** Save and load complete conversion project configurations

**Features:**
- Project templates with predefined settings
- Recent projects list
- Project import/export
- Workspace persistence

```python
class WorkspaceManagerWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.projects_dir = Path.home() / ".h2k_converter" / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        self.setup_ui()
        self.load_recent_projects()
        
    def setup_ui(self):
        """Setup workspace manager interface."""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(header_frame, text="💼 Project Workspace", 
                                  font=("Arial", 16, "bold"))
        title_label.pack(side="left", padx=10)
        
        # Project actions
        actions_frame = ctk.CTkFrame(header_frame)
        actions_frame.pack(side="right", padx=10)
        
        new_btn = ctk.CTkButton(actions_frame, text="📄 New Project", command=self.new_project)
        new_btn.pack(side="left", padx=5)
        
        save_btn = ctk.CTkButton(actions_frame, text="💾 Save Project", command=self.save_project)
        save_btn.pack(side="left", padx=5)
        
        load_btn = ctk.CTkButton(actions_frame, text="📁 Load Project", command=self.load_project)
        load_btn.pack(side="left", padx=5)
        
        # Recent projects list
        recent_frame = ctk.CTkFrame(self)
        recent_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        recent_label = ctk.CTkLabel(recent_frame, text="Recent Projects:")
        recent_label.pack(anchor="w", padx=10, pady=5)
        
        self.recent_list = ctk.CTkScrollableFrame(recent_frame, height=200)
        self.recent_list.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Project templates
        templates_frame = ctk.CTkFrame(self)
        templates_frame.pack(fill="x", padx=10, pady=10)
        
        templates_label = ctk.CTkLabel(templates_frame, text="Project Templates:")
        templates_label.pack(anchor="w", padx=10, pady=5)
        
        template_buttons_frame = ctk.CTkFrame(templates_frame)
        template_buttons_frame.pack(fill="x", padx=10, pady=5)
        
        quick_btn = ctk.CTkButton(template_buttons_frame, text="⚡ Quick Conversion", 
                                 command=lambda: self.load_template("quick"))
        quick_btn.pack(side="left", padx=5)
        
        standard_btn = ctk.CTkButton(template_buttons_frame, text="📊 Standard Analysis",
                                    command=lambda: self.load_template("standard"))
        standard_btn.pack(side="left", padx=5)
        
        detailed_btn = ctk.CTkButton(template_buttons_frame, text="🔬 Detailed Research",
                                    command=lambda: self.load_template("detailed"))
        detailed_btn.pack(side="left", padx=5)
        
        resilience_btn = ctk.CTkButton(template_buttons_frame, text="🏠 Resilience Study",
                                      command=lambda: self.load_template("resilience"))
        resilience_btn.pack(side="left", padx=5)
        
    def new_project(self):
        """Create a new project."""
        dialog = ProjectNameDialog(self, title="New Project")
        if dialog.result:
            project_name = dialog.result
            self.create_project(project_name)
            
    def save_project(self):
        """Save current project configuration."""
        # Get current settings from all widgets
        project_data = {
            "name": "Current Project",
            "created": time.time(),
            "files": [],  # Get from file selector
            "settings": {},  # Get from config widgets
            "output_path": "",  # Get from file selector
        }
        
        dialog = ProjectNameDialog(self, title="Save Project As")
        if dialog.result:
            project_name = dialog.result
            project_file = self.projects_dir / f"{project_name}.json"
            
            with open(project_file, 'w') as f:
                json.dump(project_data, f, indent=2)
                
            self.load_recent_projects()
            
    def load_project(self):
        """Load a project configuration."""
        from tkinter import filedialog
        project_file = filedialog.askopenfilename(
            title="Load Project",
            initialdir=self.projects_dir,
            filetypes=[("Project files", "*.json")]
        )
        
        if project_file:
            self.load_project_file(project_file)
            
    def load_template(self, template_type):
        """Load a predefined project template."""
        templates = {
            "quick": {
                "name": "Quick Conversion",
                "settings": {
                    "simulation": {"run": False},
                    "output": {"timestep_all": False, "timestep_total": True},
                    "validation": {"skip": True}
                }
            },
            "standard": {
                "name": "Standard Analysis", 
                "settings": {
                    "simulation": {"run": True, "component_loads": True},
                    "output": {"timestep_total": True, "timestep_fuels": True, "hourly_all": True},
                    "validation": {"skip": False}
                }
            },
            "detailed": {
                "name": "Detailed Research",
                "settings": {
                    "simulation": {"run": True, "component_loads": True, "debug": True},
                    "output": {"timestep_all": True, "hourly_all": True, "monthly_all": True},
                    "validation": {"skip": False}
                }
            },
            "resilience": {
                "name": "Resilience Study",
                "settings": {
                    "simulation": {"run": True, "component_loads": True},
                    "resilience": {"enabled": True, "scenarios": ["all"]},
                    "weather": {"type": "Both"}
                }
            }
        }
        
        template = templates.get(template_type)
        if template:
            self.apply_template(template)
            
    def apply_template(self, template):
        """Apply template settings to current configuration."""
        # Apply template settings to various widgets
        # This would integrate with the configuration editor and other widgets
        pass
        
    def load_recent_projects(self):
        """Load and display recent projects."""
        # Clear existing items
        for widget in self.recent_list.winfo_children():
            widget.destroy()
            
        # Find project files
        project_files = list(self.projects_dir.glob("*.json"))
        project_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        for project_file in project_files[:10]:  # Show last 10 projects
            try:
                with open(project_file, 'r') as f:
                    project_data = json.load(f)
                    
                project_frame = ctk.CTkFrame(self.recent_list)
                project_frame.pack(fill="x", padx=5, pady=2)
                
                # Project info
                info_frame = ctk.CTkFrame(project_frame)
                info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                
                name_label = ctk.CTkLabel(info_frame, text=project_data.get("name", project_file.stem),
                                         font=("Arial", 12, "bold"))
                name_label.pack(anchor="w")
                
                date_label = ctk.CTkLabel(info_frame, 
                                         text=f"Modified: {time.strftime('%Y-%m-%d %H:%M', time.localtime(project_file.stat().st_mtime))}")
                date_label.pack(anchor="w")
                
                # Action buttons
                buttons_frame = ctk.CTkFrame(project_frame)
                buttons_frame.pack(side="right", padx=5, pady=5)
                
                load_btn = ctk.CTkButton(buttons_frame, text="Load", width=60,
                                        command=lambda f=project_file: self.load_project_file(f))
                load_btn.pack(side="top", pady=2)
                
                delete_btn = ctk.CTkButton(buttons_frame, text="Delete", width=60,
                                          command=lambda f=project_file: self.delete_project(f))
                delete_btn.pack(side="top", pady=2)
                
            except Exception:
                continue  # Skip corrupted project files
                
    def load_project_file(self, project_file):
        """Load project from file."""
        try:
            with open(project_file, 'r') as f:
                project_data = json.load(f)
                
            # Apply project settings to GUI
            # This would integrate with other widgets to restore state
            pass
            
        except Exception as e:
            self.show_error_message(f"Failed to load project: {str(e)}")
            
    def delete_project(self, project_file):
        """Delete a project file."""
        project_file.unlink()
        self.load_recent_projects()

class ProjectNameDialog:
    """Dialog for entering project name."""
    
    def __init__(self, parent, title="Project Name"):
        self.parent = parent
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_dialog()
        
    def setup_dialog(self):
        """Setup the project name dialog."""
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        label = tk.Label(main_frame, text="Enter project name:")
        label.pack(pady=(0, 10))
        
        self.name_var = tk.StringVar()
        entry = tk.Entry(main_frame, textvariable=self.name_var, width=30)
        entry.pack(pady=(0, 20))
        entry.focus()
        
        button_frame = tk.Frame(main_frame)
        button_frame.pack()
        
        ok_btn = tk.Button(button_frame, text="OK", command=self.ok_clicked)
        ok_btn.pack(side="left", padx=5)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.cancel_clicked)
        cancel_btn.pack(side="left", padx=5)
        
        # Bind Enter key
        entry.bind("<Return>", lambda e: self.ok_clicked())
        
    def ok_clicked(self):
        """Handle OK button click."""
        name = self.name_var.get().strip()
        if name:
            self.result = name
            self.dialog.destroy()
            
    def cancel_clicked(self):
        """Handle Cancel button click."""
        self.dialog.destroy()
```

### 4. Performance & Scalability System

#### Resource Monitor (`utils/resource_monitor.py`)

**Purpose:** Real-time monitoring of system resources and performance optimization

**Features:**
- CPU, memory, and disk usage monitoring
- Dynamic adjustment of concurrent operations
- Memory leak detection and prevention
- Performance metrics and suggestions

```python
import psutil
import threading
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from collections import deque

@dataclass
class PerformanceMetrics:
    cpu_percent: float
    memory_percent: float
    memory_used_mb: int
    memory_available_mb: int
    disk_usage_percent: float
    active_processes: int
    timestamp: float

class ResourceMonitor:
    """Monitors system resources and provides performance optimization."""
    
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.monitoring = False
        self.metrics_history = deque(maxlen=100)  # Keep last 100 measurements
        self.thresholds = {
            'cpu_warning': 80.0,
            'cpu_critical': 95.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 90.0
        }
        self.performance_suggestions = []
        
    def start_monitoring(self, interval: float = 2.0):
        """Start resource monitoring in background thread."""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=1.0)
            
    def _monitor_loop(self, interval: float):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Analyze performance and generate suggestions
                self._analyze_performance(metrics)
                
                # Notify callback if provided
                if self.callback:
                    self.callback(metrics)
                    
                time.sleep(interval)
                
            except Exception as e:
                print(f"Resource monitoring error: {e}")
                time.sleep(interval)
                
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used // (1024 * 1024)
        memory_available_mb = memory.available // (1024 * 1024)
        
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        
        # Count active conversion processes (estimation)
        active_processes = len([p for p in psutil.process_iter(['name']) 
                               if 'python' in p.info['name'] or 'energyplus' in p.info['name']])
        
        return PerformanceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            active_processes=active_processes,
            timestamp=time.time()
        )
        
    def _analyze_performance(self, metrics: PerformanceMetrics):
        """Analyze performance metrics and generate suggestions."""
        suggestions = []
        
        # CPU analysis
        if metrics.cpu_percent > self.thresholds['cpu_critical']:
            suggestions.append({
                'level': 'critical',
                'message': 'CPU usage is critically high (>95%). Consider reducing concurrent conversions.',
                'action': 'reduce_threads'
            })
        elif metrics.cpu_percent > self.thresholds['cpu_warning']:
            suggestions.append({
                'level': 'warning', 
                'message': 'CPU usage is high (>80%). Performance may be affected.',
                'action': 'monitor_cpu'
            })
            
        # Memory analysis
        if metrics.memory_percent > self.thresholds['memory_critical']:
            suggestions.append({
                'level': 'critical',
                'message': 'Memory usage is critically high (>95%). Risk of system instability.',
                'action': 'free_memory'
            })
        elif metrics.memory_percent > self.thresholds['memory_warning']:
            suggestions.append({
                'level': 'warning',
                'message': 'Memory usage is high (>80%). Consider closing other applications.',
                'action': 'monitor_memory'
            })
            
        # Memory trend analysis
        if len(self.metrics_history) > 10:
            recent_memory = [m.memory_percent for m in list(self.metrics_history)[-10:]]
            if self._is_increasing_trend(recent_memory):
                suggestions.append({
                    'level': 'warning',
                    'message': 'Memory usage is steadily increasing. Possible memory leak detected.',
                    'action': 'check_memory_leak'
                })
                
        # Disk space analysis
        if metrics.disk_usage_percent > self.thresholds['disk_warning']:
            suggestions.append({
                'level': 'warning',
                'message': f'Disk space is low ({metrics.disk_usage_percent:.1f}% used).',
                'action': 'free_disk_space'
            })
            
        self.performance_suggestions = suggestions
        
    def _is_increasing_trend(self, values: List[float]) -> bool:
        """Check if values show an increasing trend."""
        if len(values) < 3:
            return False
            
        # Simple trend detection: check if slope is positive
        x = list(range(len(values)))
        n = len(values)
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope > 0.5  # Threshold for significant increase
        
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent performance metrics."""
        return self.metrics_history[-1] if self.metrics_history else None
        
    def get_suggestions(self) -> List[Dict]:
        """Get current performance suggestions."""
        return self.performance_suggestions.copy()
        
    def get_recommended_thread_count(self) -> int:
        """Get recommended thread count based on current performance."""
        if not self.metrics_history:
            return 4  # Default
            
        current = self.metrics_history[-1]
        
        # Reduce threads if high resource usage
        if current.cpu_percent > 90 or current.memory_percent > 90:
            return max(1, psutil.cpu_count() // 4)
        elif current.cpu_percent > 70 or current.memory_percent > 70:
            return max(2, psutil.cpu_count() // 2)
        else:
            return min(psutil.cpu_count(), 8)  # Cap at 8 threads
            
    def estimate_memory_per_conversion(self) -> int:
        """Estimate memory usage per conversion in MB."""
        # This would be based on historical data and file size analysis
        # For now, return a conservative estimate
        return 512  # MB per conversion
        
    def can_handle_additional_conversion(self) -> bool:
        """Check if system can handle one more conversion."""
        if not self.metrics_history:
            return True
            
        current = self.metrics_history[-1]
        estimated_memory_needed = self.estimate_memory_per_conversion()
        
        # Check if we have enough memory
        if current.memory_available_mb < estimated_memory_needed * 1.5:  # 50% buffer
            return False
            
        # Check CPU usage
        if current.cpu_percent > 85:
            return False
            
        return True

class PerformanceOptimizer:
    """Automatically optimizes performance based on system conditions."""
    
    def __init__(self, resource_monitor: ResourceMonitor):
        self.monitor = resource_monitor
        self.optimization_history = []
        
    def optimize_batch_size(self, total_files: int, available_memory_mb: int) -> int:
        """Calculate optimal batch size for file processing."""
        memory_per_file = self.monitor.estimate_memory_per_conversion()
        
        # Calculate max files that can fit in memory
        max_files_in_memory = available_memory_mb // (memory_per_file * 2)  # 100% buffer
        
        # Consider CPU cores
        cpu_cores = psutil.cpu_count()
        optimal_parallel = min(cpu_cores, 8)  # Cap at 8
        
        # Choose the limiting factor
        optimal_batch = min(max_files_in_memory, optimal_parallel, total_files)
        
        return max(1, optimal_batch)
        
    def should_pause_operations(self) -> bool:
        """Determine if operations should be paused due to resource constraints."""
        metrics = self.monitor.get_current_metrics()
        if not metrics:
            return False
            
        # Pause if critical thresholds exceeded
        if (metrics.cpu_percent > 95 or 
            metrics.memory_percent > 95 or
            metrics.memory_available_mb < 100):
            return True
            
        return False
        
    def get_conversion_priority(self, file_size_mb: int, complexity_score: int) -> str:
        """Determine conversion priority based on file characteristics and system state."""
        metrics = self.monitor.get_current_metrics()
        if not metrics:
            return "normal"
            
        # High resource usage - prioritize smaller files
        if metrics.cpu_percent > 80 or metrics.memory_percent > 80:
            if file_size_mb < 5 and complexity_score < 3:
                return "high"  # Small, simple files first
            else:
                return "low"   # Large, complex files later
        else:
            # Normal conditions - balance by complexity
            if complexity_score > 7:
                return "low"   # Complex files when resources available
            else:
                return "normal"
                
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up temporary files older than specified age."""
        import glob
        import os
        
        temp_patterns = [
            "/tmp/h2k_*",
            "/tmp/hpxml_*", 
            "*.tmp",
            "temp_*"
        ]
        
        current_time = time.time()
        cleaned_count = 0
        freed_mb = 0
        
        for pattern in temp_patterns:
            for file_path in glob.glob(pattern):
                try:
                    file_stat = os.stat(file_path)
                    age_hours = (current_time - file_stat.st_mtime) / 3600
                    
                    if age_hours > max_age_hours:
                        file_size_mb = file_stat.st_size / (1024 * 1024)
                        os.remove(file_path)
                        cleaned_count += 1
                        freed_mb += file_size_mb
                        
                except (OSError, IOError):
                    continue  # Skip files we can't access
                    
        return {
            'files_cleaned': cleaned_count,
            'space_freed_mb': freed_mb
        }

class ConversionQueue:
    """Advanced queue management with performance optimization."""
    
    def __init__(self, resource_monitor: ResourceMonitor):
        self.monitor = resource_monitor
        self.optimizer = PerformanceOptimizer(resource_monitor)
        self.queue = []
        self.running_conversions = {}
        self.completed_conversions = []
        self.failed_conversions = []
        
    def add_conversion(self, file_path: str, options: Dict, priority: str = "normal"):
        """Add a conversion to the queue with priority."""
        import os
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        complexity_score = self._estimate_complexity(file_path)
        
        # Override priority based on system state
        auto_priority = self.optimizer.get_conversion_priority(file_size_mb, complexity_score)
        final_priority = auto_priority if priority == "normal" else priority
        
        conversion_task = {
            'id': f"conv_{len(self.queue)}_{int(time.time())}",
            'file_path': file_path,
            'options': options,
            'priority': final_priority,
            'file_size_mb': file_size_mb,
            'complexity_score': complexity_score,
            'added_time': time.time(),
            'estimated_duration': self._estimate_duration(file_size_mb, complexity_score)
        }
        
        self.queue.append(conversion_task)
        self._sort_queue_by_priority()
        
    def _estimate_complexity(self, file_path: str) -> int:
        """Estimate conversion complexity (1-10 scale)."""
        # This would analyze the H2K file content
        # For now, return a simple estimate based on file size
        try:
            import os
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            if file_size_mb < 1:
                return 2
            elif file_size_mb < 5:
                return 5
            else:
                return 8
        except:
            return 5  # Default complexity
            
    def _estimate_duration(self, file_size_mb: float, complexity_score: int) -> float:
        """Estimate conversion duration in seconds."""
        # Base time + size factor + complexity factor
        base_time = 30  # seconds
        size_factor = file_size_mb * 5  # 5 seconds per MB
        complexity_factor = complexity_score * 10  # 10 seconds per complexity point
        
        return base_time + size_factor + complexity_factor
        
    def _sort_queue_by_priority(self):
        """Sort queue by priority and optimization criteria."""
        priority_order = {'high': 0, 'normal': 1, 'low': 2}
        
        self.queue.sort(key=lambda x: (
            priority_order.get(x['priority'], 1),
            -x['file_size_mb'],  # Smaller files first within same priority
            x['complexity_score']  # Simpler files first
        ))
        
    def get_next_conversion(self) -> Optional[Dict]:
        """Get the next conversion to process."""
        if not self.queue:
            return None
            
        # Check if system can handle more conversions
        if not self.monitor.can_handle_additional_conversion():
            return None
            
        return self.queue.pop(0)
        
    def get_queue_status(self) -> Dict:
        """Get current queue status."""
        total_estimated_time = sum(task['estimated_duration'] for task in self.queue)
        
        return {
            'queued': len(self.queue),
            'running': len(self.running_conversions),
            'completed': len(self.completed_conversions),
            'failed': len(self.failed_conversions),
            'estimated_time_remaining': total_estimated_time,
            'high_priority': len([t for t in self.queue if t['priority'] == 'high']),
            'normal_priority': len([t for t in self.queue if t['priority'] == 'normal']),
            'low_priority': len([t for t in self.queue if t['priority'] == 'low'])
        }
```

#### Memory Management System (`utils/memory_manager.py`)

**Purpose:** Prevent memory leaks and optimize memory usage during conversions

**Features:**
- Automatic garbage collection
- Memory usage limits per conversion
- Process isolation for large files
- Memory leak detection

```python
import gc
import psutil
import threading
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional
import weakref

class MemoryManager:
    """Manages memory usage and prevents leaks during conversions."""
    
    def __init__(self, max_memory_mb: int = 2048):
        self.max_memory_mb = max_memory_mb
        self.active_conversions = weakref.WeakValueDictionary()
        self.memory_snapshots = {}
        self.gc_threshold_mb = max_memory_mb * 0.8  # Start GC at 80%
        
    def start_conversion_tracking(self, conversion_id: str, estimated_memory_mb: int):
        """Start tracking memory usage for a conversion."""
        initial_memory = self._get_current_memory_mb()
        
        self.memory_snapshots[conversion_id] = {
            'initial_memory': initial_memory,
            'estimated_memory': estimated_memory_mb,
            'peak_memory': initial_memory,
            'start_time': time.time()
        }
        
        # Check if we need to use process isolation
        if estimated_memory_mb > 1024:  # > 1GB
            return self._should_use_process_isolation(estimated_memory_mb)
        
        return False
        
    def update_memory_usage(self, conversion_id: str):
        """Update memory usage tracking for a conversion."""
        if conversion_id not in self.memory_snapshots:
            return
            
        current_memory = self._get_current_memory_mb()
        snapshot = self.memory_snapshots[conversion_id]
        
        # Update peak memory
        if current_memory > snapshot['peak_memory']:
            snapshot['peak_memory'] = current_memory
            
        # Check if we need garbage collection
        if current_memory > self.gc_threshold_mb:
            self._force_garbage_collection()
            
    def finish_conversion_tracking(self, conversion_id: str):
        """Finish tracking and clean up for a conversion."""
        if conversion_id not in self.memory_snapshots:
            return
            
        snapshot = self.memory_snapshots[conversion_id]
        final_memory = self._get_current_memory_mb()
        duration = time.time() - snapshot['start_time']
        
        # Calculate memory efficiency metrics
        memory_used = snapshot['peak_memory'] - snapshot['initial_memory']
        memory_efficiency = memory_used / max(snapshot['estimated_memory'], 1)
        
        # Clean up
        del self.memory_snapshots[conversion_id]
        
        # Force garbage collection after each conversion
        self._force_garbage_collection()
        
        return {
            'memory_used_mb': memory_used,
            'peak_memory_mb': snapshot['peak_memory'],
            'memory_efficiency': memory_efficiency,
            'duration_seconds': duration
        }
        
    def _get_current_memory_mb(self) -> float:
        """Get current process memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
        
    def _force_garbage_collection(self):
        """Force garbage collection and clear caches."""
        # Clear any module-level caches
        gc.collect()
        
        # Clear specific caches if they exist
        try:
            import xmltodict
            if hasattr(xmltodict, '_cache'):
                xmltodict._cache.clear()
        except:
            pass
            
    def _should_use_process_isolation(self, estimated_memory_mb: int) -> bool:
        """Determine if process isolation should be used."""
        available_memory = psutil.virtual_memory().available / (1024 * 1024)
        
        # Use process isolation if:
        # 1. Estimated memory > 50% of available memory
        # 2. Multiple large conversions are running
        if estimated_memory_mb > available_memory * 0.5:
            return True
            
        large_conversions = sum(1 for s in self.memory_snapshots.values() 
                               if s['estimated_memory'] > 512)
        if large_conversions >= 2:
            return True
            
        return False
        
    def run_conversion_in_process(self, conversion_data: Dict) -> Dict:
        """Run conversion in isolated subprocess to prevent memory leaks."""
        
        # Create temporary files for input/output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(conversion_data, f)
            input_file = f.name
            
        output_file = input_file.replace('.json', '_result.json')
        
        try:
            # Run conversion in subprocess
            cmd = [
                'python', '-m', 'h2k_hpxml.cli.convert',
                '--input-json', input_file,
                '--output-json', output_file
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0 and Path(output_file).exists():
                with open(output_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    'status': 'error',
                    'error': result.stderr or 'Process failed'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'error', 
                'error': 'Conversion timed out'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            # Clean up temporary files
            for file_path in [input_file, output_file]:
                try:
                    Path(file_path).unlink(missing_ok=True)
                except:
                    pass
                    
    def get_memory_report(self) -> Dict:
        """Get current memory usage report."""
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            'process_memory_mb': memory_info.rss / (1024 * 1024),
            'process_memory_percent': (memory_info.rss / system_memory.total) * 100,
            'system_memory_used_percent': system_memory.percent,
            'system_memory_available_mb': system_memory.available / (1024 * 1024),
            'active_conversions': len(self.memory_snapshots),
            'gc_threshold_mb': self.gc_threshold_mb,
            'max_memory_mb': self.max_memory_mb
        }
```

### 5. Accessibility & Internationalization

#### Accessibility Support (`utils/accessibility.py`)

**Purpose:** Ensure GUI accessibility for users with disabilities

**Features:**
- Screen reader compatibility
- Keyboard navigation
- High contrast themes  
- Font size adjustment
- Color blind friendly design

```python
import tkinter as tk
from typing import Dict, List, Optional

class AccessibilityManager:
    """Manages accessibility features for the GUI."""
    
    def __init__(self, root_window):
        self.root = root_window
        self.accessibility_settings = {
            'high_contrast': False,
            'large_fonts': False,
            'screen_reader_mode': False,
            'keyboard_navigation': True,
            'color_blind_mode': None  # None, 'protanopia', 'deuteranopia', 'tritanopia'
        }
        
        self.setup_keyboard_navigation()
        self.load_accessibility_settings()
        
    def setup_keyboard_navigation(self):
        """Setup comprehensive keyboard navigation."""
        
        # Global keyboard shortcuts
        self.root.bind('<Alt-f>', lambda e: self._open_file_menu())
        self.root.bind('<Alt-h>', lambda e: self._open_help_menu())
        self.root.bind('<F1>', lambda e: self._show_help())
        self.root.bind('<Control-o>', lambda e: self._open_files())
        self.root.bind('<Control-s>', lambda e: self._save_project())
        self.root.bind('<Control-n>', lambda e: self._new_project())
        self.root.bind('<Escape>', lambda e: self._cancel_current_operation())
        
        # Tab order management
        self._setup_tab_order()
        
    def _setup_tab_order(self):
        """Ensure logical tab order for all widgets."""
        # This would iterate through all widgets and set appropriate tab order
        pass
        
    def enable_high_contrast(self, enabled: bool = True):
        """Enable or disable high contrast mode."""
        self.accessibility_settings['high_contrast'] = enabled
        
        if enabled:
            # High contrast color scheme
            colors = {
                'bg': '#000000',
                'fg': '#FFFFFF',
                'select_bg': '#FFFF00',
                'select_fg': '#000000',
                'button_bg': '#FFFFFF',
                'button_fg': '#000000',
                'entry_bg': '#FFFFFF',
                'entry_fg': '#000000'
            }
        else:
            # Default colors
            colors = {
                'bg': '#F0F0F0',
                'fg': '#000000',
                'select_bg': '#0078D4',
                'select_fg': '#FFFFFF',
                'button_bg': '#E1E1E1',
                'button_fg': '#000000',
                'entry_bg': '#FFFFFF',
                'entry_fg': '#000000'
            }
            
        self._apply_color_scheme(colors)
        
    def enable_large_fonts(self, enabled: bool = True):
        """Enable or disable large font mode."""
        self.accessibility_settings['large_fonts'] = enabled
        
        if enabled:
            font_multiplier = 1.5
        else:
            font_multiplier = 1.0
            
        self._apply_font_scaling(font_multiplier)
        
    def set_color_blind_mode(self, mode: Optional[str] = None):
        """Set color blind friendly mode."""
        self.accessibility_settings['color_blind_mode'] = mode
        
        if mode == 'protanopia':
            # Red-blind friendly colors
            colors = {
                'success': '#0066CC',  # Blue instead of green
                'warning': '#FF9500',  # Orange
                'error': '#5856D6',    # Purple instead of red
                'info': '#007AFF'      # Blue
            }
        elif mode == 'deuteranopia':
            # Green-blind friendly colors  
            colors = {
                'success': '#0066CC',  # Blue
                'warning': '#FF9500',  # Orange
                'error': '#FF3B30',    # Red
                'info': '#5856D6'      # Purple
            }
        elif mode == 'tritanopia':
            # Blue-blind friendly colors
            colors = {
                'success': '#32D74B',  # Green
                'warning': '#FF9500',  # Orange  
                'error': '#FF3B30',    # Red
                'info': '#8E8E93'      # Gray
            }
        else:
            # Default colors
            colors = {
                'success': '#32D74B',  # Green
                'warning': '#FF9500',  # Orange
                'error': '#FF3B30',    # Red
                'info': '#007AFF'      # Blue
            }
            
        self._apply_semantic_colors(colors)
        
    def enable_screen_reader_mode(self, enabled: bool = True):
        """Enable screen reader compatibility mode."""
        self.accessibility_settings['screen_reader_mode'] = enabled
        
        if enabled:
            # Add ARIA labels and descriptions to all widgets
            self._add_accessibility_labels()
            # Enable focus indicators
            self._enable_focus_indicators()
            # Add keyboard shortcuts to all actions
            self._add_keyboard_shortcuts()
            
    def _add_accessibility_labels(self):
        """Add accessibility labels to all widgets."""
        # This would iterate through all widgets and add appropriate labels
        pass
        
    def _enable_focus_indicators(self):
        """Enable visible focus indicators for keyboard navigation."""
        # Configure focus ring styles for all focusable widgets
        pass
        
    def _add_keyboard_shortcuts(self):
        """Add keyboard shortcuts for all major actions."""
        # This would add shortcuts for buttons, menus, etc.
        pass
        
    def _apply_color_scheme(self, colors: Dict[str, str]):
        """Apply color scheme to all widgets."""
        # This would recursively apply colors to all widgets
        pass
        
    def _apply_font_scaling(self, multiplier: float):
        """Apply font scaling to all text."""
        # This would scale all fonts by the multiplier
        pass
        
    def _apply_semantic_colors(self, colors: Dict[str, str]):
        """Apply semantic colors for status indicators."""
        # This would update success/error/warning colors
        pass
        
    def get_accessibility_status(self) -> Dict:
        """Get current accessibility settings status."""
        return self.accessibility_settings.copy()

#### Internationalization Support (`utils/i18n.py`)

**Purpose:** Support multiple languages and locales

**Features:**
- Multi-language interface
- Locale-specific formatting
- Right-to-left language support
- Cultural adaptations

```python
import json
import locale
from pathlib import Path
from typing import Dict, Optional

class InternationalizationManager:
    """Manages internationalization and localization."""
    
    def __init__(self):
        self.current_language = 'en'
        self.translations = {}
        self.supported_languages = {
            'en': 'English',
            'fr': 'Français', 
            'es': 'Español',
            'de': 'Deutsch',
            'it': 'Italiano',
            'ja': '日本語',
            'zh': '中文',
            'ar': 'العربية'
        }
        
        self.rtl_languages = {'ar', 'he', 'fa'}  # Right-to-left languages
        self.translations_dir = Path("src/h2k_hpxml/gui/resources/translations")
        
        self.load_translations()
        self.detect_system_language()
        
    def load_translations(self):
        """Load translation files for all supported languages."""
        for lang_code in self.supported_languages:
            translation_file = self.translations_dir / f"{lang_code}.json"
            if translation_file.exists():
                try:
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Failed to load translation for {lang_code}: {e}")
                    self.translations[lang_code] = {}
            else:
                self.translations[lang_code] = {}
                
    def detect_system_language(self):
        """Detect system language and set as default."""
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                lang_code = system_locale.split('_')[0]
                if lang_code in self.supported_languages:
                    self.current_language = lang_code
        except:
            pass  # Keep default 'en'
            
    def set_language(self, language_code: str):
        """Set the current language."""
        if language_code in self.supported_languages:
            self.current_language = language_code
            return True
        return False
        
    def translate(self, key: str, **kwargs) -> str:
        """Translate a text key to current language."""
        # Get translation from current language
        translation = self.translations.get(self.current_language, {}).get(key)
        
        # Fallback to English if not found
        if not translation:
            translation = self.translations.get('en', {}).get(key)
            
        # Fallback to key itself if no translation found
        if not translation:
            translation = key
            
        # Format with provided kwargs
        try:
            return translation.format(**kwargs)
        except:
            return translation
            
    def is_rtl_language(self, language_code: Optional[str] = None) -> bool:
        """Check if language is right-to-left."""
        lang = language_code or self.current_language
        return lang in self.rtl_languages
        
    def format_number(self, number: float, decimal_places: int = 2) -> str:
        """Format number according to current locale."""
        try:
            if self.current_language == 'en':
                return f"{number:,.{decimal_places}f}"
            elif self.current_language == 'fr':
                return f"{number:,.{decimal_places}f}".replace(',', ' ').replace('.', ',')
            elif self.current_language == 'de':
                return f"{number:,.{decimal_places}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                return f"{number:.{decimal_places}f}"
        except:
            return str(number)
            
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size according to current locale."""
        units = {
            'en': ['B', 'KB', 'MB', 'GB'],
            'fr': ['o', 'Ko', 'Mo', 'Go'],
            'de': ['B', 'KB', 'MB', 'GB'],
            'es': ['B', 'KB', 'MB', 'GB']
        }
        
        unit_list = units.get(self.current_language, units['en'])
        
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(unit_list) - 1:
            size /= 1024
            unit_index += 1
            
        return f"{self.format_number(size, 1)} {unit_list[unit_index]}"
        
    def get_available_languages(self) -> Dict[str, str]:
        """Get list of available languages."""
        return self.supported_languages.copy()
        
    def create_translation_template(self):
        """Create translation template with all translatable strings."""
        template = {
            # Application
            "app_title": "H2K to HPXML Converter",
            "app_subtitle": "Building Energy Model Conversion Tool",
            
            # Menu items
            "menu_file": "File",
            "menu_edit": "Edit", 
            "menu_tools": "Tools",
            "menu_view": "View",
            "menu_help": "Help",
            "menu_new_project": "New Project",
            "menu_open_project": "Open Project",
            "menu_save_project": "Save Project",
            "menu_exit": "Exit",
            "menu_preferences": "Preferences",
            "menu_about": "About",
            
            # File operations
            "select_files": "Select H2K Files",
            "browse_files": "Browse Files",
            "clear_files": "Clear Files", 
            "output_directory": "Output Directory",
            "drag_drop_hint": "Drag & Drop H2K Files Here",
            
            # Conversion options
            "conversion_options": "Conversion Options",
            "run_simulation": "Run OpenStudio Simulation",
            "add_component_loads": "Add Component Loads", 
            "debug_mode": "Debug Mode",
            "validation_settings": "Validation Settings",
            
            # Progress and status
            "progress": "Progress",
            "status_ready": "Ready",
            "status_running": "Running",
            "status_complete": "Complete",
            "status_failed": "Failed",
            "estimated_time": "Estimated time remaining: {time}",
            
            # Results
            "results": "Results",
            "conversion_successful": "Conversion successful",
            "conversion_failed": "Conversion failed",
            "open_output": "Open Output",
            "view_report": "View Report",
            
            # Error messages
            "error_file_not_found": "File not found: {filename}",
            "error_permission_denied": "Permission denied: {filename}",
            "error_invalid_file": "Invalid H2K file: {filename}",
            "error_simulation_failed": "Simulation failed for: {filename}",
            
            # Accessibility
            "accessibility_high_contrast": "High Contrast Mode",
            "accessibility_large_fonts": "Large Fonts",
            "accessibility_screen_reader": "Screen Reader Mode",
            "accessibility_keyboard_nav": "Keyboard Navigation Help",
            
            # Units and measurements
            "unit_mb": "MB",
            "unit_gb": "GB", 
            "unit_kwh": "kWh",
            "unit_kw": "kW",
            "unit_celsius": "°C",
            "unit_fahrenheit": "°F"
        }
        
        # Save template
        template_file = self.translations_dir / "template.json"
        template_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
            
        return template

# Convenience function for translation
_i18n_manager = None

def _(key: str, **kwargs) -> str:
    """Convenience function for translation."""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = InternationalizationManager()
    return _i18n_manager.translate(key, **kwargs)
```

### 6. Deployment & Distribution

#### Application Packaging (`deployment/packaging.py`)

**Purpose:** Package GUI application for distribution across platforms

**Features:**
- Cross-platform executable generation
- Dependency bundling
- Auto-updater integration
- Installation packages

```python
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict

class ApplicationPackager:
    """Packages the GUI application for distribution."""
    
    def __init__(self, app_name: str = "H2K-HPXML-Converter"):
        self.app_name = app_name
        self.version = "1.7.0"
        self.author = "NRCAN"
        self.description = "H2K to HPXML Building Energy Model Converter"
        
        self.build_dir = Path("build")
        self.dist_dir = Path("dist")
        self.assets_dir = Path("src/h2k_hpxml/gui/resources")
        
    def create_executable(self, platform: str = None):
        """Create executable using PyInstaller."""
        
        if platform is None:
            platform = sys.platform
            
        # PyInstaller spec file content
        spec_content = f'''
import sys
from pathlib import Path

block_cipher = None

# Application data
app_name = "{self.app_name}"
version = "{self.version}"

# Source paths  
src_path = Path("src")
gui_path = src_path / "h2k_hpxml" / "gui"
resources_path = gui_path / "resources"

a = Analysis(
    [str(gui_path / "app.py")],
    pathex=[str(Path.cwd())],
    binaries=[],
    datas=[
        (str(resources_path), "resources"),
        (str(src_path / "h2k_hpxml" / "resources"), "h2k_hpxml/resources"),
        ("conversionconfig.ini", "."),
    ],
    hiddenimports=[
        "customtkinter",
        "tkinterdnd2", 
        "matplotlib.backends.backend_tkagg",
        "PIL._tkinter_finder",
        "psutil",
        "openpyxl",
        "reportlab",
        "h2k_hpxml.core",
        "h2k_hpxml.components",
        "h2k_hpxml.cli",
        "h2k_hpxml.utils"
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version="version_info.txt",
    icon="resources/icons/app_icon.ico" if sys.platform.startswith('win') else "resources/icons/app_icon.icns"
)
'''

        # Write spec file
        spec_file = self.build_dir / f"{self.app_name}.spec"
        spec_file.parent.mkdir(exist_ok=True)
        
        with open(spec_file, 'w') as f:
            f.write(spec_content)
            
        # Create version info for Windows
        if platform.startswith('win'):
            self._create_version_info()
            
        # Run PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm", 
            str(spec_file)
        ]
        
        subprocess.run(cmd, check=True)
        
    def _create_version_info(self):
        """Create Windows version info file."""
        version_info = f'''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({self.version.replace('.', ', ')}, 0),
    prodvers=({self.version.replace('.', ', ')}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'{self.author}'),
            StringStruct(u'FileDescription', u'{self.description}'),
            StringStruct(u'FileVersion', u'{self.version}'),
            StringStruct(u'InternalName', u'{self.app_name}'),
            StringStruct(u'LegalCopyright', u'Copyright © 2024 NRCAN'),
            StringStruct(u'OriginalFilename', u'{self.app_name}.exe'),
            StringStruct(u'ProductName', u'{self.app_name}'),
            StringStruct(u'ProductVersion', u'{self.version}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
        
        version_file = self.build_dir / "version_info.txt"
        with open(version_file, 'w') as f:
            f.write(version_info)
            
    def create_installer(self, platform: str = None):
        """Create installation package."""
        
        if platform is None:
            platform = sys.platform
            
        if platform.startswith('win'):
            self._create_windows_installer()
        elif platform.startswith('darwin'):
            self._create_macos_installer()
        elif platform.startswith('linux'):
            self._create_linux_installer()
            
    def _create_windows_installer(self):
        """Create Windows MSI installer using WiX or Inno Setup."""
        
        # Inno Setup script
        iss_content = f'''
[Setup]
AppName={self.app_name}
AppVersion={self.version}
AppPublisher={self.author}
AppPublisherURL=https://github.com/nrcan
DefaultDirName={{autopf}}\\{self.app_name}
DefaultGroupName={self.app_name}
OutputDir=dist
OutputBaseFilename={self.app_name}-{self.version}-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=resources\\icons\\app_icon.ico
UninstallDisplayIcon={{app}}\\{self.app_name}.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{{cm:CreateQuickLaunchIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\\{self.app_name}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{self.app_name}"; Filename: "{{app}}\\{self.app_name}.exe"
Name: "{{group}}\\{{cm:UninstallProgram,{self.app_name}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{self.app_name}"; Filename: "{{app}}\\{self.app_name}.exe"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\{self.app_name}"; Filename: "{{app}}\\{self.app_name}.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\{self.app_name}.exe"; Description: "{{cm:LaunchProgram,{self.app_name}}}"; Flags: nowait postinstall skipifsilent
'''
        
        iss_file = self.build_dir / f"{self.app_name}.iss"
        with open(iss_file, 'w') as f:
            f.write(iss_content)
            
    def _create_macos_installer(self):
        """Create macOS DMG installer."""
        
        # Create app bundle structure
        app_bundle = self.dist_dir / f"{self.app_name}.app"
        contents_dir = app_bundle / "Contents"
        macos_dir = contents_dir / "MacOS"
        resources_dir = contents_dir / "Resources"
        
        for directory in [macos_dir, resources_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Info.plist
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>{self.app_name}</string>
    <key>CFBundleExecutable</key>
    <string>{self.app_name}</string>
    <key>CFBundleIconFile</key>
    <string>app_icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>ca.nrcan.{self.app_name.lower()}</string>
    <key>CFBundleName</key>
    <string>{self.app_name}</string>
    <key>CFBundleShortVersionString</key>
    <string>{self.version}</string>
    <key>CFBundleVersion</key>
    <string>{self.version}</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>'''
        
        plist_file = contents_dir / "Info.plist"
        with open(plist_file, 'w') as f:
            f.write(plist_content)
            
    def _create_linux_installer(self):
        """Create Linux AppImage or DEB package."""
        
        # Create .desktop file
        desktop_content = f'''[Desktop Entry]
Version=1.0
Type=Application
Name={self.app_name}
Comment={self.description}
Exec={self.app_name}
Icon={self.app_name.lower()}
Terminal=false
Categories=Science;Engineering;
'''
        
        desktop_file = self.dist_dir / f"{self.app_name.lower()}.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
            
    def create_auto_updater(self):
        """Create auto-updater component."""
        
        updater_content = '''
import requests
import json
import subprocess
import sys
from pathlib import Path
from packaging import version

class AutoUpdater:
    def __init__(self, current_version: str, update_url: str):
        self.current_version = current_version
        self.update_url = update_url
        
    def check_for_updates(self) -> dict:
        """Check for available updates."""
        try:
            response = requests.get(f"{self.update_url}/latest")
            response.raise_for_status()
            
            latest_info = response.json()
            latest_version = latest_info.get("version")
            
            if version.parse(latest_version) > version.parse(self.current_version):
                return {
                    "update_available": True,
                    "latest_version": latest_version,
                    "download_url": latest_info.get("download_url"),
                    "release_notes": latest_info.get("release_notes")
                }
            else:
                return {"update_available": False}
                
        except Exception as e:
            return {"error": str(e)}
            
    def download_and_install_update(self, download_url: str):
        """Download and install update."""
        # Implementation would depend on platform
        pass
'''
        
        updater_file = Path("src/h2k_hpxml/gui/utils/auto_updater.py")
        updater_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(updater_file, 'w') as f:
            f.write(updater_content)
            
    def package_for_all_platforms(self):
        """Package application for all supported platforms."""
        
        platforms = ['win32', 'darwin', 'linux']
        
        for platform in platforms:
            print(f"Creating package for {platform}...")
            
            try:
                self.create_executable(platform)
                self.create_installer(platform)
                print(f"Successfully packaged for {platform}")
                
            except Exception as e:
                print(f"Failed to package for {platform}: {e}")
                
        print("Packaging complete!")
```

#### Documentation Generation (`deployment/docs_generator.py`)

**Purpose:** Generate comprehensive user documentation

**Features:**
- User manual generation
- API documentation
- Video tutorials
- Troubleshooting guides

```python
from pathlib import Path
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

class DocumentationGenerator:
    """Generates comprehensive documentation for the GUI application."""
    
    def __init__(self):
        self.docs_dir = Path("docs")
        self.output_dir = Path("dist/docs")
        
    def generate_user_manual(self):
        """Generate comprehensive user manual."""
        
        manual_content = '''
# H2K to HPXML Converter - User Manual

## Table of Contents
1. Introduction
2. Installation
3. Getting Started
4. Basic Operations
5. Advanced Features
6. Troubleshooting
7. FAQ

## 1. Introduction

The H2K to HPXML Converter is a comprehensive tool for converting Canadian Hot2000 (H2K) building energy models to the standardized HPXML format for simulation in EnergyPlus.

### Key Features
- Intuitive graphical interface
- Batch processing capabilities
- Real-time progress tracking
- Comprehensive energy analysis and reporting
- Multiple export formats
- Building resilience analysis

## 2. Installation

### System Requirements
- Windows 10/11, macOS 10.14+, or Linux Ubuntu 18.04+
- 4 GB RAM minimum (8 GB recommended)
- 2 GB available disk space
- Internet connection for weather file downloads

### Installation Steps
1. Download the installer from the official website
2. Run the installer and follow the setup wizard
3. Launch the application from the Start menu or Applications folder

## 3. Getting Started

### First Launch
When you first launch the application, you'll see the main interface with three main areas:

1. **File Selection Panel** - Select and manage H2K input files
2. **Configuration Panel** - Set conversion and simulation options  
3. **Results Panel** - View progress and results

### Basic Workflow
1. Select H2K files to convert
2. Choose output directory
3. Configure conversion options
4. Start conversion
5. Review results and reports

## 4. Basic Operations

### Selecting Files
- Click "Browse Files" to select individual H2K files
- Drag and drop multiple files directly onto the file list
- Use "Clear Files" to remove all selected files

### Setting Output Directory
- Click the folder icon next to "Output Directory"
- Choose where converted files will be saved
- Each conversion creates a separate subdirectory

### Running Conversions
- Click "Start Conversion" to begin processing
- Monitor progress in the Results panel
- Use "Pause" or "Cancel" to control the process

## 5. Advanced Features

### Resilience Analysis
Access through the "Resilience" tab to analyze building performance under various scenarios:
- Power outage scenarios
- Extreme weather conditions
- Thermal autonomy analysis

### Energy Reports
View detailed energy analysis through the "Reports" tab:
- Monthly energy usage patterns
- Peak demand analysis
- End-use breakdowns
- Export capabilities

### Configuration Management
- Save and load project configurations
- Use templates for common scenarios
- Manage weather files and dependencies

## 6. Troubleshooting

### Common Issues

**Conversion Fails with "File Not Found" Error**
- Verify the H2K file exists and is accessible
- Check file permissions
- Ensure the file is a valid H2K format

**Simulation Fails**
- Check that OpenStudio and OpenStudio-HPXML are installed
- Verify system dependencies using the Dependency Manager
- Review error logs for specific issues

**Poor Performance**
- Close other applications to free memory
- Reduce number of concurrent conversions
- Check system resources in the Performance panel

### Getting Help
- Use F1 for context-sensitive help
- Check the FAQ section
- Contact support with error logs and system information

## 7. FAQ

**Q: What H2K file versions are supported?**
A: The converter supports H2K files from Hot2000 version 10.5 and later.

**Q: Can I convert multiple files at once?**
A: Yes, the application supports batch processing of multiple H2K files.

**Q: How long does a typical conversion take?**
A: Conversion time varies based on file size and complexity, typically 2-10 minutes per file including simulation.

**Q: Are the converted files compatible with other energy modeling software?**
A: Yes, HPXML is a standard format supported by many energy modeling tools.
'''
        
        # Save as markdown
        manual_file = self.output_dir / "user_manual.md"
        manual_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(manual_file, 'w') as f:
            f.write(manual_content)
            
        # Convert to PDF
        self._convert_markdown_to_pdf(manual_content, self.output_dir / "user_manual.pdf")
        
    def _convert_markdown_to_pdf(self, markdown_content: str, output_path: Path):
        """Convert markdown content to PDF."""
        
        # Convert markdown to HTML
        html = markdown.markdown(markdown_content)
        
        # Create PDF using ReportLab
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Parse HTML and add to PDF (simplified)
        lines = html.split('\n')
        for line in lines:
            if line.strip():
                if line.startswith('<h1>'):
                    text = line.replace('<h1>', '').replace('</h1>', '')
                    story.append(Paragraph(text, styles['Title']))
                elif line.startswith('<h2>'):
                    text = line.replace('<h2>', '').replace('</h2>', '')
                    story.append(Paragraph(text, styles['Heading1']))
                elif line.startswith('<h3>'):
                    text = line.replace('<h3>', '').replace('</h3>', '')
                    story.append(Paragraph(text, styles['Heading2']))
                else:
                    # Remove basic HTML tags
                    text = line.replace('<p>', '').replace('</p>', '')
                    text = text.replace('<strong>', '<b>').replace('</strong>', '</b>')
                    story.append(Paragraph(text, styles['Normal']))
                    
                story.append(Spacer(1, 6))
                
        doc.build(story)
```

### 7. Updated Implementation Phases

#### Phase 1: Core Infrastructure (Weeks 1-2)
- [ ] **Basic application window and layout**
- [ ] **File selection widget with validation** 
- [ ] **Basic conversion options interface**
- [ ] **Integration with existing CLI conversion logic**
- [ ] **Error recovery and notification systems**

#### Phase 2: Advanced Features (Weeks 3-4)
- [ ] **Progress tracking system with resource monitoring**
- [ ] **Background processing implementation with memory management**
- [ ] **Results display and management**
- [ ] **CLI integration (resilience analysis, dependency management)**
- [ ] **Configuration editor and project workspace**

#### Phase 3: Reports and Analysis (Weeks 5-6)
- [ ] **Reports page with file selection and energy data loading**
- [ ] **Energy data loading from simulation results (SQL, CSV)**
- [ ] **Basic charts (monthly, peak analysis) with matplotlib**
- [ ] **Energy summary calculations and metrics**
- [ ] **Export functionality (PDF, Excel, CSV)**

#### Phase 4: Advanced Analysis and UI Polish (Weeks 7-8)
- [ ] **Hottest/coldest week analysis with weather correlation**
- [ ] **Interactive chart features and comparison tools**
- [ ] **Building comparison tools and benchmarking**
- [ ] **Advanced export options and custom reports**
- [ ] **Performance optimization and scalability features**

#### Phase 5: Accessibility and Internationalization (Week 9)
- [ ] **Accessibility features (screen reader, keyboard navigation, high contrast)**
- [ ] **Internationalization support for multiple languages**
- [ ] **Drag and drop functionality with validation**
- [ ] **Settings persistence and user preferences**
- [ ] **Help system and context-sensitive documentation**

#### Phase 6: Testing and Deployment (Week 10)
- [ ] **Comprehensive testing (unit, integration, user acceptance)**
- [ ] **Cross-platform packaging and distribution**
- [ ] **Performance optimization and memory leak prevention**
- [ ] **Documentation completion and user manual**
- [ ] **Final polish, bug fixes, and deployment preparation**

## Updated Dependencies

### Core GUI Dependencies
```toml
[project.optional-dependencies]
gui = [
    "customtkinter>=5.2.0",           # Modern GUI framework
    "pillow>=9.0.0",                  # Image handling and icons  
    "tkinterdnd2>=0.3.0",             # Drag-and-drop functionality
    "matplotlib>=3.7.0",             # Charts and graphs for energy analysis
    "pandas>=2.0.0",                  # Data analysis and processing
    "numpy>=1.24.0",                  # Numerical computations
    "openpyxl>=3.1.0",                # Excel export functionality
    "reportlab>=4.0.0",               # PDF report generation
]

[project.optional-dependencies]
gui-full = [
    # Include all gui dependencies plus:
    "psutil>=5.8.0",                  # System resource monitoring
    "requests>=2.31.0",               # Auto-updater and weather downloads
    "packaging>=23.0",                # Version comparison for updates
    "markdown>=3.4.0",                # Documentation generation
    "babel>=2.12.0",                  # Internationalization support
]
```

## Conclusion

This enhanced GUI plan now addresses all the previously missing elements:

✅ **Complete CLI Integration** - Resilience analysis and dependency management  
✅ **Error Recovery & User Feedback** - Toast notifications, automatic retry, guided recovery  
✅ **Configuration Management** - Visual config editor, project workspaces, templates  
✅ **Performance & Scalability** - Resource monitoring, memory management, queue optimization  
✅ **Accessibility & Internationalization** - Screen reader support, multi-language interface  
✅ **Deployment & Distribution** - Cross-platform packaging, auto-updater, documentation

The GUI will provide a comprehensive, production-ready interface that significantly expands the tool's accessibility while maintaining all the power and flexibility of the CLI version. The modular architecture ensures maintainability and allows for future enhancements based on user feedback.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "Address missing elements in GUI plan", "status": "in_progress", "priority": "high"}, {"id": "2", "content": "Add CLI integration gaps (resilience, deps)", "status": "completed", "priority": "high"}, {"id": "3", "content": "Add error recovery and user feedback systems", "status": "in_progress", "priority": "high"}, {"id": "4", "content": "Add configuration management features", "status": "pending", "priority": "medium"}, {"id": "5", "content": "Add performance and scalability considerations", "status": "pending", "priority": "medium"}, {"id": "6", "content": "Add accessibility and deployment sections", "status": "pending", "priority": "low"}]
