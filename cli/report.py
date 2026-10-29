from outputs import (
    print_critical_summary, 
    execute_report
)



def generate_report(self, summary=False, critical_only=False, file_format="txt"):
    return

def generate_report_file(self, summary=False, critical_only=False, file_format="txt"):
    if not self.analysis_results:
        print("[-] No analysis data available. Load a file first.")
        return

    if critical_only:
        results_to_report = sorted(self.analysis_results, key=lambda x: x["safety_factor"])[:3]
    else:
        results_to_report = self.analysis_results

    if summary:
        print_critical_summary(results_to_report)
    else:
        execute_report(results_to_report)

    if file_format == "txt":
        output_filename = "structural_report.txt"
        with open(output_filename, "w") as f:
            f.write("DETAILED STRUCTURAL REPORT\n")
            f.write("=" * 75 + "\n")
            for r in results_to_report:
                f.write(f"\n--- Element {r['elem_id']} Detailed Structural Report ---\n")
                f.write(f"Nodes Connected    : {r['nodes']}\n")
                f.write(f"Member Length      : {r['length_m']:.4f} m\n")
                f.write(f"Material Weight    : {r['weight_kg']:.2f} kg\n")
                f.write(f"Loading State      : {r['state']}\n")
                f.write(f"Axial Stress       : {r['stress_MPa']:.2f} MPa\n")
                f.write(f"Axial Force        : {r['force_kN']:.2f} kN\n")
                f.write(f"Yield Capacity     : {r['P_yield_kN']:.2f} kN\n")
                f.write(f"Euler Buckling Cap : {r['P_buckle_kN']:.2f} kN\n")
                f.write(f"Governing Mechanism: {r['governing_mode']}\n")
                f.write(f"Safety Factor (SF) : {r['safety_factor']:.2f}\n")
                f.write(f"Status             : {r['status']}\n")
            f.write("=" * 75 + "\n")

        print(f"[+] Report saved to '{output_filename}'")