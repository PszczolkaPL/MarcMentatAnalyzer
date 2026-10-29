import re


def parse_marc_out(file_path):
    """Extracts node coordinates and element stresses from a Marc .out file."""
    nodes = {}
    elements = {}
    current_elem = None

    float_pattern = re.compile(
        r"[-+]?\d*\.\d+[eE][-+]?\d+|[-+]?\d+\.\d+"
    )

    reading_coords = False

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
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
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        try:
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

            if "element" in line and "point" in line:
                match_elem = re.search(r"element\s+(\d+)", line)
                if match_elem:
                    current_elem = int(match_elem.group(1))

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

            elif line.strip().startswith("engsts") and current_elem is not None:
                values = [float(v) for v in float_pattern.findall(line)]
                if len(values) >= 3:
                    tresca, mises, mean_normal = values[0], values[1], values[2]
                    axial_stress = tresca if mean_normal >= 0 else -tresca

                    if current_elem not in elements:
                        elements[current_elem] = {}
                    elements[current_elem]["mises"] = mises
                    elements[current_elem]["axial_stress"] = axial_stress
                current_elem = None

    return nodes, elements
