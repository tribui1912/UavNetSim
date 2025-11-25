# UavNetSim Test Suite

This folder contains all test files for the UavNetSim project.

## Quick Start

**Run all tests (GUI skipped by default):**
```bash
uv run tests/run_all_tests.py
```

**Run all tests including GUI:**
```bash
uv run tests/run_all_tests.py --include-gui
```

> **Note:** GUI test is skipped by default to avoid popping up matplotlib windows during automated testing.

## Test Files

### `test_sanity.py`
Basic sanity check to ensure the simulation can start and run without crashing.

**What it tests:**
- Simulation initialization
- Basic packet generation and transmission
- MAC layer functionality
- Metrics collection

**Run:**
```bash
uv run tests/test_sanity.py
```

**Expected output:**
- Simulation runs for 0.5 seconds
- Reports PDR, latency, throughput
- Prints "Sanity Check Passed"

---

### `test_formation_logic.py`
Tests the leader-follower formation switching functionality.

**What it tests:**
- Formation change trigger
- Drones switching to LeaderFollower mobility model
- Target position assignment
- Convergence towards target positions

**Run:**
```bash
uv run tests/test_formation_logic.py
```

**Expected output:**
- Formation change triggered at 2s
- All drones switch to follower mode (except leader)
- Drones move towards target positions
- Prints "TEST PASSED"

---

### `test_gui.py`
Tests GUI visualization components initialization.

**What it tests:**
- LiveVisualizer initialization
- Matplotlib figure creation
- No crashes during GUI setup

**Run:**
```bash
uv run tests/test_gui.py
```

**Expected output:**
- LiveVisualizer initializes successfully
- Prints "Test Complete"

---

## Running All Tests

### Option 1: Using Test Runner (Recommended)

Run all tests at once with the master test runner:

```bash
# Run core tests (GUI skipped by default)
uv run tests/run_all_tests.py

# Include GUI test (may pop up windows)
uv run tests/run_all_tests.py --include-gui

# Show help
uv run tests/run_all_tests.py --help
```

This will:
- Run all tests sequentially
- Show timing for each test
- Display a summary with pass/fail counts
- Return appropriate exit code (0 = all passed, 1 = some failed)
- Skip GUI test by default (use `--include-gui` to run it)

### Option 2: Run Individual Tests

```bash
# Sanity test
uv run tests/test_sanity.py

# Formation test
uv run tests/test_formation_logic.py

# GUI test
uv run tests/test_gui.py
```

### Option 3: Using pytest (Advanced)

If you have pytest installed:

```bash
# Run all tests with pytest
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_sanity.py
```

## Test Status

✅ All tests passing as of implementation completion
- test_sanity.py: PASSING
- test_formation_logic.py: PASSING  
- test_gui.py: WORKING

## Notes

- Tests automatically add project root to Python path
- Logging is configured differently per test
- Tests use fixed seeds for reproducibility
- Short simulation times for fast execution

