import re

with open("bob-example.qif", "r") as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    line_str = line.strip()

    # Skip empty T lines left over at the end of blocks
    if line_str == "T":
        continue

    # Parse 'TKYD 123.45 Dr' or 'TKYD 123.45 Cr'
    match = re.match(r"^TKYD\s*([\d,.]+)\s*(Dr|Cr)$", line_str)
    if match:
        amount_str, dr_cr = match.groups()
        amount = float(amount_str.replace(",", ""))
        if dr_cr == "Dr":
            amount = -amount
        fixed_lines.append(f"T{amount:.2f}\n")
    else:
        fixed_lines.append(line)

with open("bob-fixed.qif", "w") as f:
    f.writelines(fixed_lines)
