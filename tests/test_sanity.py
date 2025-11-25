import simpy
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.simulator import Simulator
from utils import config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def run_sanity_check():
    print("Running Sanity Check...")
    config.SIM_TIME = 0.5 * 1e6 # 0.5 seconds
    
    env = simpy.Environment()
    channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
    simulator = Simulator(seed=2024, env=env, channel_states=channel_states, n_drones=config.NUMBER_OF_DRONES, total_simulation_time=config.SIM_TIME)
    
    try:
        env.run(until=config.SIM_TIME)
        print("Sanity Check Passed: Simulation ran for 0.5s without crash.")
    except Exception as e:
        print(f"Sanity Check Failed: {e}")
        raise

if __name__ == "__main__":
    run_sanity_check()
