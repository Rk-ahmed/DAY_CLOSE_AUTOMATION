import pyautogui
import json
import time

coordinates = {}

print("Coordinate Recorder")
print("You have 5 seconds to switch to your browser...")
time.sleep(5)

while True:
    desc = input("Enter description for this element (or 'done' to finish): ")
    if desc.lower() == 'done':
        break
    input(f"Hover over the '{desc}' element and press ENTER...")
    x, y = pyautogui.position()
    coordinates[desc] = {"x": x, "y": y}
    print(f"Recorded {desc} at ({x}, {y})")

# Save to JSON
with open("coords.json", "w") as f:
    json.dump(coordinates, f, indent=4)

print("All coordinates saved to coords.json")