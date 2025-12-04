"""
Standalone Experiment 3 Runner - Formation Transition Analysis
Fixes the timing issue by running 200s simulation with transition at t=100s
"""
import simpy
import numpy as np
import pandas as pd
from simulator.simulator import Simulator
from utils import config
from datetime import datetime

def run_experiment_3_formation_transition():
    """E3: Formation transition with route churn and recovery metrics (FIXED)"""
    print("="*60)
    print("Running Experiment 3: Formation Transition Analysis (FIXED)")
    print("  Duration: 200s (down from 600s)")
    print("  Transition: t=100s (down from t=300s)")
    print("  Reason: Drones survive ~181s, need transition before death")
    print("="*60)
    
    config.DEFAULT_SPEED = 10
    config.PACKET_GENERATION_RATE = 5
    config.NUMBER_OF_DRONES = 25
    config.SIM_TIME = 200 * 1e6  # 200 seconds (was 600s)
    transition_time = 100 * 1e6  # Transition at 100s (was 300s)
    
    env = simpy.Environment()
    channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
    simulator = Simulator(seed=2024, env=env, channel_states=channel_states, 
                         n_drones=config.NUMBER_OF_DRONES, total_simulation_time=config.SIM_TIME)
    
    # Override the formation_manager to trigger at 100s instead of 300s
    def custom_formation_manager():
        yield env.timeout(transition_time)
        simulator.trigger_formation_change()
    
    # Replace the auto-triggered formation manager
    env.process(custom_formation_manager())
    
    # Track metrics
    results = []
    step_size = 1 * 1e6  # 1 second
    window_size = 10  # 10-second window for instantaneous PDR
    
    # Track packet events for windowed PDR
    packet_gen_log = []
    packet_arr_log = []
    
    # Track route churn
    prev_route_tables = {drone.identifier: dict(drone.routing_protocol.routing_table) 
                        for drone in simulator.drones}
    
    pre_transition_pdr_values = []
    recovery_time = None
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting simulation...")
    start_time = datetime.now()
    
    while env.now < config.SIM_TIME:
        prev_gen = simulator.metrics.datapacket_generated_num
        prev_arr = len(simulator.metrics.datapacket_arrived)
        
        env.run(until=env.now + step_size)
        
        time_s = env.now / 1e6
        
        # Log new packet events
        new_gen = simulator.metrics.datapacket_generated_num - prev_gen
        new_arr = len(simulator.metrics.datapacket_arrived) - prev_arr
        for _ in range(new_gen):
            packet_gen_log.append(time_s)
        for _ in range(new_arr):
            packet_arr_log.append(time_s)
        
        # Calculate windowed PDR
        gen_in_window = sum(1 for t in packet_gen_log if time_s - window_size <= t <= time_s)
        arr_in_window = sum(1 for t in packet_arr_log if time_s - window_size <= t <= time_s)
        instant_pdr = (arr_in_window / gen_in_window * 100) if gen_in_window > 0 else 0
        
        # Calculate route churn
        route_additions = 0
        route_deletions = 0
        total_routes = 0
        
        for drone in simulator.drones:
            current_routes = set(drone.routing_protocol.routing_table.keys())
            prev_routes = set(prev_route_tables[drone.identifier].keys())
            
            route_additions += len(current_routes - prev_routes)
            route_deletions += len(prev_routes - current_routes)
            total_routes += len(current_routes)
            
            prev_route_tables[drone.identifier] = dict(drone.routing_protocol.routing_table)
        
        # Identify phases
        if time_s < transition_time / 1e6:
            phase = 'Before'
            if 80 <= time_s < 100:  # Last 20s before transition
                if instant_pdr > 0:
                    pre_transition_pdr_values.append(instant_pdr)
        elif time_s == transition_time / 1e6:
            phase = 'Transition'
        else:
            phase = 'After'
            # Check for recovery
            if recovery_time is None and pre_transition_pdr_values:
                avg_pre_pdr = np.mean(pre_transition_pdr_values)
                if instant_pdr >= 0.9 * avg_pre_pdr:
                    recovery_time = time_s - (transition_time / 1e6)
        
        results.append({
            'Time_s': time_s,
            'Phase': phase,
            'Instant_PDR': instant_pdr,
            'Route_Additions': route_additions,
            'Route_Deletions': route_deletions,
            'Total_Routes': total_routes,
            'Route_Churn': route_additions + route_deletions
        })
        
        if int(time_s) % 20 == 0:
            print(f"  Time: {time_s:.0f}s, Phase: {phase:10s}, PDR: {instant_pdr:.2f}%, Route Churn: {route_additions + route_deletions:4d}")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    df = pd.DataFrame(results)
    df.to_csv('experiment_3_formation_transition.csv', index=False)
    
    # Summary statistics
    avg_pre_pdr = np.mean(pre_transition_pdr_values) if pre_transition_pdr_values else 0
    
    print(f"\n{'='*60}")
    print(f"[{end_time.strftime('%H:%M:%S')}] Experiment 3 Complete (took {duration/60:.1f} min).")
    print(f"  Saved to experiment_3_formation_transition.csv")
    print(f"  Pre-transition PDR (avg last 20s): {avg_pre_pdr:.2f}%")
    if recovery_time:
        print(f"  Time to restore (to 90% of pre-transition): {recovery_time:.2f}s")
    else:
        print(f"  Network did not recover to 90% of pre-transition PDR")
    print(f"{'='*60}\n")
    
    return results

if __name__ == "__main__":
    print("\n" + "="*60)
    print(f" UavNetSim - Experiment 3 Only (Fixed)")
    print(f" Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    run_experiment_3_formation_transition()
    
    print("\nExperiment 3 complete!")
    print("Output: experiment_3_formation_transition.csv\n")
