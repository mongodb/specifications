# Attempt to maximize staleness calculation "error" per SPEC description 

import numpy as np
import scipy.optimize as spo
ir = lambda n: int(round(n))

# Constants
s_freq = 500   #primary idle write frequency
c_freq = 10000 #client-server heartbeat frequency ms

# Simulation boundaries
threshold = 300000 # 5 minute max lag/skew
argmin = [0,-threshold,0,0,0,0,0]
argmax = [threshold,threshold,c_freq,c_freq,1000,1000,s_freq]
arglabels = ["True Lag", "Clock skew (Client to Prim)", "Last Primary ping (ms ago)", "Last Secondary ping (ms ago)", "Client Primary latency", "Client Secondary latency", "Last server write (ms ago)"]

res = 1 #simulation resolution in ms
time = threshold * 10 #arbitrary time on the primary (to avoid dealing with negative indexes)

def main():

    #Attempt to find global minima using an optimizer
    num_iterations = 500
    step=2000
    interval=10

    print("SPO Params: Iter: {}, step: {}, interval:{}".format(num_iterations,step,interval))

    result = spo.basinhopping(func=simulate_staleness
                              ,x0= (10,200000,5000 ,3000 ,250 ,250 ,250)
                              ,niter=num_iterations
                              ,minimizer_kwargs = dict(
                                method="L-BFGS-B"
                                ,bounds = list(zip(argmin,argmax)))
                              ,stepsize=step
                              ,interval=interval
                              ,disp= True)

    print("Server update frequency:     {}\n"
          "Client update frequency:     {}\n"\
          "Potential calculation error: {}".format(s_freq,c_freq,abs(round(result.fun))))

    print("\nArguments: ")
    for i in range(len(arglabels)):
        print("val: {} \t {}".format(round(result.x[i]),arglabels[i]))


# Simulate staleness "error" given the absolute true lag, clock skew, and last time P/S were pinged, etc
# This function is deterministic, given a set of inputs, there's only one output value. 

def simulate_staleness(inputs): #input clobbered into a tuple for optimizer to digest
    true_lag, c_clock_skew, last_P_ago, last_S_ago, cp_latency, cs_latency,p_offset = inputs

    #Array of reported lastWrite times, reverse order
    #first element represents the currently reported lastWrite
    #second element represents lastwrite as of 'res' ms ago
    p_writes = np.arange(time, time-ir(2.5*threshold),-res) #this is expensive :( but simple to simulate
    p_writes -= p_writes % s_freq  #truncate to every 500ms resolution

    # Offset since last server write happened (anywhere 0-500ms)
    p_writes = p_writes[ir(float(p_offset)/res):]

    #shift the primary writes to account for lag & latency on secondary
    s_offset = ir(float(true_lag)/res)
    s_writes = p_writes[s_offset:]

    #calculate last updated date from client's frame (ie: absolute time + skew)
    s_last_ut = time - last_S_ago + c_clock_skew
    p_last_ut = time - last_P_ago + c_clock_skew

    #client connects to S and receiving a response last_s_ago
    cs_offset = ir(float(last_S_ago+cs_latency)/res)
    s_last_w = s_writes[cs_offset]  # reported S writeTime at that time
    cp_offset = ir(float(last_P_ago+cp_latency)/res)
    p_last_w = p_writes[cp_offset]  #reported P last_write at that time

    lag = (s_last_ut - s_last_w) - (p_last_ut- p_last_w) + c_freq
    return -abs(lag-true_lag)

main()
