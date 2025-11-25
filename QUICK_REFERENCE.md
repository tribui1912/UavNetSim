# UavNetSim Quick Reference Card

## 🚀 Quick Start

### Run Main Simulation with GUI
```bash
uv run main.py
```

### Run All Tests
```bash
uv run tests/run_all_tests.py
```

### Run All Experiments
```bash
uv run experiment_runner.py
```
⏱️ Takes 20-35 minutes

---

## 📋 Test Commands

```bash
# All tests (GUI skipped)
uv run tests/run_all_tests.py

# All tests including GUI
uv run tests/run_all_tests.py --include-gui

# Individual tests
uv run tests/test_sanity.py               # ~3 seconds
uv run tests/test_formation_logic.py      # ~35 seconds
uv run tests/test_gui.py                  # ~1 second
```

---

## 🔬 Experiment Commands

```bash
# Run all three experiments
uv run experiment_runner.py

# Run individual experiments (in Python)
uv run python
>>> from experiment_runner import run_experiment_1_mobility_vs_latency
>>> run_experiment_1_mobility_vs_latency()
```

**Experiments:**
1. **Mobility vs Latency** (~5-10 min) → `experiment_1_mobility_vs_latency.csv`
2. **Energy-Throughput** (~5-10 min) → `experiment_2_energy_throughput.csv`
3. **Formation Transition** (~10-15 min) → `experiment_3_formation_transition.csv`

---

## ⚙️ Key Configuration (utils/config.py)

```python
SIM_TIME = 30 * 1e6                    # Simulation time (microseconds)
NUMBER_OF_DRONES = 10                   # Number of drones
DEFAULT_SPEED = 10                      # Speed (m/s)
PACKET_GENERATION_RATE = 5             # Packets per second
INITIAL_ENERGY = 20 * 1e3              # Battery (Joules)
DATA_LOSS_PROBABILITY = 0.05           # 5% packet loss
```

---

## 📁 Project Structure

```
UavNetSim/
├── main.py                    # Main simulation with GUI
├── experiment_runner.py       # Automated experiments
├── tests/
│   ├── run_all_tests.py      # Master test runner
│   ├── test_sanity.py        # Basic functionality
│   ├── test_formation_logic.py # Formation switching
│   └── test_gui.py           # GUI initialization
├── simulator/                 # Core simulation
├── routing/
│   └── aodv/                 # AODV routing protocol
├── mac/                      # MAC layer (CSMA/CA)
├── mobility/                 # Mobility models
└── visualization/            # GUI components
```

---

## 🎯 Common Tasks

### Change Number of Drones
Edit `utils/config.py`:
```python
NUMBER_OF_DRONES = 20  # Default: 10
```

### Change Simulation Duration
```python
SIM_TIME = 60 * 1e6  # 60 seconds (in microseconds)
```

### Change Drone Speed
```python
DEFAULT_SPEED = 15  # 15 m/s (default: 10)
```

### Increase Battery Life
```python
INITIAL_ENERGY = 700 * 1e3  # 700 kJ (default: 20 kJ)
```

### Change Packet Generation Rate
```python
PACKET_GENERATION_RATE = 10  # 10 pkts/s (default: 5)
```

---

## 📊 Output Files

### Test Results
- Console output only (no files generated)

### Experiment Results
- `experiment_1_mobility_vs_latency.csv`
- `experiment_2_energy_throughput.csv`
- `experiment_3_formation_transition.csv`

### Logs
- `running_log.log` - Simulation events
- `pyqt_gui_debug.log` - GUI debug info

---

## 🐛 Troubleshooting

### Tests Fail
```bash
# Check if dependencies are installed
uv run python -c "import simpy; import numpy; print('OK')"

# Re-run specific test with more info
uv run tests/test_sanity.py
```

### Experiment Runner Fails (ModuleNotFoundError)
```bash
# Install missing dependencies
uv pip install -r requirements.txt

# Verify pandas is installed
uv run python -c "import pandas; print('pandas OK')"
```

### Experiments Too Slow
Reduce simulation time in `experiment_runner.py`:
```python
config.SIM_TIME = 10 * 1e6  # 10 seconds instead of 50
```

### GUI Won't Start
```bash
# Check PyQt6 installation
uv run python -c "from PyQt6 import QtWidgets; print('PyQt6 OK')"

# Try matplotlib GUI instead
# Edit main.py, set: GUI_MODE = 'matplotlib'
```

### Out of Energy Too Fast
Increase battery or reduce simulation time:
```python
INITIAL_ENERGY = 200 * 1e3  # 200 kJ
# or
SIM_TIME = 5 * 1e6  # 5 seconds
```

---

## ✅ Verification Checklist

After setup, verify everything works:

```bash
☐ uv run tests/run_all_tests.py       # Both tests should pass
☐ uv run main.py                      # GUI should open
```

---

## 💡 Tips

- Use `--include-gui` flag only when you need to test GUI
- Run experiments overnight for longer simulations
- Start with short simulations (10-20s) for testing
- Check CSV files with: `head experiment_1_mobility_vs_latency.csv`
- Monitor energy: Lower speeds = longer flight time
- PDR < 50%? Reduce packet rate or increase speed

---

**Python:** 3.12+  
**Dependencies:** See `requirements.txt`

