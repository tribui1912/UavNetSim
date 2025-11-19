import simpy
import matplotlib.pyplot as plt
from utils import config
from simulator.simulator import Simulator
from visualization.visualizer import SimulationVisualizer

"""
  _   _                   _   _          _     ____    _             
 | | | |   __ _  __   __ | \\ | |   ___  | |_  / ___|  (_)  _ __ ___  
 | | | |  / _` | \\ \\ / / |  \\| |  / _ \\ | __| \\___ \\  | | | '_ ` _ \\ 
 | |_| | | (_| |  \\ V /  | |\\  | |  __/ | |_   ___) | | | | | | | | |
  \\___/   \\__,_|   \\_/   |_| \\_|  \\___|  \\__| |____/  |_| |_| |_| |_|
                                                                                                                                                                                                                                                                                           
"""

if __name__ == "__main__":
    # Simulation setup
    env = simpy.Environment()
    channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
    sim = Simulator(seed=2025, env=env, channel_states=channel_states, n_drones=config.NUMBER_OF_DRONES)
    
    # GUI Selection
    # Options: 'pyqt' (recommended, high performance), 'matplotlib' (original), 'none' (headless)
    GUI_MODE = 'pyqt'  # Change to 'matplotlib' or 'none' as needed
    
    if GUI_MODE == 'pyqt':
        # High-performance PyQt6 GUI with threaded simulation
        from visualization.pyqt_gui import launch_pyqt_gui
        print("Starting PyQt6 High-Performance GUI...")
        launch_pyqt_gui(sim, env)
        
    elif GUI_MODE == 'matplotlib':
        # Original matplotlib live visualization
        from visualization.live_visualizer import LiveVisualizer
        print("Starting Matplotlib Live Visualization...")
        viz = LiveVisualizer(sim, env, channel_states)
        plt.show(block=True)
        
    else:
        # Headless mode with post-run visualization
        print("Running in headless mode...")
        visualizer = SimulationVisualizer(sim, output_dir=".", vis_frame_interval=20000)
        visualizer.run_visualization()
        env.run(until=config.SIM_TIME)
        visualizer.finalize()