# Plant Population - Cell DEVS Model

## Introduction
This repository presents a **Cell-DEVS Plant Population model** that simulates tree growth, competition, and reproduction under limited environmental resources such as **water**, **nitrogen**, **potassium**, and **sunlight**.

The model is based on the paper *“Simulation of Vegetable Population Dynamics Based on Cellular Automata”* by **Stefania Bandini** and **Giulio Pavesi**, and is implemented using the Cadmium DEVS framework. It captures ecological processes like resource diffusion, growth thresholds, and tree dispersal through localized cell interactions and event-driven updates.

The system is structured using **atomic** and **coupled DEVS models**, ensuring a modular, scalable, and realistic simulation of plant dynamics.

## Repository Structure
This repository is arranged in the following manner:

```sh
.
├── config/                             # Configuration files for each test scenario
│   ├── initialTest/
│   │   ├── plant_population_config.json
│   │   └── plant_population_visualization_config.json
│   ├── test1/
│   │   ├── plant_population_config.json
│   │   └── plant_population_visualization_config.json
│   ├── test2/
│   │   ├── plant_population_config.json
│   │   └── plant_population_visualization_config.json
├── log_files/                          # Output CSV logs generated after simulation
│   ├── initialTest/
│   │   ├── grid_log.csv
│   │   └── grid_visualization_log.csv
│   ├── test1/
│   │   ├── grid_log.csv
│   │   └── grid_visualization_log.csv
│   └── test2/
│       ├── grid_log.csv
│       └── grid_visualization_log.csv
├── main/                               # Source code directory
│   ├── include/                        # Header files for the model
│   │   ├── plantPopulationCell.hpp     # Defines cell behavior and resource-based state updates
│   │   ├── plantPopulationState.hpp    # Defines cell state: resources, tree type, and height
│   │   └── plantResources.hpp          # Defines and compares cell resources (water, sunlight, nitrogen, potassium)
│   ├── main.cpp                        # Main file to simulate the full system
│   └── CMakeLists.txt                  # CMake configuration for the main directory
├── simulation_videos/                  # WebM simulation outputs for each test
│   ├── initialTest.webm
│   ├── test1.webm
│   └── test2.webm
├── build_sim.sh                        # Build script for Cadmium simulation
├── CMakeLists.txt                      # Root-level CMake configuration
├── .gitignore                          # Git ignore file
└── README.md                           # Project documentation
```

## System Components (Atomic and Coupled Models)

This project includes one **atomic model** that defines the behavior of each plant cell, and a **coupled model** automatically generated using Cadmium’s Grid Cell-DEVS infrastructure to simulate interactions across the grid.

### **1. plantPopulation (Atomic Cell-DEVS)**  
**File:** [`plantPopulationCell.hpp`](main/include/plantPopulationCell.hpp)  

The **plantPopulation** atomic model defines the local behavior of each cell. At every simulation step, each cell:
- Exchanges **water**, **sunlight**, **nitrogen**, and **potassium** with neighboring cells through diffusion.
- Produces its own resources.
- Determines whether to **survive** or **grow** based on resource thresholds.
- Increments tree height or dies based on environmental conditions.

---

### **2. Grid Coupled Model**  
**Constructed in:** [`main.cpp`](main/main.cpp)
  
**Type:** `GridCellDEVSCoupled<plantPopulationState, double>`

The **Grid Coupled Model** automatically connects a grid of `plantPopulation` atomic models using the **Von Neumann neighborhood**. Each cell interacts with its neighbors, allowing for realistic spatial dynamics such as:
- Resource distribution across the grid.
- Propagation of tree types.
- Local competition and survival mechanisms.

The coupled model is instantiated from a JSON configuration file and executed using Cadmium’s simulation engine, with outputs logged to either `grid_log.csv` or `grid_visualization_log.csv`, depending on the test scenario.

## Dependencies
This project assumes that you have Cadmium installed in a location accessible by the environment variable $CADMIUM.
_This dependency would be met by default if you are using the DEVSsim servers. To check, try `echo $CADMIUM` in the terminal_

## Build
To build this project, run:
```sh
source build_sim.sh
```

__NOTE__: Everytime you run build_sim.sh, the contents of `build/` and `bin/` will be replaced.


## **Main Simulation Files**  

This section contains the main file used to execute and test the **Plant Population Simulation**. The simulation is configured using different test scenarios, each defined in its own configuration folder.  

### **Main Simulation File**  
**File:** [main.cpp](main/main.cpp)  

This file initializes and runs the **Plant Population Model** using **Cadmium**. It loads the configuration file specified at runtime and simulates the evolution of tree populations based on resource availability and defined rules.  

### **Running a Test**  

To run a specific test scenario, use the following command:  

```bash
./bin/plant_population config/<test_name>/plant_population_config.json
```

Examples:  
```bash
./bin/plant_population config/initialTest/plant_population_config.json  
./bin/plant_population config/test1/plant_population_config.json  
./bin/plant_population config/test2/plant_population_config.json  
```

This will generate log files in the corresponding `log_files/<test_name>/` directory.

### **Visualizing the Simulation**  

To run a simulation specifically for visualization (e.g., to produce logs formatted for graphical output), use the visualization config instead:  

```bash
./bin/plant_population config/<test_name>/plant_population_visualization_config.json
```

Examples:  
```bash
./bin/plant_population config/initialTest/plant_population_visualization_config.json
./bin/plant_population config/test1/plant_population_visualization_config.json
./bin/plant_population config/test2/plant_population_visualization_config.json
```

This will generate `grid_visualization_log.csv` under `log_files/<test_name>/`, which can be used with your visualization tools.
