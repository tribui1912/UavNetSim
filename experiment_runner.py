import simpy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from simulator.simulator import Simulator
from utils import config
from mobility import start_coords
from mobility.random_waypoint_3d import RandomWaypoint3D
from mobility.leader_follower import LeaderFollower
import logging
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# Disable logging for experiments to speed up
logging.getLogger().setLevel(logging.ERROR)

def calculate_formation_offset(drone_id):
    """Calculate formation offset for V-formation pattern"""
    if drone_id == 0:
        return [0, 0, 0]  # Leader
    
    # V-formation: drones arranged in two lines behind leader
    row = (drone_id - 1) // 2 + 1
    side = 1 if (drone_id - 1) % 2 == 0 else -1
    
    offset_x = -row * 50  # Behind leader
    offset_y = side * row * 50  # To the side
    offset_z = 0
    
    return [offset_x, offset_y, offset_z]

def run_simulation(duration, n_drones, mobility_type='RandomWaypoint', seed=2024):
    """Helper function to run a single simulation"""
    env = simpy.Environment()
    channel_states = {i: simpy.Resource(env, capacity=1) for i in range(n_drones)}
    simulator = Simulator(seed=seed, env=env, channel_states=channel_states, 
                         n_drones=n_drones, total_simulation_time=duration)
    
    # Set mobility models
    if mobility_type == 'LeaderFollower':
        for drone in simulator.drones:
            if drone.identifier == 0:
                drone.mobility_model = RandomWaypoint3D(drone)  # Leader uses RWP
            else:
                offset = calculate_formation_offset(drone.identifier)
                leader_drone = simulator.drones[0]  # Leader is drone 0
                drone.mobility_model = LeaderFollower(drone, leader_drone, offset)
    # else: RandomWaypoint is default

    env.run(until=duration)
    return simulator

def run_single_mobility_config(args):
    """Run a single mobility configuration (for parallel execution)"""
    n_drones, mobility, config_dict = args
    
    # Restore config (each process needs its own)
    for key, value in config_dict.items():
        setattr(config, key, value)
    
    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] Testing {mobility} with N={n_drones} drones")
    
    # Configure
    config.NUMBER_OF_DRONES = n_drones
    config.DEFAULT_SPEED = 10
    
    # Tiered simulation durations for practical runtime while maintaining accuracy
    # N=5, N=25: 50s produces sufficient samples (2.5k and 12.5k packets)
    # N=100: 30s produces 15k packets (more than N=25 @ 100s!)
    if n_drones >= 100:
        config.SIM_TIME = 30 * 1e6  # 30 seconds for N=100
    else:
        config.SIM_TIME = 50 * 1e6  # 50 seconds for N=5, N=25
    
    config.PACKET_GENERATION_RATE = 5
    
    simulator = run_simulation(config.SIM_TIME, n_drones, mobility)
    
    # Calculate metrics
    if simulator.metrics.deliver_time_dict:
        avg_latency = np.mean(list(simulator.metrics.deliver_time_dict.values())) / 1e3
    else:
        avg_latency = 0
        
    pdr = (len(simulator.metrics.datapacket_arrived) / 
          simulator.metrics.datapacket_generated_num * 100) if simulator.metrics.datapacket_generated_num > 0 else 0
    
    if simulator.metrics.hop_cnt_dict:
        avg_hop_count = np.mean(list(simulator.metrics.hop_cnt_dict.values()))
    else:
        avg_hop_count = 0
    
    control_overhead = simulator.metrics.control_packet_num
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"[{end_time.strftime('%H:%M:%S')}] {mobility} N={n_drones} completed in {duration:.1f}s - PDR: {pdr:.2f}%")
    
    return {
        'Mobility': mobility,
        'NodeCount': n_drones,
        'Latency_ms': avg_latency,
        'PDR': pdr,
        'AvgHopCount': avg_hop_count,
        'ControlOverhead': control_overhead,
        'PacketsGenerated': simulator.metrics.datapacket_generated_num,
        'PacketsDelivered': len(simulator.metrics.datapacket_arrived)
    }

def run_single_power_config(args):
    """Run a single power configuration (for parallel execution)"""
    tx_power, config_dict = args
    
    # Restore config
    for key, value in config_dict.items():
        setattr(config, key, value)
        
    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] Testing TX Power: {tx_power} W")
    
    # Configure both energy consumption and transmission power
    config.POWER_TX = tx_power
    config.TRANSMITTING_POWER = tx_power / 10
    config.NUMBER_OF_DRONES = 25
    config.DEFAULT_SPEED = 10
    config.SIM_TIME = 600 * 1e6
    config.PACKET_GENERATION_RATE = 5
    
    simulator = run_simulation(config.SIM_TIME, 25, 'RandomWaypoint')
    
    # Find network lifetime
    death_times = []
    for drone in simulator.drones:
        if drone.death_time is not None:
            death_times.append(drone.death_time)
    
    network_lifetime = min(death_times) / 1e6 if death_times else config.SIM_TIME / 1e6
    
    # PDR
    pdr = (len(simulator.metrics.datapacket_arrived) / 
          simulator.metrics.datapacket_generated_num * 100) if simulator.metrics.datapacket_generated_num > 0 else 0
    
    # Average energy consumption
    avg_energy_consumed = np.mean([config.INITIAL_ENERGY - drone.residual_energy 
                                  for drone in simulator.drones])
    
    # Number of dead drones
    dead_drones = sum(1 for drone in simulator.drones if drone.sleep)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"[{end_time.strftime('%H:%M:%S')}] Power {tx_power}W completed in {duration:.1f}s - Lifetime: {network_lifetime:.2f} s, PDR: {pdr:.2f}%")
    
    return {
        'TX_Power_W': tx_power,
        'Network_Lifetime_s': network_lifetime,
        'PDR': pdr,
        'Avg_Energy_Consumed_J': avg_energy_consumed,
        'Dead_Drones': dead_drones,
        'PacketsGenerated': simulator.metrics.datapacket_generated_num,
        'PacketsDelivered': len(simulator.metrics.datapacket_arrived)
    }

def run_experiment_1_mobility_comparison():
    """E1: Formation vs Random Waypoint at different node counts (PARALLELIZED)"""
    print("="*60)
    print("Running Experiment 1: Mobility Model Comparison (PARALLEL)")
    print("="*60)
    
    node_counts = [5, 25, 100]
    mobility_models = ['RandomWaypoint', 'LeaderFollower']
    
    # Prepare all configurations
    configs = []
    config_dict = {
        'INITIAL_ENERGY': config.INITIAL_ENERGY,
        'POWER_TX': config.POWER_TX,
        'TRANSMITTING_POWER': config.TRANSMITTING_POWER,
        'DEFAULT_SPEED': 10,
        'PACKET_GENERATION_RATE': 5
    }
    
    for n_drones in node_counts:
        for mobility in mobility_models:
            configs.append((n_drones, mobility, config_dict))
    
    # Run in parallel
    max_workers = min(multiprocessing.cpu_count(), len(configs))
    print(f"\nRunning {len(configs)} configurations in parallel using {max_workers} workers\n")
    
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_single_mobility_config, cfg) for cfg in configs]
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error in configuration: {e}")
    
    # Sort results for consistent ordering
    results = sorted(results, key=lambda x: (x['NodeCount'], x['Mobility']))
    
    df = pd.DataFrame(results)
    df.to_csv('experiment_1_mobility_comparison.csv', index=False)
    print(f"\n{'='*60}")
    print("Experiment 1 Complete. Saved to experiment_1_mobility_comparison.csv")
    print(f"{'='*60}\n")
    return results

def run_experiment_2_power_vs_lifetime():
    """E2: TX Power levels vs lifetime/PDR (PARALLELIZED)"""
    print("="*60)
    print("Running Experiment 2: TX Power vs Lifetime/PDR (PARALLEL)")
    print("="*60)
    
    power_levels = [0.5, 1.0, 1.5, 2.0, 2.5]  # Watts
    
    # Prepare configurations
    configs = []
    config_dict = {
        'INITIAL_ENERGY': config.INITIAL_ENERGY,
        'DEFAULT_SPEED': 10,
        'PACKET_GENERATION_RATE': 5
    }
    
    for tx_power in power_levels:
        configs.append((tx_power, config_dict))
        
    # Run in parallel
    max_workers = min(multiprocessing.cpu_count(), len(configs))
    print(f"\nRunning {len(configs)} configurations in parallel using {max_workers} workers\n")
    
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_single_power_config, cfg) for cfg in configs]
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error in configuration: {e}")
    
    # Sort results
    results = sorted(results, key=lambda x: x['TX_Power_W'])
    
    # Restore original power settings
    # No need to restore power settings as they are process-local or overwritten
    # But good practice if we were running sequentially in same process
    # config.POWER_TX = original_power_tx
    # config.TRANSMITTING_POWER = original_transmitting_power
    
    df = pd.DataFrame(results)
    df.to_csv('experiment_2_power_vs_lifetime.csv', index=False)
    print(f"\n{'='*60}")
    print("Experiment 2 Complete. Saved to experiment_2_power_vs_lifetime.csv")
    print(f"{'='*60}\n")
    return results

def run_experiment_3_formation_transition():
    """E3: Formation transition with route churn and recovery metrics"""
    print("="*60)
    print("Running Experiment 3: Formation Transition Analysis")
    print("="*60)
    
    config.DEFAULT_SPEED = 10
    config.PACKET_GENERATION_RATE = 5
    config.NUMBER_OF_DRONES = 25
    config.SIM_TIME = 600 * 1e6  # 600 seconds
    transition_time = 300 * 1e6  # Transition at 300s
    
    env = simpy.Environment()
    channel_states = {i: simpy.Resource(env, capacity=1) for i in range(config.NUMBER_OF_DRONES)}
    simulator = Simulator(seed=2024, env=env, channel_states=channel_states, 
                         n_drones=config.NUMBER_OF_DRONES, total_simulation_time=config.SIM_TIME)
    
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
    
    print("\n[%s] Starting simulation..." % datetime.now().strftime('%H:%M:%S'))
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
            if 280 <= time_s < 300:  # Last 20s before transition
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
        
        if int(time_s) % 50 == 0:
            print(f"  Time: {time_s:.0f}s, Phase: {phase:10s}, PDR: {instant_pdr:.2f}%, Route Churn: {route_additions + route_deletions:4d}")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    df = pd.DataFrame(results)
    df.to_csv('experiment_3_formation_transition.csv', index=False)
    
    # Summary statistics
    avg_pre_pdr = np.mean(pre_transition_pdr_values) if pre_transition_pdr_values else 0
    
    print(f"\n{'='*60}")
    print(f"[{end_time.strftime('%H:%M:%S')}] Experiment 3 Complete (took {duration/60:.1f} min). Saved to experiment_3_formation_transition.csv")
    print(f"  Pre-transition PDR (avg last 20s): {avg_pre_pdr:.2f}%")
    if recovery_time:
        print(f"  Time to restore (to 90% of pre-transition): {recovery_time:.2f}s")
    else:
        print(f"  Network did not recover to 90% of pre-transition PDR")
    print(f"{'='*60}\n")
    
    return results

if __name__ == "__main__":
    overall_start = datetime.now()
    print("\n" + "="*60)
    print(f" UavNetSim - Experimental Evaluation ")
    print(f" Started at: {overall_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    # Run all experiments
    exp1_results = run_experiment_1_mobility_comparison()
    exp2_results = run_experiment_2_power_vs_lifetime()
    exp3_results = run_experiment_3_formation_transition()
    
    overall_end = datetime.now()
    total_duration = (overall_end - overall_start).total_seconds()
    
    print("\n" + "="*60)
    print(f" All Experiments Complete! ")
    print(f" Total Time: {total_duration/60:.1f} minutes")
    print("="*60)
    print("\nGenerated files:")
    print("  - experiment_1_mobility_comparison.csv")
    print("  - experiment_2_power_vs_lifetime.csv")
    print("  - experiment_3_formation_transition.csv")
    print("\n")
