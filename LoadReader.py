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

file = open("datacontainer.txt","a") #Open file for data
counter = 0 #initialize counter
x = []
y = []

#Get time
now = datetime.now()
dtstring = now.strftime("%D/%M/%Y %H:%M:%S")
file.write(dtstring + "\n") #Mark start time to file
print(dtstring)

start = time.perf_counter()

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

def ready():
    # if DOUT pin is low data is ready for reading
    if GPIO.input(data) == 0:
        return True
    else:
        return False

try:
    while True:
        counter = counter + 1 #so that we know how many measurements have been taken
        value = read() #hopefully this should take one value from the sensor
        #value = random.randint(100)
        measure_time = time.perf_counter()
    
        print(counter, value, measure_time-start)
        x.append(measure_time-start)
        y.append(value)
except (KeyboardInterrupt, SystemExit):
    print("bye ;)")
file.close()
for i in x:
    x[int(i)] = x[int(i)]-29800
    x[int(i)] = x[int(i)]/10000
    file.write(str(int(i)) +  " " + str(x[int(i)]) + " " + str(y[int(i)]) + "\n") #write counter, value, and time after start
plt.scatter(x,y)
plt.show()

