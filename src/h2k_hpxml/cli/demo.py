"""
Interactive demo for H2K to HPXML conversion.

This module provides an interactive, bilingual demo that guides users through
the h2k2hpxml conversion process using real example files.
"""

import tempfile
import shutil
import time
import os
import sys
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax

from ..examples import get_examples_directory, list_example_files
from .demo_strings import get_string, get_list

console = Console()


class H2KDemo:
    """Interactive demo class for H2K to HPXML conversion."""
    
    def __init__(self):
        self.lang = "en"
        self.temp_dir: Optional[Path] = None
        self.selected_file: Optional[Path] = None
        self.output_files = []
        
    def t(self, key: str) -> str:
        """Translation helper."""
        return get_string(key, self.lang)
    
    def tl(self, key: str) -> List[str]:
        """Translation helper for lists."""
        return get_list(key, self.lang)
    
    def select_language(self) -> None:
        """Language selection at start."""
        console.print(Panel.fit(
            "🌍 Language / Langue\n\n"
            "[1] English\n"
            "[2] Français",
            border_style="blue"
        ))
        
        choice = Prompt.ask("Choice/Choix", choices=["1", "2"], default="1")
        self.lang = "en" if choice == "1" else "fr"
        
    def show_welcome(self) -> None:
        """Display welcome screen."""
        console.print(Panel.fit(
            f"[bold cyan]{self.t('welcome_title')}[/bold cyan]\n"
            f"{self.t('welcome_subtitle')}",
            border_style="green"
        ))
        
    def select_example_file(self) -> bool:
        """Let user select an example H2K file."""
        try:
            examples = list_example_files(".h2k")
            if not examples:
                console.print(f"[red]{self.t('error').format(error='No example files found')}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]{self.t('error').format(error=str(e))}[/red]")
            return False
        
        console.print(f"\n[bold]{self.t('file_selection')}:[/bold]")
        
        # Create table of examples
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Num", style="cyan", width=4)
        table.add_column("File", style="yellow", width=30)
        table.add_column("Size", style="dim", width=10)
        
        for i, path in enumerate(examples[:5], 1):
            size = path.stat().st_size // 1024
            size_str = self.t('size_kb').format(size=size) if size < 1024 else self.t('size_mb').format(size=size//1024)
            table.add_row(f"[{i}]", path.name, size_str)
            
        console.print(table)
        
        choice = Prompt.ask(
            self.t('file_selection'),
            choices=[str(i) for i in range(1, min(6, len(examples)+1))],
            default="1"
        )
        
        self.selected_file = examples[int(choice)-1]
        return True
        
    def show_command(self) -> bool:
        """Display the command that will be run."""
        if not self.selected_file:
            return False
            
        cmd = f"h2k2hpxml {self.selected_file.name} --output demo_output/ --debug"
        
        console.print(f"\n[bold]{self.t('command_preview')}[/bold]")
        console.print(Panel(Syntax(cmd, "bash", theme="monokai"), border_style="dim"))
        
        # Explain what the command does
        console.print(f"\n{self.t('command_explanation')}")
        console.print(f"{self.t('convert_explanation').format(filename=self.selected_file.name)}")
        console.print(f"{self.t('output_explanation')}")
        console.print(f"{self.t('debug_explanation')}")
        
        return Confirm.ask(f"\n{self.t('confirm_run')}", default=True)
        
    def simulate_conversion(self) -> bool:
        """Simulate the conversion process with progress display."""
        # Create temp directory
        try:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="h2k_demo_"))
            console.print(f"\n[dim]Using temporary directory: {self.temp_dir}[/dim]")
        except Exception as e:
            console.print(f"[red]{self.t('error').format(error=str(e))}[/red]")
            return False
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            console=console
        ) as progress:
            
            # Conversion steps with realistic timing
            steps = [
                ("converting", 25, 1.0),
                ("parsing", 15, 0.8),
                ("hvac", 15, 0.7),
                ("weather", 10, 0.5),
                ("writing", 20, 0.6),
                ("simulation", 15, 1.2)
            ]
            
            task = progress.add_task(
                f"[cyan]{self.t('converting')}",
                total=100
            )
            
            for step_key, advance, sleep_time in steps:
                progress.update(task, description=f"[cyan]{self.t(step_key)}")
                time.sleep(sleep_time)
                progress.update(task, advance=advance)
                
        # Simulate creating output files
        self._simulate_output_files()
        
        console.print(f"[green]✓ {self.t('complete')}[/green]")
        return True
        
    def _simulate_output_files(self) -> None:
        """Create simulated output files for demonstration."""
        if not self.temp_dir:
            return
            
        output_dir = self.temp_dir / "demo_output"
        output_dir.mkdir(exist_ok=True)
        
        # Create sample files
        files_to_create = [
            ("output.xml", 245 * 1024, self._sample_xml_content()),
            ("run.sql", 1200 * 1024, "SQLite format 3\n-- Simulation results database"),
            ("results_annual.csv", 12 * 1024, self._sample_csv_content()),
        ]
        
        for filename, size, content in files_to_create:
            file_path = output_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                # Pad with spaces to approximate size
                remaining = max(0, size - len(content.encode('utf-8')))
                f.write(" " * remaining)
            self.output_files.append(file_path)
    
    def _sample_xml_content(self) -> str:
        """Generate sample HPXML content."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<HPXML xmlns="http://hpxmlonline.com/2019/10" schemaVersion="3.0">
  <XMLTransactionHeaderInformation>
    <XMLType>HPXML</XMLType>
    <XMLGeneratedBy>h2k-hpxml</XMLGeneratedBy>
    <CreatedDateAndTime>2024-01-01T00:00:00</CreatedDateAndTime>
  </XMLTransactionHeaderInformation>
  <SoftwareInfo>
    <SoftwareName>H2K-HPXML</SoftwareName>
  </SoftwareInfo>
  <Building>
    <Site>
      <SiteID id="site1"/>
      <Address>
        <StateCode>ON</StateCode>
        <ZipCode>K1A 0A3</ZipCode>
      </Address>
    </Site>
    <BuildingSummary>
      <BuildingConstruction>
        <ResidentialFacilityType>single-family detached</ResidentialFacilityType>
        <NumberofConditionedFloors>2</NumberofConditionedFloors>
        <NumberofConditionedFloorsAboveGrade>2</NumberofConditionedFloorsAboveGrade>
        <ConditionedFloorArea>2000</ConditionedFloorArea>
        <BuildingVolume>16000</BuildingVolume>
      </BuildingConstruction>
    </BuildingSummary>
  </Building>
</HPXML>'''

    def _sample_csv_content(self) -> str:
        """Generate sample CSV content."""
        return '''Output,Value,Unit
Fuel Use: Electricity: Total,45.2,MBtu
Fuel Use: Natural Gas: Total,89.7,MBtu
End Use: Electricity: Heating,12.3,MBtu
End Use: Electricity: Cooling,8.5,MBtu
End Use: Electricity: Hot Water,15.1,MBtu
End Use: Electricity: Lighting,5.8,MBtu
End Use: Electricity: Plug Loads,7.2,MBtu
End Use: Natural Gas: Heating,85.4,MBtu
End Use: Natural Gas: Hot Water,4.3,MBtu
Peak Electricity,8.2,kW
Peak Natural Gas,45.1,kBtu/hr
Total CO2e Emissions,12.5,tonnes
Energy Cost,2450,CAD'''
        
    def tour_output_files(self) -> None:
        """Show and explain output files."""
        console.print(f"\n[bold]{self.t('output_tour')}:[/bold]\n")
        
        # Create table of output files
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column(self.t('file_header'), style="cyan", width=25)
        table.add_column(self.t('size_header'), style="yellow", width=10)
        table.add_column(self.t('description_header'), style="white")
        
        files = [
            ("output.xml", "245 KB", self.t('file_description.xml')),
            ("run.sql", "1.2 MB", self.t('file_description.sql')),
            ("results_annual.csv", "12 KB", self.t('file_description.csv')),
        ]
        
        for name, size, desc in files:
            table.add_row(name, size, desc)
            
        console.print(table)
        
        # Offer to explore files
        if self.output_files and Confirm.ask(f"\n{self.t('explore_file')}", default=False):
            self._explore_files()
    
    def _explore_files(self) -> None:
        """Allow user to explore generated files."""
        while True:
            console.print(f"\n[bold]Files available:[/bold]")
            for i, file_path in enumerate(self.output_files, 1):
                console.print(f"[{i}] {file_path.name}")
            
            choice = Prompt.ask(
                "Select file to view",
                choices=[str(i) for i in range(1, len(self.output_files)+1)] + ["q"],
                default="q"
            )
            
            if choice.lower() == "q":
                break
                
            file_path = self.output_files[int(choice)-1]
            self._show_file_content(file_path)
    
    def _show_file_content(self, file_path: Path) -> None:
        """Show content of a file."""
        console.print(f"\n[bold]{self.t('view_file').format(filename=file_path.name)}[/bold]")
        console.print(f"{self.t('sample_content')}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]  # First 10 lines
                content = ''.join(lines).strip()
                
            # Syntax highlighting based on file extension
            if file_path.suffix == '.xml':
                console.print(Syntax(content, "xml", theme="monokai"))
            elif file_path.suffix == '.csv':
                console.print(Syntax(content, "csv", theme="monokai"))
            else:
                console.print(content)
                
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
        
        input(f"\n{self.t('press_enter')}")
        
    def show_next_steps(self) -> None:
        """Display what to try next."""
        points = "\n".join(self.tl('learned_points'))
        
        console.print(Panel(
            f"[bold green]{self.t('next_steps')}[/bold green]\n\n"
            f"{self.t('learned')}\n{points}\n\n"
            f"[bold]{self.t('try_next')}[/bold]\n",
            border_style="green"
        ))
        
        # Show command examples
        commands = self.tl('commands')
        for cmd in commands:
            if cmd.startswith('#'):
                console.print(f"[dim]{cmd}[/dim]")
            elif cmd.strip():
                console.print(f"[cyan]{cmd}[/cyan]")
            else:
                console.print()
        
        console.print(f"\n[dim]{self.t('help_command')}[/dim]")
        
    def cleanup(self) -> None:
        """Clean up temp files."""
        if self.temp_dir and self.temp_dir.exists():
            if Confirm.ask(f"\n{self.t('cleanup')}", default=True):
                try:
                    shutil.rmtree(self.temp_dir)
                    console.print(f"[dim]{self.t('cleanup_done')}[/dim]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not clean up {self.temp_dir}: {e}[/yellow]")


def run_interactive_demo() -> None:
    """Main entry point for demo."""
    demo = H2KDemo()
    
    try:
        # Language selection
        demo.select_language()
        
        # Welcome screen
        demo.show_welcome()
        
        # File selection
        if not demo.select_example_file():
            console.print(f"[red]{demo.t('cancelled')}[/red]")
            return
        
        # Show command and confirm
        if demo.show_command():
            # Run simulation
            if demo.simulate_conversion():
                # Tour output files
                demo.tour_output_files()
            
        # Show next steps
        demo.show_next_steps()
        
    except KeyboardInterrupt:
        console.print(f"\n[yellow]{demo.t('cancelled')}[/yellow]")
    except Exception as e:
        console.print(f"\n[red]{demo.t('error').format(error=str(e))}[/red]")
    finally:
        # Cleanup
        demo.cleanup()


if __name__ == "__main__":
    run_interactive_demo()