import simpy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from simulator.simulator import Simulator
from utils import config
from mobility import start_coords
import logging

# Disable logging for experiments to speed up
logging.getLogger().setLevel(logging.ERROR)

def run_simulation(duration):
    env = simpy.Environment()
    channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
    simulator = Simulator(seed=2024, env=env, channel_states=channel_states, n_drones=config.NUMBER_OF_DRONES, total_simulation_time=duration)
    env.run(until=duration)
    return simulator

def run_experiment_1_mobility_vs_latency():
    print("Running Experiment 1: Mobility vs Latency")
    speeds = [0, 10, 20, 30, 40, 50]
    results = []
    
    for speed in speeds:
        print(f"  Testing Speed: {speed} m/s")
        config.DEFAULT_SPEED = speed
        config.SIM_TIME = 50 * 1e6 # 50 seconds
        
        simulator = run_simulation(config.SIM_TIME)
        
        # Calculate Latency
        if simulator.metrics.deliver_time_dict:
            avg_latency = np.mean(list(simulator.metrics.deliver_time_dict.values())) / 1e3 # ms
        else:
            avg_latency = 0
            
        results.append({'Speed': speed, 'Latency': avg_latency})
        print(f"    Latency: {avg_latency:.2f} ms")
        
    df = pd.DataFrame(results)
    df.to_csv('experiment_1_mobility_vs_latency.csv', index=False)
    print("Experiment 1 Complete. Saved to experiment_1_mobility_vs_latency.csv")

def run_experiment_2_energy_throughput():
    print("Running Experiment 2: Energy-Throughput Tradeoff")
    rates = [1, 5, 10, 20, 50] # packets/s
    results = []
    
    for rate in rates:
        print(f"  Testing Rate: {rate} pkts/s")
        config.PACKET_GENERATION_RATE = rate
        config.DEFAULT_SPEED = 10 # Fixed speed
        config.SIM_TIME = 50 * 1e6 # 50 seconds
        
        simulator = run_simulation(config.SIM_TIME)
        
        # Calculate PDR
        if simulator.metrics.datapacket_generated_num > 0:
            pdr = len(simulator.metrics.datapacket_arrived) / simulator.metrics.datapacket_generated_num * 100
        else:
            pdr = 0
            
        # Calculate Avg Energy Consumption
        # Initial - Current
        consumed_energy = []
        for drone in simulator.drones:
            consumed = config.INITIAL_ENERGY - drone.residual_energy
            consumed_energy.append(consumed)
        avg_energy = np.mean(consumed_energy)
        
        throughput = len(simulator.metrics.datapacket_arrived) * config.AVERAGE_PAYLOAD_LENGTH / (config.SIM_TIME / 1e6) # bits/s
        
        results.append({'Rate': rate, 'PDR': pdr, 'Energy': avg_energy, 'Throughput': throughput})
        print(f"    PDR: {pdr:.2f}%, Energy: {avg_energy:.2f} J, Throughput: {throughput:.2f} bps")
        
    df = pd.DataFrame(results)
    df.to_csv('experiment_2_energy_throughput.csv', index=False)
    print("Experiment 2 Complete. Saved to experiment_2_energy_throughput.csv")

def run_experiment_3_formation_transition():
    print("Running Experiment 3: Formation Transition")
    config.DEFAULT_SPEED = 10
    config.PACKET_GENERATION_RATE = 5
    config.SIM_TIME = 600 * 1e6 # 600 seconds
    
    # We need to collect metrics over time.
    # Simulator doesn't store time-series metrics by default except what we added in GUI.
    # But we are running headless.
    # We can modify Simulator to record metrics periodically or just parse the event logs?
    # Or we can run the simulation in steps here.
    
    env = simpy.Environment()
    channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
    simulator = Simulator(seed=2024, env=env, channel_states=channel_states, n_drones=config.NUMBER_OF_DRONES, total_simulation_time=config.SIM_TIME)
    
    # Custom data collection loop
    results = []
    step_size = 1 * 1e6 # 1 second
    
    # Start the formation manager process (it's already in Simulator.__init__)
    
    while env.now < config.SIM_TIME:
        env.run(until=env.now + step_size)
        
        # Collect metrics
        time_s = env.now / 1e6
        
        # PDR (Cumulative)
        if simulator.metrics.datapacket_generated_num > 0:
            pdr = len(simulator.metrics.datapacket_arrived) / simulator.metrics.datapacket_generated_num * 100
        else:
            pdr = 0
            
        # Control Overhead (Cumulative)
        overhead = simulator.metrics.control_packet_num
        
        results.append({'Time': time_s, 'PDR': pdr, 'Overhead': overhead})
        
        if int(time_s) % 50 == 0:
            print(f"  Time: {time_s} s, PDR: {pdr:.2f}%")
            
    df = pd.DataFrame(results)
    df.to_csv('experiment_3_formation_transition.csv', index=False)
    print("Experiment 3 Complete. Saved to experiment_3_formation_transition.csv")

if __name__ == "__main__":
    run_experiment_1_mobility_vs_latency()
    run_experiment_2_energy_throughput()
    run_experiment_3_formation_transition()
