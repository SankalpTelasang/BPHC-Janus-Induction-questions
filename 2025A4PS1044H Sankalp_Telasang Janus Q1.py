import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd


# Setup variables that can be changed according to your data set
y_label = 'Height (m)'
x_label = 'Time (s)'
file_path = r"C:\Users\dell\Downloads\T1.csv" # The file path of the data, in csv format
interval_per_datapoint = 1 # How much the x axis unit changes per row of the csv
acceptable_deviation_factor = 1.8 # The smaller this is, the more sensitive the erroneous point detection will be
smoothing_strength = 0.3 # Higher value leads to more smoothing. Keep between 0.0 and 0.5
graph_margin = 0.05 #The extra margin on the y axis as a percent that will be drawn on the graph

fps = 20
speedup = 1 # The units (specified in the x_label) of the data that will be plotted per real life second

# Extracting the data from the csv. Only the first column will be read, 
# and it is assumed that every increment down the table is done at the 
# interval specified above (interval_per_datapoint)
df = pd.read_csv(file_path)
first_column = df.iloc[:, 0]
data_list = list(first_column)

###################################
# This section converts the list to floats, so
# that pyplot is able to plot it accurately. 
# On top of that, it detects for corrupted values,
# which are assumed to be outputed as 5 asterisks 
# from the sensor (*****)
while data_list[0] == '*****':
    data_list.pop(0)
while data_list[-1] == '*****':
    data_list.pop()
data_int_list = []
for data_val in data_list:
    if data_val == '*****':
        data_int_list.append(None)
    else:
        data_int_list.append(float(data_val))
###################################

###################################
# This section takes all the corrupted values and replaces them with 
# a suitable approximation, which is taken to be on the line between 
# the nearest uncorrupted values.
total_vals = len(data_int_list)
for i in range(total_vals):
    val = data_int_list[i]
    if val == None:
        next_i = i + 1
        prev_val = data_int_list[i - 1]
        next_val = data_int_list[next_i]
        while next_val == None:
            next_i += 1
            next_val = data_int_list[next_i]
        total_corrupted = next_i - i
        slope = (next_val - prev_val) / (total_corrupted + 1)
        inferred_val = prev_val + slope
        for j in range(total_corrupted):
            replaced_i = i + j
            data_int_list[replaced_i] = inferred_val
            inferred_val += slope

data_int_list_copy = list(data_int_list)
###################################

###################################
# Now this is the part of the code that really starts the error correction.
# The aim of this section is to detect and remove erroneous points.
# Here, we generate a smoothed graph using a LOESS method (LOcally Estimated 
# Scatterplot Smoothing) that I have manually implemented. Essentially I 
# take the 2 points closest to the current one, weight them according to their 
# distance, and then use the average value. After generating this smoothed 
# graph, I calculate the deviation of the raw data with the smoothed graph.
# Finally, I calculate a highest acceptable deviation with the range of the data,
# and then from there, and for the points with a deviation higher than this number
# I replace that point with a suitable approximation (the average of the 2 nearest 
# points). After every data point that I replace, I restart the loop from the beginning, 
# and then begin the smoothing and detection process again. Eventually, all the data
# points will have an acceptable deviation, and at this point we will break out
# of the while loop.
deviation_present = True
tent_range = max(data_int_list) - min(data_int_list)
acceptable_deviation = (tent_range / total_vals) * acceptable_deviation_factor
while deviation_present:
    deviation_present = False
    start_cushion = data_int_list[0]
    data_int_list.insert(0, start_cushion)
    data_int_list.insert(0, start_cushion)
    end_cushion = data_int_list[-1]
    data_int_list.insert(-1, end_cushion)
    data_int_list.insert(-1, end_cushion)
    
    deviation_list = []
    for i in range(2, total_vals + 2):
        original_val = data_int_list[i]
        val = original_val * (1 - (2 * smoothing_strength))
        val += data_int_list[i + 1] * smoothing_strength
        val += data_int_list[i - 1] * smoothing_strength
        deviation = abs(val - original_val)
        deviation_list.append((deviation, i - 2))

    data_int_list.pop()
    data_int_list.pop(0)

    deviation_list.sort(reverse = True)

    deviation, index = max(deviation_list)
    if deviation > acceptable_deviation:
        index += 1
        data_int_list[index] = (data_int_list[index + 1] + data_int_list[index - 1]) / 2
        deviation_present = True
        data_int_list.pop()
        data_int_list.pop(0)
###################################

###################################
# This section just uses the LOESS method described in the
# previous section to generate the final smoothed graph,
# finishing off the error correction.
data_int_list.pop()
data_int_list.pop(0)

start_cushion = data_int_list[0]
data_int_list.insert(0, start_cushion)
data_int_list.insert(0, start_cushion)
end_cushion = data_int_list[-1]
data_int_list.insert(-1, end_cushion)
data_int_list.insert(-1, end_cushion)

data_smoothed_list = []
for i in range(2, total_vals + 2):
    original_val = data_int_list[i]
    val = original_val * (1 - (2 * smoothing_strength))
    val += data_int_list[i + 1] * smoothing_strength
    val += data_int_list[i - 1] * smoothing_strength
    data_smoothed_list.append(val)
###################################



#######################################
# DATA PROCESSING SECTION
#
# So far, everything has been done generally, meaning it can be applied to
# any data set that we have in the file. This section is specific to this
# problem, and it is intended that this section will be replaced with other 
# processing methods for other data sets. For this data set, I simply convert
# the pressure data into height data using a simple P = pgh approximation.
#
# The smoothed list is data_smoothed_list
# The raw list is data_int_list
height_list = []
air_density = 1.2 #kg/m^3
gravity = 9.807 #m/s^2
ground_pressure = data_smoothed_list[0]
for val in data_smoothed_list:
    pressure_diff = ground_pressure - val
    height = pressure_diff / (gravity * air_density)
    height_list.append(height)

raw_height_list = []
for val in data_int_list_copy:
    pressure_diff = ground_pressure - val
    height = pressure_diff / (gravity * air_density)
    raw_height_list.append(height)

list_of_interest = height_list # It is needed to specifiy that this is "list of interest" for the plotting section
list_of_interest_unsmoothed = raw_height_list
#######################################



###################################
# And finally, plotting the graph. I use some interpolation to ensure that 
# the graph is plotted at the specified fps value, even if the values
# don't nicely line up.
min_val, max_val = min(list_of_interest), max(list_of_interest)
graph_absolute_margin = (max_val - min_val) * graph_margin

total_x = total_vals * interval_per_datapoint

fig, ax = plt.subplots()
ax.set_xlim(0, total_x)
ax.set_ylim(min_val - graph_absolute_margin, max_val + graph_absolute_margin)
ax.set_xlabel(x_label)
ax.set_ylabel(y_label)

line_smooth, = ax.plot([], [], label = 'Smoothed')
line_unsmooth, = ax.plot([], [], ls =':', label = 'Unsmoothed')
ax.legend(loc = 'upper left')

def init():
    line_smooth.set_data([], [])
    line_unsmooth.set_data([], [])
    return line_smooth, line_unsmooth

num_interp_points = int(total_x * fps) // speedup
x_interp = np.linspace(0, total_x, num_interp_points)
x_values = np.linspace(0, total_x, total_vals)

list_of_interest_interp = np.interp(x_interp, x_values, list_of_interest)
list_of_interest_unsmoothed_interp = np.interp(x_interp, x_values, list_of_interest_unsmoothed)

def update(frame):
    x = x_interp[:frame]
    y_smooth = list_of_interest_interp[:frame]
    y_unsmooth = list_of_interest_unsmoothed_interp[:frame]

    line_smooth.set_data(x, y_smooth)
    line_unsmooth.set_data(x, y_unsmooth)
    return line_smooth, line_unsmooth

ani = animation.FuncAnimation(fig, update, frames = int(total_x * fps), init_func = init, interval = 1000 / fps, blit = True)
plt.show()
###################################


