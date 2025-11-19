"""
PyQt6-based high-performance GUI for UavNetSim

This module provides a modern, responsive GUI using PyQt6 and PyQtGraph.
Performance improvements over matplotlib:
- 10-100x faster rendering
- Separate simulation thread (no GUI freezing)
- OpenGL-accelerated 3D view
- Real-time updates without blocking

Author: AI Assistant
Created: 2025-11-19
"""

import sys
import numpy as np
import logging
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSlider, QGridLayout)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt, QMutex, QMutexLocker
from PyQt6.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from OpenGL.GL import *
from utils import config

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pyqt_gui_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SimulationWorker(QThread):
    """
    Worker thread that runs the SimPy simulation in the background.
    Emits signals when data is ready for the GUI to display.
    """
    update_data = pyqtSignal(dict)  # Emit simulation data
    simulation_finished = pyqtSignal()
    
    def __init__(self, simulator, env, step_size=100000):
        super().__init__()
        self.simulator = simulator
        self.env = env
        self.step_size = step_size  # microseconds
        self.is_running = False
        self.is_paused = True
        
    def run(self):
        """Main simulation loop running in background thread"""
        try:
            logger.info("Simulation worker thread started")
            self.is_running = True
            while self.is_running and self.env.now < config.SIM_TIME:
                if not self.is_paused:
                    try:
                        # Run simulation for one step
                        target_time = self.env.now + self.step_size
                        self.env.run(until=target_time)
                        
                        # Collect data for GUI
                        data = self._collect_simulation_data()
                        self.update_data.emit(data)
                        
                        # Small delay to prevent CPU overload
                        self.msleep(10)
                    except Exception as e:
                        logger.error(f"Error in simulation step: {e}", exc_info=True)
                        self.msleep(100)
                else:
                    self.msleep(50)  # Sleep longer when paused
                    
            logger.info("Simulation finished normally")
            self.simulation_finished.emit()
        except Exception as e:
            logger.error(f"Fatal error in simulation thread: {e}", exc_info=True)
            self.simulation_finished.emit()
    
    def _collect_simulation_data(self):
        """Collect all data needed for visualization"""
        # Drone positions and states
        drones_data = []
        for drone in self.simulator.drones:
            drones_data.append({
                'id': drone.identifier,
                'pos': np.array(drone.coords),
                'energy': drone.residual_energy,
                'queue_size': drone.transmitting_queue.qsize()
            })
        
        # Metrics
        if self.simulator.metrics.datapacket_generated_num > 0:
            pdr = len(self.simulator.metrics.datapacket_arrived) / self.simulator.metrics.datapacket_generated_num * 100
        else:
            pdr = 0
            
        if self.simulator.metrics.deliver_time_dict:
            avg_latency = np.mean(list(self.simulator.metrics.deliver_time_dict.values())) / 1e3
        else:
            avg_latency = 0
            
        jitter = self.simulator.metrics.calculate_jitter()
        avg_energy = np.mean([d.residual_energy for d in self.simulator.drones])
        
        return {
            'time': self.env.now / 1e6,  # seconds
            'drones': drones_data,
            'pdr': pdr,
            'latency': avg_latency,
            'jitter': jitter,
            'energy': avg_energy
        }
    
    def pause(self):
        self.is_paused = True
        
    def resume(self):
        self.is_paused = False
        
    def step_forward(self):
        """Execute one simulation step"""
        if self.is_paused and self.env.now < config.SIM_TIME:
            target_time = self.env.now + self.step_size
            self.env.run(until=target_time)
            data = self._collect_simulation_data()
            self.update_data.emit(data)
    
    def set_speed(self, multiplier):
        """Adjust simulation step size"""
        self.step_size = 100000 * multiplier
    
    def stop(self):
        self.is_running = False
        self.wait()  # Wait for thread to finish


class PyQtGUI(QMainWindow):
    """
    Main window for the PyQt6-based GUI
    """
    
    def __init__(self, simulator, env):
        super().__init__()
        self.simulator = simulator
        self.env = env
        
        # Thread safety
        self.data_mutex = QMutex()
        
        # 3D update throttling to prevent GUI freeze
        self.update_3d_counter = 0
        self.update_3d_every_n = 10  # Only update 3D every 10 data updates (increased from 5)
        
        # Limit data history to prevent memory issues (keep last 1000 points)
        self.max_history = 1000
        
        # Data history for plots
        self.time_history = []
        self.pdr_history = []
        self.latency_history = []
        self.jitter_history = []
        self.energy_history = []
        
        # Create simulation worker thread
        self.sim_worker = SimulationWorker(simulator, env)
        self.sim_worker.update_data.connect(self.update_displays)
        self.sim_worker.simulation_finished.connect(self.on_simulation_finished)
        
        self.init_ui()
        
        # Start the worker thread
        self.sim_worker.start()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"UavNetSim - High Performance GUI (Seed: {self.simulator.seed})")
        self.setGeometry(100, 100, 1600, 900)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top section: 3D View
        self.setup_3d_view()
        main_layout.addWidget(self.gl_widget, stretch=3)
        
        # Middle section: 2D Metrics plots (4 plots in a row)
        metrics_layout = QHBoxLayout()
        self.setup_metric_plots()
        metrics_layout.addWidget(self.pdr_plot)
        metrics_layout.addWidget(self.latency_plot)
        metrics_layout.addWidget(self.jitter_plot)
        metrics_layout.addWidget(self.energy_plot)
        main_layout.addLayout(metrics_layout, stretch=2)
        
        # Bottom section: Queue sizes bar chart
        self.setup_queue_plot()
        main_layout.addWidget(self.queue_plot, stretch=1)
        
        # Control panel at the very bottom
        control_layout = self.setup_controls()
        main_layout.addLayout(control_layout)
        
    def setup_3d_view(self):
        """Setup 3D OpenGL view for topology"""
        logger.info("Setting up 3D view")
        
        # Create custom GLViewWidget with LIGHT GREY background
        class LightGreyGLViewWidget(gl.GLViewWidget):
            def paintGL(self, *args, **kwargs):
                # Set clear color to LIGHT GREY (0.8 = 80% brightness)
                glClearColor(0.8, 0.8, 0.8, 1.0)  # Light grey background
                super().paintGL(*args, **kwargs)
        
        self.gl_widget = LightGreyGLViewWidget()
        # Also try the backup method with a different color format
        self.gl_widget.setBackgroundColor(200, 200, 200)  # RGB 200/255 = light grey
        self.gl_widget.setCameraPosition(distance=900, elevation=25, azimuth=45)
        
        # Add grid with DARK/BLACK styling for light background  
        grid = gl.GLGridItem()
        grid.setSize(config.MAP_LENGTH, config.MAP_WIDTH)
        grid.setSpacing(100, 100)
        grid.setColor((0.0, 0.0, 0.0, 1.0))  # PURE BLACK grid for maximum visibility
        self.gl_widget.addItem(grid)
        
        # Add custom thick axes (Red=X, Green=Y, Blue=Z)
        axis_length = 200
        axis_width = 5
        
        # X-axis (Red)
        x_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [axis_length, 0, 0]]),
            color=(1, 0, 0, 1),
            width=axis_width,
            antialias=True
        )
        self.gl_widget.addItem(x_axis)
        
        # Y-axis (Green)
        y_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, axis_length, 0]]),
            color=(0, 0.8, 0, 1),
            width=axis_width,
            antialias=True
        )
        self.gl_widget.addItem(y_axis)
        
        # Z-axis (Blue)
        z_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 0, axis_length]]),
            color=(0, 0, 1, 1),
            width=axis_width,
            antialias=True
        )
        self.gl_widget.addItem(z_axis)
        
        # Store drone mesh items (spheres) and labels
        self.drone_meshes = []
        self.drone_labels = []
        
        # Create initial drone spheres - SMALLER RADIUS
        md = gl.MeshData.sphere(rows=10, cols=20, radius=10)  # Reduced from 20 to 10
        
        for drone in self.simulator.drones:
            try:
                # Create sphere mesh for each drone
                mesh = gl.GLMeshItem(
                    meshdata=md,
                    smooth=True,
                    color=(0, 0.7, 0, 1),  # Dark green for light background
                    shader='shaded',
                    glOptions='opaque'
                )
                mesh.translate(drone.coords[0], drone.coords[1], drone.coords[2])
                self.gl_widget.addItem(mesh)
                self.drone_meshes.append(mesh)
                
                # Create text label for drone ID
                # Use a larger font and "UAV X" format
                label = gl.GLTextItem(
                    pos=(drone.coords[0], drone.coords[1], drone.coords[2] + 20), # Higher offset (radius is 10)
                    text=f"UAV {drone.identifier}",
                    color=(0, 0, 0, 1), # Black text
                )
                # Set font explicitly to ensure it applies
                font = QFont("Arial", 16, QFont.Weight.Bold)
                label.setFont(font)
                
                self.gl_widget.addItem(label)
                self.drone_labels.append(label)
                
                logger.debug(f"Created mesh and label for drone {drone.identifier}")
            except Exception as e:
                logger.error(f"Error creating drone mesh/label: {e}", exc_info=True)
        
        # Link lines - DARK BLUE with TRANSPARENCY
        self.link_lines = gl.GLLinePlotItem(
            pos=np.array([[0,0,0], [0,0,0]]),  
            mode='lines', 
            color=(0, 0, 0.8, 0.3),  # Dark blue with 30% opacity (transparency)
            width=2,  # Slightly thinner for elegance
            antialias=True
        )
        self.gl_widget.addItem(self.link_lines)
        logger.info(f"3D view setup complete with {len(self.drone_meshes)} drones")
        
    def setup_metric_plots(self):
        """Setup 2D metric plots using PyQtGraph"""
        # Set white background for all plots
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOptions(antialias=True)
        
        # PDR Plot
        self.pdr_plot = pg.PlotWidget(title="PDR (%)")
        self.pdr_plot.setLabel('left', 'PDR', units='%', color='k')
        self.pdr_plot.setLabel('bottom', 'Time', units='s', color='k')
        self.pdr_plot.showGrid(x=True, y=True, alpha=0.3)
        self.pdr_curve = self.pdr_plot.plot(pen=pg.mkPen('b', width=2))
        
        # Latency Plot
        self.latency_plot = pg.PlotWidget(title="Latency (ms)")
        self.latency_plot.setLabel('left', 'Latency', units='ms', color='k')
        self.latency_plot.setLabel('bottom', 'Time', units='s', color='k')
        self.latency_plot.showGrid(x=True, y=True, alpha=0.3)
        self.latency_curve = self.latency_plot.plot(pen=pg.mkPen('r', width=2))
        
        # Jitter Plot
        self.jitter_plot = pg.PlotWidget(title="Jitter (ms)")
        self.jitter_plot.setLabel('left', 'Jitter', units='ms', color='k')
        self.jitter_plot.setLabel('bottom', 'Time', units='s', color='k')
        self.jitter_plot.showGrid(x=True, y=True, alpha=0.3)
        self.jitter_curve = self.jitter_plot.plot(pen=pg.mkPen('m', width=2))
        
        # Energy Plot
        self.energy_plot = pg.PlotWidget(title="Avg Energy (J)")
        self.energy_plot.setLabel('left', 'Energy', units='J', color='k')
        self.energy_plot.setLabel('bottom', 'Time', units='s', color='k')
        self.energy_plot.showGrid(x=True, y=True, alpha=0.3)
        self.energy_curve = self.energy_plot.plot(pen=pg.mkPen('g', width=2))
        
    def setup_queue_plot(self):
        """Setup bar chart for queue sizes with UAV IDs"""
        self.queue_plot = pg.PlotWidget(title="Queue Sizes per UAV (UAV ID shown on X-axis)")
        self.queue_plot.setLabel('left', 'Packets in Queue', color='k')
        self.queue_plot.setLabel('bottom', 'UAV ID', color='k')
        self.queue_plot.showGrid(y=True, alpha=0.3)
        
        # Force X-axis to show only integers (no 0.5, 1.5, etc.)
        ax = self.queue_plot.getAxis('bottom')
        ax.setStyle(tickTextOffset=10)
        # This will be set dynamically based on UAV count
        
        # Bar graph item
        self.queue_bargraph = pg.BarGraphItem(x=[], height=[], width=0.6, brush='orange')
        self.queue_plot.addItem(self.queue_bargraph)
        
    def setup_controls(self):
        """Setup control buttons and sliders"""
        control_layout = QHBoxLayout()
        
        # Start/Resume button
        self.btn_start = QPushButton("▶ Start/Resume")
        self.btn_start.setStyleSheet("background-color: lightgreen; font-weight: bold;")
        self.btn_start.clicked.connect(self.on_start)
        control_layout.addWidget(self.btn_start)
        
        # Pause button
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setStyleSheet("background-color: salmon; font-weight: bold;")
        self.btn_pause.clicked.connect(self.on_pause)
        control_layout.addWidget(self.btn_pause)
        
        # Step button
        self.btn_step = QPushButton("⏭ Step")
        self.btn_step.setStyleSheet("background-color: lightblue; font-weight: bold;")
        self.btn_step.clicked.connect(self.on_step)
        control_layout.addWidget(self.btn_step)
        
        # Export button
        self.btn_export = QPushButton("💾 Export")
        self.btn_export.setStyleSheet("background-color: violet; font-weight: bold;")
        self.btn_export.clicked.connect(self.on_export)
        control_layout.addWidget(self.btn_export)
        
        # Speed slider
        control_layout.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(10)
        self.speed_slider.setValue(1)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.setTickInterval(1)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        control_layout.addWidget(self.speed_slider)
        self.speed_label = QLabel("1x")
        self.speed_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        control_layout.addWidget(self.speed_label)
        
        # Status label with UAV ID legend
        control_layout.addStretch()
        self.status_label = QLabel("Ready - UAV IDs shown in Queue chart (bottom) | Green=High Energy, Red=Low Energy")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        control_layout.addWidget(self.status_label)
        
        return control_layout
    
    def update_displays(self, data):
        """Update all displays with new simulation data - THREAD SAFE"""
        try:
            # Lock data access
            with QMutexLocker(self.data_mutex):
                # Update history
                self.time_history.append(data['time'])
                self.pdr_history.append(data['pdr'])
                self.latency_history.append(data['latency'])
                self.jitter_history.append(data['jitter'])
                self.energy_history.append(data['energy'])
                
                # Trim history to prevent memory issues (keep last max_history points)
                if len(self.time_history) > self.max_history:
                    self.time_history = self.time_history[-self.max_history:]
                    self.pdr_history = self.pdr_history[-self.max_history:]
                    self.latency_history = self.latency_history[-self.max_history:]
                    self.jitter_history = self.jitter_history[-self.max_history:]
                    self.energy_history = self.energy_history[-self.max_history:]
                
                # Copy data for plotting (avoid holding lock during plotting)
                time_copy = self.time_history.copy()
                pdr_copy = self.pdr_history.copy()
                latency_copy = self.latency_history.copy()
                jitter_copy = self.jitter_history.copy()
                energy_copy = self.energy_history.copy()
            
            # Update 2D plots (outside lock) - these are fast
            self.pdr_curve.setData(time_copy, pdr_copy)
            self.latency_curve.setData(time_copy, latency_copy)
            self.jitter_curve.setData(time_copy, jitter_copy)
            self.energy_curve.setData(time_copy, energy_copy)
            
            # Update queue bar chart with UAV IDs  
            queue_sizes = [d['queue_size'] for d in data['drones']]
            uav_ids = [d['id'] for d in data['drones']]
            self.queue_bargraph.setOpts(x=uav_ids, height=queue_sizes)
            
            # Set X-axis range to show only integer UAV IDs (no 0.5, 1.5, etc.)
            if uav_ids:
                self.queue_plot.setXRange(min(uav_ids) - 0.5, max(uav_ids) + 0.5, padding=0)
                # Force integer ticks on X-axis
                ax = self.queue_plot.getAxis('bottom')
                ax.setTicks([[(i, str(i)) for i in uav_ids]])
            
            # Throttle 3D updates to prevent GUI freeze
            self.update_3d_counter += 1
            if self.update_3d_counter >= self.update_3d_every_n:
                self.update_3d_counter = 0
                self.update_3d_topology(data['drones'])
            
            # Update status with UAV energy legend
            green_count = sum(1 for d in data['drones'] if d['energy'] > config.INITIAL_ENERGY * 0.5)
            red_count = len(data['drones']) - green_count
            self.status_label.setText(
                f"Time: {data['time']:.1f}s | PDR: {data['pdr']:.1f}% | "
                f"UAVs: {green_count} Green (high energy), {red_count} Red (low energy)"
            )
        except Exception as e:
            logger.error(f"Error updating display: {e}", exc_info=True)
        
    def update_3d_topology(self, drones_data):
        """Update 3D drone positions and colors - THREAD SAFE"""
        if not drones_data or len(self.drone_meshes) == 0:
            return
        
        try:
            # Update each drone mesh position and color
            for i, drone_data in enumerate(drones_data):
                if i < len(self.drone_meshes):
                    mesh = self.drone_meshes[i]
                    
                    # Reset transform and move to new position
                    mesh.resetTransform()
                    pos = drone_data['pos']
                    mesh.translate(pos[0], pos[1], pos[2])
                    
                    # Update label position
                    if i < len(self.drone_labels):
                        label = self.drone_labels[i]
                        # Position label slightly above the drone
                        label.setData(pos=(pos[0], pos[1], pos[2] + 20))
                    
                    # Update color based on energy (darker colors for light background)
                    if drone_data['energy'] > config.INITIAL_ENERGY * 0.5:
                        mesh.setColor((0, 0.7, 0, 1))  # Dark green for high energy
                    else:
                        mesh.setColor((0.8, 0, 0, 1))   #Dark red for low energy
            
            # Update communication links
            from phy.large_scale_fading import maximum_communication_range
            from utils.util_function import euclidean_distance_3d
            
            max_range = maximum_communication_range()
            link_positions = []
            
            for i, drone_i in enumerate(drones_data):
                for j, drone_j in enumerate(drones_data):
                    if i < j:  # Avoid duplicate links
                        dist = euclidean_distance_3d(drone_i['pos'], drone_j['pos'])
                        if dist <= max_range:
                            link_positions.append(drone_i['pos'])
                            link_positions.append(drone_j['pos'])
            
            if link_positions:
                link_positions = np.array(link_positions)
                # Dark blue links with transparency
                self.link_lines.setData(pos=link_positions, color=(0, 0, 0.8, 0.3), width=2)
            else:
                # Clear links if none exist
                self.link_lines.setData(pos=np.array([[0,0,0], [0,0,0]]), color=(0,0,0,0))
        except Exception as e:
            logger.error(f"Error updating 3D topology: {e}", exc_info=True)
            # Don't crash - just skip this update
            pass
        
    def on_start(self):
        """Start/resume simulation"""
        self.sim_worker.resume()
        self.status_label.setText("Running...")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        
    def on_pause(self):
        """Pause simulation"""
        self.sim_worker.pause()
        self.status_label.setText("Paused")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        
    def on_step(self):
        """Execute one simulation step"""
        self.sim_worker.step_forward()
        
    def on_speed_changed(self, value):
        """Update simulation speed"""
        self.sim_worker.set_speed(value)
        self.speed_label.setText(f"{value}x")
        
    def on_export(self):
        """Export data to CSV and save screenshot"""
        import pandas as pd
        
        # Export metrics data
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
        
        # Save 3D view screenshot
        self.gl_widget.grabFramebuffer().save(f"topology_3d_{self.simulator.seed}.png")
        
        self.status_label.setText(f"Exported to {filename}")
        print(f"Data exported to {filename}")
        
    def on_simulation_finished(self):
        """Handle simulation completion"""
        self.status_label.setText("Simulation Complete!")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.sim_worker.stop()
        event.accept()


def launch_pyqt_gui(simulator, env):
    """
    Launch the PyQt6 GUI
    
    Args:
        simulator: Simulator instance
        env: SimPy environment
    """
    logger.info("Launching PyQt6 GUI")
    app = QApplication(sys.argv)
    
    # Force light theme to override Windows dark mode
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    try:
        window = PyQtGUI(simulator, env)
        window.show()
        logger.info("GUI window shown successfully")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Fatal error in GUI: {e}", exc_info=True)
        raise
