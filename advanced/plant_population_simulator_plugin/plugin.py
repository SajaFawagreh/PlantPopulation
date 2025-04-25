from PyQt5.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QComboBox,
    QPushButton,
    QWidget,
    QDockWidget,
    QFileDialog,
    QAction,
    QSlider,
    QMessageBox
)
from PyQt5.QtCore import (
    Qt,
    QVariant
)
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsFields,
    QgsField,
    QgsGeometry,
    QgsWkbTypes,
    QgsFeature,
    QgsProcessingFeedback,
    QgsVectorLayerTemporalProperties,
    QgsDataSourceUri,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsMessageLog,
    Qgis,
    QgsTemporalNavigationObject,
)
from qgis.gui import QgsMapToolIdentifyFeature
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from qgis.PyQt.QtGui import QColor
from pathlib import Path
import json
import os
import processing
import rasterio
import numpy
import math
import subprocess
import threading
import csv

#########################
# CONSTANTS
#########################

FUELS = {
    1: 10,   # temperate or sub-polar needleleaf forest -> FM10
    2: 13,   # sub-polar taiga -> FM13
    5: 9,    # temperate or sub-polar broadleaf deciduous forest -> FM9
    6: 8,    # forest foliage temperate or sub-polar -> FM8
    8: 141,  # temperate or sub-polar shrubland -> SH1
    10: 101, # temperate or sub-polar grassland -> GR1
    11: 93,  # sub-polar or polar shrubland-lichen-moss -> NB3
    12: 103, # sub-polar or polar grassland-lichen-moss -> GR3
    13: 99,  # sub-polar or polar barren-lichen-moss -> NB9
    14: 94,  # wetland -> NB4
    15: 93,  # cropland -> NB3
    16: 99,  # barren lands -> NB9
    17: 91,  # urban -> NB1
    18: 98,  # water -> NB8
    19: 92,  # snow and ice -> NB2
}

# TODO OP landcover map can be used to determine water features (check for 18)

#########################
# PLUGIN CLASSES
#########################

class PPSPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.dock_widget = None
        self.map_tool = None
        self.rubber_band = None
        self.selected_region = None
        self.pine_region = None

    def initGui(self):
        self.action = QAction('Plant Population Simulator', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        if not self.dock_widget:
            self.dock_widget = PPSDockWidget(self)
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)
        self.dock_widget.show()

class PPSDockWidget(QDockWidget):
    def __init__(self, plugin):
        super(PPSDockWidget, self).__init__(plugin.iface.mainWindow())
        self.plugin = plugin
        self.setWindowTitle("Plant Population Simulator")
        self.iface = plugin.iface

        # Initialize resolution with default values
        self.resolution = 50

        # Set up rubber bands
        self.plugin.rubber_band = QgsRubberBand(self.plugin.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.plugin.rubber_band.setColor(QColor(Qt.green))
        self.plugin.rubber_band.setWidth(2)

        self.plugin.pine_origin_rubber_band = QgsRubberBand(self.plugin.iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.plugin.pine_origin_rubber_band.setColor(QColor(Qt.red))
        self.plugin.pine_origin_rubber_band.setWidth(2)

        # Set up map selection tools
        self.map_tool = RegionSelectionTool(self.iface, self, self.plugin.rubber_band, is_pine_region=False)
        self.pine_origin_map_tool = RegionSelectionTool(self.iface, self, self.plugin.pine_origin_rubber_band, is_pine_region=True)

        self.layout = QVBoxLayout()

        self.refresh_button = QPushButton("Refresh Layers")
        self.refresh_button.clicked.connect(self.refresh)
        self.layout.addWidget(self.refresh_button)

        # --- DTM layer dropdown ---
        self.dtm_label = QLabel("Select Elevation Layer:")
        self.layout.addWidget(self.dtm_label)
        self.dtm_selector = QComboBox()
        self.populate_raster_layers(self.dtm_selector)
        self.layout.addWidget(self.dtm_selector)

        # --- Landcover layer dropdown ---
        self.landcover_label = QLabel("Select Landcover Layer:")
        self.layout.addWidget(self.landcover_label)
        self.landcover_selector = QComboBox()
        self.populate_raster_layers(self.landcover_selector)
        self.layout.addWidget(self.landcover_selector)

        # --- Buttons ---
        self.select_button = QPushButton("Select Simulation Area")
        self.select_button.clicked.connect(self.activate_selection)
        self.layout.addWidget(self.select_button)

        self.confirm_selection_button = QPushButton("Confirm Simulation Area")
        self.confirm_selection_button.clicked.connect(self.confirm_drawn_area)
        self.layout.addWidget(self.confirm_selection_button)

        self.pine_origin_button = QPushButton("Select Initial Pine Area")
        self.pine_origin_button.clicked.connect(self.activate_pine_origin_selection)
        # self.pine_origin_button.setEnabled(False)  # Disabled by default
        self.layout.addWidget(self.pine_origin_button)

        self.confirm_pine_button = QPushButton("Confirm Initial Pine Area")
        self.confirm_pine_button.clicked.connect(self.confirm_initial_pine_region)
        # self.confirm_pine_button.setEnabled(False)  # Disabled by default
        self.layout.addWidget(self.confirm_pine_button)

        # TODO OP add buttons for other selecting other tree type regions

        self.clear_button = QPushButton("Clear Selected Areas")
        self.clear_button.clicked.connect(self.clear_selection)
        self.layout.addWidget(self.clear_button)

        # --- Simulation Resolution Slider ---
        self.resolution_label = QLabel(f"Resolution: {self.resolution}m")
        self.layout.addWidget(self.resolution_label)
        self.resolution_slider = QSlider(Qt.Horizontal)
        self.resolution_slider.setMinimum(1)  # Minimum resolution (metres between samples)
        self.resolution_slider.setMaximum(1000)  # Maximum resolution (metres between samples)
        self.resolution_slider.setValue(self.resolution)  # Default value
        self.resolution_slider.valueChanged.connect(self.update_resolution)
        self.layout.addWidget(self.resolution_slider)

        self.convert_button = QPushButton("Prepare Simulation Scenario")
        self.convert_button.clicked.connect(self.convert_to_json)
        self.layout.addWidget(self.convert_button)

        self.display_results_button = QPushButton("Visualize Results")
        self.display_results_button.clicked.connect(self.open_results_csv)
        self.layout.addWidget(self.display_results_button)

        container = QWidget()
        container.setLayout(self.layout)
        self.setWidget(container)

    def refresh(self):
        self.dtm_selector.clear()
        self.landcover_selector.clear()
        self.populate_raster_layers(self.dtm_selector)
        self.populate_raster_layers(self.landcover_selector)
        # TODO OP add selectors for clay and soil types

    def populate_raster_layers(self, selector):
        """Populate the dropdown with GeoTIFF (raster) layers."""
        selector.clear()
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if isinstance(layer, QgsRasterLayer):
                ds = layer.dataProvider().dataSourceUri().lower()
                if ds.endswith('.tif') or ds.endswith('.tiff'):
                    selector.addItem(layer.name(), layer)

    def update_resolution(self, value):
        """Update the simulation resolution when the slider is moved."""
        self.resolution = value
        self.resolution_label.setText(f"Resolution: {self.resolution}m")
        print(f"Resolution updated to: {self.resolution}m")

    def activate_selection(self):
        """Activate the polygon drawing tool."""
        self.plugin.iface.mapCanvas().setMapTool(self.map_tool)
        print("Draw tool activated. Draw a polygon on the map.")

    def activate_pine_origin_selection(self):
        """Activate the pine origin selection tool."""
        if self.plugin.selected_region:
            self.plugin.iface.mapCanvas().setMapTool(self.pine_origin_map_tool)
            print("Pine origin drawing tool activated. Draw a polygon within the selected region.")
        else:
            print("No selected region. Please draw a selected region first.")

    # TODO OP will need new functions for other tree type regions (likely same as other functions)

    def confirm_drawn_area(self):
        """Confirm the drawn polygon and set it as the selected region."""
        if self.map_tool.points:
            self.plugin.selected_region = QgsGeometry.fromPolygonXY([self.map_tool.points])
            print("Selected region confirmed.")
            # Enable the pine origin button since a selected region exists
        #     self.pine_origin_button.setEnabled(True)
        # else:
        #     print("No polygon drawn. Please draw a polygon first.")
        #     # Disable the pine origin button if no selected region exists
        #     self.pine_origin_button.setEnabled(False)
    
    def confirm_initial_pine_region(self):
        """Confirm the drawn polygon and set it as the initial pine region."""
        if self.pine_origin_map_tool.points:
            self.plugin.initial_pine_region = QgsGeometry.fromPolygonXY([self.pine_origin_map_tool.points])
            print("Initial pine region confirmed.")
            # self.confirm_pine_button.setEnabled(False)  # Disable the button after confirmation
        else:
            print("No polygon drawn. Please draw a polygon first.")
    
    # TODO OP is this duplicate of above? Need to take a closer look
    def activate_pine_origin_selection(self):
        """Activate the pine origin selection tool."""
        if self.plugin.selected_region:
            self.plugin.iface.mapCanvas().setMapTool(self.pine_origin_map_tool)
            # self.confirm_pine_button.setEnabled(True)  # Enable the button
            print("Pine origin drawing tool activated. Draw a polygon within the selected region.")
        else:
            print("No selected region. Please draw a selected region first.")

    def clear_selection(self):
        """Clear the current selection and rubber band."""
        if self.plugin.rubber_band:
            self.plugin.selected_region = None
            self.plugin.rubber_band.reset()
            self.plugin.rubber_band = None
            self.plugin.iface.mapCanvas().refresh()
        if self.plugin.pine_origin_rubber_band:
            self.plugin.initial_pine_region = None
            self.plugin.pine_origin_rubber_band.reset()
            self.plugin.pine_origin_rubber_band = None
            self.plugin.iface.mapCanvas().refresh()
        self.map_tool.points = []
        self.pine_origin_map_tool.points = []
        self.plugin.iface.mapCanvas().setMapTool(None)
        # self.pine_origin_button.setEnabled(False)
        # self.confirm_pine_button.setEnabled(False)  # Disable the button
        print("Selection cleared!")

    def clip_initial_pine_region(self, json_file_path):
        """Clip the initial pine region as a binary raster and resample it to match the slope raster."""
        if not self.plugin.initial_pine_region:
            print("No initial pine region to clip.")
            return None

        # Create an in-memory mask layer from the initial pine region polygon
        mask_layer = createTemporaryPolygonLayer(self.plugin.initial_pine_region)

        # Create a binary raster with the same dimensions as the slope raster
        dtm_layer = self.dtm_selector.currentData()
        if not dtm_layer:
            print("No dtm layer selected.")
            return None

        # Determine output file path for the clipped initial pine region raster
        
        # TODO OP fix filepath names (should not be ignited)
        initial_pine_raster_path_temp = os.path.splitext(json_file_path)[0] + f"_initial_pine_temp.tif"
        initial_pine_raster_path = os.path.splitext(json_file_path)[0] + f"_initial_pine.tif"

        # Use the GDAL Clip algorithm to clip the raster using the mask
        params = {
            "INPUT": dtm_layer.source(),
            "MASK": mask_layer,
            "CROP_TO_CUTLINE": True,
            "OUTPUT": initial_pine_raster_path_temp
        }

        # Run the clip operation
        processing.run("gdal:cliprasterbymasklayer", params)

        # Open the slope raster to get its dimensions and transform
        with rasterio.open(dtm_layer.source()) as elevation_src:
            elevation_height = elevation_src.height
            elevation_width = elevation_src.width
            elevation_transform = elevation_src.transform
            elevation_crs = elevation_src.crs

        # Open the clipped ignited raster
        with rasterio.open(initial_pine_raster_path_temp) as initial_pine_src:
            initial_pine_data = initial_pine_src.read(1)
            initial_pine_transform = initial_pine_src.transform
            initial_pine_crs = initial_pine_src.crs

            # Create an empty array for the resampled initial pine raster
            resampled_initial_pine_data = numpy.zeros((elevation_height, elevation_width), dtype=numpy.uint8)

            # Resample the ignited raster to match the slope raster
            rasterio._warp._reproject(
                source=initial_pine_data,
                destination=resampled_initial_pine_data,
                src_transform=initial_pine_transform,
                src_crs=initial_pine_crs,
                dst_transform=elevation_transform,
                dst_crs=elevation_crs,
                resampling=rasterio._warp.Resampling.nearest
            )

            # Save the resampled initial pine raster
        with rasterio.open(initial_pine_raster_path_temp, 'w', driver='GTiff', height=elevation_height, width=elevation_width,
                        count=1, dtype=resampled_initial_pine_data.dtype, crs=elevation_crs, transform=elevation_transform) as dst:
            dst.write(resampled_initial_pine_data, 1)
                
        # Use the GDAL Clip algorithm to clip the raster using the mask
        params = {
            "INPUT": initial_pine_raster_path_temp,
            "MASK": mask_layer,
            "CROP_TO_CUTLINE": True,
            "OUTPUT": initial_pine_raster_path
        }

        # Run the clip operation
        processing.run("gdal:cliprasterbymasklayer", params)

        return initial_pine_raster_path

    def convert_to_json(self):
        """Clip the selected GeoTIFFs to the drawn area, process them, and output JSON."""
        dtm_layer = self.dtm_selector.currentData()
        landcover_layer = self.landcover_selector.currentData()

        if dtm_layer and landcover_layer and self.plugin.selected_region and self.plugin.selected_region.isGeosValid():
            # json_file_path, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json);;All Files (*)")
            # if not json_file_path:
            #     print("No JSON file path provided.")
            #     return

            # Create an in-memory mask layer from the drawn polygon
            mask_layer = createTemporaryPolygonLayer(self.plugin.selected_region)

            root = os.path.dirname(os.path.abspath(__file__))
            #slope_path = os.path.join(root, "slope.tif") # TODO OP remove?
            #aspect_path = os.path.join(root, "aspect.tif") # TODO OP remove?
            json_file_path = os.path.join(root, "map.json")

            # Determine output file paths for the clipped rasters
            clipped_dtm_path = os.path.splitext(json_file_path)[0] + "_dtm.tif"
            clipped_land_path = os.path.splitext(json_file_path)[0] + "_landcover.tif"

            # Use the GDAL Clip algorithm to clip the rasters using the mask
            params_dtm = {
                "INPUT": dtm_layer.source(),
                "MASK": mask_layer,
                "CROP_TO_CUTLINE": True,
                "OUTPUT": clipped_dtm_path
            }
            params_land = {
                "INPUT": landcover_layer.source(),
                "MASK": mask_layer,
                "CROP_TO_CUTLINE": True,
                "OUTPUT": clipped_land_path
            }

            processing.run("gdal:cliprasterbymasklayer", params_dtm)
            processing.run("gdal:cliprasterbymasklayer", params_land)

            # Clip the initial pine region as a binary raster
            initial_pine_raster_path = self.clip_initial_pine_region(json_file_path)


            # TODO OP remove calculation of slope/aspect, we only need elevation so no processing needed. Might 
            # need some processing here for soil type from sand/clay percentages but should be straight forward.
            """
            # Calculate slope and aspect
            feedback = QgsProcessingFeedback()
            processing.run("qgis:slope", {
                "INPUT": dtm_layer,
                "Z_FACTOR": 1.0,
                "OUTPUT": slope_path, 
            }, feedback=feedback)
            processing.run("qgis:aspect", {
                "INPUT": dtm_layer,
                "Z_FACTOR": 1.0,
                "OUTPUT": aspect_path, 
            }, feedback=feedback)

            slope_layer = QgsRasterLayer(slope_path, "slope")
            aspect_layer = QgsRasterLayer(aspect_path, "aspect")
            if not slope_layer.isValid():
                print("Failed to load slope layer!")
                return
            if not aspect_layer.isValid():
                print("Failed to load slope layer!")
                return
            QgsProject.instance().addMapLayer(slope_layer, False)
            QgsProject.instance().addMapLayer(aspect_layer, False)
            """

            # Prepare paths for further processing
            paths = {
                #"aspect": aspect_path,
                #"slope": slope_path,
                "dtm": clipped_dtm_path,
                "land": clipped_land_path,
                "initial_pine": initial_pine_raster_path,
                "json": json_file_path,
            }

            # Resample and align the landcover raster to match the slope and aspect rasters
            with rasterio.open(paths["dtm"]) as dtm_src:
                elevation_transform = dtm_src.transform
                elevation_crs = dtm_src.crs
                elevation_width = dtm_src.width
                elevation_height = dtm_src.height

            with rasterio.open(paths["land"]) as land_src:
                land_data = land_src.read(1)
                land_transform = land_src.transform
                land_crs = land_src.crs

                # Resample landcover to match slope raster
                resampled_land_data = numpy.empty((elevation_height, elevation_width), dtype=numpy.float32)
                rasterio._warp._reproject(
                    source=land_data,
                    destination=resampled_land_data,
                    src_transform=land_transform,
                    src_crs=land_crs,
                    dst_transform=elevation_transform,
                    dst_crs=elevation_crs,
                    resampling=rasterio._warp.Resampling.nearest
                )

                # Save the resampled landcover raster
                resampled_land_path = os.path.splitext(json_file_path)[0] + "_landcover_resampled.tif"
                with rasterio.open(resampled_land_path, 'w', driver='GTiff', height=elevation_height, width=elevation_width,
                                count=1, dtype=resampled_land_data.dtype, crs=elevation_crs, transform=elevation_transform) as dst:
                    dst.write(resampled_land_data, 1)

                paths["land"] = resampled_land_path

            dump_json(paths, self)
            print("JSON conversion completed.")
        else:
            #print(self.plugin.selected_region.isGeosValid())
            print("No valid layers or selected region. Cannot convert to JSON.")

    def open_results_csv(self):
        # Path to the CSV file
        root = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(root, "plant_population_out.csv")

        # Define the vector layer with temporal properties
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "TemporalLayer", "memory")
        provider = layer.dataProvider()

        # Define fields: Time Step, Height
        fields = QgsFields()
        fields.append(QgsField("time_step", QVariant.Int))
        fields.append(QgsField("height", QVariant.Int))

        provider.addAttributes(fields)
        layer.updateFields()

        # Read and process the CSV
        with open(csv_path, "r") as file:
            line_count = 0
            for line in file:
                if line_count < 2:
                    line_count += 1
                    continue
                parts = line.strip().split(";")

                if len(parts) < 5:
                    continue  # Ensure correct formatting

                # Extract time step
                time_step = int(parts[0])

                # Extract coordinates
                coords = parts[2].split("_")
                point = QgsPointXY(float(coords[0]), float(coords[1]))

                # Extract the fifth value inside "< >"
                values = parts[4].strip("<>").split(",")
                height = int(values[4])  # Index starts at 0

                # Create feature
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPointXY(point))
                feature.setAttributes([time_step, height])

                # Add feature to layer
                provider.addFeatures([feature])

        layer.updateExtents()

        # Enable temporal properties
        layer.setTemporalPropertiesDefinition({
            "startField": "time_step",
            "endField": "time_step",
            "mode": 0  # Discrete temporal mode
        })

        # Add to QGIS project
        QgsProject.instance().addMapLayer(layer)

    def on_cadmium_finish_running(self, csv_path):
        uri = f"file:///{csv_path}?delimiter=,&xField=x&yField=y&crs=EPSG:2959"
        # TODO OP load plant population output csv instead of "ignition"
        layer = QgsVectorLayer(uri, "ignition", "delimitedtext")
        if not layer.isValid():
            print("Failed to load layer!")
            return
        QgsProject.instance().addMapLayer(layer)
        props = layer.temporalProperties()
        props.setIsActive(True)
        props.setAccumulateFeatures(True)
        props.setMode(QgsVectorLayerTemporalProperties.TemporalMode.ModeFeatureDateTimeInstantFromField)
        props.setStartField("time")



class RegionSelectionTool(QgsMapToolEmitPoint):
    def __init__(self, iface, plugin, rubber_band, is_pine_region=False):
        super(RegionSelectionTool, self).__init__(iface.mapCanvas())
        self.points = []  # List to store clicked QgsPointXY objects
        self.plugin = plugin
        self.rubber_band = rubber_band
        # TODO OP will likely need to change boolean flag to enum for tree types
        self.is_pine_region = is_pine_region  # Flag to indicate if this is for the initial pine region

    def canvasPressEvent(self, event):
        point = self.toMapCoordinates(event.pos())


        # TODO will need to expand this if-state to check new enum for tree type regions
        # If this is for the initial pine region, enforce the selected region constraint
        if self.is_pine_region:
            if not self.plugin.selected_region or not self.plugin.selected_region.contains(point):
                print("Point is outside the selected region. Ignoring.")
                return

        # Automatically close the polygon if the user clicks near the first point
        if len(self.points) > 2 and self.is_near_first_point(point):
            self.points.append(self.points[0])
            # TODO can we check which region in a better way? If no then just change to tree type enum
            if self.is_pine_region:
                self.plugin.initial_pine_region = QgsGeometry.fromPolygonXY([self.points])
                print("Polygon closed and initial pine region set.")
                print(f"Initial pine region geometry: {self.plugin.initial_pine_region.asWkt()}")  # Debug print
            else:
                self.plugin.selected_region = QgsGeometry.fromPolygonXY([self.points])
                print("Polygon closed and selected region set.")
            self.highlight_region()
            return

        # Add the new point to the list
        self.points.append(point)
        self.highlight_region()

    def is_near_first_point(self, point, tolerance=50):
        """Check if the current point is near the first point (within a certain tolerance)."""
        first_point = self.points[0]
        dist = math.sqrt((first_point.x() - point.x())**2 + (first_point.y() - point.y())**2)
        return dist <= tolerance

    def highlight_region(self):
        """Highlight the drawn polygon on the map."""
        self.rubber_band.reset()
        for p in self.points:
            self.rubber_band.addPoint(p)

    def clear_highlight(self):
        """Clear the drawn polygon from the map."""
        self.rubber_band.reset()
        self.plugin.iface.mapCanvas().refresh()

#########################
# HELPER FUNCTIONS
#########################

def createTemporaryPolygonLayer(geometry):
    """
    Creates an in-memory vector layer (Polygon) with the given geometry.
    This layer will be used as a mask for clipping.
    """
    crs = QgsProject.instance().crs().authid()
    mem_layer = QgsVectorLayer(f"Polygon?crs={crs}", "mask", "memory")
    prov = mem_layer.dataProvider()
    feat = QgsFeature()
    feat.setGeometry(geometry)
    prov.addFeatures([feat])
    mem_layer.updateExtents()
    return mem_layer

def read_raster(path):
    """Read a raster file and return its data and metadata."""
    with rasterio.open(path) as src:
        data = src.read(1)  # Read the first band
        transform = src.transform
        crs = src.crs
        return data, transform, crs

def dump_json(paths, widget):
    """Read raster data and populate the JSON file."""
    # Read raster data
    #slope_data, elevation_transform, _ = read_raster(paths['slope'])
    #aspect_data, _, _ = read_raster(paths['aspect'])
    dtm_data, elevation_transform, _ = read_raster(paths['dtm'])
    landcover_data, _, _ = read_raster(paths['land'])
    initial_pine_data, _, _ = read_raster(paths['initial_pine']) if paths.get('initial_pine') else (None, None, None)        

    resolution = widget.resolution

    # Get dimensions
    height, width = initial_pine_data.shape
    print(str(height) + " : " + str(width))

    # Initialize JSON structure
    data = {
        "cells": {
            "default": {
                "delay": "inertial",
                "model": "plant_population",
                "state": { 
                    "current_resources" : {
                    "water" : 0,
                    "sunlight" : 0,
                    "nitrogen" : 0,
                    "potassium" : 0
                    },
                    "soil_type": 0,
                    "elevation": 0,
                    "tree_height" : 0,
                    "tree_type" : 0
                }            
            }
        }
    }

    # TODO: hexagonal grid is broken

    # shift = 0

    # Iterate over each cell
    # y_resolution = int(resolution / 2 * 1.1547)
    # x_resolution = int(resolution * 2)
    # for row in range(0, height, y_resolution):
    #     for col in range(0, width, x_resolution):
    for row in range(0, height, resolution):
        for col in range(0, width, resolution):
            # Get values from rasters
            #slope_value = slope_data[row][col]
            #aspect_value = aspect_data[row][col]
            dtm_value = dtm_data[row][col]
            landcover_value = landcover_data[row][col]
            initial_pine_value = initial_pine_data[row][col] if initial_pine_data is not None else 0
            
            #print("row: " + str(row) + " ; col: " + str(col) + " ; ignited: " + str(initial_pine_value))

            # Skip invalid values
            #if slope_value <= -9999.0 or aspect_value <= -9999.0:
            #    continue

            # Get cell coordinates
            x, y = elevation_transform * (col, row)
            # if shift % 2:
            #     x += int(x_resolution / 2)
            cell_name = f"{int(x)}_{int(y)}"

            # Map landcover value to fuel model
            try:
                fuel = FUELS[int(landcover_value)]
            except KeyError:
                continue

            if (dtm_value < 0):
                continue

            # Set ignited to true or false based on the ignited raster
            initial_pine = bool(initial_pine_value) if initial_pine_data is not None else False

            tree_type = 1 if initial_pine else 0

            # Add cell to JSON
            data["cells"][cell_name] = {
                "state": { 
                    "current_resources" : {
                        "water" : 0,
                        "sunlight" : 0,
                        "nitrogen" : 0,
                        "potassium" : 0
                    },
                    "soil_type": 0,
                    "elevation": int(dtm_value),
                    "tree_height" : 0,
                    "tree_type" : int(tree_type)
                },
                "neighborhood": {}
            }
        
            # Add neighborhood logic (unchanged)
            # if not shift % 2:
            #     neighborhood = [(0, -2), (0, -1), (0, 1), (0, 2), (-1, -1), (-1, 1)]
            # else:
            #     neighborhood = [(0, -2), (0, -1), (0, 1), (0, 2), (1, -1), (1, 1)]
            neighborhood = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for neighbor in neighborhood:
                # c = col + neighbor[0] * x_resolution
                # r = row + neighbor[1] * y_resolution
                c = col + (neighbor[0] * resolution)
                r = row + (neighbor[1] * resolution)

                # Skip out-of-bounds neighbors
                if c < 0 or r < 0 or c >= width or r >= height:
                    continue

                try:
                    fuel = FUELS[int(landcover_data[r][c])]
                except KeyError:
                    continue

                if (dtm_data[r][c] < 0):
                    continue

                # Get neighbor coordinates
                neighbor_x, neighbor_y = elevation_transform * (c, r)
                # if not shift % 2 and abs(neighbor[1]) == 1:
                #     neighbor_x += int(x_resolution / 2)
                neighbor_name = f"{int(neighbor_x)}_{int(neighbor_y)}"

                # Add neighbor to neighborhood
                data["cells"][cell_name]["neighborhood"][neighbor_name] = resolution
        # shift += 1
        

    # Write JSON to file
    with open(paths['json'], "w") as f:
        json.dump(data, f, indent=4)
    print(f"JSON file saved to: {paths['json']}")
