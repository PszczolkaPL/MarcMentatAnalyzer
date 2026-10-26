# Marc/Mentat FEA Post-Processor & Structural Analysis Engine

An automated Python tool designed to parse, extract, and analyze structural FEA results directly from MSC Marc/Mentat output (`.out`) files. This engine processes truss geometry, stress states, and member capacities to identify critical failure modes and calculate total structural load limits.

---

## 🚀 Features

- **Automated Results Extraction:** Parses member stresses, forces, connectivity, and lengths straight from `.out` files.
- **Buckling & Yield Analysis:** Evaluates governing failure mechanisms (Euler Buckling vs. Tensile/Compressive Yielding) for every individual member.
- **Safety Factor Calculation:** Computes member-by-member safety factors based on geometric and material capacity limits.
- **Critical Member Identification:** Isolates the governing member(s) that restrict total structural capacity.
- **Maximum Allowable Load:** Automatically calculates the maximum permissible applied external point load scaled from a benchmark load.

---

## ⚠️ Capabilities & Limitations

> [!NOTE]  
> **2D vs. 3D Workflows**
> - **2D Designs (Fully Automated):** Complete automated extraction and calculation of all lengths, forces, buckling capacities, and safety factors.
> - **3D Designs (Semi-Automated):** Stress extraction works automatically. For full capacity calculations, extracted stresses can be exported to Excel, where member lengths are manually input for 3D geometric evaluation.

---

## 📊 Sample Output Format

When executed on a Marc/Mentat output deck, the script generates structured reports detailing member-by-member performance and structural limits:

```text
Elem   | Nodes      | State       | Length(m) | Stress(MPa)  | Force(kN)  | P_cr(kN)   | Gov. Mode         | SF
===================================================================================================================
1      | N1-N2      | Tension     | 0.360     | 19.16        | 2.87       | 30.0       | Tensile Yield     | 12.27
2      | N3-N4      | Compression | 0.180     | -33.34       | -5.00      | 119.9      | Compressive Yield | 7.05
3      | N4-N6      | Compression | 0.180     | -33.34       | -5.00      | 119.9      | Compressive Yield | 7.05
10     | N3-N36     | Compression | 0.769     | -8.36        | -1.25      | 6.6        | Euler Buckling    | 5.24
11     | N4-N30     | Compression | 0.409     | -21.67       | -3.25      | 23.2       | Euler Buckling    | 7.13
27     | N26-N48    | Compression | 0.135     | -0.00        | -0.00      | 213.2      | Compressive Yield | Inf
===================================================================================================================

===========================================================================
        MAXIMUM ALLOWABLE EXTERNAL POINT LOAD CALCULATION
===========================================================================
  Benchmark External Load (P_applied) : 3.00 kN
  Governing Minimum Safety Factor (SF): 5.24
  ==> MAXIMUM ALLOWABLE POINT LOAD   : 15.72 kN
---------------------------------------------------------------------------
  CRITICAL MEMBER(S) GOVERNING THIS LIMIT:
   • Element 10 (N3-N36): Force = 1.25 kN (Compression), Capacity = 6.60 kN (Euler Buckling)
===========================================================================
```

---

## 🔧 Prerequisites & Usage

### Prerequisites
- Python 3.x
- Standard Python Libraries (`sys`, `re`, `math`)

### Running the Script
1. Place your Marc/Mentat output log (`.out`) in the working directory.
2. Run the script via terminal:
   ```bash
   python analyze_marc_output.py
   ```
3. View the generated summary in the console or inspect the output text report.