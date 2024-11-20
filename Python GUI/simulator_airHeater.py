#  -*- coding: utf-8 -*-
"""

Author: Finn Haugen, USN
finn.haugen@usn.no

Modified by Benjamin Castin

Simulator of air heater

https://techteach.no/lab/air_heater/

Process model:
    
    T' = (Kh*u(t-tau) + (T_env - T))/theta
    
where:
    
    - T [C] is pipe outlet air temperature
    - T_env [C] is environmental (room) temp
    - u [V] is control signal to the heater

Updated 2024 09 16.

"""

# %% Imports

import matplotlib.pyplot as plt
import numpy as np
import configparser
from Libraries.MQTT_config import MQTT_config
import time
import json

#Library created by Benjamin Castin
from Libraries.Controllers import controllers

# %% MQTT configuration
mqtt_client = MQTT_config(type=1) # Type 1 means it is a publisher and subscriber

# %% Def of process model simulator

def process_sim(T_k,
                u_k,
                delay_array_k,
                process_params,
                ts):

    # Reading process params:
    (Kh, theta, t_delay, T_min, T_max) = process_params
    
    # Limiting the state:
    T_k = np.clip(T_k, T_min, T_max)

    # Time delay:
    u_delayed_k = delay_array_k[-1]
    delay_array_k[1:] = delay_array_k[0:-1]
    delay_array_k[0] = u_k
    delay_array_kp1 = delay_array_k

    # Euler-forward integration of process state variable:
    dT_dt_k = (Kh*u_delayed_k + (T_env_k - T_k))/theta
    T_kp1 = T_k + ts*dT_dt_k

    return (T_kp1, delay_array_kp1)

# %% Time settings

ts = 0.1  # Time-step [s]
t_start = 0.0  # [s]
t_stop = 150.0  # [s]
N_sim = int((t_stop - t_start)/ts) + 1

# %% Process params

Kh = 3.5  # [deg C/V]
theta = 23.0  # [s]
t_delay = 3.0  # [s]

T_min = -273.16  # [deg C]
T_max = np.inf  # [deg C]

process_params = (Kh, theta, t_delay, T_min, T_max)

# %% Initialization of time delay

u_delayed_init = 0.0  # [V]
N_delay = int(round(t_delay/ts)) + 1
delay_array_k = np.zeros(N_delay) + u_delayed_init

# %% Defining arrays for plotting

t_array = np.zeros(N_sim)
T_array = np.zeros(N_sim)
T_env_array = np.zeros(N_sim)
u_array = np.zeros(N_sim)

# %% Initial state

T_k = 20.0  # [deg C]
T_env_k = 20.0  # [deg C]

# %% Controller
target = 30
controller = controllers(r=target, ts=0.1)

# %% Simulation for-loop

for k in range(0, N_sim):

    t_k = k*ts

    # Manipulating process input variables:
    if t_k <= 70:
        controller.r = 30
    #    u_k = 0  # [V]
        T_env_k = 20.0  # [deg C]
    else:
        controller.r = 30
    #    u_k = 0
        T_env_k = 20.0

    #u_k = controller.on_off_controller(input=T_k)
    
    # Value of Kc and Ti with the ziegler nichols method
    # u_k = controller.PI_controller(input=T_k, Kc=1.98, Ti=10, ts=ts)

    # Value of Kc and Ti with the relaxed ziegler nichols method
    u_k = controller.PI_controller(input=T_k, Kc=0.85, Ti=15)
    
    # ziegler nichols experimentation
    #u_k = controller.PI_controller(input=T_k, Kc=3.4, Ti=10000000000, ts=ts)

    # Process simulator:
    (T_kp1, delay_array_kp1) = process_sim(
        T_k,
        u_k,
        delay_array_k,
        process_params,
        ts)
    
    # Storage for plotting:
    t_array[k] = t_k
    u_array[k] = u_k
    T_array[k] = T_k
    T_env_array[k] = T_env_k
    
    # Time index shift:
    T_k = T_kp1
    delay_array_k = delay_array_kp1
    
    # MQTT Publish
    
    mqtt_client.send_data(T_k, u_k, t_k, target)
    
    # time delay
    time.sleep(ts)
    
# %% Plotting

plt.close('all')
plt.figure(1, figsize=(8, 6))

plt.subplot(2, 1, 1)
plt.plot(t_array, T_array, 'r', label='T')
plt.plot(t_array, T_env_array, 'g', label='T_env')
plt.legend()
plt.grid()
#plt.ylim(20, 25)
plt.xlim(t_start, t_stop)
plt.xlabel('t [s]')
plt.ylabel('[deg C]')

plt.subplot(2, 1, 2)
plt.plot(t_array, u_array, 'b', label='u')
plt.legend()
plt.grid()
#plt.ylim(-1, 6)
plt.xlim(t_start, t_stop)
plt.xlabel('t [s]')
plt.ylabel('[V]')

# plt.savefig('plot_sim_air_heater.pdf')
plt.show()