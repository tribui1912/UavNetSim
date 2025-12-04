# UavNetSim: User Manual & Documentation

**Version:** 1.0  
**Date:** December 2025  
**Group:** 1  

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation & Setup](#2-installation--setup)
3. [User Interface Guide](#3-user-interface-guide)
4. [Simulation Features](#4-simulation-features)
   - [Physical Layer](#41-physical-layer)
   - [MAC Layer](#42-mac-layer)
   - [Network Layer](#43-network-layer)
   - [Mobility Models](#44-mobility-models)
5. [Running Experiments](#5-running-experiments)
6. [Statement of Work](#6-statement-of-work)
7. [References](#7-references)

---

## 1. Introduction

**UavNetSim** is a high-fidelity, discrete-event simulator designed for Unmanned Aerial Vehicle (UAV) networks, also known as Flying Ad-hoc Networks (FANETs). It provides a comprehensive environment to model, simulate, and analyze the complex interactions between physical mobility, wireless communication protocols, and energy consumption in 3D space.

Key capabilities include:
- **Realistic Mobility:** 3D Random Waypoint and Leader-Follower formation flight.
- **Protocol Stack:** Modular implementation of PHY, CSMA/CA MAC, and AODV routing.
- **Energy Modeling:** Detailed power consumption tracking for flight and communication.
- **Interactive GUI:** Real-time 3D visualization with manual controls and live metrics.

---

## 2. Installation & Setup

### Option A: The Easy Way (Recommended)
UavNetSim comes with a "zero-setup" launcher that handles dependencies and virtual environments automatically.

**Windows Users:**
1.  Navigate to the `launcher` folder.
2.  Double-click `run_uavnetsim.bat`.

**Mac/Linux Users:**
1.  Open a terminal.
2.  Run: `./launcher/run_uavnetsim.sh`
    *(Note: You may need to run `chmod +x launcher/*.sh` first)*

The launcher provides an interactive menu to:
- [1] Run the Simulation (GUI)
- [2] Run Unit Tests
- [4] Run All Experiments (E1-E3)
- [6] Check System Status

### Option B: Manual Installation
If you prefer to manage the environment yourself:

1.  **Prerequisites:**
    - Python 3.8 or higher
    - pip package manager

2.  **Clone the repository:**
    ```bash
    git clone https://github.com/tribui1912/UavNetSim.git
    cd UavNetSim
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Key dependencies: `simpy`, `pyqt6`, `pyqtgraph`, `pyopengl`, `numpy`, `pandas`.*

### Running the Simulator (Manual Mode)
To launch the main GUI application:
```bash
python main.py
```

To run the automated experiments (headless mode):
```bash
python experiment_runner.py
```

---

## 3. User Interface Guide

The UavNetSim GUI provides a powerful interface for visualizing network behavior and controlling simulation parameters in real-time.

![UavNetSim GUI Screenshot](img/screenshot.png)
*Figure 1: The UavNetSim Main Interface*

### 3.1 Main Visualization Area (3D View)
The central panel displays the 3D simulation environment.
- **UAV Nodes:** Represented as spheres.
    - **Color Coding:** Indicates energy level.
        - <span style="color:green">**Green:**</span> > 50% Energy
        - <span style="color:yellow">**Yellow:**</span> 20% - 50% Energy
        - <span style="color:red">**Red:**</span> < 20% Energy
- **Links:** Lines drawn between nodes indicate active communication links (neighbors within range).
- **Navigation:**
    - **Rotate:** Left-click and drag.
    - **Pan:** Middle-click (or Shift + Left-click) and drag.
    - **Zoom:** Scroll wheel.

### 3.2 Control Panel (Left/Bottom)
Controls the execution flow of the simulation.
- **Start:** Begins the simulation.
- **Pause:** Temporarily halts the simulation.
- **Reset:** Stops and resets the environment to initial conditions.
- **Speed Slider:** Adjusts the simulation speed multiplier (1x to 10x).
- **Trigger Formation Change:** Manually forces the UAV swarm to switch from Random Waypoint to Leader-Follower formation.

### 3.3 Statistics Panel (Right)
Displays real-time Key Performance Indicators (KPIs).
- **Live Metrics:**
    - **PDR (Packet Delivery Ratio):** Percentage of packets successfully delivered.
    - **Latency:** Average end-to-end delay (ms).
    - **Throughput:** Current network throughput (Kbps).
- **Charts:**
    - **PDR vs Time:** Tracks reliability over the simulation run.
    - **Energy Profile:** Shows average residual energy of the swarm.
    - **Queue Size:** Monitors buffer occupancy to detect congestion.

### 3.4 Exporting Data
- **Export Screenshot:** Saves the current 3D view as a PNG file.
- **Export CSV:** Saves the collected metrics (PDR, Latency, Energy) to a CSV file for external analysis.

---

## 4. Simulation Features

### 4.1 Physical Layer
The PHY layer models the wireless medium and hardware characteristics.
- **Channel Model:** Implements a Log-Distance Path Loss model with probabilistic shadowing. Data loss is simulated with a configurable probability (default 5%) to mimic fading and interference.
- **Energy Model:** Tracks power consumption in four states:
    - **TX (Transmission):** 1.5 W
    - **RX (Reception):** 1.0 W
    - **Idle:** 0.1 W
    - **Sleep:** 0.001 W
    - **Flight Power:** Calculated based on velocity using aerodynamic principles (Zeng et al. model).

### 4.2 MAC Layer
The Link Layer manages access to the shared medium.
- **Protocol:** CSMA/CA (Carrier Sense Multiple Access with Collision Avoidance).
- **Features:**
    - **Backoff Mechanism:** Exponential backoff with configurable contention window ($CW_{min}=31$).
    - **Reliability:** Stop-and-Wait ARQ with ACKs.
    - **Retransmissions:** Packets are dropped after `MAX_RETRANSMISSION_ATTEMPT` (5) failures.
    - **Queuing:** Per-node FIFO queues with finite capacity.

### 4.3 Network Layer
Handles routing and end-to-end packet delivery.
- **Protocol:** AODV (Ad hoc On-Demand Distance Vector).
- **Mechanism:** Reactive routing. Routes are discovered only when needed via RREQ (Route Request) and RREP (Route Reply) cycles.
- **Maintenance:**
    - **Hello Packets:** Periodic beacons (1 Hz) to maintain neighbor tables.
    - **Link Breaks:** Detected via MAC layer feedback (ACK timeout), triggering RERR (Route Error) packets and local repair.
    - **Buffering:** Packets are buffered at the source while waiting for route discovery.

### 4.4 Mobility Models
Defines how UAVs move in the 3D space.
- **3D Random Waypoint:** Nodes select random destinations within the $600 \times 600 \times 100$ m volume, move at constant speed, pause, and repeat.
- **Leader-Follower Formation:** A designated leader follows a path (e.g., RWP), while follower nodes maintain fixed relative offsets (e.g., V-formation).
- **Dynamic Switching:** The simulator supports switching mobility models mid-run (e.g., at $t=300s$) to test protocol adaptability.

---

## 5. Running Experiments

The `experiment_runner.py` script automates the execution of predefined scenarios.

### E1: Mobility vs. Latency
- **Goal:** Analyze how UAV speed impacts network latency.
- **Setup:** 25 nodes, speeds varying from 0 to 50 m/s.
- **Expectation:** Higher speeds cause more frequent link breaks, increasing latency due to route rediscovery delays.

### E2: Energy-Throughput Tradeoff
- **Goal:** Evaluate the energy cost of high network load.
- **Setup:** Static topology, varying packet generation rates (1-50 packets/s).
- **Expectation:** Higher throughput increases energy consumption linearly until saturation.

### E3: Formation Transition
- **Goal:** Assess network stability during topology changes.
- **Setup:** Switch from Random Waypoint to Formation flight at $t=300s$.
- **Metrics:** Monitor PDR dip and recovery time during the transition phase.

---

## 6. Statement of Work

This project was collaboratively developed by a team of 10 members. The responsibilities were divided to ensure coverage of all system components, from low-level physical modeling to high-level application GUI and analysis.

| **Member Name** | **Role** | **Primary Contributions** |
| :--- | :--- | :--- |
| [Name 1] | **Project Lead & Architect** | System architecture design, core event engine (SimPy) integration, overall project management. |
| [Name 2] | **PHY Layer Lead** | Implementation of Channel models (Path Loss, Fading) and SINR calculations. |
| [Name 3] | **Energy Model Specialist** | Development of the Energy Consumption Model (Flight + Comm power) and battery state logic. |
| [Name 4] | **MAC Layer Developer** | Implementation of CSMA/CA protocol, Backoff logic, and ACK/Retransmission mechanisms. |
| [Name 5] | **Network Layer Lead** | Implementation of AODV Routing Protocol (RREQ, RREP, RERR handling) and routing tables. |
| [Name 6] | **Mobility Model Developer** | Implementation of 3D Random Waypoint and Leader-Follower formation logic. |
| [Name 7] | **GUI & Visualization** | Development of the PyQt6/OpenGL 3D visualization, rendering pipeline, and interactive controls. |
| [Name 8] | **Data Analysis & Metrics** | Implementation of the statistics collection system, real-time plotting, and CSV/PNG export features. |
| [Name 9] | **Experiment Runner** | Creation of `experiment_runner.py`, automation of E1/E2/E3 scenarios, and result aggregation. |
| [Name 10] | **QA & Documentation** | Comprehensive testing, bug tracking, and compilation of the User Manual and Design Document. |

---

## 7. References

[1] Z. Zhou et al., "UavNetSim-v1: A Python-based Simulation Platform for UAV Communication Networks," *arXiv preprint arXiv:2507.09852*, 2025.

[2] C. Perkins, E. Belding-Royer, and S. Das, "Ad hoc On-Demand Distance Vector (AODV) Routing," RFC 3561, 2003.

[3] Y. Zeng, J. Xu, and R. Zhang, "Energy Minimization for Wireless Communication with Rotary-Wing UAV," *IEEE Transactions on Wireless Communications*, vol. 18, no. 4, pp. 2329-2345, 2019.

[4] IEEE Standard for Information technology—Telecommunications and information exchange between systems Local and metropolitan area networks—Specific requirements - Part 11: Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications, *IEEE Std 802.11-2016*.
