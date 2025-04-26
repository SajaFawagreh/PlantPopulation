# Plant Population - Cell DEVS Model

## Introduction
This repository presents a **Cell-DEVS Plant Population model** that simulates tree growth, competition, and reproduction under limited environmental resources such as **water**, **nitrogen**, **potassium**, and **sunlight**.

The model is based on the paper *“Simulation of Vegetable Population Dynamics Based on Cellular Automata”* by **Stefania Bandini** and **Giulio Pavesi**, and is implemented using the Cadmium DEVS framework. It captures ecological processes like resource diffusion, growth thresholds, and tree dispersal through localized cell interactions and event-driven updates.

The system is structured using **atomic** and **coupled DEVS models**, ensuring a modular, scalable, and realistic simulation of plant dynamics.

## Cloning the Repository
To download this project, run the following command in your Ubuntu terminal:

```bash
git clone https://github.com/SajaFawagreh/PlantPopulation.git
```

Then navigate into the cloned directory:

```bash
cd PlantPopulation
```

From there, you can choose between the basic or advanced versions of the simulation as described below.

## Repository Structure
This repository is arranged in the following manner:

```sh
.
├── basic/                                # Basic model (no QGIS)
├── advanced/                             # Advanced model (QGIS-integrated)
├── .gitignore                            # Git ignore file
├── Plant_Population-Cell_DEVS_Model.pdf  # Final project report detailing model design, implementation, and results
└── README.md                             # Project documentation
```

## Choosing a Version
This project includes two versions of the simulation:

- `basic/` – A standalone version that runs the full model and outputs logs viewable using the [Cell-DEVS Web Viewer](https://devssim.carleton.ca/cell-devs-viewer/).

- `advanced/` – A QGIS-integrated version that extracts information from real-world maps to automatically generate the configuration file for the simulation.

To get started:

Navigate to the version you want using the following command in the terminal:

- Basic Version:
    ```bash
    cd basic
    ```

- Advanced Version:
    ```bash
    cd advanced
    ```

**Please refer to the README inside each folder for detailed instructions on how to simulate the plant population.**

## Dependencies
This project is designed to run on a **Linux-based environment (e.g., Ubuntu)** and assumes that you have **Cadmium** installed in a location accessible by the environment variable `$CADMIUM`.

_This dependency is typically met by default if you are using the DEVSsim servers._

To verify that Cadmium is set up properly, run the following command in your terminal:

```bash
echo $CADMIUM
```