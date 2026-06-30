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

data_filename = data_path + "/curOpLatencyCollect_Vector_Insert.csv"

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
if header != "Vector_Insert":
    raise ValueError("Data is not for insert into a Vector. Please check the source file!!!")

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
    'vectorLength': x,
    'latency': y
})

# Group by x and compute statistics
mean_y = data['latency'].mean()
std_y = data['latency'].std()

# Merge and compute z-scores
data['z_score'] = (data['latency'] - mean_y).abs() / std_y

# Categorize each data point
def categorize(z):
    if z <= 1:
        return 'within 1σ'
    elif z <= 2:
        return 'within 2σ'
    else:
        return 'outside 2σ'

data['category'] = data['z_score'].apply(categorize)

# Count and compute percentages per category
counts = data['category'].value_counts().reindex(['within 1σ', 'within 2σ', 'outside 2σ'], fill_value=0)
percentages = counts / len(data) * 100

# Print summary
print("Summary of deviation ranges:")
summary = pd.DataFrame({
    'count': counts,
    'percentage (%)': percentages.round(2)
})
print(summary)
print(f"\nOverall outlier percentage (outside 2σ): {percentages['outside 2σ']:.2f}%")

# Plot stacked distribution
plt.figure(figsize=(8, 5))
plt.bar(summary.index, summary['percentage (%)'],
        color=['#90EE90', '#FFD700', '#FF6347'], edgecolor='black')
plt.title("Distribution of Data Points by Deviation Range")
plt.ylabel("Percentage (%)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# Visualize histogram with mean ± std lines
plt.figure(figsize=(8, 5))
plt.hist(data['latency'], bins=15, color='lightblue', edgecolor='black', alpha=0.7)
plt.axvline(mean_y, color='red', linestyle='--', label='Mean')
plt.axvline(mean_y + std_y, color='green', linestyle=':', label='+1σ')
plt.axvline(mean_y - std_y, color='green', linestyle=':', label='-1σ')
plt.axvline(mean_y + 2*std_y, color='orange', linestyle=':', label='+2σ')
plt.axvline(mean_y - 2*std_y, color='orange', linestyle=':', label='-2σ')
plt.title("Histogram of y-values with ±1σ and ±2σ Ranges")
plt.xlabel("y")
plt.ylabel("Frequency")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()