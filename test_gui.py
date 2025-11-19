import simpy
import matplotlib.pyplot as plt
from utils import config
from simulator.simulator import Simulator
from visualization.live_visualizer import LiveVisualizer

def test_live_visualizer():
    print("Testing LiveVisualizer initialization...")
    try:
        # Setup mock environment
        env = simpy.Environment()
        channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
        sim = Simulator(seed=2025, env=env, channel_states=channel_states, n_drones=config.NUMBER_OF_DRONES)
        
        # Instantiate Visualizer
        # Turn off interactive mode for test to avoid window popping up if possible, 
        # but LiveVisualizer calls plt.ion() and plt.show() in __init__.
        # We just want to see if it crashes.
        viz = LiveVisualizer(sim, env, channel_states)
        
        print("LiveVisualizer initialized successfully.")
        
        # Close figure to finish test
        plt.close(viz.fig)
        print("Test Complete.")
        
    except Exception as e:
        print(f"Test Failed with error: {e}")
        raise e

if __name__ == "__main__":
    test_live_visualizer()
