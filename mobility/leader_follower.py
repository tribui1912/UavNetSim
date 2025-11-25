import numpy as np
import math
from utils import config

class LeaderFollower:
    """
    Leader-Follower Mobility Model
    """
    def __init__(self, drone, leader_drone, offset):
        self.my_drone = drone
        self.leader = leader_drone
        self.offset = np.array(offset) # [x, y, z] offset from leader
        
        self.position_update_interval = 1 * 1e5  # 0.1s
        
        self.my_drone.simulator.env.process(self.mobility_update())

    def mobility_update(self):
        while True:
            # Calculate desired position
            leader_pos = np.array(self.leader.coords)
            target_pos = leader_pos + self.offset
            
            # Ensure target is within bounds
            target_pos[0] = max(0, min(target_pos[0], config.MAP_LENGTH))
            target_pos[1] = max(0, min(target_pos[1], config.MAP_WIDTH))
            target_pos[2] = max(0, min(target_pos[2], config.MAP_HEIGHT))
            
            cur_pos = np.array(self.my_drone.coords)
            vector = target_pos - cur_pos
            distance = np.linalg.norm(vector)
            
            if distance > 0.1:
                # Move towards target
                # Speed depends on distance to catch up, but capped at max speed?
                # Or just move at max speed until close?
                # Let's use max speed.
                
                direction = vector / distance
                step_dist = self.my_drone.speed * (self.position_update_interval / 1e6)
                
                if step_dist >= distance:
                    new_pos = target_pos
                    velocity = direction * (distance / (self.position_update_interval / 1e6)) # effective velocity
                else:
                    new_pos = cur_pos + direction * step_dist
                    velocity = direction * self.my_drone.speed
                
                self.my_drone.coords = new_pos.tolist()
                self.my_drone.velocity = velocity.tolist()
                
                # Update direction/pitch
                self.my_drone.direction = math.atan2(velocity[1], velocity[0])
                if np.linalg.norm(velocity) > 0:
                    self.my_drone.pitch = math.asin(max(-1.0, min(1.0, velocity[2] / np.linalg.norm(velocity))))
            else:
                # Already at target (maintaining formation)
                # Velocity matches leader? Or zero relative?
                # If leader is moving, we should be moving too.
                # But in this discrete step, if we are close enough, we just stay put relative to target?
                # No, if leader moves, target moves.
                # If distance is small, we just snap to target?
                self.my_drone.coords = target_pos.tolist()
                self.my_drone.velocity = self.leader.velocity # Assume matching velocity
                self.my_drone.direction = self.leader.direction
                self.my_drone.pitch = self.leader.pitch

            yield self.my_drone.simulator.env.timeout(self.position_update_interval)
