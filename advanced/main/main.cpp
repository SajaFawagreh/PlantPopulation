#include "nlohmann/json.hpp"
#include <cadmium/modeling/celldevs/asymm/coupled.hpp>
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

std::shared_ptr<AsymmCell<plantPopulationState, double>> addCell(const std::string & cellId, const std::shared_ptr<const AsymmCellConfig<plantPopulationState, double>>& cellConfig) {
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
		std::cout << argv[0] << " SCENARIO_CONFIG.json RESULTS.CSV" << std::endl;
		return -1;
	}

	std::string configFilePath = argv[1];
	double simTime = (argc > 2) ? std::stod(argv[2]) : 200;

	// Define log file paths
	std::string mapLogPath = "log_files/map_log.csv";

	auto model = std::make_shared<AsymmCellDEVSCoupled<plantPopulationState, double>>("plantPopulation", addCell, configFilePath);
	model->buildModel();
	
	auto rootCoordinator = RootCoordinator(model);

	rootCoordinator.setLogger<CSVLogger>(mapLogPath, ";");
	
	rootCoordinator.start();
	rootCoordinator.simulate(simTime);
	rootCoordinator.stop();
}
