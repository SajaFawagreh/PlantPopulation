#ifndef PLANT_POPULATION_CELL_HPP
#define PLANT_POPULATION_CELL_HPP

#include <cmath>
#include <nlohmann/json.hpp>
#include <cadmium/modeling/celldevs/asymm/cell.hpp>
#include <cadmium/modeling/celldevs/asymm/config.hpp>
#include "plantPopulationState.hpp"
#include "plantSpeciesInfo.hpp"

using namespace cadmium::celldevs;

//! Plant population cell.
class plantPopulation : public AsymmCell<plantPopulationState, double> {
	public:
	plantPopulation(const std::string& id, 
			const std::shared_ptr<const AsymmCellConfig<plantPopulationState, double>>& config
		  ): AsymmCell<plantPopulationState, double>(id, config) { }

	[[nodiscard]] plantPopulationState localComputation(plantPopulationState state,
		const std::unordered_map<std::string, NeighborData<plantPopulationState, double>>& neighborhood) const override 
	{
		treeSpecies best_seed = treeSpecies::None;

		for (const auto& [neighborId, neighborData]: neighborhood) {
			auto nStateResources = neighborData.state->current_resources;

			// Calculation for dispersing resources from higher concentrations to lower concentrations
			// (Based off of calculation from Oil Spill Model shown in class)

			// If either the current cell OR the neighbor is water → only spread/take water
			if (state.tree_type == treeSpecies::Water || neighborData.state->tree_type == treeSpecies::Water) {
				// Only spread/take water
				state.current_resources.water += 
					0.25 * (nStateResources.water - state.current_resources.water);
			} else {
				// Spread/take all resources
				state.current_resources.water += 
					0.25 * (nStateResources.water - state.current_resources.water);
				state.current_resources.sunlight += 
					0.25 * (nStateResources.sunlight - state.current_resources.sunlight);
				state.current_resources.nitrogen += 
					0.25 * (nStateResources.nitrogen - state.current_resources.nitrogen);
				state.current_resources.potassium += 
					0.25 * (nStateResources.potassium - state.current_resources.potassium);
			}

			// Does this cell already have a tree? (if not, seed can spread from neighbors)
			if (treeSpecies::None == state.tree_type) {
				uint32_t best_elevation = std::numeric_limits<uint32_t>::max();  // track lowest elevation
				for (const auto& [neighborId, neighborData]: neighborhood) {
					auto& neighborState = *neighborData.state;

					// Is neighboring tree tall enough to spread seed?
					bool canSpread = 
						(neighborState.tree_type == treeSpecies::Locust && neighborState.tree_height >= 8) ||
						(neighborState.tree_type == treeSpecies::Pine && neighborState.tree_height >= 12) ||
						(neighborState.tree_type == treeSpecies::Oak && neighborState.tree_height >= 20);

					// Check if the species can grow in current soil
					bool canGrowInSoil = false;
					if (canSpread) {
						const auto& speciesInfo = speciesInfoMap.at(neighborState.tree_type);
						const auto& allowedSoils = speciesInfo.growable_soil;
						canGrowInSoil = std::find(allowedSoils.begin(), allowedSoils.end(), state.soil_type) != allowedSoils.end();
					}

					if (canSpread && canGrowInSoil) {
						uint32_t elev = neighborState.elevation;
						if (elev < best_elevation) {
							best_elevation = elev;
							best_seed = neighborState.tree_type;
						} else if (elev == best_elevation) {
							// If same elevation, choose stronger species
							best_seed = (treeSpecies)std::max((int)best_seed, (int)neighborState.tree_type);
						}
					}
				}
			}
		}

		auto species = speciesInfoMap.at(state.tree_type);
		state.max_resources = species.max_resources;
		state.produced_resources = species.produced_resources;
		state.req_to_survive = species.req_to_survive;
		state.req_to_grow = species.req_to_grow;

		// Cell produces its own resources
		state.current_resources.water += state.produced_resources.water;
		state.current_resources.sunlight += state.produced_resources.sunlight;
		state.current_resources.nitrogen += state.produced_resources.nitrogen;
		state.current_resources.potassium += state.produced_resources.potassium;

		// Apply maximum resource rule
		state.current_resources.water = 
			std::min(state.current_resources.water, state.max_resources.water);
		state.current_resources.sunlight = 
			std::min(state.current_resources.sunlight, state.max_resources.sunlight);
		state.current_resources.nitrogen = 
			std::min(state.current_resources.nitrogen, state.max_resources.nitrogen);
		state.current_resources.potassium = 
			std::min(state.current_resources.potassium, state.max_resources.potassium);
			
		if (state.tree_type != treeSpecies::Water) {
			// Plant seed if there is not already on in the cell
			if (treeSpecies::None == state.tree_type) {
				state.tree_type = best_seed;
			} else {
				// Does tree lack enough of any one resource in order to survive?
				if ((state.req_to_survive.water > state.current_resources.water) ||
					(state.req_to_survive.sunlight > state.current_resources.sunlight) ||
					(state.req_to_survive.nitrogen > state.current_resources.nitrogen) ||
					(state.req_to_survive.potassium > state.current_resources.potassium))
				{
					// Dead tree become available for new seeds to spread again
					state.tree_height = 0;
					state.tree_type = treeSpecies::None;
				} 
				// Is tree at max height for species?
				else if (((treeSpecies::Locust == state.tree_type) &&
							(40 > state.tree_height)) ||
							((treeSpecies::Pine == state.tree_type) &&
							(55 > state.tree_height)) ||
							((treeSpecies::Oak == state.tree_type) &&
							(70 > state.tree_height)))
				{
					// Does tree have enough resources to grow?
					if ((state.req_to_grow.water <= state.current_resources.water) &&
						(state.req_to_grow.sunlight <= state.current_resources.sunlight) &&
						(state.req_to_grow.nitrogen <= state.current_resources.nitrogen) &&
						(state.req_to_grow.potassium <= state.current_resources.potassium))
					{
						// Consume resources required to grow then increase height
						state.current_resources.water = 
							state.current_resources.water - state.req_to_grow.water;
						state.current_resources.sunlight = 
							state.current_resources.sunlight - state.req_to_grow.sunlight;
						state.current_resources.nitrogen = 
							state.current_resources.nitrogen - state.req_to_grow.nitrogen;
						state.current_resources.potassium = 
							state.current_resources.potassium - state.req_to_grow.potassium;
					
						state.tree_height++;
					}
				}
				else {
					// Consume resources needed to survive
					state.current_resources.water = 
						state.current_resources.water - state.req_to_survive.water;
					state.current_resources.sunlight = 
						state.current_resources.sunlight - state.req_to_survive.sunlight;
					state.current_resources.nitrogen = 
						state.current_resources.nitrogen - state.req_to_survive.nitrogen;
					state.current_resources.potassium = 
						state.current_resources.potassium - state.req_to_survive.potassium;
				}
			}
		}

		return state;
	}

	[[nodiscard]] double outputDelay(const plantPopulationState& state) const override {
		return 1.;
	}
};

#endif //PLANT_POPULATION_CELL_HPP
