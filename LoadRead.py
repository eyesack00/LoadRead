#This program is for gathering lots of data from the 500 lb load cell and HX711 load cell amp
#All of the prebuilt programs I could find only found a value every several seconds
#Hopefully this will be better.


import statistics as stat
import RPi.GPIO as GPIO
import time
from numpy import random
from datetime import datetime
import matplotlib.pyplot as plt

GPIO.setmode(GPIO.BCM) # Set GPIO numbering notation to BCM
clock = 21
data = 20

GPIO.setup(clock, GPIO.OUT) 
GPIO.setup(data, GPIO.IN)

counter = 0 #initialize counter
x = []
y = []

#Get time
now = datetime.now()
dtstring = now.strftime("%D/%M/%Y %H:%M:%S")

file = open("datacontainer.txt","a") #Open file for data
file.write(dtstring + "\n") #Mark start time to file
print(dtstring)

def ready():
    # if DOUT pin is low data is ready for reading
    if GPIO.input(data) == 0:
        return True
    else:
        return False
    
def read():
    GPIO.output(clock, False)  # start by setting the pd_sck to 0
    ready_counter = 0
    while (not ready() and ready_counter <= 40):
        time.sleep(0.01)  # sleep for 10 ms because data is not ready
        ready_counter += 1
        if ready_counter == 50:  # if counter reached max value then return False
            print('self._read() not ready after 40 trials\n')
            return False
    # read first 24 bits of data
    data_in = 0  # 2's complement data from hx 711
    for _ in range(24):
        start_counter = time.perf_counter()
        # request next bit from hx 711
        GPIO.output(clock, True)
        GPIO.output(clock, False)
        end_counter = time.perf_counter()
        if end_counter - start_counter >= 0.00006:  # check if the hx 711 did not turn off...
            # if clock pin is HIGH for 60 us and more than the HX 711 enters power down mode.
                
            print('Not enough fast while reading data')
            print('Time elapsed: {}'.format(end_counter - start_counter))
            return False
            # Shift the bits as they come to data_in variable.
            # Left shift by one bit then bitwise OR with the new bit.
        data_in = (data_in << 1) | GPIO.input(data)
        
    #Set gain to 128
    GPIO.output(clock, True)
    GPIO.output(clock, False)

    #check if data is valid
    if (data_in == 0x7fffff
        or  # 0x7fffff is the highest possible value from hx711
            data_in == 0x800000
        ):  # 0x800000 is the lowest possible value from hx711
       
        print('Invalid data detected: {}\n'.format(data_in))
        return False

    # calculate int from 2's complement
    signed_data = 0
    # 0b1000 0000 0000 0000 0000 0000 check if the sign bit is 1. Negative number.
    if (data_in & 0x800000):
        signed_data = -(
            (data_in ^ 0xffffff) + 1)  # convert from 2's complement to int
    else:  # else do not do anything the value is positive number
        signed_data = data_in
    return signed_data
    
def tare():
    #Wait for key press, take some measurements, and use the median to tare the pi. We're using the median because
    #there tend to be some random huge measurements mixed in with the bunch.
    input("Press enter when you're ready to tare...")
    unstable = True #used for while loop
    while unstable:
        #take 30 values, remove the top and bottom five, take the standard deviation and median, show them to the user, and ask if they want another 30
        #return the median for use in calibration
        torn_values = []
        for j in range(1,30):
            torn_values.append(read())
        for j in range(1,5):
            torn_values.remove(max(torn_values))
            torn_values.remove(min(torn_values))
        torn_median = stat.median(torn_values)
        torn_std = stat.stdev(torn_values)
        print("Median: " + str(torn_median))
        print("Standard Deviation: " + str(torn_std))
        good = input("Acceptable? y for yes, anything else for no... ")
        if good == "y":
            unstable = False
    return torn_median

def calibrate(torn_value):
    unstable = True
    while unstable:
        multiplier = []
        known_force = input("Place a known force against the load cell in compression.\nEnter that value here, in the units you would like the measurements to be... ")
        for j in range(1,30):
            multiplier.append((float(read())-torn_value)/float(known_force))
        for j in range(1,5):
            multiplier.remove(max(multiplier))
            multiplier.remove(min(multiplier))

        multi_median = stat.median(multiplier)
        multi_std = stat.stdev(multiplier)
        print("Median: " + str(multi_median))
        print("Standard Deviation: " + str(multi_std))
        good = input("Acceptable? y for yes, anything else for no... ")
        if good == "y":
            unstable = False
    return multi_median

try:
    offset = tare()
    multiplier = calibrate(offset)
    start = time.perf_counter()
    while True:
        counter = counter + 1 #so that we know how many measurements have been taken
        value = (read()-offset)/multiplier #hopefully this should take one value from the sensor
        #value = random.randint(100)
        measure_time = time.perf_counter()
    
        print(counter, value, measure_time-start)
        file.write(str(counter) +  " " + str(value) + " " + str(measure_time-start) + "\n") #write counter, value, and time after start
        x.append(measure_time-start)
        y.append(value)
except (KeyboardInterrupt, SystemExit):
    print("bye ;)")


file.close()
plt.scatter(x,y)
plt.show()
