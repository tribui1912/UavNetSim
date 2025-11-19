import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Button, Slider
import numpy as np
from utils import config

class LiveVisualizer:
    """
    Interactive Visualizer that controls the SimPy environment.
    Allows Start, Pause, Step, and Reset functionality.
    """
    def __init__(self, simulator, env, channel_states):
        self.simulator = simulator
        self.env = env
        self.channel_states = channel_states
        
        self.is_running = False
        self.step_size = 100000  # 0.1s in us
        self.current_time = 0
        
        # Setup Figure
        self.fig = plt.figure(figsize=(16, 9))
        self.gs = gridspec.GridSpec(3, 3, height_ratios=[3, 1, 1])
        
        # 3D Topology View
        self.ax_3d = self.fig.add_subplot(self.gs[0, :], projection='3d')
        self.ax_3d.set_title("3D Topology View")
        
        # Panels
        self.ax_pdr = self.fig.add_subplot(self.gs[1, 0])
        self.ax_pdr.set_title("PDR (%)")
        self.ax_latency = self.fig.add_subplot(self.gs[1, 1])
        self.ax_latency.set_title("Avg Latency (ms)")
        self.ax_energy = self.fig.add_subplot(self.gs[1, 2])
        self.ax_energy.set_title("Avg Residual Energy (J)")
        
        self.ax_queue = self.fig.add_subplot(self.gs[2, :])
        self.ax_queue.set_title("Queue Sizes per UAV")
        
        # Data History
        self.time_history = []
        self.pdr_history = []
        self.latency_history = []
        self.energy_history = []
        
        # Controls
        self._setup_controls()
        
        plt.ion()  # Interactive mode
        self.fig.show()

    def _setup_controls(self):
        # Add buttons
        ax_start = plt.axes([0.1, 0.02, 0.1, 0.04])
        self.btn_start = Button(ax_start, 'Start/Resume')
        self.btn_start.on_clicked(self.start_sim)
        
        ax_pause = plt.axes([0.21, 0.02, 0.1, 0.04])
        self.btn_pause = Button(ax_pause, 'Pause')
        self.btn_pause.on_clicked(self.pause_sim)
        
        ax_step = plt.axes([0.32, 0.02, 0.1, 0.04])
        self.btn_step = Button(ax_step, 'Step')
        self.btn_step.on_clicked(self.step_sim)
        
        ax_formation = plt.axes([0.8, 0.02, 0.15, 0.04])
        self.btn_formation = Button(ax_formation, 'Trigger Formation')
        self.btn_formation.on_clicked(self.trigger_formation)

    def start_sim(self, event):
        self.is_running = True
        while self.is_running and self.env.now < config.SIM_TIME:
            self.step_sim(None)
            plt.pause(0.01)

    def pause_sim(self, event):
        self.is_running = False

    def step_sim(self, event):
        # Run simulation for step_size
        target_time = self.env.now + self.step_size
        self.env.run(until=target_time)
        self.update_plot()

    def trigger_formation(self, event):
        print(f"Formation change triggered at {self.env.now}")
        # Logic to trigger formation change event in simulator
        self.simulator.trigger_formation_change()

    def update_plot(self):
        self.ax_3d.clear()
        self.ax_3d.set_xlim(0, config.MAP_LENGTH)
        self.ax_3d.set_ylim(0, config.MAP_WIDTH)
        self.ax_3d.set_zlim(0, config.MAP_HEIGHT)
        
        # Draw Drones
        for drone in self.simulator.drones:
            x, y, z = drone.coords
            color = 'green' if drone.residual_energy > config.INITIAL_ENERGY * 0.5 else 'red'
            self.ax_3d.scatter(x, y, z, c=color, s=50)
            self.ax_3d.text(x, y, z, str(drone.identifier))
            
            # Draw Links
            from phy.large_scale_fading import maximum_communication_range
            from utils.util_function import euclidean_distance_3d
            
            max_range = maximum_communication_range()
            
            for other_drone in self.simulator.drones:
                if drone.identifier < other_drone.identifier: # Avoid double drawing
                    dist = euclidean_distance_3d(drone.coords, other_drone.coords)
                    if dist <= max_range:
                        x_link = [drone.coords[0], other_drone.coords[0]]
                        y_link = [drone.coords[1], other_drone.coords[1]]
                        z_link = [drone.coords[2], other_drone.coords[2]]
                        self.ax_3d.plot(x_link, y_link, z_link, color='black', linestyle='dashed', linewidth=1)

        # Update Metrics
        current_time_sec = self.env.now / 1e6
        self.time_history.append(current_time_sec)
        
        # PDR
        if self.simulator.metrics.datapacket_generated_num > 0:
            pdr = len(self.simulator.metrics.datapacket_arrived) / self.simulator.metrics.datapacket_generated_num * 100
        else:
            pdr = 0
        self.pdr_history.append(pdr)
        self.ax_pdr.plot(self.time_history, self.pdr_history, 'b-')
        
        # Latency
        if self.simulator.metrics.deliver_time_dict:
            avg_latency = np.mean(list(self.simulator.metrics.deliver_time_dict.values())) / 1e3
        else:
            avg_latency = 0
        self.latency_history.append(avg_latency)
        self.ax_latency.plot(self.time_history, self.latency_history, 'r-')
        
        # Energy
        avg_energy = np.mean([d.residual_energy for d in self.simulator.drones])
        self.energy_history.append(avg_energy)
        self.ax_energy.plot(self.time_history, self.energy_history, 'g-')
        
        # Queue Sizes
        queue_sizes = [d.transmitting_queue.qsize() for d in self.simulator.drones]
        self.ax_queue.clear()
        self.ax_queue.bar(range(len(queue_sizes)), queue_sizes)
        self.ax_queue.set_ylim(0, config.MAX_QUEUE_SIZE)
        
        self.fig.canvas.draw_idle()
