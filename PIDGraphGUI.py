import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
import time
import serial


# Initialize data lists
times = []
actual_distances = []
aimed_distances = []
start_time = time.time()
count = 0

# font formatting
main_font_size = 18
font = { 'size'   : main_font_size }
plt.rc('font', **font)

# Set up the figure and axis
fig = plt.figure(figsize=(6,6))
# [left, bottom, width, height]
ax = fig.add_axes([0.1, 0.1, 0.65, 0.8]) # bound to left side
plt.tight_layout()
line1, = ax.plot([], [], 'r-', label='Actual Distance')
line3, = ax.plot([], [], 'c--', label='Current Distance Aimed')
kp_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=main_font_size)
ki_text = ax.text(0.02, 0.90, '', transform=ax.transAxes, fontsize=main_font_size)
kd_text = ax.text(0.02, 0.85, '', transform=ax.transAxes, fontsize=main_font_size)

# Set the plot limits
ax.set_xlim(0, 10)
ax.set_ylim(0, 500)
ax.set_xlabel('Time (s)', fontsize=main_font_size)
ax.set_ylabel('Distance', fontsize=main_font_size)
ax.legend()

# add buttons
ButtonHeightHigh = fig.add_axes([0.77, 0.05, 0.2, 0.25])
ButtonHeightMedium = fig.add_axes([0.77, 0.35, 0.2, 0.25])
ButtonHeightLow = fig.add_axes([0.77, 0.65, 0.2, 0.25])

BHClick = Button(ButtonHeightHigh, '400')
BMClick = Button(ButtonHeightMedium, '250')
BLClick = Button(ButtonHeightLow, '125')

def init():
    """Initialize the background of the animation."""
    line1.set_data([], [])
    #line2.set_data([], [])
    line3.set_data([], [])
    kp_text.set_text('')
    ki_text.set_text('')
    kd_text.set_text('')
    return line1, line3, kp_text, ki_text, kd_text


def serialSetup():
    # baud rate for serial data
    baudRate = 9600


    # test and find serial port that will be used
    portName = '/dev/ttyACM0'
    serialUsed = serial.Serial(portName, baudRate, timeout=1)
    

    return serialUsed


# used later for serial setup
initialSetup = False
current_aimed_distances = []
previous_aimed_distances = []
previous_aimed_distance = 100

# previous_aimed_distance = 0
# Global variables to track state changes
previous_aimed_distances = [0]
change_detected_time = None

def update(frame):
    current_time = time.time() - start_time
    arduino = serialSetup()
    
    try:
        # Simulate or get actual data from serial
        serialData = arduino.readline().decode('utf-8')
        # print(arduino.readline().decode('utf-8').rstrip())
        kp, ki, kd, actual_distance, current_aimed_distance = map(float, serialData.split('|'))
        
        global previous_aimed_distances
        global count
        
        count += 1
        
        if count >= 80:
            actual_distances.pop(0)
            current_aimed_distances.pop(0)
            times.pop(0)
            
            actual_distances.append(actual_distance)
            current_aimed_distances.append(current_aimed_distance)
            times.append(current_time)

        
        else:
            actual_distances.append(actual_distance)
            current_aimed_distances.append(current_aimed_distance)
            times.append(current_time)

        
        line1.set_data(times, actual_distances)
        #line2.set_data(times, previous_aimed_distances)
        line3.set_data(times, current_aimed_distances)
        
        kp_text.set_text(f'kp: {kp:.2f}')
        ki_text.set_text(f'ki: {ki:.2f}')
        kd_text.set_text(f'kd: {kd:.2f}')
        
        ax.set_xlim(max(1.0, current_time - 10), current_time + 0.01)
        ax.figure.canvas.draw()
        
        previous_aimed_distance = current_aimed_distance
        previous_aimed_distances = current_aimed_distances
        
        
        
        # right at the end here, send the current set position
        BHClick.on_clicked(setpoint=400)
        BMClick.on_clicked(setpoint=250)
        BLClick.on_clicked(setpoint=125)
        
        arduino.write(setpoint)
    
    except Exception as e:
        print(f"Error: {e}")
    
    return line1, line3, kp_text, ki_text, kd_text




# Create the animation
graphAnimation = FuncAnimation(fig, update, init_func=init, blit=True, interval=50)


# Make the plot fullscreen
figManager = plt.get_current_fig_manager()
figManager.full_screen_toggle()

# Display the plot
plt.show()
