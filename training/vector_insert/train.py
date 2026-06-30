import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os


# define the model (constant)
# Update the model function here if needed
def model_function(x, c):
    return c

def filter_outliers(df):
    mean_y = df['y'].mean()
    std_y = df['y'].std()

    return df[np.abs(df['y'] - mean_y) <= std_y]

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

data_filename = data_path + "/curOpLatencyCollect_Vector_Insert.csv"
model_filename = model_path + "/Vector_Insert.model"

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
if header != "Vector_Insert":
    raise ValueError("Data is not for insert into vector. Please check the source file!!!")

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
filtered_data = filter_outliers(data)
x = filtered_data['x']
y = filtered_data['y']

# Step 3: Now fit the model
# For constant model, we just use the mean of all data points as the model
c_hat = filtered_data['y'].mean()

# save parameters into file
with open(model_filename, "w") as m:
    # write model type first
    m.write("Constant\n")
    m.write(f"{c_hat}\n")
    print(f"Model have been saved in file {model_filename}")

print(f"Fitted parameters: c={c_hat:.4f}")
