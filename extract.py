import cmd
import math
import os
import re
import sys


class MarcAnalyzerApp(cmd.Cmd):
    intro = (
        "\n" + "=" * 75 + "\n"
        "  MSC MARC STRUCTURAL FAILURE ANALYSIS INTERACTIVE SHELL\n"
        "  Type 'help' or '--help' to list available commands.\n"
        + "=" * 75
        + "\n"
    )
    prompt = "(marc) > "

    def __init__(self, default_file=None):
        super().__init__()
        # Section properties
        self.area_mm2 = 150.0  # mm²
        self.E_GPa = 210.0  # GPa
        self.yield_MPa = 235.0  # MPa
        self.section_shape = (
            "square"  # Options: solid_circular, square, pipe
        )

        self.file_path = None
        self.nodes = {}
        self.elements_data = {}
        self.analysis_results = []

        if default_file and os.path.exists(default_file):
            self.load_file(default_file)

    # ----------------------------------------------------------------------
    # Core Extraction & Analysis Engine
    # ----------------------------------------------------------------------

    def parse_marc_out(self, file_path):
        """Extracts node coordinates and element stresses from Marc .out file."""
        nodes = {}
        elements = {}
        current_elem = None

        float_pattern = re.compile(r"[-+]?\d*\.\d+[eE][-+]?\d+|[-+]?\d+\.\d+")

        reading_coords = False

        with open(file_path, "r") as f:
            for line in f:
                # 1. Parse Node Coordinates
                if "c o o r d i n a t e s" in line:
                    reading_coords = True
                    continue

                if reading_coords:
                    if (
                        "t o t a l   d i s p l a c e m e n t s" in line
                        or "i n c r e m e n t a l" in line
                    ):
                        reading_coords = False
                    else:
                        # Parse lines like: 1  0.50000  0.0000  0.0000  2  0.50000 ...
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            try:
                                # Standard Marc coordinate formatting has 2 nodes per line
                                idx = 0
                                while idx < len(parts):
                                    node_id = int(parts[idx])
                                    x = float(parts[idx + 1])
                                    y = float(parts[idx + 2])
                                    z = float(parts[idx + 3])
                                    nodes[node_id] = (x, y, z)
                                    idx += 4
                            except (ValueError, IndexError):
                                pass

                # 2. Parse Integration Point & Stress Output
                if "element" in line and "point" in line:
                    match_elem = re.search(r"element\s+(\d+)", line)
                    if match_elem:
                        current_elem = int(match_elem.group(1))

                    # Try to extract integration point coordinate (midpoint of element)
                    match_coord = re.search(
                        r"integration pt\. coordinate=\s*("
                        + float_pattern.pattern
                        + r")\s+("
                        + float_pattern.pattern
                        + r")\s+("
                        + float_pattern.pattern
                        + r")",
                        line,
                    )
                    if match_coord and current_elem:
                        mid_x = float(match_coord.group(1))
                        mid_y = float(match_coord.group(2))
                        mid_z = float(match_coord.group(3))
                        if current_elem not in elements:
                            elements[current_elem] = {}
                        elements[current_elem]["midpoint"] = (
                            mid_x,
                            mid_y,
                            mid_z,
                        )

                elif (
                    line.strip().startswith("engsts")
                    and current_elem is not None
                ):
                    values = [float(v) for v in float_pattern.findall(line)]
                    if len(values) >= 3:
                        tresca, mises, mean_normal = (
                            values[0],
                            values[1],
                            values[2],
                        )
                        axial_stress = (
                            tresca if mean_normal >= 0 else -tresca
                        )

                        if current_elem not in elements:
                            elements[current_elem] = {}
                        elements[current_elem]["mises"] = mises
                        elements[current_elem]["axial_stress"] = axial_stress
                    current_elem = None

        return nodes, elements

    def _calculate_member_length(self, elem_id, elem_info):
        """Reconstructs bar length L by finding node pair matching element midpoint."""
        if "midpoint" not in elem_info or not self.nodes:
            return 0.20  # Fallback default length (0.2m) if coords missing

        mid = elem_info["midpoint"]
        node_ids = list(self.nodes.keys())

        best_pair = None
        min_midpoint_err = float("inf")

        # Find pair of nodes whose midpoint best matches integration point
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                n1, n2 = self.nodes[node_ids[i]], self.nodes[node_ids[j]]
                calc_mid = (
                    (n1[0] + n2[0]) / 2.0,
                    (n1[1] + n2[1]) / 2.0,
                    (n1[2] + n2[2]) / 2.0,
                )
                err = math.sqrt(
                    sum((calc_mid[k] - mid[k]) ** 2 for k in range(3))
                )

                if err < min_midpoint_err:
                    min_midpoint_err = err
                    best_pair = (n1, n2, node_ids[i], node_ids[j])

        if best_pair and min_midpoint_err < 0.05:
            n1, n2, id1, id2 = best_pair
            L = math.sqrt(sum((n1[k] - n2[k]) ** 2 for k in range(3)))
            elem_info["nodes"] = (id1, id2)
            return L

        return 0.20

    def run_analysis(self):
        """Performs Yielding and Euler Buckling analysis."""
        A = self.area_mm2 * 1e-6  # m²
        E = self.E_GPa * 1e9  # Pa
        sigma_y = self.yield_MPa * 1e6  # Pa
        P_yield = sigma_y * A  # N

        # Moment of Inertia (I) calculation
        if self.section_shape == "solid_circular":
            r = math.sqrt(A / math.pi)
            I = (math.pi * r**4) / 4.0
        elif self.section_shape == "square":
            a = math.sqrt(A)
            I = (a**4) / 12.0
        else:  # Thin Pipe (r_out - r_in approx)
            I = (A**2) / (4.0 * math.pi)

        self.analysis_results = []

        for elem_id, data in sorted(self.elements_data.items()):
            if "axial_stress" not in data:
                continue

            sigma = data["axial_stress"]  # Pa
            P_applied = sigma * A  # N
            abs_P = abs(P_applied)

            L = self._calculate_member_length(elem_id, data)
            nodes_str = (
                f"N{data['nodes'][0]}-N{data['nodes'][1]}"
                if "nodes" in data
                else "N/A"
            )

            # Euler Buckling Load P_cr = (pi^2 * E * I) / L^2
            P_cr = (math.pi**2 * E * I) / (L**2) if L > 0 else float("inf")
            sigma_cr = P_cr / A  # Pa

            state = "Tension" if sigma >= 0 else "Compression"

            if state == "Tension":
                governing_cap = P_yield
                governing_mode = "Tensile Yield"
                SF = P_yield / abs_P if abs_P > 0 else float("inf")
            else:
                # Compression: compare Yielding vs Buckling
                if P_cr < P_yield:
                    governing_cap = P_cr
                    governing_mode = "Euler Buckling"
                else:
                    governing_cap = P_yield
                    governing_mode = "Compressive Yield"

                SF = governing_cap / abs_P if abs_P > 0 else float("inf")

            status = "FAILED" if SF <= 1.0 else "Safe"

            self.analysis_results.append(
                {
                    "elem_id": elem_id,
                    "nodes": nodes_str,
                    "state": state,
                    "length_m": L,
                    "stress_MPa": sigma / 1e6,
                    "force_kN": P_applied / 1000.0,
                    "P_yield_kN": P_yield / 1000.0,
                    "P_buckle_kN": P_cr / 1000.0,
                    "governing_cap_kN": governing_cap / 1000.0,
                    "governing_mode": governing_mode,
                    "safety_factor": SF,
                    "status": status,
                }
            )

    # ----------------------------------------------------------------------
    # Interactive Commands
    # ----------------------------------------------------------------------

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
        """load <filename.out>
        Load and parse a Marc output (.out) file.
        """
        if not arg.strip():
            print("[-] Usage: load <filename.out>")
            return
        self.load_file(arg.strip())

    def do_analyze(self, arg):
        """analyze
        Re-run structural failure analysis (Yielding & Buckling) on loaded model.
        """
        if not self.elements_data:
            print("[-] No file loaded. Use 'load <file.out>' first.")
            return
        self.run_analysis()
        print("[+] Analysis updated successfully.")

    def do_show_all(self, arg):
        """show_all
        Display detailed failure report table for all truss elements.
        """
        if not self.analysis_results:
            print("[-] No data available. Load a file first using 'load'.")
            return

        print("\n" + "=" * 105)
        print(
            f"{'Elem':<6} | {'Nodes':<10} | {'State':<11} | {'Length(m)':<9} | {'Stress(MPa)':<12} | {'Force(kN)':<10} | {'P_cr(kN)':<10} | {'Gov. Mode':<15} | {'SF':<7}"
        )
        print("=" * 105)

        for r in self.analysis_results:
            print(
                f"{r['elem_id']:<6} | {r['nodes']:<10} | {r['state']:<11} | {r['length_m']:<9.3f} | {r['stress_MPa']:<12.2f} | {r['force_kN']:<10.2f} | {r['P_buckle_kN']:<10.1f} | {r['governing_mode']:<15} | {r['safety_factor']:<7.2f}"
            )
        print("=" * 105 + "\n")

    def do_critical(self, arg):
        """critical
        Display critical members closest to failure and governing failure mechanism.
        """
        if not self.analysis_results:
            print("[-] No analysis data available. Load a file first.")
            return

        sorted_risk = sorted(
            self.analysis_results, key=lambda x: x["safety_factor"]
        )

        print("\n" + "=" * 75)
        print("         CRITICAL MEMBERS EXPECTED TO FAIL FIRST")
        print("=" * 75)

        print("\n1. Top Most Critical Compressive Bars (Buckling / Compressive Risk):")
        comp = [r for r in sorted_risk if r["state"] == "Compression"][:3]
        for c in comp:
            print(
                f"   • Element {c['elem_id']:<2} ({c['nodes']}): Stress = {c['stress_MPa']:.2f} MPa, Force = {c['force_kN']:.2f} kN"
            )
            print(
                f"     └─ Governing Limit: {c['governing_mode']} | Capacity = {c['P_buckle_kN']:.1f} kN | Safety Factor = {c['safety_factor']:.2f}"
            )

        print("\n2. Top Most Critical Tensile Bars (Tensile Yielding Risk):")
        tens = [r for r in sorted_risk if r["state"] == "Tension"][:3]
        for t in tens:
            print(
                f"   • Element {t['elem_id']:<2} ({t['nodes']}): Stress = +{t['stress_MPa']:.2f} MPa, Force = +{t['force_kN']:.2f} kN"
            )
            print(
                f"     └─ Governing Limit: Tensile Yield | Capacity = {t['P_yield_kN']:.1f} kN | Safety Factor = {t['safety_factor']:.2f}"
            )
        print("=" * 75 + "\n")

    def do_max_load(self, arg):
        """max_load <applied_load_kN>
        Calculate the maximum allowable external point load before the first member fails.
        Usage: max_load 3.0
        """
        if not self.analysis_results:
            print("[-] No analysis data available. Load a file first.")
            return

        try:
            P_applied_kN = float(arg.strip()) if arg.strip() else 3.0
        except ValueError:
            print("[-] Invalid input. Please enter a numerical load in kN (e.g., max_load 3.0).")
            return

        # Find the absolute minimum safety factor across all elements
        min_sf = min(r["safety_factor"] for r in self.analysis_results)

        # Retrieve ALL elements matching this minimum safety factor (allowing tiny floating-point tolerance)
        crit_elems = [
            r for r in self.analysis_results 
            if abs(r["safety_factor"] - min_sf) < 1e-4
        ]

        max_point_load_kN = P_applied_kN * min_sf

        print("\n" + "=" * 75)
        print("        MAXIMUM ALLOWABLE EXTERNAL POINT LOAD CALCULATION")
        print("=" * 75)
        print(f"  Benchmark External Load (P_applied) : {P_applied_kN:.2f} kN")
        print(f"  Governing Minimum Safety Factor (SF): {min_sf:.2f}")
        print(f"  ==> MAXIMUM ALLOWABLE POINT LOAD   : {max_point_load_kN:.2f} kN")
        print("-" * 75)
        print("  CRITICAL MEMBER(S) GOVERNING THIS LIMIT:")
        for elem in crit_elems:
            print(
                f"   • Element {elem['elem_id']:<2} ({elem['nodes']}): "
                f"Force = {abs(elem['force_kN']):.2f} kN ({elem['state']}), "
                f"Capacity = {elem['governing_cap_kN']:.2f} kN ({elem['governing_mode']})"
            )
        print("=" * 75 + "\n")

    def do_element(self, arg):
        """element <elem_id>
        Inspect complete diagnostic data for a single specific bar element.
        """
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

        print(f"\n--- Element {eid} Detailed Structural Report ---")
        print(f"Nodes Connected    : {match['nodes']}")
        print(f"Member Length      : {match['length_m']:.4f} m")
        print(f"Loading State      : {match['state']}")
        print(f"Axial Stress       : {match['stress_MPa']:.2f} MPa")
        print(f"Axial Force        : {match['force_kN']:.2f} kN")
        print(f"Yield Capacity     : {match['P_yield_kN']:.2f} kN")
        print(f"Euler Buckling Cap : {match['P_buckle_kN']:.2f} kN")
        print(f"Governing Mechanism: {match['governing_mode']}")
        print(f"Safety Factor (SF) : {match['safety_factor']:.2f}")
        print(f"Status             : {match['status']}\n")

    def do_set_prop(self, arg):
        """set_prop [area=150] [E=210] [yield=250] [shape=solid_circular]
        Configure section properties (Area mm², Young's Modulus GPa, Yield Stress MPa, Shape).
        Shapes: solid_circular, square, pipe
        """
        parts = arg.split()
        for p in parts:
            if "=" in p:
                k, v = p.split("=", 1)
                if k.lower() == "area":
                    self.area_mm2 = float(v)
                elif k.lower() == "e":
                    self.E_GPa = float(v)
                elif k.lower() == "yield":
                    self.yield_MPa = float(v)
                elif k.lower() == "yield_stress":
                    self.yield_MPa = float(v)
                elif k.lower() == "shape":
                    self.section_shape = v.lower()

        print(
            f"[+] Updated Parameters: Area={self.area_mm2}mm², E={self.E_GPa}GPa, Yield={self.yield_MPa}MPa, Shape={self.section_shape}"
        )
        if self.elements_data:
            self.run_analysis()

    # Aliases and Help Support
    def do_help(self, arg):
        """Displays help and list of available actions."""
        if arg == "--help" or arg == "-h" or not arg:
            print("\n" + "=" * 60)
            print("                AVAILABLE ACTIONS & COMMANDS")
            print("=" * 60)
            print("  load <file.out>      : Load Marc MSC output (.out) file")
            print(
                "  critical             : Show bars expected to fail first & mechanisms"
            )
            print(
                "  max_load <load_kN>   : Calculate maximum point load before failure"
            )
            print(
                "  show_all             : Display table of all parsed members"
            )
            print(
                "  element <id>         : Show detailed inspection for one element"
            )
            print(
                "  set_prop [k=v]       : Set Area, E, Yield Stress, or Shape"
            )
            print(
                "  analyze              : Re-calculate yielding & buckling limits"
            )
            print("  help / --help        : Display this help menu")
            print("  exit / quit          : Exit application")
            print("=" * 60 + "\n")
        else:
            super().default(arg)

    def default(self, line):
        if line.strip() in ["--help", "-h"]:
            self.do_help("--help")
        else:
            print(f"[-] Unknown command: '{line}'. Type 'help' for options.")

    def do_exit(self, arg):
        """Exit the application."""
        print("Exiting Marc Analyzer.")
        return True

    def do_quit(self, arg):
        """Exit the application."""
        return self.do_exit(arg)


if __name__ == "__main__":
    default_file = sys.argv[1] if len(sys.argv) > 1 else "model6_Stress.out"
    app = MarcAnalyzerApp(
        default_file=default_file if os.path.exists(default_file) else None
    )
    app.cmdloop()