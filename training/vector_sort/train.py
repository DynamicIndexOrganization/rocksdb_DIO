import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os

# Define the model function
# Update the model function here if needed
def model_function(x, a, b, c):
    return a * x * np.log(x) + b * x + c

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

data_filename = data_path + "/curOpLatencyCollect_Vector_Sort.csv"
model_filename = model_path + "/Vector_Sort.model"

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
if header != "Vector_Sort":
    raise ValueError("Data is not for sorting vector. Please check the source file!!!")

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

if (number != len(x)):
    raise ValueError(f"We expect {number} lines of data but only get {len(x)} lines.")

# Step 3: Now fit the model
params, cov = curve_fit(model_function, x, y, bounds=(0, [np.inf, np.inf, np.inf]))
a_hat, b_hat, c_hat = params
# save parameters into file
with open(model_filename, "w") as m:
    # write model type first
    m.write("NLogN\n")
    for n in params:
        m.write(f"{n}\n")
    print(f"Model have been saved in file {model_filename}")

print(f"Fitted parameters: a={a_hat:.4f}, b={b_hat:.4f}, c={c_hat:.4f}")

# Step 4: Plot the fit vs. data
x = np.array(x)
y = np.array(y)
plt.scatter(x, y, label="Data")
plt.plot(x, model_function(x, *params), color="red", label="Fitted model")
plt.legend()
plt.xlabel("x")
plt.ylabel("y")
# plt.savefig("./plot.png", bbox_inches='tight')
plt.show()
