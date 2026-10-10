import math

from .models import SectionProperties


def calculate_member_length(nodes, elem_info):
    """Reconstruct member length L by matching the element midpoint to node pairs."""
    if "midpoint" not in elem_info or not nodes:
        return 0.20

    mid = elem_info["midpoint"]
    node_ids = list(nodes.keys())

    best_pair = None
    min_midpoint_err = float("inf")

    for i in range(len(node_ids)):
        for j in range(i + 1, len(node_ids)):
            n1, n2 = nodes[node_ids[i]], nodes[node_ids[j]]
            calc_mid = (
                (n1[0] + n2[0]) / 2.0,
                (n1[1] + n2[1]) / 2.0,
                (n1[2] + n2[2]) / 2.0,
            )
            err = math.sqrt(sum((calc_mid[k] - mid[k]) ** 2 for k in range(3)))

            if err < min_midpoint_err:
                min_midpoint_err = err
                best_pair = (n1, n2, node_ids[i], node_ids[j])

    if best_pair and min_midpoint_err < 0.05:
        n1, n2, id1, id2 = best_pair
        length = math.sqrt(sum((n1[k] - n2[k]) ** 2 for k in range(3)))
        elem_info["nodes"] = (id1, id2)
        return length

    return 0.20


def perform_analysis(nodes, elements_data, section):
    """Performs yielding and Euler buckling analysis for all elements."""
    if not isinstance(section, SectionProperties):
        section = SectionProperties(**section)

    A = section.area_mm2 * 1e-6
    E = section.E_GPa * 1e9
    sigma_y = section.yield_MPa * 1e6
    P_yield = sigma_y * A

    if section.section_shape == "solid_circular":
        r = math.sqrt(A / math.pi)
        I = (math.pi * r**4) / 4.0
    elif section.section_shape == "square":
        a = math.sqrt(A)
        I = (a**4) / 12.0
    else:
        I = (A**2) / (4.0 * math.pi)

    analysis_results = []

    for elem_id, data in sorted(elements_data.items()):
        if "axial_stress" not in data:
            continue

        sigma = data["axial_stress"]
        P_applied = sigma * A
        abs_P = abs(P_applied)

        L = calculate_member_length(nodes, data)
        nodes_str = (
            f"N{data['nodes'][0]}-N{data['nodes'][1]}"
            if "nodes" in data
            else "N/A"
        )

        P_cr = (math.pi**2 * E * I) / (L**2) if L > 0 else float("inf")
        state = "Tension" if sigma >= 0 else "Compression"

        if state == "Tension":
            governing_cap = P_yield
            governing_mode = "Tensile Yield"
            SF = P_yield / abs_P if abs_P > 0 else float("inf")
        else:
            if P_cr < P_yield:
                governing_cap = P_cr
                governing_mode = "Euler Buckling"
            else:
                governing_cap = P_yield
                governing_mode = "Compressive Yield"

            SF = governing_cap / abs_P if abs_P > 0 else float("inf")

        status = "FAILED" if SF <= 1.0 else "Safe"

        analysis_results.append(
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

    return analysis_results
