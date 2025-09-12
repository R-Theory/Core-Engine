# Create an Excel workbook with the user's PHYS 118 Studio 02 analysis,
# including data, LINEST outputs, physics calculations, unit conversions,
# and a final results table (with proper sig figs).

import math
import pandas as pd
import numpy as np

from datetime import datetime

# Data (user-provided)
tA = [0,1.03,1.67,2.01,2.49,3.07,3.19]
xA = [0,7,23,31,50,70,85]  # cm
tB = [0,0.62,1.06,1.14,1.80,2.15,2.16]
xB = [0,7,20,32,61,75,85]  # cm

dfA = pd.DataFrame({
    "t (s)": tA,
    "t^2 (s^2)": [round(v*v, 6) for v in tA],
    "x (cm)": xA
})

dfB = pd.DataFrame({
    "t (s)": tB,
    "t^2 (s^2)": [round(v*v, 6) for v in tB],
    "x (cm)": xB
})

path = "/mnt/data/PHYS118_Studio02_Analysis.xlsx"

with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
    # --- Sheet 1: Data ---
    dfA.to_excel(writer, sheet_name="Data", index=False, startrow=1, startcol=0)
    dfB.to_excel(writer, sheet_name="Data", index=False, startrow=1, startcol=5)
    wb  = writer.book
    wsD = writer.sheets["Data"]

    # Titles
    wsD.write(0, 0, "Trial A Data")
    wsD.write(0, 5, "Trial B Data")

    # Add units note
    wsD.write(10, 0, "Units: time in seconds (s), position in centimeters (cm). t^2 computed as (t)^2.")

    # --- Sheet 2: Analysis ---
    wsA = wb.add_worksheet("Analysis")

    # Headers for LINEST interpretation
    headers = ["slope (cm/s^2)", "intercept x0 (cm)", "R^2", "s_y (cm)", "F"]
    headers2= ["σ_slope", "σ_intercept", "df", "SS_reg", "SS_resid"]

    wsA.write(0, 0, "Trial A: LINEST (x vs t^2)")
    for j, h in enumerate(headers):
        wsA.write(1, j+1, h)
    for j, h in enumerate(headers2):
        wsA.write(2, j+1, h)

    wsA.write(9, 0, "Trial B: LINEST (x vs t^2)")
    for j, h in enumerate(headers):
        wsA.write(10, j+1, h)
    for j, h in enumerate(headers2):
        wsA.write(11, j+1, h)

    # Array formulas for LINEST (2x5). Data ranges:
    # Trial A data: Data!B2:B8 (t^2), Data!C2:C8 (x)
    # Trial B data: Data!G2:G8 (t^2), Data!H2:H8 (x)

    # Placeholders so the 2x5 block is obvious:
    for r in range(2):
        for c in range(5):
            wsA.write(1+r, 1+c, "")  # A block for A
            wsA.write(10+r, 1+c, "") # A block for B

    # Write array formulas with LINEST (y, x, TRUE, TRUE)
    # Note: xlsxwriter uses R1C1-style array formula ranges.
    # We'll use A1 style via utility function to compute ranges.
    def a1_range(row1, col1, row2, col2):
        # 0-indexed in code, convert to A1
        def col_to_name(c):
            s=""
            c0 = c
            while True:
                s = chr(c0 % 26 + ord('A')) + s
                c0 = c0 // 26 - 1
                if c0 < 0:
                    break
            return s
        return f"{col_to_name(col1)}{row1+1}:{col_to_name(col2)}{row2+1}"

    # Trial A array output at B2:F3 (rows 1-2, cols 1-5 in 0-index)
    A_out = a1_range(1,1,2,5)  # B2:F3
    # Trial B array output at B11:F12
    B_out = a1_range(10,1,11,5)  # B11:F12

    # Ranges for A
    yA = "Data!C2:C8"  # x (cm)
    xA = "Data!B2:B8"  # t^2 (s^2)
    # Ranges for B
    yB = "Data!H2:H8"  # x (cm)
    xB = "Data!G2:G8"  # t^2 (s^2)

    wsA.write_array_formula(A_out, f"=LINEST({yA},{xA},TRUE,TRUE)")
    wsA.write_array_formula(B_out, f"=LINEST({yB},{xB},TRUE,TRUE)")

    # Labels & physics calculations
    wsA.write(4, 0, "Physics Calculations (Trial A)")
    wsA.write(5, 0, "acceleration a (cm/s^2) = 2*slope")
    wsA.write(6, 0, "uncertainty σ_a (cm/s^2) = 2*σ_slope")
    wsA.write(7, 0, "x0 (cm) and σ_x0 (cm) from intercept outputs")

    # Place formulas for Trial A
    wsA.write(5, 4, "=2*B2")   # a_cm
    wsA.write(6, 4, "=2*B3")   # ua_cm
    wsA.write(5, 5, "cm/s^2")
    wsA.write(6, 5, "cm/s^2")
    wsA.write(7, 4, "=C2")     # x0_cm
    wsA.write(7, 5, "cm")
    wsA.write(7, 6, "=C3")     # ux0_cm
    wsA.write(7, 7, "cm")

    # Conversions to SI (Trial A)
    wsA.write(5, 7, "a (m/s^2)")
    wsA.write(5, 8, "=E6/100")   # a_m
    wsA.write(6, 7, "σ_a (m/s^2)")
    wsA.write(6, 8, "=E7/100")   # ua_m
    wsA.write(7, 7, "x0 (m)")
    wsA.write(7, 8, "=E8/100")   # x0_m
    wsA.write(7, 9, "σ_x0 (m)")
    wsA.write(7,10, "=G8/100")   # ux0_m

    # Physics Calculations for Trial B
    wsA.write(13, 0, "Physics Calculations (Trial B)")
    wsA.write(14, 0, "acceleration a (cm/s^2) = 2*slope")
    wsA.write(15, 0, "uncertainty σ_a (cm/s^2) = 2*σ_slope")
    wsA.write(16, 0, "x0 (cm) and σ_x0 (cm) from intercept outputs")

    # Place formulas for Trial B (referencing the second LINEST block B11:F12)
    wsA.write(14, 4, "=2*B11")  # a_cm
    wsA.write(15, 4, "=2*B12")  # ua_cm
    wsA.write(14, 5, "cm/s^2")
    wsA.write(15, 5, "cm/s^2")
    wsA.write(16, 4, "=C11")    # x0_cm
    wsA.write(16, 5, "cm")
    wsA.write(16, 6, "=C12")    # ux0_cm
    wsA.write(16, 7, "cm")

    # Conversions to SI (Trial B)
    wsA.write(14, 7, "a (m/s^2)")
    wsA.write(14, 8, "=E15/100")  # a_m
    wsA.write(15, 7, "σ_a (m/s^2)")
    wsA.write(15, 8, "=E16/100")  # ua_m
    wsA.write(16, 7, "x0 (m)")
    wsA.write(16, 8, "=E17/100")  # x0_m
    wsA.write(16, 9, "σ_x0 (m)")
    wsA.write(16,10, "=G17/100")  # ux0_m

    # --- Sheet 3: Results ---
    wsR = wb.add_worksheet("Results")

    # Helper formulas for 1-sig-fig rounding of uncertainty;
    # We'll define a small block for each trial in SI units.
    wsR.write(0,0,"Final Results (SI units)")
    wsR.write(2,0,"Quantity")
    wsR.write(2,1,"Value")
    wsR.write(2,2,"Uncertainty (1 s.f.)")
    wsR.write(2,3,"Reported")

    # Trial A
    wsR.write(1,0,"Trial A")
    wsR.write(3,0,"Acceleration a (m/s^2)")
    wsR.write(4,0,"Initial position x0 (m)")

    # Pull raw SI values from Analysis
    wsR.write(3,1,"=Analysis!I6")    # a_m
    wsR.write(3,2,"=Analysis!I7")    # ua_m
    wsR.write(4,1,"=Analysis!I8")    # x0_m
    wsR.write(4,2,"=Analysis!K8")    # ux0_m

    # Rounding to 1 s.f. uncertainty:
    # u1sf = ROUNDUP(u / 10^FLOOR(LOG10(u),1), 0) * 10^FLOOR(LOG10(u),1)
    wsR.write(3,5,"=IF(C4=0,0,ROUNDUP(C4/10^FLOOR(LOG10(C4),1),0)*10^FLOOR(LOG10(C4),1))")
    wsR.write(4,5,"=IF(C5=0,0,ROUNDUP(C5/10^FLOOR(LOG10(C5),1),0)*10^FLOOR(LOG10(C5),1))")
    wsR.write(3,4,"u (1 s.f.)")
    wsR.write(4,4,"u (1 s.f.)")

    # Decimal places to match uncertainty: dp = -FLOOR(LOG10(u1sf),1)
    wsR.write(3,6,"=IF(E4=0,0,-FLOOR(LOG10(E4),1))")
    wsR.write(4,6,"=IF(E5=0,0,-FLOOR(LOG10(E5),1))")
    wsR.write(3,7,"dp")
    wsR.write(4,7,"dp")

    # Rounded central values to those decimal places
    wsR.write(3,8,"=IF(G4=\"\",B4,ROUND(B4,G4))")
    wsR.write(4,8,"=IF(G5=\"\",B5,ROUND(B5,G5))")
    wsR.write(3,9,"value rounded")
    wsR.write(4,9,"value rounded")

    # Reported strings: "value ± u"
    wsR.write(3,3,'=TEXT(I4,"0."&REPT("0",G4))&" ± "&TEXT(E4,"0."&REPT("0",G4))&" m/s^2"')
    wsR.write(4,3,'=TEXT(I5,"0."&REPT("0",G5))&" ± "&TEXT(E5,"0."&REPT("0",G5))&" m"')

    # Trial B
    wsR.write(6,0,"Trial B")
    wsR.write(7,0,"Acceleration a (m/s^2)")
    wsR.write(8,0,"Initial position x0 (m)")

    wsR.write(7,1,"=Analysis!I15")   # a_m (B)
    wsR.write(7,2,"=Analysis!I16")   # ua_m (B)
    wsR.write(8,1,"=Analysis!I17")   # x0_m (B)
    wsR.write(8,2,"=Analysis!K17")   # ux0_m (B)

    wsR.write(7,5,"=IF(C8=0,0,ROUNDUP(C8/10^FLOOR(LOG10(C8),1),0)*10^FLOOR(LOG10(C8),1))")
    wsR.write(8,5,"=IF(C9=0,0,ROUNDUP(C9/10^FLOOR(LOG10(C9),1),0)*10^FLOOR(LOG10(C9),1))")
    wsR.write(7,4,"u (1 s.f.)")
    wsR.write(8,4,"u (1 s.f.)")

    wsR.write(7,6,"=IF(E8=0,0,-FLOOR(LOG10(E8),1))")
    wsR.write(8,6,"=IF(E9=0,0,-FLOOR(LOG10(E9),1))")
    wsR.write(7,7,"dp")
    wsR.write(8,7,"dp")

    wsR.write(7,8,"=IF(G8=\"\",B8,ROUND(B8,G8))")
    wsR.write(8,8,"=IF(G9=\"\",B9,ROUND(B9,G9))")
    wsR.write(7,9,"value rounded")
    wsR.write(8,9,"value rounded")

    wsR.write(7,3,'=TEXT(I8,"0."&REPT("0",G8))&" ± "&TEXT(E8,"0."&REPT("0",G8))&" m/s^2"')
    wsR.write(8,3,'=TEXT(I9,"0."&REPT("0",G9))&" ± "&TEXT(E9,"0."&REPT("0",G9))&" m"')

    # Notes
    wsR.write(11,0,"Notes:")
    wsR.write(12,0,"- LINEST blocks are 2x5 arrays (slope, intercept, R^2, s_y, F; then their uncertainties, df, SS).")
    wsR.write(13,0,"- Acceleration a = 2*slope. Uncertainty σ_a = 2*σ_slope. cm→m conversion divides by 100.")
    wsR.write(14,0,"- Uncertainty is rounded to 1 significant figure; central value rounded to the same decimal place.")
    wsR.write(15,0,"- Units are included in the 'Reported' column.")

path
