#include "nlohmann/json.hpp"
#include <cadmium/modeling/celldevs/grid/coupled.hpp>
#include <cadmium/simulation/logger/csv.hpp>
#include <cadmium/simulation/root_coordinator.hpp>
#include <chrono>
#include <fstream>
#include <string>
#include <filesystem>
#include "include/plantPopulationCell.hpp"

using namespace cadmium::celldevs;
using namespace cadmium;
namespace fs = std::filesystem;

std::shared_ptr<GridCell<plantPopulationState, double>> addGridCell(const coordinates & cellId, const std::shared_ptr<const GridCellConfig<plantPopulationState, double>>& cellConfig) {
	auto cellModel = cellConfig->cellModel;

	if (cellModel == "plant_population") {
		return std::make_shared<plantPopulation>(cellId, cellConfig);
	} else {
		throw std::bad_typeid();
	}
}

int main(int argc, char ** argv) {
	if (argc < 2) {
		std::cout << "Program used with wrong parameters. The program must be invoked as follows:" << std::endl;
		std::cout << argv[0] << " SCENARIO_CONFIG.json [MAX_SIMULATION_TIME (default: 200)]" << std::endl;
		return -1;
	}

	std::string configFilePath = argv[1];
	double simTime = (argc > 2) ? std::stod(argv[2]) : 200;

	// Define log file paths
	std::string gridLogPath = "log_files/grid_log.csv";
	std::string visLogPath = "log_files/grid_visualization_log.csv";

	auto model = std::make_shared<GridCellDEVSCoupled<plantPopulationState, double>>("plantPopulation", addGridCell, configFilePath);
	model->buildModel();

	auto rootCoordinator = RootCoordinator(model);

	// Choose logger based on config type
	if (configFilePath.find("visualization") != std::string::npos) {
		rootCoordinator.setLogger<CSVLogger>(visLogPath, ";");
	} else {
		rootCoordinator.setLogger<CSVLogger>(gridLogPath, ";");
	}

	rootCoordinator.start();
	rootCoordinator.simulate(simTime);
	rootCoordinator.stop();
}
