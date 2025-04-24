#ifndef PLANT_RESOURCES_HPP
#define PLANT_RESOURCES_HPP

#include <iostream>
#include <nlohmann/json.hpp>

struct plantResources {
	uint water;
	uint sunlight;
	uint nitrogen;
	uint potassium;

	plantResources() : water(0), sunlight(0), nitrogen(0), potassium(0) {}
	
	// Constructor for easy initialization
    plantResources(uint w, uint s, uint n, uint p) : water(w), sunlight(s), nitrogen(n), potassium(p) {}

};

//! It prints the life of the cell in an output stream.
std::ostream& operator<<(std::ostream& os, const plantResources& x) {
	os << "<" << x.water << "," << x.sunlight << "," << x.nitrogen << "," << x.potassium << ">";
	return os;
}

//! The simulator must be able to compare the equality of two state objects
bool operator!=(const plantResources& x, const plantResources& y) {
	return (x.water != y.water) ||
            (x.sunlight != y.sunlight) ||
            (x.nitrogen != y.nitrogen) ||
            (x.potassium != y.potassium);
}

//! It parses a JSON file and generates the corresponding plantResources object.
void from_json(const nlohmann::json& j, plantResources& s) {
	j.at("water").get_to(s.water);
    j.at("sunlight").get_to(s.sunlight);
    j.at("nitrogen").get_to(s.nitrogen);
    j.at("potassium").get_to(s.potassium);
}


#endif