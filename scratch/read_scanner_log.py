import sys

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Harsh Shet\.gemini\antigravity-ide\brain\6ea9fcad-7dd5-4452-ba0a-bf47bfc032fa\.system_generated\tasks\task-282.log"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
    print("Total lines:", len(lines))
    for line in lines[-150:]:
        print(line.strip())
