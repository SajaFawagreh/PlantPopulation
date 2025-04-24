#ifndef PLANT_SPECIES_INFO_HPP
#define PLANT_SPECIES_INFO_HPP

#include "plantResources.hpp"
#include "plantPopulationState.hpp"
#include <map>
#include <vector>

struct SpeciesInfo {
    plantResources max_resources;
    plantResources produced_resources;
    plantResources req_to_survive;
    plantResources req_to_grow;
    std::vector<soilType> growable_soil;
};

const std::map<treeSpecies, SpeciesInfo> speciesInfoMap = {
    {treeSpecies::None,   SpeciesInfo(plantResources(30, 30, 15, 15), plantResources(8, 8, 8, 8), plantResources(0, 0, 0, 0), plantResources(0, 0, 0, 0), {soilType::Dry, soilType::Clay})},
    {treeSpecies::Locust, SpeciesInfo(plantResources(30, 30, 15, 15), plantResources(6, 6, 6, 6), plantResources(2, 2, 1, 1), plantResources(8, 8, 7, 7), {soilType::Dry})},
    {treeSpecies::Pine,   SpeciesInfo(plantResources(30, 30, 15, 15), plantResources(5, 5, 5, 5), plantResources(2, 2, 2, 2), plantResources(7, 7, 7, 7), {soilType::Dry, soilType::Clay})},
    {treeSpecies::Oak,    SpeciesInfo(plantResources(30, 30, 15, 15), plantResources(4, 4, 4, 4), plantResources(3, 3, 2, 2), plantResources(9, 9, 8, 8), {soilType::Clay})},
    {treeSpecies::Water,  SpeciesInfo(plantResources(30, 0, 0, 0),    plantResources(10, 0, 0, 0), plantResources(0, 0, 0, 0), plantResources(0, 0, 0, 0), {})}
};

#endif // PLANT_SPECIES_INFO_HPP
