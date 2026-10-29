import argparse
import cmd
import os
import shlex

try:
    from ..core.analysis import perform_analysis
    from ..core.models import SectionProperties
    from ..core.parser import parse_marc_out
    from .outputs import (
        print_analysis_table,
        print_critical_summary,
        print_element_report,
        print_max_load_summary,
    )
    from .report import (
        generate_report,
        generate_report_file,
    )
    from .subreport import report_help
    from .help import (
         print_help_menu,
         print_about_info,
         print_version_info
    )

except ImportError:  # pragma: no cover
    from core.analysis import perform_analysis
    from core.models import SectionProperties
    from core.parser import parse_marc_out
    from .outputs import (
        print_analysis_table,
        print_critical_summary,
        print_element_report,
        print_max_load_summary,
    )
    from .report import (
        generate_report,
        generate_report_file,
    )
    from .subreport import report_help
    from .help import (
        print_help_menu,
        print_about_info,
        print_version_info
    )


class MarcAnalyzerApp(cmd.Cmd):
    intro = (
        "\n" + "=" * 75 + "\n"
        "  MSC MARC STRUCTURAL FAILURE ANALYSIS INTERACTIVE SHELL\n"
        "  Type 'help' or '--help' to list available commands.\n"
        + "=" * 75
        + "\n"
    )
    prompt = "(Marc/Mentat Analyzer) > "

    def __init__(self, default_file=None):
        super().__init__()
        self.section_properties = SectionProperties()
        self.file_path = None
        self.nodes = {}
        self.elements_data = {}
        self.analysis_results = []

        if default_file and os.path.exists(default_file):
            self.load_file(default_file)

    def run_analysis(self):
        """Performs yielding and Euler buckling analysis."""
        self.analysis_results = perform_analysis(
            self.nodes,
            self.elements_data,
            self.section_properties,
        )

    def parse_marc_out(self, file_path):
        """Backward compatible wrapper around the parser module."""
        return parse_marc_out(file_path)

    def load_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"[-] Error: File '{file_path}' does not exist.")
            return False

        self.file_path = file_path
        self.nodes, self.elements_data = self.parse_marc_out(file_path)
        print(
            f"[+] Loaded '{file_path}': Found {len(self.nodes)} nodes, {len(self.elements_data)} truss elements."
        )
        self.run_analysis()
        return True

    def do_load(self, arg):
        if not arg.strip():
            print("[-] Usage: load <filename.out>")
            return
        self.load_file(arg.strip())

    def do_analyze(self, arg):
        if not self.elements_data:
            print("[-] No file loaded. Use 'load <file.out>' first.")
            return
        self.run_analysis()
        print("[+] Analysis updated successfully.")

    def do_show_all(self, arg):
        if not self.analysis_results:
            print("[-] No data available. Load a file first using 'load'.")
            return
        print_analysis_table(self.analysis_results)

    def do_critical(self, arg):
        if not self.analysis_results:
            print("[-] No analysis data available. Load a file first.")
            return
        print_critical_summary(self.analysis_results)

    def do_max_load(self, arg):
        if not self.analysis_results:
            print("[-] No analysis data available. Load a file first.")
            return

        try:
            P_applied_kN = float(arg.strip()) if arg.strip() else 3.0
        except ValueError:
            print("[-] Invalid input. Please enter a numerical load in kN (e.g., max_load 3.0).")
            return

        print_max_load_summary(self.analysis_results, P_applied_kN)

    def do_element(self, arg):
        if not arg.isdigit():
            print("[-] Usage: element <elem_id>  (e.g., element 9)")
            return

        eid = int(arg)
        match = next(
            (r for r in self.analysis_results if r["elem_id"] == eid), None
        )

        if not match:
            print(f"[-] Element {eid} not found.")
            return

        print_element_report(match)

    def do_set_prop(self, arg):
        parts = arg.split()
        for p in parts:
            if "=" in p:
                k, v = p.split("=", 1)
                if k.lower() == "area":
                    self.section_properties.area_mm2 = float(v)
                elif k.lower() == "e":
                    self.section_properties.E_GPa = float(v)
                elif k.lower() == "yield":
                    self.section_properties.yield_MPa = float(v)
                elif k.lower() == "yield_stress":
                    self.section_properties.yield_MPa = float(v)
                elif k.lower() == "shape":
                    self.section_properties.section_shape = v.lower()

        print(
            f"[+] Updated Parameters: Area={self.section_properties.area_mm2}mm², E={self.section_properties.E_GPa}GPa, Yield={self.section_properties.yield_MPa}MPa, Shape={self.section_properties.section_shape}"
        )
        if self.elements_data:
            self.run_analysis()



    def do_report(self, arg):
        try:
            tokens = shlex.split(arg)
        except ValueError as error:
            print(f"[-] Invalid command: {error}")
            return

        parser = argparse.ArgumentParser(prog="report", add_help=False)
        parser.add_argument("-h", "--help", action="store_true")
        parser.add_argument("--file", "-f", choices=["txt", "csv"], default="txt", action="store_true")
        parser.add_argument("--summary", "-s", action="store_true")
        parser.add_argument("--critical-only", "-c", action="store_true")
        try:
            options = parser.parse_args(tokens)
        except SystemExit:
            return

        if options.help:
            report_help()
            return
    
        if options.file:
            generate_report_file(options.summary, options.critical_only, options.file)
            return

        
    def do_help(self, arg):
        if arg == "--help" or arg == "-h" or not arg:
            print_help_menu()
        else:
            super().default(arg)

    def default(self, line):
        if line.strip() in ["--help", "-h"]:
            self.do_help("--help")
        else:
            print(f"[-] Unknown command: '{line}'. Type 'help' for options.")

    def do_about(self, arg):
        print_about_info()

    def do_version(self, arg):
        print_version_info()

    def do_exit(self, arg):
        print("Exiting Marc Analyzer.")
        return True

    def do_quit(self, arg):
        return self.do_exit(arg)
