import random
import math
import numpy as np
from utils import config

class RandomWaypoint3D:
    """
    3-D Random Waypoint Mobility Model
    """
    def __init__(self, drone):
        self.my_drone = drone
        self.rng = random.Random(self.my_drone.identifier + self.my_drone.simulator.seed + 2)
        
        self.position_update_interval = 1 * 1e5  # 0.1s
        self.pause_time = 0 # seconds
        
        self.min_x = 0
        self.max_x = config.MAP_LENGTH
        self.min_y = 0
        self.max_y = config.MAP_WIDTH
        self.min_z = 0
        self.max_z = config.MAP_HEIGHT
        
        self.current_destination = None
        self.is_paused = False
        self.pause_start_time = 0
        self.active = True
        
        self.my_drone.simulator.env.process(self.mobility_update())

    def stop(self):
        self.active = False

    def pick_new_destination(self):
        x = self.rng.uniform(self.min_x, self.max_x)
        y = self.rng.uniform(self.min_y, self.max_y)
        z = self.rng.uniform(self.min_z, self.max_z)
        return np.array([x, y, z])

    def mobility_update(self):
        while self.active:
            if self.my_drone.target_position is not None:
                # Override for formation change or specific target
                self.current_destination = np.array(self.my_drone.target_position)
            
            if self.current_destination is None:
                self.current_destination = self.pick_new_destination()
                
            cur_pos = np.array(self.my_drone.coords)
            vector = self.current_destination - cur_pos
            distance = np.linalg.norm(vector)
            
            if distance < 1.0: # Reached destination
                if not self.is_paused:
                    self.is_paused = True
                    self.pause_start_time = self.my_drone.simulator.env.now
                    yield self.my_drone.simulator.env.timeout(self.pause_time * 1e6)
                    self.is_paused = False
                    self.current_destination = self.pick_new_destination()
                    # Clear target position if it was set
                    if self.my_drone.target_position is not None:
                        self.my_drone.target_position = None
                else:
                    # Should not happen if yield works
                    pass
            else:
                # Move towards destination
                direction = vector / distance
                step_dist = self.my_drone.speed * (self.position_update_interval / 1e6)
                
                if step_dist >= distance:
                    new_pos = self.current_destination
                else:
                    new_pos = cur_pos + direction * step_dist
                
                self.my_drone.coords = new_pos.tolist()
                
                # Update velocity vector for physics/energy
                velocity = direction * self.my_drone.speed
                self.my_drone.velocity = velocity.tolist()
                
                # Update direction/pitch for visualization
                self.my_drone.direction = math.atan2(velocity[1], velocity[0])
                if self.my_drone.speed > 0:
                    self.my_drone.pitch = math.asin(max(-1.0, min(1.0, velocity[2] / self.my_drone.speed)))
                
            # Energy consumption
            yield self.my_drone.simulator.env.timeout(self.position_update_interval)
            
            # Calculate energy
            # Note: energy_model.energy_monitor handles consumption now!
            # But wait, I modified energy_model to calculate consumption based on speed.
            # So I don't need to subtract energy here.
            # The previous GaussMarkov3D implementation subtracted energy manually (lines 169-170).
            # My new EnergyModel.energy_monitor does it automatically.
            # I should REMOVE manual subtraction from mobility models to avoid double counting.
            # I will check GaussMarkov3D again.
