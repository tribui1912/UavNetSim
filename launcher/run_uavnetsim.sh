#!/bin/bash
# UavNetSim Launcher for Mac/Linux
# This script provides a menu-driven interface to run tests, simulations, and experiments

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python installation
check_python() {
    echo "[1/3] Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo ""
        echo "Please install Python 3.12+ from:"
        echo "  Mac: brew install python@3.12"
        echo "  Linux: sudo apt install python3.12"
        exit 1
    fi
    python3 --version
    print_success "Python is installed"
    echo ""
}

# Check uv installation
check_uv() {
    echo "[2/3] Checking uv installation..."
    if ! command -v uv &> /dev/null; then
        print_warning "uv is not installed"
        echo ""
        echo "Installing uv..."
        pip3 install uv
        if [ $? -ne 0 ]; then
            print_error "Failed to install uv"
            exit 1
        fi
        print_success "uv installed successfully"
    else
        uv --version
        print_success "uv is installed"
    fi
    echo ""
}

# Check/Create virtual environment
check_venv() {
    echo "[3/3] Checking virtual environment..."
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment..."
        uv venv
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment"
            exit 1
        fi
        print_success "Virtual environment created"
    else
        print_success "Virtual environment exists"
    fi
    echo ""
}

# Check dependencies
check_deps() {
    echo "Checking dependencies..."
    if ! uv pip list | grep -q "simpy"; then
        print_warning "Dependencies not installed"
        echo "Installing dependencies from requirements.txt..."
        uv pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            print_error "Failed to install dependencies"
            exit 1
        fi
        print_success "Dependencies installed"
    else
        print_success "Dependencies are installed"
    fi
    echo ""
}

# Setup function
setup() {
    clear
    print_header "UavNetSim - UAV Network Simulator"
    
    check_python
    check_uv
    check_venv
    check_deps
    
    print_header "Setup complete!"
    sleep 2
}

# Main menu
show_menu() {
    clear
    print_header "UavNetSim - Main Menu"
    
    echo "Please select an option:"
    echo ""
    echo "[1] Run Main Simulation (with GUI)"
    echo "[2] Run All Tests"
    echo "[3] Run Individual Test"
    echo "[4] Run All Experiments (20-35 min)"
    echo "[5] Run Individual Experiment"
    echo "[6] Check System Status"
    echo "[7] Install/Update Dependencies"
    echo "[8] View Quick Reference"
    echo "[9] Exit"
    echo ""
    echo "========================================"
    read -p "Enter your choice (1-9): " choice
    echo ""
    
    case $choice in
        1) run_main ;;
        2) run_all_tests ;;
        3) run_individual_test ;;
        4) run_all_experiments ;;
        5) run_individual_experiment ;;
        6) check_status ;;
        7) install_deps ;;
        8) view_reference ;;
        9) exit_script ;;
        *) 
            print_error "Invalid choice. Please try again."
            sleep 2
            show_menu
            ;;
    esac
}

# Run main simulation
run_main() {
    clear
    print_header "Running Main Simulation"
    
    echo "Starting UavNetSim with GUI..."
    echo "(Press Ctrl+C to stop)"
    echo ""
    
    uv run main.py
    
    echo ""
    echo "Simulation ended."
    read -p "Press Enter to continue..."
    show_menu
}

# Run all tests
run_all_tests() {
    clear
    print_header "Running All Tests"
    
    uv run tests/run_all_tests.py
    
    echo ""
    echo "Tests completed."
    read -p "Press Enter to continue..."
    show_menu
}

# Run individual test
run_individual_test() {
    clear
    print_header "Run Individual Test"
    
    echo "[1] Sanity Test (~3 seconds)"
    echo "[2] Formation Logic Test (~35 seconds)"
    echo "[3] GUI Test (~1 second)"
    echo "[4] Back to Main Menu"
    echo ""
    read -p "Select test (1-4): " test_choice
    echo ""
    
    case $test_choice in
        1)
            echo "Running Sanity Test..."
            uv run tests/test_sanity.py
            ;;
        2)
            echo "Running Formation Logic Test..."
            uv run tests/test_formation_logic.py
            ;;
        3)
            echo "Running GUI Test..."
            uv run tests/test_gui.py
            ;;
        4)
            show_menu
            return
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    show_menu
}

# Run all experiments
run_all_experiments() {
    clear
    print_header "Running All Experiments"
    
    echo "WARNING: This will take 20-35 minutes!"
    echo ""
    echo "Experiments to run:"
    echo "  1. Mobility vs Latency (~5-10 min)"
    echo "  2. Energy-Throughput (~5-10 min)"
    echo "  3. Formation Transition (~10-15 min)"
    echo ""
    read -p "Continue? (y/N): " confirm
    
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        show_menu
        return
    fi
    
    echo ""
    echo "Starting experiments..."
    echo "Results will be saved as CSV files."
    echo ""
    
    uv run experiment_runner.py
    
    echo ""
    print_header "Experiments completed!"
    echo ""
    echo "Output files:"
    echo "  - experiment_1_mobility_vs_latency.csv"
    echo "  - experiment_2_energy_throughput.csv"
    echo "  - experiment_3_formation_transition.csv"
    echo ""
    read -p "Press Enter to continue..."
    show_menu
}

# Run individual experiment
run_individual_experiment() {
    clear
    print_header "Run Individual Experiment"
    
    echo "[1] Experiment 1: Mobility vs Latency (~5-10 min)"
    echo "[2] Experiment 2: Energy-Throughput (~5-10 min)"
    echo "[3] Experiment 3: Formation Transition (~10-15 min)"
    echo "[4] Back to Main Menu"
    echo ""
    read -p "Select experiment (1-4): " exp_choice
    echo ""
    
    case $exp_choice in
        1)
            echo "Running Experiment 1: Mobility vs Latency..."
            uv run python -c "from experiment_runner import run_experiment_1_mobility_vs_latency; run_experiment_1_mobility_vs_latency()"
            echo ""
            echo "Results saved to: experiment_1_mobility_vs_latency.csv"
            ;;
        2)
            echo "Running Experiment 2: Energy-Throughput..."
            uv run python -c "from experiment_runner import run_experiment_2_energy_throughput; run_experiment_2_energy_throughput()"
            echo ""
            echo "Results saved to: experiment_2_energy_throughput.csv"
            ;;
        3)
            echo "Running Experiment 3: Formation Transition..."
            uv run python -c "from experiment_runner import run_experiment_3_formation_transition; run_experiment_3_formation_transition()"
            echo ""
            echo "Results saved to: experiment_3_formation_transition.csv"
            ;;
        4)
            show_menu
            return
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    show_menu
}

# Check system status
check_status() {
    clear
    print_header "System Status Check"
    
    echo "Python Version:"
    python3 --version
    echo ""
    
    echo "uv Version:"
    uv --version
    echo ""
    
    echo "Virtual Environment:"
    if [ -d ".venv" ]; then
        print_success "Virtual environment exists at .venv"
    else
        print_warning "Virtual environment not found"
    fi
    echo ""
    
    echo "Installed Packages:"
    echo "--------------------"
    uv pip list
    echo ""
    
    echo "Configuration:"
    echo "--------------------"
    echo "Project Directory: $(pwd)"
    echo "OS: $(uname -s)"
    echo ""
    
    read -p "Press Enter to continue..."
    show_menu
}

# Install/Update dependencies
install_deps() {
    clear
    print_header "Install/Update Dependencies"
    
    echo "Installing dependencies from requirements.txt..."
    echo ""
    
    uv pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo ""
        print_success "Dependencies installed successfully"
    else
        echo ""
        print_error "Failed to install dependencies"
    fi
    
    echo ""
    read -p "Press Enter to continue..."
    show_menu
}

# View quick reference
view_reference() {
    clear
    print_header "Quick Reference"
    
    if [ -f "QUICK_REFERENCE.md" ]; then
        less QUICK_REFERENCE.md
    else
        echo "QUICK_REFERENCE.md not found"
        echo ""
        echo "Key Commands:"
        echo "  - Run simulation: uv run main.py"
        echo "  - Run tests: uv run tests/run_all_tests.py"
        echo "  - Run experiments: uv run experiment_runner.py"
    fi
    
    echo ""
    read -p "Press Enter to continue..."
    show_menu
}

# Exit script
exit_script() {
    clear
    print_header "UavNetSim - Goodbye!"
    
    echo "Thank you for using UavNetSim"
    echo ""
    sleep 1
    exit 0
}

# Main execution
cd "$(dirname "$0")/.."  # Go to project root
setup
show_menu

