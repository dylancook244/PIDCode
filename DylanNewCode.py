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
main_font_size = 40
font = { 'size'   : main_font_size }
plt.rc('font', **font)

# Set up the figure and axis
fig = plt.figure(figsize=(6,6))
# [left, bottom, width, height]
ax = fig.add_axes([0.125, 0.12, 0.82, 0.77]) # bound to left side
plt.tight_layout()
line1, = ax.plot([], [], 'r-', label='Ball Height', linewidth=8)
line3, = ax.plot([], [], 'c--', label='Setpoint', linewidth=8)
kp_text = ax.text(0.02, 0.93, '', transform=ax.transAxes, fontsize=main_font_size)
ki_text = ax.text(0.02, 0.855, '', transform=ax.transAxes, fontsize=main_font_size)
kd_text = ax.text(0.02, 0.78, '', transform=ax.transAxes, fontsize=main_font_size)

# Set the plot limits
ax.set_xlim(0, 10)
ax.set_ylim(0, 500)
ax.set_xlabel('Time (s)', fontsize=main_font_size)
ax.set_ylabel('Height', fontsize=main_font_size)
ax.legend(loc='upper right')

# add buttons
#ButtonHeightHigh = fig.add_axes([0.77, 0.65, 0.2, 0.25])
#ButtonHeightMedium = fig.add_axes([0.77, 0.35, 0.2, 0.25])
#ButtonHeightLow = fig.add_axes([0.77, 0.05, 0.2, 0.25])

#BHClick = Button(ButtonHeightHigh, '400')
#BMClick = Button(ButtonHeightMedium, '250')
#BLClick = Button(ButtonHeightLow, '125')

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
    baudRate = 115200


    # test and find serial port that will be used
    portName = '/dev/ttyACM0'
    serialUsed = serial.Serial(portName, baudRate, timeout=1)
    

    return serialUsed


# used later for serial setup
initialSetup = False
current_setpoints = []
previous_setpoints = []
current_setpoint = 250

# previous_aimed_distance = 0
# Global variables to track state changes
previous_setpoints = [0]
change_detected_time = None

def update(frame):
    current_time = time.time() - start_time
    arduino = serialSetup()
    
    try:
        # Simulate or get actual data from serial
        serialDataString = arduino.readline().decode('utf-8')
        
        #if not serialDataString:
        #    serialDataString = "0.0|0.0|0.0|0"
        
        # print(arduino.readline().decode('utf-8').rstrip())
        kp, ki, kd, actual_distance, unused_setpoint = map(float, serialDataString.split('|'))
        
        global previous_setpoints
        global count
        global current_setpoint
        
        count += 1
        
        if count >= 100:
            actual_distances.pop(0)
            current_setpoints.pop(0)
            times.pop(0)
            
            actual_distances.append(actual_distance)
            current_setpoints.append(current_setpoint)
            times.append(current_time)

        
        else:
            actual_distances.append(actual_distance)
            current_setpoints.append(current_setpoint)
            times.append(current_time)

        
        line1.set_data(times, actual_distances)
        #line2.set_data(times, previous_aimed_distances)
        line3.set_data(times, current_setpoints)
        
        kp_text.set_text(f'kp: {kp:.2f}')
        ki_text.set_text(f'ki: {ki:.2f}')
        kd_text.set_text(f'kd: {kd:.2f}')
        
        ax.set_xlim(max(1.0, current_time - 10), current_time + 0.1)
        ax.figure.canvas.draw()
        
        previous_setpoint = current_setpoint
        previous_setpoints = current_setpoints
        
        # right at the end here, send the current set position
        #BHClick.on_clicked(BHClicked)
        #BMClick.on_clicked(BMClicked)
        #BLClick.on_clicked(BLClicked)
        
        #current_setpoint_string = f"{current_setpoint}\n"
        #arduino.write(current_setpoint_string.encode())
    
    except Exception as e:
        print(f"Error: {e}")
    
    return line1, line3, kp_text, ki_text, kd_text

# so this code was for 3 setpoints, meaning a two way data transfer between
# arduino and pi. I didn't get it working, maybe the next person can.
# Since the monitor is a touch screen you can click buttons, then those buttons
# would send the setpoint back to the arduino. Whatever I did didn't work
# so i commented out the part that used this, and took the 250 setpoint
def BHClicked(event):
    global current_setpoint
    current_setpoint = 400

def BMClicked(event):
    global current_setpoint
    current_setpoint = 250

def BLClicked(event):
    global current_setpoint
    current_setpoint = 125

# Create the animation
graphAnimation = FuncAnimation(fig, update, init_func=init, blit=True, interval=50)


# Make the plot fullscreen
figManager = plt.get_current_fig_manager()
figManager.full_screen_toggle()

# Display the plot
plt.show()
