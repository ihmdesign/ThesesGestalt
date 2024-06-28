import json
import matplotlib.pyplot as plt
from collections import defaultdict

# Read the file
with open("commands/commands_phantom_gaussian_2cm.json") as f:
    lines = f.readlines()

# Convert each line to a JSON object and organize the data
data = defaultdict(list)
for line in lines:
    obj = json.loads(line)
    data[obj["addr"]].append((obj["time"], obj["duty"]))

# Create a plot for each group
for addr, values in data.items():
    times, duties = zip(*values)
    plt.plot(times, duties, label=f'addr={addr}')

# Set plot details
plt.xlabel('Time')
plt.ylabel('Duty')
plt.legend()
plt.title('Duty over time for different addr')
plt.show()
