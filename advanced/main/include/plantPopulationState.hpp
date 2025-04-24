#ifndef PLANT_POPULATION_STATE_HPP_
#define PLANT_POPULATION_STATE_HPP_

#include <iostream>
#include <nlohmann/json.hpp>
#include "plantResources.hpp"

enum class treeSpecies {
	None = 0,
	Locust = 1,
	Pine = 2,
	Oak = 3,
	Water = 4,
};

enum class soilType {
	Dry = 0,
	Clay = 1,
	Water = 2,
};

std::ostream& operator<<(std::ostream& os, const treeSpecies& x) {
	os << (uint32_t)x;
	return os;
}

std::ostream& operator<<(std::ostream& os, const soilType& x) {
	os << (uint32_t)x;
	return os;
}

//! Plant population cell state.
struct plantPopulationState {
	plantResources current_resources;
	plantResources max_resources;
	plantResources produced_resources;
	plantResources req_to_survive;
	plantResources req_to_grow;
	uint32_t tree_height;
	soilType soil_type;
	uint32_t elevation;
	treeSpecies tree_type;

	//! Default constructor function.
	plantPopulationState() : current_resources(),
							 max_resources(), 
							 produced_resources(),
							 req_to_survive(),
							 req_to_grow(), 
							 tree_height(0),
							 soil_type(soilType::Dry),
							 elevation(0),
							 tree_type(treeSpecies::None) {}   // <- NEW
};

//! It prints the life of the cell in an output stream.
std::ostream& operator<<(std::ostream& os, const plantPopulationState& x) {
	os << "<" << x.current_resources.water << "," 
		<< x.current_resources.sunlight << ","
		<< x.current_resources.nitrogen << "," 
		<< x.current_resources.potassium << "," 
		<< x.tree_height << "," 
		<< x.soil_type << "," 
		<< x.elevation << "," 
		<< x.tree_type << ">";
	return os;
}

//! The simulator must be able to compare the equality of two state objects
bool operator!=(const plantPopulationState& x, const plantPopulationState& y) {
	return (x.current_resources != y.current_resources) ||
			(x.max_resources != y.max_resources) ||
			(x.produced_resources != y.produced_resources) ||
			(x.req_to_survive != y.req_to_survive) ||
			(x.req_to_grow != y.req_to_grow) ||
			(x.tree_height != y.tree_height) ||
			(x.soil_type != y.soil_type) ||
			(x.elevation != y.elevation) ||
			(x.tree_type != y.tree_type);
}

//! It parses a JSON file and generates the corresponding plantPopulationState object.
void from_json(const nlohmann::json& j, plantPopulationState& s) {
	j.at("current_resources").get_to(s.current_resources);
	j.at("tree_height").get_to(s.tree_height);
	j.at("soil_type").get_to(s.soil_type);
	j.at("elevation").get_to(s.elevation);
	j.at("tree_type").get_to(s.tree_type);
}

#endif //PLANT_POPULATION_STATE_HPP_
