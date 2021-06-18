# FITS 3D & Stellar Movement Visualization Program
The program enables examining the 3D structure of any fits datacube file, sharing some of the features as the AstroSlicer extension (https://www.slicer.org/wiki/Documentation/Nightly/Extensions/SlicerAstro) for the 3DSlicer visualization software package (https://www.slicer.org/). It was written in Python and utilizes the 3D visualization capabilities of the Mayavi software package (https://docs.enthought.com/mayavi/mayavi/) that wraps the VTK rendering engine (https://vtk.org/) which is embedded in a graphical user interface (GUI) using the TraitsUI GUI visualization package (https://docs.enthought.com/traitsui/).

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

## Requirements

The program is written in Python and was only tested on version 3.7 on Windows but should probably work on. Due to complications with the packages dependencies, the program will work only with the following package versions (any other packages version combinations will not necessarily work):
* altgraph==0.17
* apptools==4.5.0
* astropy==4.0.1.post1
* configobj==5.0.6
* cycler==0.10.0
* envisage==4.9.2
* future==0.18.2
* h5py==2.10.0
* kiwisolver==1.2.0
* matplotlib==3.2.1
* mayavi==4.7.1
* numpy==1.18.2
* packaging==20.3
* pefile==2019.4.18
* pip==20.0.2
* pyface==6.1.2
* Pygments==2.6.1
* PyInstaller==3.6
* pyparsing==2.4.7
* PyQt5==5.14.2
* PyQt5-sip==12.7.2
* python-dateutil==2.8.1
* scipy==1.4.1
* setuptools==46.1.3
* sip==5.2.0
* six==1.14.0
* spectral-cube==0.4.5
* toml==0.10.0
* traits==6.0.0
* traitsui==6.1.3
* vtk==8.1.2
* wheel==0.34.2
* xmltodict==0.12.0
