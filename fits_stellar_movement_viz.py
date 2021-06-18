import os, glob, json, datetime, sys, pprint, subprocess, io, threading, configparser
from traits.api import HasTraits, Button, Instance, List, Str, Enum, Float, File, Int, Range, Bool, on_trait_change, \
    Color, Directory, Array
from traitsui.api import View, Item, VGroup, HSplit, HGroup, FileEditor, ListEditor, DirectoryEditor
from tvtk.pyface.scene_editor import SceneEditor
from tvtk.pyface.scene import Scene

from mayavi.tools.mlab_scene_model import MlabSceneModel
from mayavi.core.ui.mayavi_scene import MayaviScene
from mayavi.core.api import PipelineBase, Source
from mayavi import mlab
import astropy.io.fits as fits
import numpy as np

from collections import namedtuple
from scipy.interpolate import splrep, splev
from tvtk.api import tvtk
from pyface.image_resource import ImageResource

class StellarMovementSimulation(HasTraits):
    FitsFileData = namedtuple('FitsFileData', 'xend yend zend data_min data_max')
    fits_file_data = FitsFileData(10,10,10,0.0,10)

    xstart_low = Int(0)
    xstart_high = Int(fits_file_data.xend)
    xstart = Range('xstart_low', 'xstart_high', 0, mode='slider')
    xend_low = Int(0)
    xend_high = Int(fits_file_data.xend)
    xend = Range('xend_low', 'xend_high', fits_file_data.xend, mode='slider')

    ystart_low = Int(0)
    ystart_high = Int(fits_file_data.yend)
    ystart = Range('ystart_low', 'ystart_high', mode='slider')
    yend_low = Int(0)
    yend_high = Int(fits_file_data.yend)
    yend = Range('yend_low', 'yend_high', fits_file_data.xend, mode='slider')

    zstart_low = Int(0)
    zstart_high = Int(fits_file_data.zend)
    zstart = Range('zstart_low', 'zstart_high', mode='slider')
    zend_low = Int(0)
    zend_high = Int(fits_file_data.zend)
    zend = Range('zend_low', 'zend_high', fits_file_data.xend, fits_file_data.zend, mode='slider')

    for i in range(1, 11):
        if i == 1:
            exec('is_star_curve_visible_' + str(i) + ' = Bool(True)')
        else:
            exec('is_star_curve_visible_' + str(i) + ' = Bool(False)')
        exec('radius_' + str(i) + " = Range(0.0, 15.0, 0.0, mode='slider')")
        exec('angle0_' + str(i) + " = Range(0,360, mode='slider')")
        exec('rot_vel_' + str(i) + " = Range(-25.0, 25.0, 0.0, mode='slider')")
        exec('x0_' + str(i) + ' = Float(0.0)')
        exec('y0_' + str(i) + ' = Float(0.0)')
        exec('z0_' + str(i) + ' = Float(0.0)')
        exec('z_vel_' + str(i) + ' = Float(0.0)')
        exec('color_' + str(i) + " = Color('red')")
        exec('initial_tube_radius_' + str(i) + ' = Float(5)')
        exec('is_star_curve_display_' + str(i) + ' = Bool(True)')

    starCurveGroups = []

    for i in range(1, 11):
        starCurveGroup = VGroup(HGroup(
            Item('radius_' + str(i), tooltip=u"Curve Radius", show_label=True, width=4),
            Item('angle0_' + str(i), tooltip=u"Initial Rotation Angle", show_label=True, width=4),
            Item('rot_vel_' + str(i), tooltip=u"Rotation Velocity", show_label=True, width=4),
        ),
            HGroup(
                Item('x0_' + str(i), tooltip=u"Initial X Axis Position", show_label=True),
                Item('y0_' + str(i), tooltip=u"Initial Y Axis Position", show_label=True),
                Item('z0_' + str(i), tooltip=u"Initial Z Axis Position", show_label=True),
                Item('z_vel_' + str(i), tooltip=u"Z Axis Velocity", show_label=True),
                Item('color_' + str(i), tooltip=u"Curve Color", show_label=True),
                Item('initial_tube_radius_' + str(i), label='TB', tooltip=u"Initial Tube Radius in cone approximation", show_label=True),
                Item('is_star_curve_display_' + str(i), tooltip=u"Toggle display of star curve", label='Display')),
            label='Star Curve #' + str(i), visible_when='is_star_curve_visible_' + str(i) + ' == True')  #
        starCurveGroups.append(starCurveGroup)

    stars_curves_number = Range(1, 10, mode='spinner')
    use_letters = Bool(True)
    text_prefix = Str('Star_')
    show_star_curves_text = Bool(False)

    plot_curves_button = Button(u"Plot Curves")
    show_cone_approximation = Bool(False)

    fitsfile = File('test.fits', filter=[u"*.fits"])
    plotbutton = Button(u"Plot")
    clearbutton = Button(u"Clear")

    scene = Instance(MlabSceneModel, ())

    scene_x = Instance(MlabSceneModel, ())
    scene_y = Instance(MlabSceneModel, ())
    scene_z = Instance(MlabSceneModel, ())

    is_scene_x = Bool(False)
    is_scene_y = Bool(False)
    is_scene_z = Bool(False)

    x_plane_low = Int(0)
    x_plane_high = Int(fits_file_data.xend)
    x_plane = Range('x_plane_low', 'x_plane_high', 0, mode='slider')
    x_plane_slice_position = Int(0)
    y_plane_low = Int(0)
    y_plane_high = Int(fits_file_data.xend)
    y_plane = Range('y_plane_low', 'y_plane_high', 0, mode='slider')
    y_plane_slice_position = Int(0)
    z_plane_low = Int(0)
    z_plane_high = Int(fits_file_data.xend)
    z_plane = Range('z_plane_low', 'z_plane_high', 0, mode='slider')
    z_plane_slice_position = Int(0)

    ipw_3d_x = Instance(PipelineBase)
    ipw_3d_y = Instance(PipelineBase)
    ipw_3d_z = Instance(PipelineBase)

    azimuth_x = Range(0, 360, 0, mode='spinner')
    elevation_x = Range(0, 360, 270, mode='spinner')
    distance_x = Int(-45)
    setview_x_button = Button(u"Set View (X)")

    azimuth_y = Range(0, 360, 270, mode='spinner')
    elevation_y = Range(0, 360, 90, mode='spinner')
    distance_y = Int(45)
    setview_y_button = Button(u"Set View (Y)")

    azimuth_z = Range(0, 360, 0, mode='spinner')
    elevation_z = Range(0, 360, 0, mode='spinner')
    distance_z = Int(-45)
    setview_z_button = Button(u"Set View (Z)")

    _axis_names = dict(x=0, y=1, z=2)

    save_the_scene_button = Button(u"Save Scene")
    save_in_file = Str("test.json")
    load_scene_file = File('test.json', filter=[u"*.json"])
    load_the_scene_button = Button('Load Scene')
    result = Str('Saved Successfully')
    display_success_result = Bool(False)
    display_fail_result = Bool(False)
    save_backup = Bool(True)

    record = Button(u"Record Video")
    stop_record = Button(u"Stop Recording")
    spin = Button(u"Spin")
    num_pics = Range(1,1000,200)
    quality = Range(0,20,20,mode='spinner')
    fps = Range(0,60,40,mode='spinner')
    delay = Int(0)
    angle = Int(360)
    record_video_result = Str('Saved Successfully')
    display_success_record_video_result = Bool(False)
    display_fail_record_video_result = Bool(False)
    is_recording_video = Bool(False)
    record_video_state = Str('Testing')
    video_name = Str()
    save_video_dir = Directory()

    data_min = round(np.float(fits_file_data.data_min), 2)
    data_max = round(np.float(fits_file_data.data_max), 2)
    minDT = Float(data_min)
    maxDT = Float(data_max)
    opacity = Range(0.0, 1.0, 0.1)

    azimuth = Range(0, 360, 180, mode='slider')
    elevation = Range(0, 180, 0, mode='slider')
    distance = Int(-350)
    setview_button = Button(u"Set View")
    update_view = Bool(False)

    display_arrows = Bool(True)
    arrows_density = Range(1,100,5, mode='spinner')

    factor = Float(1.5)
    dx = Range(-256,256,0,mode='slider')
    dy = Range(-256,256,0,mode='slider')
    dz = Range(-256,256,0,mode='slider')

    plot_colormap = Enum("Earth", "Rainbow", "Gray")
    plot_colormap_button1 = Button(u"Set Colormap")
    plot_colormap_button2 = Button(u"Set Colormap")
    plot_colormap_button3 = Button(u"Set Colormap")
    background_color = Color((127,127,127))

    blank_gap = Str(''.ljust(10))

    intensity_units = Str('Jy')

    is_debug_mode = Bool(False)

    view = View(
        HSplit(
            HGroup(
                VGroup(
                    HGroup(Item("fitsfile", label=u"FITS Datacube:", show_label=True,
                                editor=FileEditor(dialog_style='open')),
                           Item("plotbutton", show_label=False, width=3),
                           Item("clearbutton", show_label=False, width=3), show_border=True),
                    VGroup(
                        HGroup(Item('xstart', tooltip=u"starting pixel in X axis", show_label=True, springy=True),
                               Item('xend', tooltip=u"ending pixel in X axis", show_label=True, springy=True)),
                        HGroup(Item('ystart', tooltip=u"starting pixel in Y axis", show_label=True, springy=True),
                               Item('yend', tooltip=u"ending pixel in Y axis", show_label=True, springy=True)),
                        HGroup(Item('zstart', tooltip=u"starting pixel in Z axis", show_label=True, springy=True),
                               Item('zend', tooltip=u"ending pixel in Z axis", show_label=True, springy=True)),
                        HGroup(Item('minDT', tooltip=u"Minimum display threshold", label="Min DT", show_label=True,
                                    springy=True),
                               Item('maxDT', tooltip=u"Maximum display threshold", label="Max DT", show_label=True,
                                    springy=True),
                               Item('opacity', tooltip=u"Opacity of the scene", show_label=True), show_labels=False),
                        show_border=True, label='Datacube View Configuration'),
                    HGroup(Item('display_arrows', tooltip='Toggle display of arrows', label='Display Arrows'),
                           Item('arrows_density', tooltip='Reduce number of arrows so that only 1 out of every \'Arrows Density\' arrows are displayed', show_label=True, style_sheet='*{width:20}'),
                           show_border=True, label='Velocity Arrows View Configuration'),
                    VGroup(HGroup(
                        Item('num_pics', tooltip=u"Number of pictures making up the video", label='Pics #', style_sheet='*{width:30}'),
                        Item('fps', tooltip=u"Frames per sec of video file", label='FPS', style_sheet='*{width:15}'),
                        Item('quality', tooltip=u"Quality of plots, 0 is worst, 8 is good, 20 is perfect", show_label=True, style_sheet='*{width:15}'),
                        Item('angle', tooltip=u"Angle the cube spins", show_label=True, springy=True),
                        Item("spin", tooltip=u"Spin 360 degrees", show_label=False, springy=True),
                        Item("record", tooltip="Make a MP4 video", show_label=False, springy=True),
                        Item("stop_record", tooltip="Stop recording video", show_label=False, springy=True, visible_when='is_recording_video == True')),
                        # HGroup(
                        #     ,
                        # ),
                        HGroup(Item('video_name', tooltip=u"Video file name", label='Video File Name', style_sheet='*{width:50}'),
                                    Item("save_video_dir", label=u"Save Video File Folder", tooltip=u"Folder where video file will be saved", editor=DirectoryEditor(dialog_style='open'), springy=True),
                               ),
                        HGroup(
                            Item('record_video_state', style='readonly', label='State:', visible_when='is_recording_video == True', style_sheet='*{font-weight:bold}'),
                            Item('record_video_result', style='readonly', visible_when='display_success_record_video_result == True',
                                 style_sheet="*{color:'green'}"),
                            Item('record_video_result', style='readonly', visible_when='display_fail_record_video_result == True',
                                 style_sheet="*{color:'red'}"),
                        ),
                        show_border=True, label='Spinning View'),
                    HGroup(Item('azimuth', tooltip=u"Angle on the x-y plane which varies from 0-360 degrees",
                                show_label=True, springy=True),
                           Item('elevation', tooltip=u"Angle from the z axis and varies from 0-180 degrees",
                                show_label=True, springy=True),
                           Item('distance', tooltip=u"Radius of the sphere centered around the visualization",
                                show_label=True, springy=True),
                           Item('update_view', tooltip='Toggle live updating of view', label='Update View'),
                           Item("setview_button", show_label=False, width=3),
                           show_border=True, label='Viewing Angles and Distance'),
                    HGroup(
                        Item('background_color', tooltip='Change 3d plot background color', label='Background Color'),
                        Item("plot_colormap", tooltip=u"Choose the colormap for the 3d plot", label='Choose Colormap'),
                        Item("intensity_units", tooltip=u"Legend colorscale's intensity units", label='Intensity Units'),
                        # Item('plot_colormap_button1', show_label=False, visible_when="plot_colormap=='Earth'"),
                        # Item('plot_colormap_button2', show_label=False, visible_when="plot_colormap=='Rainbow'"),
                        # Item('plot_colormap_button3', show_label=False, visible_when="plot_colormap=='Gray'"),
                        show_border=True, label='Color and Legend Settings'
                    ),
                    HGroup(Item('show_star_curves_text', tooltip=u"Show star curves names in the 3D plot next to the curve's start",
                                label='Show Star Curve Names'),
                           Item('text_prefix', tooltip=u"Star curve names prefix",
                                label='Star Curve Name Prefix'),
                           Item('use_letters', tooltip=u"Use letters instead of numbers differentiate stars",
                                label='Use Letters'),
                           show_border=True, label='Star Curves Optional'),
                    VGroup(
                        HGroup(Item("save_the_scene_button", label="Save View Settings & Star Curves",
                                    tooltip=u"Save current scene in a JSON file"),
                               Item("save_in_file", tooltip=u"JSON filename to save", show_label=False),
                               Item('save_backup', tooltip='Save backup of existing file in format FILENAME_YEAR.MONTH.DAY_HOUR.MINUTE.SEC.json', label='Save Backup')),
                        HGroup(Item("load_scene_file", label=u"JSON filename to load:", show_label=True,
                                    editor=FileEditor(dialog_style='open')),
                               Item("load_the_scene_button", tooltip=u"JSON file name to load", show_label=False)),
                        Item('result', style='readonly', visible_when='display_success_result == True',
                             style_sheet="*{color:'green'}"),
                        Item('result', style='readonly', visible_when='display_fail_result == True',
                             style_sheet="*{color:'red'}"),
                        show_border=True, label='Save and Load Scenes'),
                    label="View Settings",
                    show_labels=False
                ),
                VGroup(
                    HGroup(
                        Item('stars_curves_number', label='Stars #', style_sheet='*{width:15}'),
                        Item('show_cone_approximation', tooltip='Toggle approximation of stellar wind as a cone like shape', label='Cones'),
                        # Item('plot_curves_button', show_label=False),
                        Item('factor', tooltip='Star curves dimensions scale factor', show_label=True),
                        Item('dx', tooltip='Displacement of star curves in X axis', label='DX'),
                        Item('dy', tooltip='Displacement of star curves in X axis', label='DY'),
                        Item('dz', tooltip='Displacement of star curves in X axis', label='DZ'),
                    ),
                    # HGroup(
                    #
                    # ),
                    starCurveGroups, label="Star Curves"),
                VGroup(
                    VGroup(
                        HGroup(
                            Item('x_plane', tooltip=u"X plane position in X axis", label='X Plane Index', springy=True),
                            Item('is_scene_x', label='3D Display')),
                        HGroup(
                            VGroup(
                                HGroup(
                                    Item('azimuth_x', tooltip=u"Angle on the x-y plane which varies from 0-360 degrees",
                                         label='Azimuth (X)', style_sheet='*{width:25}')),
                                HGroup(
                                    Item('elevation_x', tooltip=u"Angle from the z axis and varies from 0-360 degrees",
                                         label='Elevation (X)', style_sheet='*{width:25}')),
                                HGroup(Item('distance_x',
                                            tooltip=u"Radius of the sphere centered around the visualization",
                                            label='Distance (X)', style_sheet='*{width:15}')),
                                Item("setview_x_button", show_label=False, width=30), visible_when='is_debug_mode == True'),
                            Item('blank_gap', style='readonly', show_label=False, ),
                            Item('scene_x', editor=SceneEditor(scene_class=Scene), show_label=False),
                            Item('blank_gap', style='readonly', show_label=False, )),
                    ),
                    VGroup(
                        HGroup(
                            Item('y_plane', tooltip=u"Y plane position in Y axis", label='Y Plane Index', springy=True),
                            Item('is_scene_y', label='3D Display')),
                        HGroup(
                            VGroup(
                                HGroup(
                                    Item('azimuth_y', tooltip=u"Angle on the x-y plane which varies from 0-360 degrees",
                                         label='Azimuth (Y)', style_sheet='*{width:25}')),
                                HGroup(
                                    Item('elevation_y', tooltip=u"Angle from the z axis and varies from 0-360 degrees",
                                         label='Elevation (Y)', style_sheet='*{width:25}')),
                                HGroup(Item('distance_y',
                                            tooltip=u"Radius of the sphere centered around the visualization",
                                            label='Distance (Y)', style_sheet='*{width:15}')),
                                Item("setview_y_button", show_label=False, width=30), visible_when='is_debug_mode == True'),
                            Item('blank_gap', style='readonly', show_label=False, ),
                            Item('scene_y', editor=SceneEditor(scene_class=Scene), show_label=False),
                            Item('blank_gap', style='readonly', show_label=False, )),
                    ),
                    VGroup(
                        HGroup(
                            Item('z_plane', tooltip=u"Z plane position in Z axis", label='Z Plane Index', springy=True),
                            Item('is_scene_z', label='3D Display')),
                        HGroup(
                            VGroup(
                                HGroup(
                                    Item('azimuth_z', tooltip=u"Angle on the x-y plane which varies from 0-360 degrees",
                                         label='Azimuth (Z)', style_sheet='*{width:25}')),
                                HGroup(
                                    Item('elevation_z', tooltip=u"Angle from the z axis and varies from 0-360 degrees",
                                         label='Elevation (Z)', style_sheet='*{width:25}')),
                                HGroup(Item('distance_z',
                                            tooltip=u"Radius of the sphere centered around the visualization",
                                            label='Distance (Z)', style_sheet='*{width:15}')),
                                Item("setview_z_button", show_label=False, width=30), visible_when='is_debug_mode == True'),
                            Item('blank_gap', style='readonly', show_label=False, ),
                            Item('scene_z', editor=SceneEditor(scene_class=Scene), show_label=False),
                            Item('blank_gap', style='readonly', show_label=False, )),
                    ),
                    label="Plane Slices"),
                # VGroup(Item('logText', show_label=False, style='custom')),
                layout="tabbed"
            ),
            VGroup(
                Item('scene',
                     editor=SceneEditor(scene_class=MayaviScene),
                     resizable=True,
                     height=600,
                     width=600
                     ), show_labels=False
            )
        ),
        resizable=True,
        title=u"Stellar Movement Simulation",
        icon=ImageResource('shooting_star2.png')
    )

    def __init__(self):
        self.colormap = 'gist_earth'

        self.is_loading = True

        for i in range(1, 11):
            if i == 1:
                setattr(self, 'is_star_curve_visible_' + str(i), True)
            else:
                setattr(self, 'is_star_curve_visible_' + str(i), False)
            setattr(self, 'radius_' + str(i), 0.0)
            setattr(self, 'angle0_' + str(i), 0)
            setattr(self, 'rot_vel_' + str(i), 0.0)
            setattr(self, 'x0_' + str(i), 0.0)
            setattr(self, 'y0_' + str(i), 0.0)
            setattr(self, 'z0_' + str(i), 0.0)
            setattr(self, 'z_vel_' + str(i), 0.0)
            setattr(self, 'color_' + str(i), (255,0,0))
            setattr(self, 'initial_tube_radius_' + str(i), 5)
            setattr(self, 'is_star_curve_display_' + str(i), True)

        self.star_curve_1 = None
        self.star_curve_2 = None
        self.star_curve_3 = None
        self.star_curve_4 = None
        self.star_curve_5 = None
        self.star_curve_6 = None
        self.star_curve_7 = None
        self.star_curve_8 = None
        self.star_curve_9 = None
        self.star_curve_10 = None

        self.star_curve_cone_1 = [None] * 100
        self.star_curve_cone_2 = [None] * 100
        self.star_curve_cone_3 = [None] * 100
        self.star_curve_cone_4 = [None] * 100
        self.star_curve_cone_5 = [None] * 100
        self.star_curve_cone_6 = [None] * 100
        self.star_curve_cone_7 = [None] * 100
        self.star_curve_cone_8 = [None] * 100
        self.star_curve_cone_9 = [None] * 100
        self.star_curve_cone_10 = [None] * 100

        self.star_curve_start_1 = None
        self.star_curve_start_2 = None
        self.star_curve_start_3 = None
        self.star_curve_start_4 = None
        self.star_curve_start_5 = None
        self.star_curve_start_6 = None
        self.star_curve_start_7 = None
        self.star_curve_start_8 = None
        self.star_curve_start_9 = None
        self.star_curve_start_10 = None

        self.star_curve_end_1 = None
        self.star_curve_end_2 = None
        self.star_curve_end_3 = None
        self.star_curve_end_4 = None
        self.star_curve_end_5 = None
        self.star_curve_end_6 = None
        self.star_curve_end_7 = None
        self.star_curve_end_8 = None
        self.star_curve_end_9 = None
        self.star_curve_end_10 = None

        self.star_curve_text_1 = None
        self.star_curve_text_2 = None
        self.star_curve_text_3 = None
        self.star_curve_text_4 = None
        self.star_curve_text_5 = None
        self.star_curve_text_6 = None
        self.star_curve_text_7 = None
        self.star_curve_text_8 = None
        self.star_curve_text_9 = None
        self.star_curve_text_10 = None

        self.letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']

        self.xstart_low = 0
        self.xstart_high = 10
        self.xstart = 0
        self.xend_low = 0
        self.xend_high = 10
        self.xend = 10

        self.ystart_low = 0
        self.ystart_high = 10
        self.ystart = 0
        self.yend_low = 0
        self.yend_high = 10
        self.yend = 10

        self.zstart_low = 0
        self.zstart_high = 10
        self.zstart = 0
        self.zend_low = 0
        self.zend_high = 10
        self.zend = 10

        self.minDT = 0.0
        self.maxDT = 10.0

        self.opacity = 0.1

        self.display_arrows = True
        self.arrows_density = 5

        self.num_pics = 200
        self.fps = 40
        self.quality = 20
        self.angle = 360
        self.video_name = 'test.mp4'
        self.save_video_dir = os.path.join(os.getcwd(), 'Screenshots')

        self.azimuth = 180
        self.elevation = 0
        self.distance = -350
        self.update_view = False

        self.background_color = (127,127,127)
        self.plot_colormap = 'Earth'

        self.show_star_curves_text = False
        self.text_prefix = 'Star_'
        self.use_letters = True

        self.save_in_file = 'test.json'
        self.load_scene_file = 'test.json'
        self.save_backup = True

        self.stars_curves_number = 1
        self.factor = 1.5
        self.dx = -256
        self.dy = -256
        self.dz = -256

        self.ffmpeg_path = 'C:\\ffmpeg\\bin\\ffmpeg'
        self.fitsfile = 'test.fits'
        self.min_itensity_for_velocity = 0.12

        if os.path.exists('conf.ini'):
            print('loading from conf.ini')

            config = configparser.ConfigParser()
            config.read('conf.ini')
            self.ffmpeg_path = config['DEFAULT']['FFMPEG_PATH']
            self.fitsfile = config['DEFAULT']['DEFAULT_FITS_FILE_NAME']
            self.min_itensity_for_velocity = float(config['DEFAULT']['MIN_INTENSITY_FOR_VELOCITY'])

            print(self.ffmpeg_path, self.fitsfile)

        self.ipw_3d_x = None
        self.ipw_3d_y = None
        self.ipw_3d_z = None
        self.ipw_x = None
        self.ipw_y = None
        self.ipw_z = None
        self.ipw_axes_x = None
        self.ipw_axes_y = None
        self.ipw_axes_z = None

        self.data = []

        self.data_src = None
        self.data_src_x = None
        self.data_src_y = None
        self.data_src_z = None

        self.is_loading = False

    def _background_color_changed(self):
        # if self.fig is None:
        #     return
        color = self.background_color.getRgb()[:-1]
        color_temp = (color[0] / 255, color[1] / 255, color[2] / 255)

        mlab.gcf().scene.background = color_temp

    def _plot_colormap_changed(self):
        if self.obj is None:
            return

        colormap = ''
        if self.plot_colormap == 'Earth':
            colormap = 'gist_earth'
        elif self.plot_colormap == 'Rainbow':
            colormap = 'gist_rainbow'
        elif self.plot_colormap == 'Gray':
            colormap = 'gist_gray'

        self.obj.module_manager.scalar_lut_manager.lut_mode = colormap

    def _azimuth_changed(self):
        if self.update_view:
            mlab.view(self.azimuth, self.elevation, self.distance)

    def _elevation_changed(self):
        if self.update_view:
            mlab.view(self.azimuth, self.elevation, self.distance)

    def _distance_changed(self):
        if self.update_view:
            mlab.view(self.azimuth, self.elevation, self.distance)

    def _arrows_density_changed(self):
        self.obj2.glyph.mask_points.on_ratio = self.arrows_density
        mlab.draw()

    def _display_arrows_changed(self):
        self.obj2.actor.property.opacity = self.display_arrows is True if 1 else 0

    def _stars_curves_number_changed(self):
        for i in range(1, 11):
            # self.is_star_curve_visible_1 = True
            # print(self['is_star_curve_visible_' + str(i)])
            if i <= self.stars_curves_number:
                exec('self.is_star_curve_visible_' + str(i) + ' = True')
            else:
                exec('self.is_star_curve_visible_' + str(i) + ' = False')
        self.handle_star_curves_changes(-1)

    def _load_the_scene_button_fired(self):
        try:
            print('_load_the_scene_fired')

            print('Loading settings from ' + self.load_scene_file)

            scene_json_file = open(self.load_scene_file, 'r')
            scene_json_str = scene_json_file.read()
            scene_json_file.close()

            scene = json.loads(scene_json_str)
            print(scene)

            self.is_loading = True

            self.fitsfile = scene['scene']['sceneSettings']['fits_file']

            self.xstart = scene['scene']['sceneSettings']['scene_settings']['xstart']
            self.xend = scene['scene']['sceneSettings']['scene_settings']['xend']
            self.ystart = scene['scene']['sceneSettings']['scene_settings']['ystart']
            self.yend = scene['scene']['sceneSettings']['scene_settings']['yend']
            self.zstart = scene['scene']['sceneSettings']['scene_settings']['zstart']
            self.zend = scene['scene']['sceneSettings']['scene_settings']['zend']

            self.minDT = scene['scene']['sceneSettings']['scene_settings']['minDT']
            self.maxDT = scene['scene']['sceneSettings']['scene_settings']['maxDT']
            self.opacity = scene['scene']['sceneSettings']['scene_settings']['opacity']

            self.display_arrows = scene['scene']['sceneSettings']['velocityArrowsSettings']['display_arrows']
            self.arrows_density = scene['scene']['sceneSettings']['velocityArrowsSettings']['arrows_density']

            self.azimuth = scene['scene']['sceneSettings']['viewSettings']['azimuth']
            self.elevation = scene['scene']['sceneSettings']['viewSettings']['elevation']
            self.distance = scene['scene']['sceneSettings']['viewSettings']['distance']
            self.background_color = tuple(map(int, scene['scene']['sceneSettings']['viewSettings']['background_color'].replace('(', '').replace(')', '').split(', ')))
            self.plot_colormap = scene['scene']['sceneSettings']['viewSettings']['plot_colormap']

            self.num_pics = scene['scene']['sceneSettings']['spinningViewsSettings']['num_pics']
            self.quality = scene['scene']['sceneSettings']['spinningViewsSettings']['quality']
            self.fps = scene['scene']['sceneSettings']['spinningViewsSettings']['quality']
            self.angle = scene['scene']['sceneSettings']['spinningViewsSettings']['angle']
            self.video_name = scene['scene']['sceneSettings']['spinningViewsSettings']['video_name']
            self.save_video_dir = scene['scene']['sceneSettings']['spinningViewsSettings']['save_video_dir']

            self.stars_curves_number = scene['scene']['starCurvesSettings']['starCurvesNumber']
            self.show_cone_approximation = scene['scene']['starCurvesSettings']['show_cone_approximation']
            self.factor = scene['scene']['starCurvesSettings']['factor']
            self.dx = scene['scene']['starCurvesSettings']['dx']
            self.dy = scene['scene']['starCurvesSettings']['dy']
            self.dz = scene['scene']['starCurvesSettings']['dz']

            self.show_star_curves_text = scene['scene']['starCurvesSettings']['show_star_curves_text']
            self.text_prefix = scene['scene']['starCurvesSettings']['text_prefix']
            self.use_letters = scene['scene']['starCurvesSettings']['use_letters']

            starCurves = scene['scene']['starCurvesSettings']['starCurves']
            for starCurve in starCurves:
                num = starCurve['num']

                setattr(self, 'radius_' + str(num), starCurve['r'])
                print(starCurve['angle0'])
                setattr(self, 'angle0_' + str(num), starCurve['angle0'])
                setattr(self, 'rot_vel_' + str(num), starCurve['rot_vel'])
                setattr(self, 'x0_' + str(num), starCurve['x0'])
                setattr(self, 'y0_' + str(num), starCurve['y0'])
                setattr(self, 'z0_' + str(num), starCurve['z0'])
                setattr(self, 'z_vel_' + str(num), starCurve['z_vel'])
                setattr(self, 'color_' + str(num),
                        tuple(map(int, starCurve['color'].replace('(', '').replace(')', '').split(', '))))
                setattr(self, 'initial_tube_radius_' + str(num), starCurve['init_tb'])

            self.is_loading = False

            self.display_success_result = True
            self.display_fail_result = False
            self.result = 'Loaded Successfully'

            self.update_display('view_configuration')
            # time.sleep(5)
            self.handle_star_curves_changes(-1)
        except Exception:
            err_type, err_value, traceback = sys.exc_info()
            self.display_success_result = False
            self.display_fail_result = True
            self.result = 'Load Failed: %s - %s' % (err_type, err_value)
            raise

    def _save_the_scene_button_fired(self):
        try:
            starCurvesParams = self.get_star_curves_params()

            scene = {
                'scene': {
                    'sceneSettings': {
                        'fits_file': self.fitsfile,
                        'scene_settings': {
                            'xstart': self.xstart,
                            'xend': self.xend,
                            'ystart': self.ystart,
                            'yend': self.yend,
                            'zstart': self.zstart,
                            'zend': self.zend,
                            'minDT': self.minDT,
                            'maxDT': self.maxDT,
                            'opacity': self.opacity,
                        },
                        'velocityArrowsSettings': {
                            'display_arrows': self.display_arrows,
                            'arrows_density': self.arrows_density,
                        },
                        'spinningViewsSettings': {
                            'num_pics': self.num_pics,
                            'quality': self.quality,
                            'fps': self.fps,
                            'angle': self.angle,
                            'video_name': self.video_name,
                            'save_video_dir': self.save_video_dir
                        },
                        'viewSettings': {
                            'azimuth': self.azimuth,
                            'elevation': self.elevation,
                            'distance': self.distance,
                            'background_color': str(self.background_color.getRgb()[:-1]),
                            'plot_colormap': self.plot_colormap
                        },
                    },
                    'starCurvesSettings': {
                        'starCurvesNumber': self.stars_curves_number,
                        'show_cone_approximation': self.show_cone_approximation,
                        'factor': self.factor,
                        'dx': self.dx,
                        'dy': self.dy,
                        'dz': self.dz,
                        'show_star_curves_text': self.show_star_curves_text,
                        'text_prefix': self.text_prefix,
                        'use_letters': self.use_letters,
                        'starCurves': []
                    }
                }
            }

            for i in range(0, 10):
                scene['scene']['starCurvesSettings']['starCurves'].append({
                    'num': i + 1,
                    'r': starCurvesParams[i].r,
                    'angle0': starCurvesParams[i].angle0,
                    'rot_vel': starCurvesParams[i].rot_vel,
                    'x0': starCurvesParams[i].x0,
                    'y0': starCurvesParams[i].y0,
                    'z0': starCurvesParams[i].z0,
                    'z_vel': starCurvesParams[i].z_vel,
                    'color': str(starCurvesParams[i].color),
                    'init_tb': starCurvesParams[i].init_tb,
                })

            print(scene)
            scene_json_str = json.dumps(scene, indent=4)

            if self.save_backup:
                filename = self.save_in_file
                filename = filename.replace('.json', '_%s.json' % datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
                print('Renaming existing json file \'%s\' to \'%s\'' % (self.save_in_file, filename))
                if os.path.exists(self.save_in_file):
                    os.rename(self.save_in_file, filename)

            print('Saving settings to ' + self.save_in_file)

            scene_json_file = open(self.save_in_file, 'w')
            scene_json_file.write(scene_json_str)
            scene_json_file.close()

            self.display_success_result = True
            self.display_fail_result = False
            self.result = 'Saved Successfully at ' + datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        except Exception:
            err_type, err_value, traceback = sys.exc_info()
            self.display_success_result = False
            self.display_fail_result = True
            self.result = 'Save Failed: %s - %s' % (err_type, err_value)
            raise

    def _stop_record_fired(self):
        self.is_recording_video = False

    def _record_fired(self):
        try:
            print('_record_fired')

            self.display_success_record_video_result = False
            self.display_fail_record_video_result = False

            screenshots_dir = 'Screenshots'

            if os.path.exists(screenshots_dir) is False:
                print('Creating screenshots directory')
                os.mkdir(screenshots_dir)

            print('Clearing screenshots directory of existing png files')
            png_files = [f for f in os.listdir(screenshots_dir) if os.path.isfile(os.path.join(screenshots_dir, f)) and f.endswith('.png')]
            if len(png_files) > 0:
                for i in range(len(png_files)):
                    os.remove(os.path.join(screenshots_dir, png_files[i]))

            self.is_recording_video = True

            ## Quality of the movie: 0 is the worst, 8 is ok.
            self.obj.scene.anti_aliasing_frames = self.quality
            self.obj.scene.disable_render = True

            for i in range(0, self.num_pics):
                if self.is_recording_video is not True:
                    break
                self.record_video_state = 'Saving Image %d/%d' % (i+1, self.num_pics)
                mlab.savefig(os.path.join(screenshots_dir, 'image_' + str(i).zfill(3) + '.png'))

                self.obj.scene.camera.azimuth(self.angle / self.num_pics)
                self.obj.scene.render()

            if self.is_recording_video is not True:
                return

            self.record_video_state = 'Running ffmpeg'

            self.obj.scene.disable_render = False

            image_path = os.path.join(os.getcwd(), screenshots_dir, 'image_%03d.png')
            output_path = os.path.join(self.save_video_dir, self.video_name)
            ffmpeg_command_with_args = self.ffmpeg_path + ' -r ' + str(self.fps) + ' -f image2 -s 964x954 -i ' + image_path + ' -vcodec libx264 -crf 0 -pix_fmt yuv420p ' + output_path
            print(ffmpeg_command_with_args)

            if os.path.exists(output_path):
                os.remove(output_path)

            completed = subprocess.run(ffmpeg_command_with_args.split(' '), stdout=subprocess.PIPE)
            print('returncode:', completed.returncode)
            print('{} bytes in stdout:\n{}'.format(len(completed.stdout),completed.stdout.decode('utf-8')))

            self.is_recording_video = False

            if completed.returncode == 0:
                self.record_video_result = 'Recorded Video Successfully to ' + output_path
                self.display_success_record_video_result = True
                self.display_fail_record_video_result = False
            else:
                self.record_video_result = 'Record Video Failed - ffmpeg ERROR'
                self.display_success_record_video_result = False
                self.display_fail_record_video_result = True
        except Exception:
            self.is_recording_video = False

            err_type, err_value, traceback = sys.exc_info()
            self.display_success_record_video_result = False
            self.display_fail_record_video_result = True
            self.record_video_result = 'Record Video Failed: %s - %s' % (err_type, err_value)
            raise

    def _spin_fired(self):
        i = 0
        self.obj.scene.disable_render = True

        @mlab.animate
        def anim():
            while i < self.num_pics:
                self.obj.scene.camera.azimuth(360/self.num_pics)
                self.obj.scene.render()
                yield

        a = anim()
        self.obj.scene.disable_render = False

    def _clearbutton_fired(self):
        print('_clearbutton_fired')
        mlab.clf()

        self.sregion = None
        self.region = None
        self.vol = None
        self.v_opt = None
        self.obj = None
        self.obj2 = None
        self.ax = None

        self.__init__()

    def _plotbutton_fired(self):
        print('_plotbutton_fired')
        self.load_fits_file(self.fitsfile)

    def _setview_button_fired(self):
        mlab.view(self.azimuth, self.elevation, self.distance)

    def _xstart_changed(self):
        self.update_display(change_source='view_configuration')
    def _xend_changed(self):
        self.update_display(change_source='view_configuration')
    def _ystart_changed(self):
        self.update_display(change_source='view_configuration')
    def _yend_changed(self):
        self.update_display(change_source='view_configuration')
    def _zstart_changed(self):
        self.update_display(change_source='view_configuration')
    def _zend_changed(self):
        self.update_display(change_source='view_configuration')

    def _minDT_changed(self):
        self.update_display(change_source='view_configuration')
    def _maxDT_changed(self):
        self.update_display(change_source='view_configuration')
    def _opacity_changed(self):
        self.update_display(change_source='view_configuration')

    def _factor_changed(self):
        self.handle_star_curves_changes(-1)
    def _dx_changed(self):
        self.handle_star_curves_changes(-1)
    def _dy_changed(self):
        self.handle_star_curves_changes(-1)
    def _dz_changed(self):
        self.handle_star_curves_changes(-1)

    def _show_star_curves_text_changed(self):
        self.handle_star_curves_changes(-1)
    def _text_prefix_changed(self):
        self.handle_star_curves_changes(-1)
    def _use_letters_changed(self):
        self.handle_star_curves_changes(-1)

    def _show_cone_approximation_changed(self):
        self.handle_star_curves_changes(-1)

    def get_star_curves_params(self):
        StarCurveParams = namedtuple('StarCurveParams', 'r angle0 rot_vel x0 y0 z0 z_vel color init_tb')

        starCurvesParams = []
        starCurvesParams.append(
            StarCurveParams(self.radius_1, self.angle0_1, self.rot_vel_1, self.x0_1, self.y0_1, self.z0_1, self.z_vel_1,
                            self.color_1.getRgb()[:-1], self.initial_tube_radius_1))
        starCurvesParams.append(
            StarCurveParams(self.radius_2, self.angle0_2, self.rot_vel_2, self.x0_2, self.y0_2, self.z0_2, self.z_vel_2,
                            self.color_2.getRgb()[:-1], self.initial_tube_radius_2))
        starCurvesParams.append(
            StarCurveParams(self.radius_3, self.angle0_3, self.rot_vel_3, self.x0_3, self.y0_3, self.z0_3, self.z_vel_3,
                            self.color_3.getRgb()[:-1], self.initial_tube_radius_3))
        starCurvesParams.append(
            StarCurveParams(self.radius_4, self.angle0_4, self.rot_vel_4, self.x0_4, self.y0_4, self.z0_4, self.z_vel_4,
                            self.color_4.getRgb()[:-1], self.initial_tube_radius_4))
        starCurvesParams.append(
            StarCurveParams(self.radius_5, self.angle0_5, self.rot_vel_5, self.x0_5, self.y0_5, self.z0_5, self.z_vel_5,
                            self.color_5.getRgb()[:-1], self.initial_tube_radius_5))
        starCurvesParams.append(
            StarCurveParams(self.radius_6, self.angle0_6, self.rot_vel_6, self.x0_6, self.y0_6, self.z0_6, self.z_vel_6,
                            self.color_6.getRgb()[:-1], self.initial_tube_radius_6))
        starCurvesParams.append(
            StarCurveParams(self.radius_7, self.angle0_7, self.rot_vel_7, self.x0_7, self.y0_7, self.z0_7, self.z_vel_7,
                            self.color_7.getRgb()[:-1], self.initial_tube_radius_7))
        starCurvesParams.append(
            StarCurveParams(self.radius_8, self.angle0_8, self.rot_vel_8, self.x0_8, self.y0_8, self.z0_8, self.z_vel_8,
                            self.color_8.getRgb()[:-1], self.initial_tube_radius_8))
        starCurvesParams.append(
            StarCurveParams(self.radius_9, self.angle0_9, self.rot_vel_9, self.x0_9, self.y0_9, self.z0_9, self.z_vel_9,
                            self.color_9.getRgb()[:-1], self.initial_tube_radius_9))
        starCurvesParams.append(
            StarCurveParams(self.radius_10, self.angle0_10, self.rot_vel_10, self.x0_10, self.y0_10, self.z0_10,
                            self.z_vel_10, self.color_10.getRgb()[:-1], self.initial_tube_radius_10))

        return starCurvesParams

    def get_star_curve_name(self, i):
        if self.use_letters:
            return self.letters[i-1]
        else:
            return str(i)

    def handle_star_curves_changes(self, curve_num):
        if self.is_loading:
            return 0
        print('handle_star_curves_changes', curve_num)
        StarCurveParams = namedtuple('StarCurveParams', 'r angle0 rot_vel x0 y0 z0 z_vel color initial_tube_radius')

        starCurvesParams = self.get_star_curves_params()

        for i in range(self.stars_curves_number + 1, 11):
            # exec('self.is_star_curve_visible_' + str(i) + ' = True')

            star_curve = getattr(self, 'star_curve_' + str(i))
            star_curve_start = getattr(self, 'star_curve_start_' + str(i))
            star_curve_end = getattr(self, 'star_curve_end_' + str(i))
            star_curve_text = getattr(self, 'star_curve_text_' + str(i))
            star_curve_cone_parts = getattr(self, 'star_curve_cone_' + str(i))
            for j in range(len(star_curve_cone_parts)):
                if star_curve_cone_parts[j] is not None:
                    star_curve_cone_parts[j].actor.property.opacity = 0
            if star_curve is not None:
                star_curve.actor.property.opacity = 0
            if star_curve_start is not None:
                star_curve_start.actor.property.opacity = 0
            if star_curve_end is not None:
                star_curve_end.actor.property.opacity = 0
            if star_curve_text is not None:
                star_curve_text.actor.property.opacity = 0


        min_range = curve_num
        max_range = curve_num + 1

        if curve_num == -1:
            min_range = 1
            max_range = self.stars_curves_number + 1

        text_opacity_val = self.show_star_curves_text is True if 1 else 0

        self.scene.disable_render = True

        for j in range(min_range, max_range):
            print('STAR', j)
            star_curve = getattr(self, 'star_curve_' + str(j))
            star_curve_start = getattr(self, 'star_curve_start_' + str(j))
            star_curve_end = getattr(self, 'star_curve_end_' + str(j))
            star_curve_text = getattr(self, 'star_curve_text_' + str(j))
            star_curve_cone_parts = getattr(self, 'star_curve_cone_' + str(j))
            is_star_curve_display = getattr(self, 'is_star_curve_display_' + str(j))

            opacity_val = is_star_curve_display is True if 1 else 0

            for k in range(len(star_curve_cone_parts)):
                if star_curve_cone_parts[k] is not None:
                    star_curve_cone_parts[k].actor.property.opacity = opacity_val
            if star_curve is not None:
                star_curve.actor.property.opacity = opacity_val
            if star_curve_start is not None:
                star_curve_start.actor.property.opacity = 0
            if star_curve_end is not None:
                star_curve_end.actor.property.opacity = 0
            if star_curve_text is not None:
                star_curve_text.actor.property.opacity = text_opacity_val

            if is_star_curve_display is False:
                continue

            # draw each curve
            r = starCurvesParams[j - 1].r
            angle0 = starCurvesParams[j - 1].angle0
            rot_vel = starCurvesParams[j - 1].rot_vel
            x0 = starCurvesParams[j - 1].x0
            y0 = starCurvesParams[j - 1].y0
            z0 = starCurvesParams[j - 1].z0
            z_vel = starCurvesParams[j - 1].z_vel
            color = starCurvesParams[j - 1].color

            mid_point_x = 0
            mid_point_y = 0
            mid_point_z = 0

            xx = 0
            yy = 0
            zz = 0
            x = []
            y = []
            z = []
            for i in np.linspace(0, 20, 500):
                angle = np.sign(rot_vel) * (np.abs(rot_vel) * i + angle0) * np.pi / 180
                xx = x0 + r * np.cos(angle)
                yy = y0 + r * np.sin(angle)
                zz = z0 + z_vel * i

                x.append(xx)
                y.append(yy)
                z.append(zz)

                if i == 0:
                    print(j, r, rot_vel, angle0, x0, y0, z0, xx, yy, zz, z_vel)

                if i == 10:
                    mid_point_x = xx
                    mid_point_y = yy
                    mid_point_z = zz

            x = np.array(x)
            y = np.array(y)
            z = np.array(z)

            color_temp = (color[0] / 255, color[1] / 255, color[2] / 255)

            final_tube_radius = 0.25
            initial_tube_radius = getattr(self, 'initial_tube_radius_' + str(j))

            fff = 20
            inc = (1.5 - initial_tube_radius) / len(x) * fff

            # plot star cone
            if (self.show_cone_approximation == True):
                for i in range(0, len(x), fff):
                    if star_curve_cone_parts[int(i / fff)] is not None:
                        star_curve_cone_parts[int(i / fff)].remove()
                    star_curve_cone_parts[int(i / fff)] = mlab.plot3d(self.factor * x[i:i + fff - 1] + self.dx, -self.factor * y[i:i + fff - 1] + self.dy, -self.factor * z[i:i + fff - 1] + self.dz,
                                                                      tube_radius=initial_tube_radius + i / fff * inc, color=color_temp)
            else:
                for i in range(0, len(x), fff):
                    if star_curve_cone_parts[int(i / fff)] is not None:
                        star_curve_cone_parts[int(i / fff)].remove()
                        star_curve_cone_parts[int(i / fff)] = None

            # plot star curve
            if star_curve is None:
                setattr(self, 'star_curve_' + str(j),
                        mlab.plot3d(self.factor * x + self.dx, -self.factor * y + self.dy, -self.factor * z + self.dz, tube_radius=final_tube_radius,
                                    color=color_temp))  # colormap='Spectral')
            else:
                star_curve.mlab_source.reset(x=self.factor * x + self.dx, y=-self.factor * y + self.dy, z=-self.factor * z + self.dz)
                star_curve.actor.property.color = color_temp

            # plot star start and stop glyphs
            if star_curve_start is not None:
                star_curve_start.mlab_source.set(x=self.factor * x[0] + self.dx, y=-self.factor * y[0] + self.dy, z=-self.factor * z[0] + self.dz)
            setattr(self, 'star_curve_start_' + str(j),
                    mlab.points3d(self.factor * x[0] + self.dx, -self.factor * y[0] + self.dy, -self.factor * z[0] + self.dz, color=color_temp, mode='cube'))

            if star_curve_end is not None:
                star_curve_end.mlab_source.set(x=self.factor * x[len(x) - 1] + self.dx, y=-self.factor * y[len(y) - 1] + self.dy, z=-self.factor * z[len(z) - 1] + self.dz)
            setattr(self, 'star_curve_end_' + str(j),
                    mlab.points3d(self.factor * x[len(x) - 1] + self.dx, -self.factor * y[len(y) - 1] + self.dy, -self.factor * z[len(z) - 1] + self.dz, color=color_temp, mode='sphere'))

            if text_opacity_val:
                if star_curve_text is not None:
                    star_curve_text.remove()
                star_curve_text = mlab.text3d(self.factor * x[0] + self.dx, -self.factor * y[0] + self.dy - 3, -self.factor * z[0] + self.dz, self.text_prefix + self.get_star_curve_name(j),
                                              color=color_temp, scale=1.2)
                star_curve_text.actor.property.edge_color = color_temp
                star_curve_text.actor.property.edge_visibility = True
                setattr(self, 'star_curve_text_' + str(j), star_curve_text)

        self.scene.disable_render = False



    def _radius_1_changed(self):
        self.handle_star_curves_changes(1)

    def _angle0_1_changed(self):
        self.handle_star_curves_changes(1)

    def _rot_vel_1_changed(self):
        self.handle_star_curves_changes(1)

    def _x0_1_changed(self):
        self.handle_star_curves_changes(1)

    def _y0_1_changed(self):
        self.handle_star_curves_changes(1)

    def _z0_1_changed(self):
        self.handle_star_curves_changes(1)

    def _z_vel_1_changed(self):
        self.handle_star_curves_changes(1)

    def _radius_2_changed(self):
        self.handle_star_curves_changes(2)

    def _angle0_2_changed(self):
        self.handle_star_curves_changes(2)

    def _rot_vel_2_changed(self):
        self.handle_star_curves_changes(2)

    def _x0_2_changed(self):
        self.handle_star_curves_changes(2)

    def _y0_2_changed(self):
        self.handle_star_curves_changes(2)

    def _z0_2_changed(self):
        self.handle_star_curves_changes(2)

    def _z_vel_2_changed(self):
        self.handle_star_curves_changes(2)

    def _radius_3_changed(self):
        self.handle_star_curves_changes(3)

    def _angle0_3_changed(self):
        self.handle_star_curves_changes(3)

    def _rot_vel_3_changed(self):
        self.handle_star_curves_changes(3)

    def _x0_3_changed(self):
        self.handle_star_curves_changes(3)

    def _y0_3_changed(self):
        self.handle_star_curves_changes(3)

    def _z0_3_changed(self):
        self.handle_star_curves_changes(3)

    def _z_vel_3_changed(self):
        self.handle_star_curves_changes(3)

    def _radius_4_changed(self):
        self.handle_star_curves_changes(4)

    def _angle0_4_changed(self):
        self.handle_star_curves_changes(4)

    def _rot_vel_4_changed(self):
        self.handle_star_curves_changes(4)

    def _x0_4_changed(self):
        self.handle_star_curves_changes(4)

    def _y0_4_changed(self):
        self.handle_star_curves_changes(4)

    def _z0_4_changed(self):
        self.handle_star_curves_changes(4)

    def _z_vel_4_changed(self):
        self.handle_star_curves_changes(4)

    def _radius_5_changed(self):
        self.handle_star_curves_changes(5)

    def _angle0_5_changed(self):
        self.handle_star_curves_changes(5)

    def _rot_vel_5_changed(self):
        self.handle_star_curves_changes(5)

    def _x0_5_changed(self):
        self.handle_star_curves_changes(5)

    def _y0_5_changed(self):
        self.handle_star_curves_changes(5)

    def _z0_5_changed(self):
        self.handle_star_curves_changes(5)

    def _z_vel_5_changed(self):
        self.handle_star_curves_changes(5)

    def _radius_6_changed(self):
        self.handle_star_curves_changes(6)

    def _angle0_6_changed(self):
        self.handle_star_curves_changes(6)

    def _rot_vel_6_changed(self):
        self.handle_star_curves_changes(6)

    def _x0_6_changed(self):
        self.handle_star_curves_changes(6)

    def _y0_6_changed(self):
        self.handle_star_curves_changes(6)

    def _z0_6_changed(self):
        self.handle_star_curves_changes(6)

    def _z_vel_6_changed(self):
        self.handle_star_curves_changes(6)

    def _radius_7_changed(self):
        self.handle_star_curves_changes(7)

    def _angle0_7_changed(self):
        self.handle_star_curves_changes(7)

    def _rot_vel_7_changed(self):
        self.handle_star_curves_changes(7)

    def _x0_7_changed(self):
        self.handle_star_curves_changes(7)

    def _y0_7_changed(self):
        self.handle_star_curves_changes(7)

    def _z0_7_changed(self):
        self.handle_star_curves_changes(7)

    def _z_vel_7_changed(self):
        self.handle_star_curves_changes(7)

    def _radius_8_changed(self):
        self.handle_star_curves_changes(8)

    def _angle0_8_changed(self):
        self.handle_star_curves_changes(8)

    def _rot_vel_8_changed(self):
        self.handle_star_curves_changes(8)

    def _x0_8_changed(self):
        self.handle_star_curves_changes(8)

    def _y0_8_changed(self):
        self.handle_star_curves_changes(8)

    def _z0_8_changed(self):
        self.handle_star_curves_changes(8)

    def _z_vel_8_changed(self):
        self.handle_star_curves_changes(8)

    def _radius_9_changed(self):
        self.handle_star_curves_changes(9)

    def _angle0_9_changed(self):
        self.handle_star_curves_changes(9)

    def _rot_vel_9_changed(self):
        self.handle_star_curves_changes(9)

    def _x0_9_changed(self):
        self.handle_star_curves_changes(9)

    def _y0_9_changed(self):
        self.handle_star_curves_changes(9)

    def _z0_9_changed(self):
        self.handle_star_curves_changes(9)

    def _z_vel_9_changed(self):
        self.handle_star_curves_changes(9)

    def _radius_10_changed(self):
        self.handle_star_curves_changes(10)

    def _angle0_10_changed(self):
        self.handle_star_curves_changes(10)

    def _rot_vel_10_changed(self):
        self.handle_star_curves_changes(10)

    def _x0_10_changed(self):
        self.handle_star_curves_changes(10)

    def _y0_10_changed(self):
        self.handle_star_curves_changes(10)

    def _z0_10_changed(self):
        self.handle_star_curves_changes(10)

    def _z_vel_10_changed(self):
        self.handle_star_curves_changes(10)

    def _color_1_changed(self):
        self.handle_star_curves_changes(1)

    def _color_2_changed(self):
        self.handle_star_curves_changes(2)

    def _color_3_changed(self):
        self.handle_star_curves_changes(3)

    def _color_4_changed(self):
        self.handle_star_curves_changes(4)

    def _color_5_changed(self):
        self.handle_star_curves_changes(5)

    def _color_6_changed(self):
        self.handle_star_curves_changes(6)

    def _color_7_changed(self):
        self.handle_star_curves_changes(7)

    def _color_8_changed(self):
        self.handle_star_curves_changes(8)

    def _color_9_changed(self):
        self.handle_star_curves_changes(9)

    def _color_10_changed(self):
        self.handle_star_curves_changes(10)

    def _initial_tube_radius_1_changed(self):
        self.handle_star_curves_changes(1)

    def _initial_tube_radius_2_changed(self):
        self.handle_star_curves_changes(2)

    def _initial_tube_radius_3_changed(self):
        self.handle_star_curves_changes(3)

    def _initial_tube_radius_4_changed(self):
        self.handle_star_curves_changes(4)

    def _initial_tube_radius_5_changed(self):
        self.handle_star_curves_changes(5)

    def _initial_tube_radius_6_changed(self):
        self.handle_star_curves_changes(6)

    def _initial_tube_radius_7_changed(self):
        self.handle_star_curves_changes(7)

    def _initial_tube_radius_8_changed(self):
        self.handle_star_curves_changes(8)

    def _initial_tube_radius_9_changed(self):
        self.handle_star_curves_changes(9)

    def _initial_tube_radius_10_changed(self):
        self.handle_star_curves_changes(10)

    def _is_star_curve_display_1_changed(self):
        self.handle_star_curves_changes(1)

    def _is_star_curve_display_2_changed(self):
        self.handle_star_curves_changes(2)

    def _is_star_curve_display_3_changed(self):
        self.handle_star_curves_changes(3)

    def _is_star_curve_display_4_changed(self):
        self.handle_star_curves_changes(4)

    def _is_star_curve_display_5_changed(self):
        self.handle_star_curves_changes(5)

    def _is_star_curve_display_6_changed(self):
        self.handle_star_curves_changes(6)

    def _is_star_curve_display_7_changed(self):
        self.handle_star_curves_changes(7)

    def _is_star_curve_display_8_changed(self):
        self.handle_star_curves_changes(8)

    def _is_star_curve_display_9_changed(self):
        self.handle_star_curves_changes(9)

    def _is_star_curve_display_10_changed(self):
        self.handle_star_curves_changes(10)

    def scf_scene(self):
        mlab.get_engine().current_scene = self.scene.mayavi_scene

    def handle_plane_changed(self, axis_name):
        pos = getattr(self, axis_name + '_plane')
        print('handle_plane_changed', axis_name, pos)

        ipw_3d_axis = getattr(self, 'ipw_3d_' + axis_name)
        is_scene_axis = getattr(self, 'is_scene_' + axis_name)
        if not (ipw_3d_axis == None or is_scene_axis == False):
            ipw_3d_axis.ipw.slice_index = pos # - getattr(self, axis_name + 'start')

        ipw_axis = getattr(self, 'ipw_' + axis_name)
        if ipw_axis is not None:
            ipw_axis.ipw.slice_index = pos
            self.handle_setview_axis_fired(axis_name) # unclear bug forces me to run this

        self.scf_scene()

    def _x_plane_changed(self):
        self.handle_plane_changed('x')
    def _y_plane_changed(self):
        self.handle_plane_changed('y')
    def _z_plane_changed(self):
        self.handle_plane_changed('z')

    def handle_is_scene_axis_changed(self, axis_name):
        print('handle_is_scene_axis_changed', axis_name)
        is_scene_axis = getattr(self, 'is_scene_' + axis_name)
        ipw_3d_axis = getattr(self, 'ipw_3d_' + axis_name)

        if ipw_3d_axis is not None:
            ipw_3d_axis.remove()
            setattr(self, 'ipw_3d_' + axis_name, None)

        if is_scene_axis:
            self.load_image_plane(axis_name)

        self.scf_scene()

    def _is_scene_x_changed(self):
        self.handle_is_scene_axis_changed('x')
    def _is_scene_y_changed(self):
        self.handle_is_scene_axis_changed('y')
    def _is_scene_z_changed(self):
        self.handle_is_scene_axis_changed('z')

    def load_image_planes(self):
        self.x_plane_high = self.data.shape[0]
        self.y_plane_high = self.data.shape[1]
        self.z_plane_high = self.data.shape[2]

        self.x_plane = int(self.x_plane_high / 2)
        self.y_plane = int(self.y_plane_high / 2)
        self.z_plane = int(self.z_plane_high / 2)

        print('load_image_planes', self.data.shape)

        for axis_name in self._axis_names:
            if getattr(self, 'is_scene_' + axis_name) == False:
                continue
            self.load_image_plane(axis_name)

        self.scf_scene()

    def load_image_plane(self, axis_name):
        pos = getattr(self, axis_name + '_plane')

        print('load_image_plane', axis_name, getattr(self, axis_name + '_plane'), getattr(self, axis_name + '_plane_slice_position'), getattr(self, 'ipw_' + axis_name).ipw.slice_index)

        ipw3d = mlab.pipeline.image_plane_widget(self.data_src, plane_orientation='%s_axes' % axis_name, opacity=0.1,
                                               transparent=True,
                                               slice_index=pos,
                                               reset_zoom= False,
                                               colormap=self.colormap, vmin=self.minDT, vmax=self.maxDT, figure=self.scene.mayavi_scene)

        ipw3d.ipw.margin_size_x = 0
        ipw3d.ipw.margin_size_y = 0

        ipw3d.ipw.sync_trait('slice_index', self, axis_name + '_plane_slice_position')

        setattr(self, 'ipw_3d_' + axis_name, ipw3d)

        # self.make_side_view(axis_name)
        self.scf_scene()

    def make_side_view(self, axis_name):
        print('make_side_view', axis_name)

        scene = getattr(self, 'scene_' + axis_name)

        ipw = mlab.pipeline.image_plane_widget(getattr(self,'data_src_' + axis_name),
                                               plane_orientation='%s_axes' % axis_name, opacity=0.1,
                                               transparent=True,
                                               slice_index=getattr(self, axis_name + '_plane'),
                                               reset_zoom=True,
                                               colormap=self.colormap, vmin=self.minDT, vmax=self.maxDT, figure=scene.mayavi_scene)
        ipw.ipw.margin_size_x = 0
        ipw.ipw.margin_size_y = 0
        ipw.ipw.interaction = False
        ipw.ipw.display_text = False

        if axis_name == 'x':
            vertical_size = ipw.ipw.point1[1] - 0.5
            horizontal_size = ipw.ipw.point2[2] - 0.5
        elif axis_name == 'y':
            vertical_size = ipw.ipw.point1[2] - 0.5
            horizontal_size = ipw.ipw.point2[0] - 0.5
        else:
            vertical_size = ipw.ipw.point1[0] - 0.5
            horizontal_size = ipw.ipw.point2[1] - 0.5

        # print(axis_name, vertical_size, horizontal_size)

        sign = np.sign(getattr(self, 'distance_' + axis_name))
        if sign == 0:
            sign = 1

        new_distance = 45
        if vertical_size >= horizontal_size:
            new_distance = sign*int(0.714*vertical_size)
        else:
            new_distance = sign*int(0.684*horizontal_size)

        setattr(self, 'distance_' + axis_name, new_distance)
        print(axis_name, 'vert', vertical_size, 'horz', horizontal_size, 'new_distance', new_distance)

        setattr(self, 'ipw_' + axis_name, ipw)

        ax = mlab.axes(nb_labels=5, figure=scene.mayavi_scene)
        ax.axes.property.color = (0, 0, 0)
        ax.axes.axis_title_text_property.color = (0, 0, 0)
        ax.axes.axis_title_text_property.italic = 0
        ax.axes.axis_label_text_property.color = (0, 0, 0)
        ax.axes.axis_label_text_property.italic = 0
        ax.axes.label_format = '%.0f'
        ax.axes.font_factor = 2.0
        if axis_name == 'x':
            ax.axes.x_axis_visibility = False
        elif axis_name == 'y':
            if vertical_size >= horizontal_size:
                ax.axes.z_axis_visibility = False
            else:
                ax.axes.x_axis_visibility = False
        elif axis_name == 'z':
            ax.axes.y_axis_visibility = False

        setattr(self, 'ipw_axes_' + axis_name, ax)

        azimuth = getattr(self, 'azimuth_' + axis_name)
        elevation = getattr(self, 'elevation_' + axis_name)
        distance = getattr(self, 'distance_' + axis_name)

        scene.scene.interactor.interactor_style = tvtk.InteractorStyleImage()
        scene.scene.parallel_projection = True
        scene.scene.background = (1, 1, 1)
        scene.mlab.view(azimuth, elevation, distance, figure=scene.mayavi_scene)
        scene.camera.parallel_scale = distance

        self.scf_scene()

    def handle_setview_axis_fired(self, axis_name):
        print('handle_setview_axis_fired', axis_name)

        azimuth = getattr(self, 'azimuth_' + axis_name)
        elevation = getattr(self, 'elevation_' + axis_name)
        distance = getattr(self, 'distance_' + axis_name)

        scene = getattr(self, 'scene_' + axis_name)
        # print(scene.mayavi_scene.name)
        scene.mlab.view(azimuth, elevation, distance, figure=scene.mayavi_scene)
        scene.camera.parallel_scale = distance

        self.scf_scene()

    def _setview_x_button_fired(self):
        self.handle_setview_axis_fired('x')
    def _setview_y_button_fired(self):
        self.handle_setview_axis_fired('y')
    def _setview_z_button_fired(self):
        self.handle_setview_axis_fired('z')

    def handle_axis_plane_slice_position_changed(self, axis_name):
        pos = getattr(self, axis_name + '_plane_slice_position')
        print('handle_axis_plane_slice_position_changed', axis_name, pos) #- getattr(self, axis_name + 'start'))
        setattr(self, axis_name + '_plane', int(round(pos))) # - getattr(self, axis_name + 'start'))

    def _x_plane_slice_position_changed(self):
        self.handle_axis_plane_slice_position_changed('x')
    def _y_plane_slice_position_changed(self):
        self.handle_axis_plane_slice_position_changed('y')
    def _z_plane_slice_position_changed(self):
        self.handle_axis_plane_slice_position_changed('z')

    def dump(self, obj):
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))

    def load_fits_file(self, fits_file):
        print('load_fits_file', fits_file)

        self.is_loading = True

        img = fits.open(fits_file)  # Read the fits data
        dat = img[0].data
        hdr = img[0].header

        ## The three axes loaded by fits are: velo, dec, ra so swap the axes, RA<->velo
        print(dat.shape)

        data = np.swapaxes(dat, 0, 2)
        print(data.shape)

        data[np.isnan(data)] = 0.0
        data[np.isinf(data)] = 0.0

        xstart = 0
        ystart = 0
        zstart = 0
        xend = data.shape[0] - 1
        yend = data.shape[1] - 1
        zend = data.shape[2] - 1

        region = data

        self.xstart_low = 0
        self.xstart_high = xend
        self.xend_low = 0
        self.xend_high = xend
        self.xstart = self.xstart_low
        self.xend = self.xstart_high

        self.ystart_low = 0
        self.ystart_high = yend
        self.yend_low = 0
        self.yend_high = yend
        self.ystart = self.ystart_low
        self.yend = self.ystart_high

        self.zstart_low = 0
        self.zstart_high = zend
        self.zend_low = 0
        self.zend_high = zend
        self.zstart = self.zstart_low
        self.zend = self.zstart_high

        vol = region.shape
        print(vol)
        sregion = np.empty((vol[0], vol[1], vol[2]))
        chanindex = np.linspace(0, vol[2] - 1, vol[2])
        chanindex2 = np.linspace(0, vol[2] - 1, vol[2])
        for j in range(0, vol[0] - 1):
            for k in range(0, vol[1] - 1):
                spec = region[j, k, :]
                tck = splrep(chanindex, spec, k=5)
                sregion[j, k, :] = splev(chanindex2, tck)

        ## Keep a record of the coordinates:
        crval1 = hdr['crval1']
        cdelt1 = hdr['cdelt1']
        crpix1 = hdr['crpix1']
        crval2 = hdr['crval2']
        cdelt2 = hdr['cdelt2']
        crpix2 = hdr['crpix2']
        crval3 = hdr['crval3']
        cdelt3 = hdr['cdelt3']
        crpix3 = hdr['crpix3']

        ra_start = (xstart + 1 - crpix1) * cdelt1 + crval1
        ra_end = (xend + 1 - crpix1) * cdelt1 + crval1

        dec_start = (ystart + 1 - crpix2) * cdelt2 + crval2
        dec_end = (yend + 1 - crpix2) * cdelt2 + crval2

        vel_start = (zstart + 1 - crpix3) * cdelt3 + crval3
        vel_end = (zend + 1 - crpix3) * cdelt3 + crval3

        vel_start /= 1e3
        vel_end /= 1e3

        extent = [ra_start, ra_end, dec_start, dec_end, vel_start, vel_end]
        print(extent)

        v_opt = np.linspace(vel_end, vel_start, vol[2]) * 1000
        print('v_opt', v_opt)

        self.sregion = sregion
        self.region = region
        self.vol = vol
        self.v_opt = v_opt

        sregion = np.copy(self.sregion)
        region = np.copy(self.region)

        print('!!!!!!!!!!', np.min(sregion))

        self.maxDT = np.max(sregion)

        temp_region = np.zeros(self.vol)

        sub_extent = [self.xstart, self.xend, self.ystart, self.yend, self.zstart, self.zend]
        print(sub_extent)



        sregion = self.sregion[sub_extent[0]:sub_extent[1], sub_extent[2]:sub_extent[3], sub_extent[4]:sub_extent[5]]
        temp_region = temp_region[sub_extent[0]:sub_extent[1], sub_extent[2]:sub_extent[3], sub_extent[4]:sub_extent[5]]
        region = self.region[sub_extent[0]:sub_extent[1], sub_extent[2]:sub_extent[3], sub_extent[4]:sub_extent[5]]

        mlab.clf()
        fig = mlab.gcf()
        fig.scene.interactor.interactor_style = tvtk.InteractorStyleTerrain()
        fig.scene.disable_render = True

        X, Y, Z = np.mgrid[sub_extent[0]:sub_extent[1]:complex(0, sub_extent[1] - sub_extent[0]),
                  sub_extent[2]:sub_extent[3]:complex(0, sub_extent[3] - sub_extent[2]),
                  sub_extent[4]:sub_extent[5]:complex(0, sub_extent[4] - sub_extent[5])]

        obj = mlab.contour3d(sregion, contours=28, transparent=True, opacity=0.1, colormap=self.colormap,
                             vmin=self.minDT, vmax=self.maxDT)

        # print(obj.module)
        fig.scene.renderer.use_depth_peeling = True
        fig.scene.renderer.maximum_number_of_peels = 1

        obj2 = mlab.quiver3d(X, Y, Z, temp_region, temp_region, region, colormap='rainbow', mask_points=self.arrows_density)
        obj2.module_manager.vector_lut_manager.reverse_lut = True

        cb = mlab.colorbar(obj, orientation='vertical', title='Intensity [' + self.intensity_units + ']')
        cb.scalar_bar.unconstrained_font_size = True
        cb.label_text_property.italic = 0
        cb.label_text_property.font_size = 20
        cb.title_text_property.italic = 0
        cb.title_text_property.font_size = 20
        cb.scalar_bar_representation.position = np.array([0.02145833, 0.14152542])
        cb.scalar_bar_representation.position2 = np.array([0.1, 0.78411017])

        cb2 = mlab.colorbar(obj2, orientation='vertical', title='Velocity [km/s]',
                            nb_labels=10)  # italic=False, font_size=8
        cb2.scalar_bar.unconstrained_font_size = True
        cb2.label_text_property.italic = 0
        cb2.label_text_property.font_size = 24
        cb2.title_text_property.italic = 0
        cb2.title_text_property.font_size = 20
        cb2.title_text_property.line_offset = 10

        ax = mlab.axes(nb_labels=5)
        ax.axes.property.color = (1, 1, 1)
        ax.axes.axis_title_text_property.color = (1, 1, 1)
        ax.axes.axis_title_text_property.italic = 0
        ax.axes.axis_label_text_property.color = (1, 1, 1)
        ax.axes.axis_label_text_property.italic = 0
        ax.axes.label_format = '%.0f'

        self.obj = obj
        self.obj2 = obj2
        self.ax = ax

        print('loaded')

        mlab.view(self.azimuth, self.elevation, self.distance)

        fig.scene.disable_render = False

        mlab.show()

        print('velocity range', np.array([np.min(np.abs(v_opt)), np.max(np.abs(v_opt))]))

        self.is_loading = False
        self.update_display('view_configuration')

    def update_display(self, change_source=''):
        if self.is_loading:
            return 0

        print('update_display', change_source)

        ms = self.obj.mlab_source
        ms2 = self.obj2.mlab_source

        temp_region = np.zeros(self.vol)

        sub_extent = [self.xstart, self.xend, self.ystart, self.yend, self.zstart, self.zend]
        print(sub_extent)

        sregion = np.copy(self.sregion)
        region = np.copy(self.region)

        print('min1: ', np.min(sregion))

        sregion = sregion[sub_extent[0]:sub_extent[1], sub_extent[2]:sub_extent[3], sub_extent[4]:sub_extent[5]]
        temp_region = temp_region[sub_extent[0]:sub_extent[1], sub_extent[2]:sub_extent[3], sub_extent[4]:sub_extent[5]]
        region = region[sub_extent[0]:sub_extent[1], sub_extent[2]:sub_extent[3], sub_extent[4]:sub_extent[5]]

        # displayThreshold update
        for i in range(sregion.shape[0]):
            for j in range(sregion.shape[1]):
                for k in range(sregion.shape[2]):
                    # print(i,j,k)
                    region[i, j, k] = 0
                    if sregion[i, j, k] < self.minDT:
                        sregion[i, j, k] = 0
                    if self.min_itensity_for_velocity <= sregion[i, j, k] < self.maxDT:
                        region[i, j, k] = self.v_opt[k + sub_extent[4]]

        X, Y, Z = np.mgrid[sub_extent[0]:sub_extent[1]:complex(0, sub_extent[1] - sub_extent[0]),
                  sub_extent[2]:sub_extent[3]:complex(0, sub_extent[3] - sub_extent[2]),
                  sub_extent[4]:sub_extent[5]:complex(0, sub_extent[4] - sub_extent[5])]

        print(sregion.shape, temp_region.shape, region.shape)

        print('min2: ', self.minDT, np.min(sregion))

        fig = mlab.gcf()
        fig.scene.disable_render = True

        ms.reset(x=X, y=Y, z=Z, scalars=sregion, vmin=self.minDT, vmax=self.maxDT)
        self.obj.actor.property.opacity = self.opacity

        self.ax.axes.bounds = np.array(sub_extent)

        self.obj.module_manager.scalar_lut_manager.data_range = np.array([self.minDT, self.maxDT])
        print(self.obj2.module_manager.vector_lut_manager.data_range)
        self.obj2.module_manager.vector_lut_manager.data_range = np.array([0, np.max(self.v_opt)])

        ms2.reset(x=X, y=Y, z=Z, u=temp_region, v=temp_region, w=region, extent=sub_extent)

        self.obj2.module_manager.vector_lut_manager.use_default_range = False
        self.obj2.module_manager.vector_lut_manager.data_range = np.array([np.min(np.abs(region)), np.max(np.abs(region))])

        self.data = sregion
        try:
            if self.data_src is not None:
                self.data_src.remove()
            if self.data_src_x is not None:
                self.data_src_x.remove()
            if self.data_src_y is not None:
                self.data_src_y.remove()
            if self.data_src_z is not None:
                self.data_src_z.remove()
        except:
            pass
        self.data_src = mlab.pipeline.scalar_field(X,Y,Z,sregion, figure=self.scene.mayavi_scene)
        self.data_src_x = mlab.pipeline.scalar_field(sregion, figure=self.scene_x.mayavi_scene)
        self.data_src_y = mlab.pipeline.scalar_field(sregion, figure=self.scene_y.mayavi_scene)
        self.data_src_z = mlab.pipeline.scalar_field(sregion, figure=self.scene_z.mayavi_scene)

        self.load_image_planes()

        if change_source == 'view_configuration':
            for axis_name in self._axis_names:
                axis_plane = getattr(self, axis_name + '_plane')
                axis_start = getattr(self, axis_name + 'start')
                axis_end = getattr(self, axis_name + 'end')

                axis_end -= axis_start
                axis_start = 0

                print('!!!!!', axis_name, axis_plane, axis_start, axis_end)

                if axis_plane < axis_start:
                    setattr(self, axis_name + '_plane', axis_start)
                elif axis_plane > axis_end:
                    setattr(self, axis_name + '_plane', axis_end)

                setattr(self, axis_name + '_plane_low', axis_start)
                setattr(self, axis_name + '_plane_high', axis_end)

                if getattr(self, 'is_scene_' + axis_name):
                    self.handle_is_scene_axis_changed(axis_name)

                ipw_axis = getattr(self, 'ipw_' + axis_name)
                ipw_axis_axes = getattr(self, 'ipw_axes_' + axis_name)
                if ipw_axis is not None:
                    ipw_axis.remove()
                    ipw_axis_axes.remove()
                    setattr(self, 'ipw_' + axis_name, None)
                self.make_side_view(axis_name)

        fig.scene.disable_render = False

        mlab.draw()

app = StellarMovementSimulation()
app.configure_traits()
