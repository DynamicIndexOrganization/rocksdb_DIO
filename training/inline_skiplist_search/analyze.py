import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

data_path = os.getenv("LATENCY_SAMPLE_STORAGE_PATH")

if data_path is None:
    print("DIOERROR: LATENCY_SAMPLE_STORAGE_PATH is not defined in the environment.")
    sys.exit(1)
else:
    print("LATENCY_SAMPLE_STORAGE_PATH is defined at" + data_path)

data_filename = data_path + "/curOpLatencyCollect_Inline_Skiplist_Search.csv"

# load data here
# Initialize lists
data_type = None
num = None
x = []
y = []

with open(data_filename, "r") as f:
    lines = [line.strip() for line in f if line.strip()]  # ignore blank lines

if len(lines) < 2:
    raise ValueError("File must have at least two lines (a string and a number).")

# load the type here
header = lines[0]
if header != "Inline_Skiplist_Search":
    raise ValueError("Data is not for searching in an InlineSkipList. Please check the source file!!!")

# load how many line of data we have now
try:
    # Try int first, then float fallback
    number = int(lines[1])
except ValueError:
    number = float(lines[1])

# load the data now
for line in lines[2:]:
    try:
        # Skip empty lines
        if not line.strip():
            continue
        a, b = map(int, line.split(','))
        x.append(a)
        y.append(b)
    except ValueError:
        raise ValueError(f"Invalid pair format in line: {line}")

if (number != len(x)):
    raise ValueError(f"We expect {number} lines of data but only get {len(x)} lines.")

data = pd.DataFrame({
    'skipListHeight': x,
    'latency': y
})

# Group by x and compute statistics
stats = data.groupby('skipListHeight')['latency'].agg(['mean', 'std']).reset_index()

# Merge and compute z-scores
merged = data.merge(stats, on='skipListHeight')
merged['z_score'] = (merged['latency'] - merged['mean']).abs() / merged['std']

# Categorize each data point
def categorize(z):
    if z <= 1:
        return 'within 1σ'
    elif z <= 2:
        return 'within 2σ'
    else:
        return 'outside 2σ'

merged['category'] = merged['z_score'].apply(categorize)

# Count and compute percentages per category
counts = merged.groupby(['skipListHeight', 'category']).size().unstack(fill_value=0)
counts['total'] = counts.sum(axis=1)
counts['outlier_%'] = 100 * counts['outside 2σ'] / counts['total']

# Print summary
print("Counts and Outlier Percentage per skipListHeight:")
print(counts[['within 1σ', 'within 2σ', 'outside 2σ', 'outlier_%']])


# Plot stacked distribution
percentages = counts[['within 1σ', 'within 2σ', 'outside 2σ']].div(counts['total'], axis=0) * 100

plt.figure(figsize=(10, 6))
percentages.plot(
    kind='bar',
    stacked=True,
    color=['#90EE90', '#FFD700', '#FF6347'],
    edgecolor='black'
)
plt.title("Percentage of Data Points by Deviation Range per skipListHeight")
plt.xlabel("skipListHeight")
plt.ylabel("Percentage (%)")
plt.legend(title="Deviation Range")
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()