import simpy
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.simulator import Simulator
from utils import config

def test_formation_convergence():
    print("Setting up simulation for formation test...")
    env = simpy.Environment()
    
    # Create simulator with small number of drones for easier debugging
    config.NUMBER_OF_DRONES = 5
    config.SIM_TIME = 20 * 1e6 # 20 seconds
    
    # Mock channel states
    channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
    
    sim = Simulator(seed=2024, env=env, channel_states=channel_states, n_drones=config.NUMBER_OF_DRONES)
    
    # Run for 2 seconds then trigger formation
    env.run(until=2 * 1e6)
    print(f"Triggering formation change at {env.now/1e6}s")
    sim.trigger_formation_change()
    
    # Get initial distances to targets
    initial_distances = {}
    for drone in sim.drones:
        if drone.target_position:
            dist = np.linalg.norm(np.array(drone.coords) - np.array(drone.target_position))
            initial_distances[drone.identifier] = dist
            print(f"Drone {drone.identifier} initial distance to target: {dist:.2f}m")
            
    # Run for 10 more seconds
    print("Running simulation for 10 seconds...")
    env.run(until=12 * 1e6)
    
    # Check final distances
    print("\nChecking convergence...")
    all_moved_closer = True
    for drone in sim.drones:
        if drone.target_position:
            final_dist = np.linalg.norm(np.array(drone.coords) - np.array(drone.target_position))
            start_dist = initial_distances[drone.identifier]
            moved = start_dist - final_dist
            print(f"Drone {drone.identifier}: Start Dist={start_dist:.2f}m, Final Dist={final_dist:.2f}m, Moved={moved:.2f}m")
            
            if final_dist >= start_dist and start_dist > 1.0:
                print(f"FAILURE: Drone {drone.identifier} did not move closer to target!")
                all_moved_closer = False
            elif final_dist < 1.0:
                print(f"SUCCESS: Drone {drone.identifier} reached target!")
            else:
                print(f"PROGRESS: Drone {drone.identifier} is moving closer.")
                
    if all_moved_closer:
        print("\nTEST PASSED: All drones are moving towards or have reached their targets.")
    else:
        print("\nTEST FAILED: Some drones are not moving towards targets.")

if __name__ == "__main__":
    test_formation_convergence()
