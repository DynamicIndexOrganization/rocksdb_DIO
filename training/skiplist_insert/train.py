import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import os

# Define the model function
# Update the model function here if needed
def model_function(x, a, c):
    return a * x + c

# function to filter out outlier data
def filter_outliers_by_x(df):
    def filter_group(group):
        mean_y = group['y'].mean()
        std_y = group['y'].std()

        # In case std = 0 (all values same), keep all points
        if std_y == 0:
            return group

        return group[np.abs(group['y'] - mean_y) <= std_y]

    return df.groupby('x', group_keys=False).apply(filter_group)

# Step 1: Check for environmental variables
data_path = os.getenv("LATENCY_SAMPLE_STORAGE_PATH")
model_path = os.getenv("LATENCY_PREDICT_MODEL_PATH")
if data_path is None:
    print("DIOERROR: LATENCY_SAMPLE_STORAGE_PATH is not defined in the environment.")
    sys.exit(1)
else:
    print("LATENCY_SAMPLE_STORAGE_PATH = " + data_path)
if model_path is None:
    print("DIOERROR: LATENCY_PREDICT_MODEL_PATH is not defined in the environment.")
    sys.exit(1)
else:
    print("LATENCY_PREDICT_MODEL_PATH = " + model_path)

data_filename = data_path + "/curOpLatencyCollect_Skiplist_Insert.csv"
model_filename = model_path + "/Skiplist_Insert.model"

# Step 2: Read data from sampled latency file
data_type = None
num = None
x = []
y = []

with open(data_filename, "r") as f:
    lines = [line.strip() for line in f if line.strip()]  # ignore blank lines

if len(lines) < 2:
    raise ValueError("File must have at least two lines (a string and a number).")

# Step 2.1 Load the type here
header = lines[0]
if header != "Skiplist_Insert":
    raise ValueError("Data is not for insert into a SkipList. Please check the source file!!!")

# Step 2.2 Load how many line of data we have now
try:
    # Try int first, then float fallback
    number = int(lines[1])
except ValueError:
    number = float(lines[1])

# Step 2.3 Load the data now
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

# Step 2.4 Double check if the file is correct with the correct number of data
if (number != len(x)):
    raise ValueError(f"We expect {number} lines of data but only get {len(x)} lines.")

# Step 2.5 filter out outliers
data = pd.DataFrame({
    'x': x,
    'y': y
})
filtered_data = filter_outliers_by_x(data)

# Step 2.6 Show data count for each unique x
count_per_x = filtered_data['x'].value_counts().sort_index()
print("\nNumber of data points for each unique x:")
for xi, count in count_per_x.items():
    print(f"x = {xi}: {count} points")

# Step 2.7 sample at most 5000 data for each unique x
sampled_data = (
    filtered_data.groupby('x', group_keys=False)
    .apply(lambda g: g.sample(n=min(len(g), 5000), random_state=42))
)
# Replace x, y with sampled data for model fitting
x = sampled_data['x']
y = sampled_data['y']

# Step 3: Now fit the model
params, cov = curve_fit(model_function, x, y, bounds=(0, [np.inf, np.inf]))
a_hat, c_hat = params
# save parameters into file
with open(model_filename, "w") as m:
    # write model type first
    m.write("N\n")
    for n in params:
        m.write(f"{n}\n")
    print(f"Model have been saved in file {model_filename}")

print(f"Fitted parameters: a={a_hat:.4f}, c={c_hat:.4f}")

# Step 4: Plot violin diagram, scatter plot, and fitted function within one figure
x = np.array(x)
y = np.array(y)
plt.figure(figsize=(10, 6))

unique_xs = sorted(filtered_data['x'].unique())

# Step 4.1 Draw violin (KDE) per unique x
for xi in unique_xs:
    ys = filtered_data.loc[filtered_data['x'] == xi, 'y']
    if len(ys) < 2:
        continue  # skip single-point groups
    
    kde = gaussian_kde(ys)
    y_min, y_max = ys.min(), ys.max()
    y_vals = np.linspace(y_min, y_max, 200)
    density = kde(y_vals)
    
    # Normalize density for consistent violin width
    scale = 0.4 / density.max()
    
    # Mirror violin left and right around xi
    plt.fill_betweenx(
        y_vals,
        xi - density * scale,
        xi + density * scale,
        color='skyblue',
        alpha=0.4,
        edgecolor='none'
    )

# Step 4.2 Plot scatter points
plt.scatter(x, y, color="black", s=10, label="Filtered data", zorder=3)

# Step 4.3 Plot fitted line
x_sorted = np.sort(np.unique(x))
plt.plot(x_sorted, model_function(x_sorted, *params), color="red", lw=2, label="Fitted model", zorder=4)

plt.title("Latency Distribution by X (Violin per Unique X)")
plt.xlabel("SkipListHeight (x)")
plt.ylabel("Latency (y)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("./plot.png", bbox_inches='tight')
plt.show()


