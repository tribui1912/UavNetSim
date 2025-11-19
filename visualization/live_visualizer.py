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
        self.fig = plt.figure(figsize=(18, 10))
        self.gs = gridspec.GridSpec(3, 4, height_ratios=[3, 1, 1])
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.15, top=0.95, hspace=0.4, wspace=0.3)
        
        # 3D Topology View
        self.ax_3d = self.fig.add_subplot(self.gs[0, :], projection='3d')
        self.ax_3d.set_title("3D Topology View\nGreen: High Energy | Red: Low Energy", fontsize=12, fontweight='bold')
        self.ax_3d.set_xlabel("X (m)")
        self.ax_3d.set_ylabel("Y (m)")
        self.ax_3d.set_zlabel("Z (m)")
        
        # Panels - Initialize Lines
        self.ax_pdr = self.fig.add_subplot(self.gs[1, 0])
        self.ax_pdr.set_ylabel("PDR (%)")
        self.ax_pdr.grid(True)
        self.line_pdr, = self.ax_pdr.plot([], [], 'b-', linewidth=1.5)
        
        self.ax_latency = self.fig.add_subplot(self.gs[1, 1])
        self.ax_latency.set_ylabel("Latency (ms)")
        self.ax_latency.grid(True)
        self.line_latency, = self.ax_latency.plot([], [], 'r-', linewidth=1.5)

        self.ax_jitter = self.fig.add_subplot(self.gs[1, 2])
        self.ax_jitter.set_ylabel("Jitter (ms)")
        self.ax_jitter.grid(True)
        self.line_jitter, = self.ax_jitter.plot([], [], 'm-', linewidth=1.5)
        
        self.ax_energy = self.fig.add_subplot(self.gs[1, 3])
        self.ax_energy.set_ylabel("Energy (J)")
        self.ax_energy.grid(True)
        self.line_energy, = self.ax_energy.plot([], [], 'g-', linewidth=1.5)
        
        self.ax_queue = self.fig.add_subplot(self.gs[2, :])
        self.ax_queue.set_title("Queue Sizes per UAV")
        self.ax_queue.set_ylabel("Packets")
        self.ax_queue.set_xlabel("UAV ID")
        self.bar_container = None
        
        # Data History
        self.time_history = []
        self.pdr_history = []
        self.latency_history = []
        self.jitter_history = []
        self.energy_history = []
        
        # Controls
        self._setup_controls()
        
        plt.ion()  # Interactive mode
        self.fig.show()

    def _setup_controls(self):
        # Buttons
        ax_start = plt.axes([0.05, 0.02, 0.08, 0.04])
        self.btn_start = Button(ax_start, 'Start', color='lightgreen', hovercolor='0.975')
        self.btn_start.on_clicked(self.start_sim)
        
        ax_pause = plt.axes([0.14, 0.02, 0.08, 0.04])
        self.btn_pause = Button(ax_pause, 'Pause', color='salmon', hovercolor='0.975')
        self.btn_pause.on_clicked(self.pause_sim)
        
        ax_step = plt.axes([0.23, 0.02, 0.08, 0.04])
        self.btn_step = Button(ax_step, 'Step', color='lightblue', hovercolor='0.975')
        self.btn_step.on_clicked(self.step_sim)
        
        ax_formation = plt.axes([0.32, 0.02, 0.12, 0.04])
        self.btn_formation = Button(ax_formation, 'Formation Change', color='gold', hovercolor='0.975')
        self.btn_formation.on_clicked(self.trigger_formation)

        ax_export = plt.axes([0.45, 0.02, 0.08, 0.04])
        self.btn_export = Button(ax_export, 'Export', color='violet', hovercolor='0.975')
        self.btn_export.on_clicked(self.export_data)

        # Speed Slider
        ax_speed = plt.axes([0.6, 0.03, 0.25, 0.02])
        self.slider_speed = Slider(ax_speed, 'Speed', 1, 10, valinit=1, valstep=1)
        self.slider_speed.on_changed(self.update_speed)

        # Seed Display
        plt.figtext(0.9, 0.03, f"Seed: {self.simulator.seed}", fontsize=10, fontweight='bold')

    def update_speed(self, val):
        # Adjust step size based on speed
        self.step_size = 100000 * int(val) 

    def export_data(self, event):
        import pandas as pd
        data = {
            'Time': self.time_history,
            'PDR': self.pdr_history,
            'Latency': self.latency_history,
            'Jitter': self.jitter_history,
            'Energy': self.energy_history
        }
        df = pd.DataFrame(data)
        filename = f"simulation_metrics_{self.simulator.seed}.csv"
        df.to_csv(filename, index=False)
        print(f"Data exported to {filename}")
        self.fig.savefig(f"simulation_snapshot_{self.simulator.seed}.png")
        print(f"Snapshot saved.")

    def start_sim(self, event):
        self.is_running = True
        while self.is_running and self.env.now < config.SIM_TIME:
            # Instead of running for full step_size, run in smaller increments if step_size is large
            # But since we optimized plotting, let's try just calling step_sim and pause.
            # If step_size is too large (e.g. 1s), the env.run() call blocks for that long in simulation time,
            # which might be fast in real time unless the simulation is heavy.
            # The issue is likely that env.run() takes too long to compute 0.1s of sim time.
            
            self.step_sim(None)
            
            # Increase pause time slightly to give GUI more breathing room
            plt.pause(0.01) 

    def pause_sim(self, event):
        self.is_running = False

    def step_sim(self, event):
        target_time = self.env.now + self.step_size
        self.env.run(until=target_time)
        self.update_plot()

    def trigger_formation(self, event):
        print(f"Formation change triggered at {self.env.now}")
        self.simulator.trigger_formation_change()

    def update_plot(self):
        # 1. Update Metrics Data
        current_time_sec = self.env.now / 1e6
        self.time_history.append(current_time_sec)
        
        # PDR
        if self.simulator.metrics.datapacket_generated_num > 0:
            pdr = len(self.simulator.metrics.datapacket_arrived) / self.simulator.metrics.datapacket_generated_num * 100
        else:
            pdr = 0
        self.pdr_history.append(pdr)
        self.line_pdr.set_data(self.time_history, self.pdr_history)
        self.ax_pdr.set_title(f"PDR: {pdr:.1f}%", fontsize=10, fontweight='bold')
        self.ax_pdr.relim()
        self.ax_pdr.autoscale_view()
        
        # Latency
        if self.simulator.metrics.deliver_time_dict:
            avg_latency = np.mean(list(self.simulator.metrics.deliver_time_dict.values())) / 1e3
        else:
            avg_latency = 0
        self.latency_history.append(avg_latency)
        self.line_latency.set_data(self.time_history, self.latency_history)
        self.ax_latency.set_title(f"Lat: {avg_latency:.1f}ms", fontsize=10, fontweight='bold')
        self.ax_latency.relim()
        self.ax_latency.autoscale_view()

        # Jitter
        jitter = self.simulator.metrics.calculate_jitter()
        self.jitter_history.append(jitter)
        self.line_jitter.set_data(self.time_history, self.jitter_history)
        self.ax_jitter.set_title(f"Jit: {jitter:.1f}ms", fontsize=10, fontweight='bold')
        self.ax_jitter.relim()
        self.ax_jitter.autoscale_view()
        
        # Energy
        avg_energy = np.mean([d.residual_energy for d in self.simulator.drones])
        self.energy_history.append(avg_energy)
        self.line_energy.set_data(self.time_history, self.energy_history)
        self.ax_energy.set_title(f"Egy: {avg_energy:.1f}J", fontsize=10, fontweight='bold')
        self.ax_energy.relim()
        self.ax_energy.autoscale_view()
        
        # Queue Sizes (Bar chart needs clearing usually, but we can optimize if needed. For now, simple clear is fast enough for 10 bars)
        queue_sizes = [d.transmitting_queue.qsize() for d in self.simulator.drones]
        self.ax_queue.clear()
        bars = self.ax_queue.bar(range(len(queue_sizes)), queue_sizes, color='orange', alpha=0.7)
        self.ax_queue.set_title("Queue Sizes per UAV", fontsize=10, fontweight='bold')
        self.ax_queue.set_ylabel("Packets")
        self.ax_queue.set_xlabel("UAV ID")
        self.ax_queue.set_xticks(range(len(queue_sizes)))
        self.ax_queue.set_ylim(0, max(config.MAX_QUEUE_SIZE, max(queue_sizes) + 1))
        self.ax_queue.grid(axis='y', alpha=0.3)
        
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                self.ax_queue.text(bar.get_x() + bar.get_width()/2., height,
                                f'{int(height)}',
                                ha='center', va='bottom', fontsize=8)

        # 2. Update 3D Plot (Expensive)
        # We clear and redraw because updating 3D scatter/lines is complex in Matplotlib
        self.ax_3d.clear()
        self.ax_3d.set_title("3D Topology View\nGreen: High Energy | Red: Low Energy", fontsize=12, fontweight='bold')
        self.ax_3d.set_xlim(0, config.MAP_LENGTH)
        self.ax_3d.set_ylim(0, config.MAP_WIDTH)
        self.ax_3d.set_zlim(0, config.MAP_HEIGHT)
        self.ax_3d.set_xlabel("X (m)")
        self.ax_3d.set_ylabel("Y (m)")
        self.ax_3d.set_zlabel("Z (m)")
        
        # Draw Drones
        for drone in self.simulator.drones:
            x, y, z = drone.coords
            color = 'green' if drone.residual_energy > config.INITIAL_ENERGY * 0.5 else 'red'
            self.ax_3d.scatter(x, y, z, c=color, s=50, edgecolors='black')
            self.ax_3d.text(x, y, z, f"U{drone.identifier}", fontsize=9)
            
            # Draw Links
            from phy.large_scale_fading import maximum_communication_range
            from utils.util_function import euclidean_distance_3d
            
            max_range = maximum_communication_range()
            
            for other_drone in self.simulator.drones:
                if drone.identifier < other_drone.identifier:
                    dist = euclidean_distance_3d(drone.coords, other_drone.coords)
                    if dist <= max_range:
                        quality = 1 - (dist / max_range)
                        alpha = 0.2 + 0.8 * quality
                        self.ax_3d.plot([drone.coords[0], other_drone.coords[0]], 
                                      [drone.coords[1], other_drone.coords[1]], 
                                      [drone.coords[2], other_drone.coords[2]], 
                                      color='black', linestyle='--', linewidth=0.5 + quality, alpha=alpha)
        
        self.fig.canvas.draw_idle()
