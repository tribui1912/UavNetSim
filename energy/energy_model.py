import math
import matplotlib.pyplot as plt
from utils import config


class EnergyModel:
    """
    Implementation of energy model (Y. Zeng2019)

    It should be noted that this class mainly calculates the power consumption required for UAV flight, while
    communication-related energy consumption does not require a special model.

    Attributes:
        delta: profile drag coefficient
        rho: air density
        s: rotor solidity, defined as the ratio of the total blade area to the disc area
        a: rotor disc area
        omega: blade angular velocity in radians/second
        r: rotor radius in meter
        k: incremental correction factor to induced power
        w: aircraft weight in Newton
        u_tip: tip speed of the rotor blade
        v0: mean rotor induced velocity in hover
        d0: fuselage drag ratio

    References:
        [1] Y. Zeng, J. Xu and R. Zhang, "Energy Minimization for Wireless Communication with Rotary-wing UAV," IEEE
            transactions on wireless communications, vol. 18, no. 4, pp. 2329-2345, 2019.

    Author: Zihao Zhou, eezihaozhou@gmail.com
    Created at: 2024/3/21
    Updated at: 2025/4/23
    """

    def __init__(self, drone):
        self.my_drone = drone

        self.delta = config.PROFILE_DRAG_COEFFICIENT
        self.rho = config.AIR_DENSITY
        self.s = config.ROTOR_SOLIDITY
        self.a = config.ROTOR_DISC_AREA
        self.omega = config.BLADE_ANGULAR_VELOCITY
        self.r = config.ROTOR_RADIUS
        self.k = config.INCREMENTAL_CORRECTION_FACTOR
        self.w = config.AIRCRAFT_WEIGHT
        self.u_tip = config.ROTOR_BLADE_TIP_SPEED
        self.v0 = config.MEAN_ROTOR_VELOCITY
        self.d0 = config.FUSELAGE_DRAG_RATIO

        self.current_state = 'IDLE'  # IDLE, TX, RX, SLEEP
        self.my_drone.simulator.env.process(self.energy_monitor())

    def set_state(self, state):
        """Set the current communication state of the drone"""
        if self.my_drone.sleep:
            return
        self.current_state = state

    def power_consumption(self, speed):
        p0 = (self.delta / 8) * self.rho * self.s * self.a * (self.omega ** 3) * (self.r ** 3)
        pi = (1 + self.k) * (self.w ** 1.5) / (math.sqrt(2 * self.rho * self.a))
        blade_profile = p0 * (1 + (3 * speed ** 2) / (self.u_tip ** 2))
        induced = pi * (math.sqrt(1 + speed ** 4 / (4 * self.v0 ** 4)) - speed ** 2 / (2 * self.v0 ** 2)) ** 0.5
        parasite = 0.5 * self.d0 * self.rho * self.s * self.a * speed ** 3

        p = blade_profile + induced + parasite
        return p

    def get_comm_power(self):
        """Get power consumption based on communication state"""
        if self.current_state == 'TX':
            return config.POWER_TX
        elif self.current_state == 'RX':
            return config.POWER_RX
        elif self.current_state == 'SLEEP':
            return config.POWER_SLEEP
        else:  # IDLE
            return config.POWER_IDLE

    def energy_monitor(self):
        """Monitoring energy consumption of drone under a certain energy model"""
        interval = 0.1  # seconds
        interval_us = interval * 1e6

        while True:
            yield self.my_drone.simulator.env.timeout(interval_us)
            
            if self.my_drone.sleep:
                continue

            # Calculate energy consumed in this interval
            # Flight power
            flight_power = self.power_consumption(self.my_drone.speed)
            
            # Communication power
            comm_power = self.get_comm_power()
            
            total_power = flight_power + comm_power
            energy_consumed = total_power * interval  # Joules = Watts * Seconds
            
            self.my_drone.residual_energy -= energy_consumed

            if self.my_drone.residual_energy <= 0:
                self.my_drone.residual_energy = 0
                self.my_drone.sleep = True
                self.current_state = 'SLEEP'
                # print('UAV: ', self.my_drone.identifier, ' run out of energy at: ', self.my_drone.simulator.env.now)
            elif self.my_drone.residual_energy <= config.ENERGY_THRESHOLD:
                # Optional: trigger low energy warning behavior
                pass


# if __name__ == "__main__":
#     em = EnergyModel()
#     em.test()
