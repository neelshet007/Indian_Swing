import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("task-log.txt", "rb") as f:
    content = f.read()

try:
    text = content.decode('utf-16')
except Exception:
    text = content.decode('utf-8', errors='ignore')

lines = text.splitlines()
idx = -1
for i, line in enumerate(lines):
    if "gkpj" in line:
        idx = i
        break

if idx != -1:
    print(f"Found 'gkpj' at line {idx}. Printing 40 lines before it (truncated to 100 chars per line):")
    start = max(0, idx - 40)
    for j in range(start, idx + 1):
        line = lines[j]
        # truncate very long SQL insert statements
        if len(line) > 120:
            line = line[:100] + "... [TRUNCATED LINE] ..." + line[-20:]
        print(f"{j}: {line}")
else:
    # If gkpj is not found, print the last 40 lines of the file
    print("No 'gkpj' found, printing last 40 lines:")
    for j in range(max(0, len(lines)-40), len(lines)):
        line = lines[j]
        if len(line) > 120:
            line = line[:100] + "... [TRUNCATED] ..." + line[-20:]
        print(f"{j}: {line}")
