def print_analysis_table(results):
    print("\n" + "=" * 105)
    print(
        f"{'Elem':<6} | {'Nodes':<10} | {'State':<11} | {'Length(m)':<9} | {'Stress(MPa)':<12} | {'Force(kN)':<10} | {'P_cr(kN)':<10} | {'Gov. Mode':<15} | {'SF':<7}"
    )
    print("=" * 105)

    for r in results:
        print(
            f"{r['elem_id']:<6} | {r['nodes']:<10} | {r['state']:<11} | {r['length_m']:<9.3f} | {r['stress_MPa']:<12.2f} | {r['force_kN']:<10.2f} | {r['P_buckle_kN']:<10.1f} | {r['governing_mode']:<15} | {r['safety_factor']:<7.2f}"
        )
    print("=" * 105 + "\n")


def print_critical_summary(results):
    sorted_risk = sorted(results, key=lambda x: x["safety_factor"])

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


def print_max_load_summary(results, P_applied_kN):
    min_sf = min(r["safety_factor"] for r in results)
    crit_elems = [
        r for r in results if abs(r["safety_factor"] - min_sf) < 1e-4
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


def print_element_report(match):
    print(f"\n--- Element {match['elem_id']} Detailed Structural Report ---")
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


def execute_report(results):
    print("\n" + "=" * 75)
    print("                DETAILED STRUCTURAL REPORT")
    print("=" * 75)

    for r in results:
        print(f"\n--- Element {r['elem_id']} Detailed Structural Report ---")
        print(f"Nodes Connected    : {r['nodes']}")
        print(f"Member Length      : {r['length_m']:.4f} m")
        print(f"Material Weight    : {r['weight_kg']:.2f} kg")
        print(f"Loading State      : {r['state']}")
        print(f"Axial Stress       : {r['stress_MPa']:.2f} MPa")
        print(f"Axial Force        : {r['force_kN']:.2f} kN")
        print(f"Yield Capacity     : {r['P_yield_kN']:.2f} kN")
        print(f"Euler Buckling Cap : {r['P_buckle_kN']:.2f} kN")
        print(f"Governing Mechanism: {r['governing_mode']}")
        print(f"Safety Factor (SF) : {r['safety_factor']:.2f}")
        print(f"Status             : {r['status']}")
    print("=" * 75 + "\n")