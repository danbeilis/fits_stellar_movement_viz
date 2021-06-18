# FITS 3D & Stellar Movement Visualization Program
Astronomy FITS 3D Visualization using Mayavi and Stellar Movement Visualizer
The program enables examining the 3D structure of any fits datacube file, sharing some of the features as the AstroSlicer extension (https://www.slicer.org/wiki/Documentation/Nightly/Extensions/SlicerAstro) for the 3DSlicer visualization software package (https://www.slicer.org/). 

The program was written in Python and utilizes the 3D visualization capabilities of the Mayavi software package (https://docs.enthought.com/mayavi/mayavi/) that wraps the VTK rendering engine (https://vtk.org/) which is embedded in a graphical user interface (GUI) using the TraitsUI GUI visualization package (https://docs.enthought.com/traitsui/).

The program allows the following:
* FITS file 3D visualization cropping using adjustable sliders for the 2 spatial axes and the spectral/kinematic axis.
* Adjusting the minimum and maximum of the intensity of the 3D visualization.
* Arrows representing the spectral/kinematic axis placed 3-dimensionally at each point of the 3D visualization with colors representing the velocity based on the color bar at the bottom. The density of the velocity arrows can be adjusted and they can be toggled on or off.
* Changing the viewing angle of the 3D visualization and spinning the 3D display and recording the screenshots images to a folder. These images are also compiled to a video file.
* Changing the background color and the visualization color-scale (the color scheme of the 3D visualization).
* Saving and loading the configuration of the viewing settings and star movement curves parameters. An additional option is to save a copy of the previous configuration as backup before overwriting the configuration file.
* Adding 2D slices along each of the 3 axes. These can be dragged directly inside of the 3D visualization or using sliders in the GUI.
* Dynamically adjusting the parameters of up to 10 star curves using sliders and numeric input (each star curve start is marked by a cube and its end is marked by a sphere). The curves positions and scale within the 3D space can be adjusted numerically. Additionally, 3D cones that are made up of increasingly smaller circles placed at intervals along each star movement curve can be added. These help visualize the separations and overlapping of the multiple stars movement produced cometary tails before running the 3D hydrodynamics simulation in PLUTO.

Example screenshots of the program showing the main interface and the 2D slicing interface:
![Screenshot of the Stellar Movement Program showing the main interface](/stellar_movement_program_1.png)
![Screenshot of the Stellar Movement Program showing the 2D slicing interface](/stellar_movement_program_2.png)
Example screenshots of the program showing the star movement curves interface with cones turned off and on:
![Screenshot of the Stellar Movement Program showing the star movement curves interface with cones turned off](/stellar_movement_program_3.png)
![Screenshot of the Stellar Movement Program showing the star movement curves interface with cones turned on](/stellar_movement_program_4.png)
