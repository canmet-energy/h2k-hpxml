"""
Interactive demo for H2K to HPXML conversion.

This module provides an interactive, bilingual demo that guides users through
the h2k-hpxml conversion process using real example files.
"""

import os
import shutil
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
from rich.prompt import Confirm
from rich.prompt import Prompt
from rich.table import Table

from ..examples import list_example_files
from .demo_strings import get_list
from .demo_strings import get_string

console = Console()


class H2KDemo:
    """Interactive demo class for H2K to HPXML conversion."""

    def __init__(self):
        self.lang = "en"
        self.demo_dir: Path | None = None
        self.selected_file: Path | None = None
        self.output_files = []

    def t(self, key: str) -> str:
        """Translation helper."""
        return get_string(key, self.lang)

    def tl(self, key: str) -> list[str]:
        """Translation helper for lists."""
        return get_list(key, self.lang)

    def select_language(self) -> None:
        """Language selection at start."""
        console.print(
            Panel.fit(
                "🌍 Language / Langue\n\n" "[1] English\n" "[2] Français", border_style="blue"
            )
        )

        choice = Prompt.ask("Choice/Choix", choices=["1", "2"], default="1")
        self.lang = "en" if choice == "1" else "fr"

    def show_welcome(self) -> None:
        """Display welcome screen."""
        console.print(
            Panel.fit(
                f"[bold cyan]{self.t('welcome_title')}[/bold cyan]\n"
                f"{self.t('welcome_subtitle')}",
                border_style="green",
            )
        )

    def select_example_file(self) -> bool:
        """Let user select an example H2K file."""
        try:
            examples = list_example_files(".h2k")
            if not examples:
                console.print(
                    f"[red]{self.t('error').format(error='No example files found')}[/red]"
                )
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
            size_str = (
                self.t("size_kb").format(size=size)
                if size < 1024
                else self.t("size_mb").format(size=size // 1024)
            )
            table.add_row(f"[{i}]", path.name, size_str)

        console.print(table)

        choice = Prompt.ask(
            self.t("file_selection"),
            choices=[str(i) for i in range(1, min(6, len(examples) + 1))],
            default="1",
        )

        self.selected_file = examples[int(choice) - 1]
        return True

    def show_command(self) -> bool:
        """Display the command that will be run."""
        if not self.selected_file:
            return False

        # First, explain what the demo will set up
        console.print(
            f"\n• {self.t('demo_setup_explanation').format(filename=self.selected_file.name)}"
        )

        # Show the actual command with flags that will be used
        cmd = (
            f"h2k-hpxml h2k_demo_output/{self.selected_file.name} --hourly ALL --output-format csv"
        )

        console.print(f"\n[bold]{self.t('command_preview')}[/bold]")
        console.print(Panel(f"[cyan]{cmd}[/cyan]", border_style="dim"))

        # Explain what the command does (without demo setup)
        console.print(f"\n{self.t('command_explanation')}")
        console.print(
            f"{self.t('convert_explanation').format(filename=self.selected_file.name)}"
        )  # No bullet - string already has one
        console.print(f"• {self.t('run_simulation_step')}")
        console.print(f"• {self.t('save_outputs_step').format(stem=self.selected_file.stem)}")
        console.print(f"• {self.t('hourly_all_explanation')}")
        console.print(f"• {self.t('output_format_csv_explanation')}")

        return Confirm.ask(f"\n{self.t('confirm_run')}", default=True)

    def simulate_conversion(self) -> bool:
        """Run actual H2K to HPXML conversion with full EnergyPlus simulation."""
        import logging

        # Suppress INFO messages during demo for cleaner output
        # Target the specific h2k_hpxml loggers
        h2k_logger = logging.getLogger("h2k_hpxml")
        original_h2k_level = h2k_logger.level
        h2k_logger.setLevel(logging.WARNING)

        # Also suppress the root logger just in case
        root_logger = logging.getLogger()
        original_root_level = root_logger.level
        root_logger.setLevel(logging.WARNING)

        try:
            # Create demo output directory in current working directory
            try:
                self.demo_dir = Path.cwd() / "h2k_demo_output"
                self.demo_dir.mkdir(exist_ok=True)
                console.print(f"\n[dim]{self.t('creating_demo_dir')}[/dim]")
            except Exception as e:
                console.print(f"[red]{self.t('error').format(error=str(e))}[/red]")
                return False

            # Check for dependencies first
            console.print(f"\n[yellow]{self.t('checking_deps')}[/yellow]")
            try:
                from ..utils.dependencies import validate_dependencies

                if not validate_dependencies(check_only=True, interactive=False, skip_deps=False):
                    console.print(f"[red]{self.t('deps_missing')}[/red]")
                    return False
            except Exception as e:
                console.print(f"[yellow]Warning: Could not validate dependencies: {e}[/yellow]")

            # Copy H2K file to demo directory
            try:
                local_h2k_file = self.demo_dir / self.selected_file.name
                shutil.copy2(self.selected_file, local_h2k_file)
                console.print(
                    f"[dim]{self.t('copied_file').format(filename=self.selected_file.name)}[/dim]"
                )
            except Exception as e:
                console.print(f"[red]{self.t('error').format(error=str(e))}[/red]")
                return False

            # Import conversion functions
            try:
                from ..api import _build_simulation_flags
                from ..api import _convert_h2k_file_to_hpxml
                from ..api import _run_hpxml_simulation
                from ..config.manager import ConfigManager
            except ImportError as e:
                console.print(f"[red]Import error: {e}[/red]")
                return False

            success = True

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green", finished_style="green"),
                console=console,
            ) as progress:

                # Step 1: Convert H2K to HPXML
                task = progress.add_task(f"[cyan]{self.t('converting')}[/cyan]", total=2)

                try:
                    hpxml_path = _convert_h2k_file_to_hpxml(
                        filepath=str(local_h2k_file), dest_hpxml_path=str(self.demo_dir)
                    )
                    progress.update(task, advance=1)
                    console.print(f"[green]✓ HPXML created: {hpxml_path}[/green]")

                except Exception as e:
                    console.print(f"[red]✗ Conversion failed: {e}[/red]")
                    return False

                # Step 2: Run EnergyPlus simulation
                progress.update(task, description=f"[cyan]{self.t('simulation')}[/cyan]")

                try:
                    # Get configuration
                    config = ConfigManager()
                    hpxml_os_path = config.hpxml_os_path  # Use property accessor for auto-detection

                    # Check if path was found
                    if not hpxml_os_path:
                        console.print("[red]✗ OpenStudio-HPXML installation not found[/red]")
                        return False

                    ruby_hpxml_path = os.path.join(hpxml_os_path, "workflow", "run_simulation.rb")

                    # Build simulation flags (with hourly outputs to showcase capabilities)
                    flags = _build_simulation_flags(
                        add_component_loads=True,
                        debug=True,
                        skip_validation=False,
                        output_format="csv",
                        timestep=(),  # Empty tuple - no timestep outputs
                        daily=(),  # Empty tuple - no daily outputs
                        hourly=("ALL",),  # Request ALL hourly outputs for demo
                        monthly=(),  # Empty tuple - no monthly outputs
                        add_stochastic_schedules=False,
                        add_timeseries_output_variable=(),
                    )

                    # Run simulation
                    status, error_msg = _run_hpxml_simulation(
                        hpxml_path=hpxml_path,
                        ruby_hpxml_path=ruby_hpxml_path,
                        hpxml_os_path=hpxml_os_path,
                        flags=flags,
                    )

                    progress.update(task, advance=1)

                    if status == "Success":
                        console.print(f"[green]✓ {self.t('simulation_complete')}[/green]")
                    else:
                        console.print(f"[red]✗ Simulation failed: {error_msg}[/red]")
                        success = False

                except Exception as e:
                    console.print(f"[red]✗ Simulation error: {e}[/red]")
                    success = False

            # Collect actual output files
            self._collect_output_files()

            if success:
                console.print(f"[green]✓ {self.t('complete')}[/green]")

            return success

        finally:
            # Restore original logging levels
            h2k_logger.setLevel(original_h2k_level)
            root_logger.setLevel(original_root_level)

    def _collect_output_files(self) -> None:
        """Collect actual generated output files."""
        if not self.demo_dir or not self.selected_file:
            return

        output_dir = self.demo_dir / self.selected_file.stem
        if not output_dir.exists():
            return

        # Collect important files
        file_patterns = [
            "*.xml",  # HPXML file
            "run/results_annual.csv",
            "run/results_annual.json",
            "run/results_timeseries.csv",
            "run/eplusout.sql",
            "run/in.xml",
            "run/in.osm",
            "run/eplusout.err",
        ]

        for pattern in file_patterns:
            for file_path in output_dir.glob(pattern):
                if file_path.is_file():
                    self.output_files.append(file_path)

    def tour_output_files(self) -> None:
        """Show and explain output files in tree format."""
        console.print(f"\n[bold]{self.t('output_tour')}:[/bold]\n")

        if not self.output_files:
            console.print("[yellow]No output files were generated.[/yellow]")
            return

        # Show tree structure of output directory
        self._display_directory_tree()

        # Show demo directory location
        console.print(
            f"\n[dim]{self.t('all_files_location').format(location=self.demo_dir.relative_to(Path.cwd()))}[/dim]"
        )

    def _display_directory_tree(self) -> None:
        """Display output directory structure in tree format with full filenames."""
        if not self.demo_dir or not self.demo_dir.exists():
            return

        console.print(f"[bold cyan]{self.demo_dir.name}/[/bold cyan]")

        # Collect and sort all files and directories
        items = []
        for item in self.demo_dir.iterdir():
            if item.is_file():
                items.append(("file", item))
            elif item.is_dir():
                items.append(("dir", item))

        # Sort: directories first, then files, both alphabetically
        items.sort(key=lambda x: (x[0] == "file", x[1].name.lower()))

        for i, (item_type, item_path) in enumerate(items):
            is_last = i == len(items) - 1
            prefix = "└── " if is_last else "├── "

            if item_type == "file":
                # Display file with size and description
                try:
                    size_bytes = item_path.stat().st_size
                    size_str = self._format_file_size(size_bytes)

                    # Get localized description
                    desc = self._get_localized_file_description(item_path.name)

                    console.print(
                        f"{prefix}[green]{item_path.name}[/green] [dim]({size_str})[/dim] [yellow]- {desc}[/yellow]"
                    )
                except Exception:
                    console.print(f"{prefix}[green]{item_path.name}[/green]")

            elif item_type == "dir":
                # Display directory and its contents
                console.print(f"{prefix}[bold blue]{item_path.name}/[/bold blue]")

                # Show directory contents with proper tree indentation
                self._display_directory_contents(item_path, indent="    " if is_last else "│   ")

    def _display_directory_contents(self, dir_path, indent=""):
        """Display contents of a directory with tree formatting."""
        try:
            # Get all items in directory
            items = []
            for item in dir_path.iterdir():
                if item.is_file():
                    items.append(("file", item))
                elif item.is_dir():
                    items.append(("dir", item))

            # Sort: directories first, then files, both alphabetically
            items.sort(key=lambda x: (x[0] == "file", x[1].name.lower()))

            for i, (item_type, item_path) in enumerate(items):
                is_last = i == len(items) - 1
                prefix = f"{indent}└── " if is_last else f"{indent}├── "

                if item_type == "file":
                    try:
                        size_bytes = item_path.stat().st_size
                        size_str = self._format_file_size(size_bytes)

                        # Get localized description
                        desc = self._get_localized_file_description(item_path.name)

                        console.print(
                            f"{prefix}[green]{item_path.name}[/green] [dim]({size_str})[/dim] [yellow]- {desc}[/yellow]"
                        )
                    except Exception:
                        console.print(f"{prefix}[green]{item_path.name}[/green]")

                elif item_type == "dir":
                    console.print(f"{prefix}[bold blue]{item_path.name}/[/bold blue]")

                    # Recursively display subdirectory contents
                    sub_indent = indent + ("    " if is_last else "│   ")
                    self._display_directory_contents(item_path, sub_indent)

        except Exception as e:
            console.print(f"{indent}[dim]Error reading directory: {e}[/dim]")

    def _format_file_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes // 1024} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes // (1024 * 1024)} MB"
        else:
            return f"{size_bytes // (1024 * 1024 * 1024)} GB"

    def _get_localized_file_description(self, filename):
        """Get localized description for a file based on its name or extension."""
        # Get file descriptions dictionary for current language
        file_descriptions = self.t("file_descriptions")

        # Check for specific filename patterns first
        filename_lower = filename.lower()

        # Specific file mappings
        if ".xml" in filename_lower:
            if "in.xml" == filename_lower:
                return file_descriptions.get("in_xml", "XML file")
            else:
                return file_descriptions.get("xml_general", "XML file")
        elif "in.idf" == filename_lower:
            return file_descriptions.get("in_idf", "IDF file")
        elif "in.osm" == filename_lower:
            return file_descriptions.get("in_osm", "OSM file")
        elif "results_annual.csv" == filename_lower:
            return file_descriptions.get("results_annual_csv", "Annual results")
        elif "results_annual.json" == filename_lower:
            return file_descriptions.get("results_annual_json", "Annual results JSON")
        elif "results_timeseries.csv" == filename_lower:
            return file_descriptions.get("results_timeseries_csv", "Timeseries data")
        elif "eplusout_hourly.msgpack" == filename_lower:
            return file_descriptions.get("eplusout_hourly_msgpack", "Hourly data")
        elif "eplusout_runperiod.msgpack" == filename_lower:
            return file_descriptions.get("eplusout_runperiod_msgpack", "Run period data")
        elif "eplusout.msgpack" == filename_lower:
            return file_descriptions.get("eplusout_msgpack", "EnergyPlus output")
        elif "results_bills.csv" == filename_lower:
            return file_descriptions.get("results_bills_csv", "Bills data")
        elif "results_bills_monthly.csv" == filename_lower:
            return file_descriptions.get("results_bills_monthly_csv", "Monthly bills")
        elif "results_design_load_details.csv" == filename_lower:
            return file_descriptions.get("results_design_load_details_csv", "Design loads")
        elif "eplusout.err" == filename_lower:
            return file_descriptions.get("eplusout_err", "Error log")
        elif "eplusout.end" == filename_lower:
            return file_descriptions.get("eplusout_end", "Completion status")
        elif "run.log" == filename_lower:
            return file_descriptions.get("run_log", "Processing log")
        elif "stderr-energyplus.log" == filename_lower:
            return file_descriptions.get("stderr_energyplus_log", "Error messages")
        elif "stdout-energyplus.log" == filename_lower:
            return file_descriptions.get("stdout_energyplus_log", "Standard output")
        elif "eplustbl.htm" == filename_lower:
            return file_descriptions.get("eplustbl_htm", "HTML report")
        elif "eplusmtr.csv" == filename_lower:
            return file_descriptions.get("eplusmtr_csv", "Meter data")
        elif "eplusout.audit" == filename_lower:
            return file_descriptions.get("eplusout_audit", "Audit trail")
        elif "eplusout.bnd" == filename_lower:
            return file_descriptions.get("eplusout_bnd", "Branch details")
        elif "eplusout.csv" == filename_lower:
            return file_descriptions.get("eplusout_csv", "CSV output")
        elif "eplusout.eio" == filename_lower:
            return file_descriptions.get("eplusout_eio", "Initialization")
        elif "eplusout.eso" == filename_lower:
            return file_descriptions.get("eplusout_eso", "Standard output")
        elif "eplusout_hourly.json" == filename_lower:
            return file_descriptions.get("eplusout_hourly_json", "Hourly JSON")
        elif "eplusout.json" == filename_lower:
            return file_descriptions.get("eplusout_json", "JSON output")
        elif "eplusout.mdd" == filename_lower:
            return file_descriptions.get("eplusout_mdd", "Meter dictionary")
        elif "eplusout.mtd" == filename_lower:
            return file_descriptions.get("eplusout_mtd", "Meter details")
        elif "eplusout.mtr" == filename_lower:
            return file_descriptions.get("eplusout_mtr", "Meter data")
        elif "eplusout_perflog.csv" == filename_lower:
            return file_descriptions.get("eplusout_perflog_csv", "Performance log")
        elif "eplusout.rdd" == filename_lower:
            return file_descriptions.get("eplusout_rdd", "Report dictionary")
        elif "eplusout_runperiod.json" == filename_lower:
            return file_descriptions.get("eplusout_runperiod_json", "Annual JSON")
        elif "eplusout.shd" == filename_lower:
            return file_descriptions.get("eplusout_shd", "Shadow calc")
        elif "eplusout.sql" == filename_lower:
            return file_descriptions.get("eplusout_sql", "SQLite database")
        elif "in.epw" == filename_lower:
            return file_descriptions.get("in_epw", "Weather file")
        elif "sqlite.err" == filename_lower:
            return file_descriptions.get("sqlite_err", "SQLite errors")
        elif filename_lower.endswith(".h2k"):
            return file_descriptions.get("h2k_file", "H2K file")

        # Fallback to extension-based descriptions
        elif filename.endswith(".xml"):
            return file_descriptions.get("xml_fallback", "XML file")
        elif filename.endswith(".csv"):
            return file_descriptions.get("csv_fallback", "CSV file")
        elif filename.endswith(".json"):
            return file_descriptions.get("json_fallback", "JSON file")
        elif filename.endswith(".log"):
            return file_descriptions.get("log_fallback", "Log file")
        elif filename.endswith(".sql"):
            return file_descriptions.get("sql_fallback", "Database file")
        elif filename.endswith(".err"):
            return file_descriptions.get("err_fallback", "Error log")
        elif filename.endswith(".osm"):
            return file_descriptions.get("osm_fallback", "OpenStudio model")
        elif filename.endswith(".idf"):
            return file_descriptions.get("idf_fallback", "EnergyPlus input")
        elif filename.endswith(".msgpack"):
            return file_descriptions.get("msgpack_fallback", "Binary data")
        elif filename.endswith(".htm") or filename.endswith(".html"):
            return file_descriptions.get("html_fallback", "HTML report")
        elif filename.endswith(".txt"):
            return file_descriptions.get("txt_fallback", "Text file")
        elif filename.endswith(".end"):
            return file_descriptions.get("end_fallback", "Status file")
        else:
            return file_descriptions.get("default_fallback", "Output file")

    def show_next_steps(self) -> None:
        """Display what to try next."""
        points = "\n".join(self.tl("learned_points"))

        console.print(
            Panel(
                f"[bold green]{self.t('next_steps')}[/bold green]\n\n"
                f"{self.t('learned')}\n{points}\n\n"
                f"[bold]{self.t('try_next')}[/bold]\n",
                border_style="green",
            )
        )

        # Show command examples
        commands = self.tl("commands")
        for cmd in commands:
            if cmd.startswith("#"):
                console.print(f"[dim]{cmd}[/dim]")
            elif cmd.strip():
                console.print(f"[cyan]{cmd}[/cyan]")
            else:
                console.print()

        console.print(f"\n[dim]{self.t('help_command')}[/dim]")

    def cleanup(self) -> None:
        """Clean up demo files."""
        if self.demo_dir and self.demo_dir.exists():
            console.print(
                f"\n[dim]{self.t('demo_files_location').format(location=self.demo_dir.relative_to(Path.cwd()))}[/dim]"
            )
            if Confirm.ask(f"{self.t('cleanup')}", default=False):
                try:
                    shutil.rmtree(self.demo_dir)
                    console.print(f"[dim]{self.t('cleanup_done')}[/dim]")
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not clean up {self.demo_dir}: {e}[/yellow]"
                    )
            else:
                console.print("[green]Demo files kept for your exploration![/green]")
                console.print(
                    f"[dim]To remove later: rm -rf {self.demo_dir.relative_to(Path.cwd())}[/dim]"
                )


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
