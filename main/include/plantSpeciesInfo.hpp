#ifndef PLANT_SPECIES_INFO_HPP
#define PLANT_SPECIES_INFO_HPP

#include "plantResources.hpp"
#include "plantPopulationState.hpp"
#include <map>

struct SpeciesInfo {
    plantResources max_resources;
    plantResources produced_resources;
    plantResources req_to_survive;
    plantResources req_to_grow;
};

const std::map<treeSpecies, SpeciesInfo> speciesInfoMap = {
    {treeSpecies::None,   SpeciesInfo(plantResources(30, 30, 15, 15), plantResources(5, 5, 3, 2), plantResources(3, 3, 2, 1), plantResources(8, 7, 4, 3))},
    {treeSpecies::Locust, SpeciesInfo(plantResources(30, 30, 15, 15), plantResources(5, 5, 3, 2), plantResources(3, 3, 2, 1), plantResources(8, 7, 4, 3))},
    {treeSpecies::Pine,   SpeciesInfo(plantResources(30, 30, 15, 15), plantResources(5, 5, 3, 2), plantResources(3, 3, 2, 1), plantResources(8, 7, 4, 3))},
    {treeSpecies::Oak,    SpeciesInfo(plantResources(30, 30, 15, 15), plantResources(5, 5, 3, 2), plantResources(3, 3, 2, 1), plantResources(8, 7, 4, 3))}
};

#endif // PLANT_SPECIES_INFO_HPP
