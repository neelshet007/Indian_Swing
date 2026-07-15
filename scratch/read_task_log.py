import sys

# Reconfigure stdout to use utf-8 to avoid encoding errors on windows
sys.stdout.reconfigure(encoding='utf-8')

# Try open with utf-16 first, if total lines is small or weird, try other encodings.
# Actually let's try reading the file as binary first to inspect it, or read with errors='ignore' on both open and print.
try:
    with open("task-log.txt", "r", encoding="utf-16", errors="ignore") as f:
        lines = f.readlines()
        print("Total lines (utf-16):", len(lines))
        for line in lines[-200:]:
            print(line.strip().encode('ascii', errors='ignore').decode('ascii'))
except Exception as e:
    print("Error reading utf-16:", e)

try:
    with open("task-log.txt", "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        print("Total lines (utf-8):", len(lines))
        for line in lines[-200:]:
            print(line.strip().encode('ascii', errors='ignore').decode('ascii'))
except Exception as e:
    print("Error reading utf-8:", e)
