# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 21:50:53 2017

LSDPlottingRaster

@author: DAV and SMM

Object-oriented plotting module for constructing
drape maps in a reusable, generic way.

Experimental. Use at your own risk.

This software is realsed under the Artistic Licence v2.0

"""

# LSDPlottingTools must be in your pythonpath
import LSDPlottingTools as LSDP
from . import PlottingHelpers as phelp
import matplotlib.pyplot as plt
import matplotlib.cm as _cm
import matplotlib.colors as _mcolors
import matplotlib.axes
import numpy as np
from matplotlib import ticker
from matplotlib import rcParams


class BaseRaster(object):
    """
    Class BaseRaster represents the data associated with the basic rasters
    used to create to image to be plotted. It also contains the methods
    associated with performing any basic analyses to that raster.

    Args:
        RasterName (str): The name of the rasters (with extension). It is read by gdal so should cope with mulitple formats
        Directory (str): The path to the raster. Needs to have the trailing slash
        NFF_opti (bool): experimental test of reading raster using numpy.fromfile() which a super efficient binary reader
    """
    def __init__(self, RasterName, Directory, NFF_opti = False):

        self._RasterFileName = RasterName
        self._RasterDirectory = Directory
        self._FullPathRaster = self._RasterDirectory + self._RasterFileName

        # I think the BaseRaster should contain a numpy array of the Raster
        if(NFF_opti):
            self._RasterArray = LSDP.ReadRasterArrayBlocks_numpy(self._FullPathRaster)
        else:
            self._RasterArray = LSDP.ReadRasterArrayBlocks(self._FullPathRaster)

        # Get the extents as a list
        self._RasterExtents = LSDP.GetRasterExtent(self._FullPathRaster)
        self._RasterAspectRatio = (self._RasterExtents[1]-self._RasterExtents[0])/(self._RasterExtents[3]-self._RasterExtents[2])

        # set the default colourmap
        self._colourmap = "gray"

        # get the EPSG string
        self._EPSGString = LSDP.LSDMap_IO.GetUTMEPSG(self._FullPathRaster)
        #print("The EPSGString is: "+ self._EPSGString)

    @property
    def extents(self):
        return self._RasterExtents

    @property
    def fullpath_to_raster(self):
        return self._FullPathRaster

    @property
    def raster_filename(self):
        return self._RasterFileName

    @property
    def xmin(self):
        self.x_min = self._RasterExtents[0]

    @property
    def ymin(self):
        self.y_min = self._RasterExtents[2]

    @property
    def xmax(self):
        self.x_max = self._RasterExtents[1]

    @property
    def ymax(self):
        self.x_max = self._RasterExtents[3]

    # The default colormap is gray
    @property
    def colourmap(self):
        self._colourmap = "gray"

    # This controls the zorder of the raster
    @property
    def zorder(self):
        self._zorder = 1

    #def get_apect_ratio(self):
    #    # Get the aspect ratio
    #    self._RasterAspectRatio = (self.xmax-self.xmin)/(self.ymax-self.ymin)
    #    return self._RasterAspectRatio

    def set_raster_type(self, rastertype):
        """
        Renders the background image that
        will form the drape plot, e.g. a hillshade

        Args:
            rastertype (str): The type of raster. Not many supported, but basically just changes the colourmap
        """
        self._rastertype = rastertype
        if self._rastertype == "Hillshade":
            print("I'm using a hillshade colour scheme")
            self._colourmap = "gray"

        elif self._rastertype == "Terrain":
            print("I'm using a terrain colour scheme")
            self._colourmap = LSDP.colours.UsefulColourmaps.darkearth
        else:
            print ("That raster style is not yet supported. Currently only " \
                   " 'Hillshade' and 'Terrain' are supported.")

    def set_colourmap(self, cmap):
        """
        There must be a more pythonic way to do this! But sets the colourmap

        Args:
            cmap (list or str): the colourmap
        """
        self._colourmap = cmap

    def _initialise_masks(self):
        """
        Some logic Declan wrote to mask values.
        """
        if self._drapeminthreshold is not None:
            self.mask_low_values()
        if self._drapemaxthreshold is not None:
            self.mask_high_values()
        if self._middlemaskrange is not None:
            self.mask_middle_values()

    def mask_low_values(self):#
        """
        Reads from the self._drapeminthreshold to mask low values.
        """
        low_values_index = self._RasterArray < self._drapeminthreshold
        self._RasterArray[low_values_index] = np.nan

    def mask_high_values(self):
        """
        Reads from the self._drapeminthreshold to mask high values.
        """
        high_values_index = self._RasterArray < self._drapemaxthreshold
        self._RasterArray[high_values_index] = np.nan

    def mask_middle_values(self):
        """Masks a centre range of values."""
        masked_mid_values_index = (np.logical_and(self._RasterArray > self._middlemaskrange[0],
                                   self._RasterArray < self._middlemaskrange[1]))
        self._RasterArray[masked_mid_values_index] = np.nan

    def show_raster(self):
        """
        Low level show function. Only really used for debugging since it contains
        no sizing, labelling etc.
        """
        plt.imshow(self._RasterArray,
                   cmap=self._colourmap,
                   extent=self.extents)
        plt.show()

    def replace_raster_values(self, old_values = [], new_values = []):
        """
        Function to take a list of raster values and replace it with
        a new list. Can be used to overwrite basin junction IDs with other
        information about the basin, for example.
        FJC 17/06/17
        """
        for idx, value in enumerate(old_values):
            old_values_index = self._RasterArray == value
            self._RasterArray[old_values_index] = new_values[idx]
        #print self._RasterArray


class MapFigure(object):
    """
    This is the main object used for plotting. It contains the underlying axes of the figures.
    At the moment the4 axes contain typically a colourbar and a main image axis.
    The function also contains routines for sizing, draping, adding point data,
    etc.
    """
    def __init__(self, BaseRasterName, Directory,
                 coord_type="UTM", colourbar_location = "None",NFF_opti = False,*args, **kwargs):

        # A map figure has one figure
        #self.fig = plt.figure(1, facecolor='white',figsize=(6,3))
        #self.fig

        # There can be mulitple axes in the figure. These are maptlotlib artists
        # that can be used to place plotting elements
        #self.ax = self.fig.add_axes([0.1,0.1,0.7,0.7])
        #self.ax = plt.subplots()

        #self.fig, self.ax = plt.subplots()
        fig = plt.figure()
        self.ax_list = []
        ax = fig.add_axes([0,0,1,1])
        self.ax_list.append(ax)

        # check the colourbar location
        if colourbar_location == "Top" or colourbar_location == "TOP":
            colourbar_location = "top"
        if colourbar_location == "Bottom" or colourbar_location == "BOTTOM":
            colourbar_location = "bottom"
        if colourbar_location == "Left" or colourbar_location == "LEFT":
            colourbar_location = "left"
        if colourbar_location == "Right" or colourbar_location == "RIGHT":
            colourbar_location = "right"

        print("Your colourbar will be located: "+ colourbar_location)
        if colourbar_location == "top" or colourbar_location == "bottom":
            self.colourbar_location = colourbar_location
            self.colourbar_orientation = "horizontal"
        elif colourbar_location == "left" or colourbar_location == "right":
            self.colourbar_location = colourbar_location
            self.colourbar_orientation = "vertical"
        elif colourbar_location == "None":
            self.colourbar_location = "None"
            self.colourbar_orientation = "None"
        else:
            print("You did not choose a valid colourbar location. Options are top, left, right, bottom and None. Defaulting to None.")
            self.colourbar_location = "None"
            self.colourbar_orientation = "None"

        # Names of the directory and the base raster
        self._Directory = Directory
        self._BaseRasterName = BaseRasterName
        self._BaseRasterFullName = Directory+BaseRasterName


        self.FigFileName = self._Directory+"TestFig.png"
        self.FigFormat = "png"


        # The way this is going to work is that you can have many rasters in the
        # plot that get appended into a list. Each one has its own colourmap
        # and properties
        self._RasterList = []
        self._RasterList.append(BaseRaster(BaseRasterName,Directory, NFF_opti = NFF_opti))

        # The coordinate type. UTM and UTM with tick in km are supported at the moment
        self._set_coord_type(coord_type)

        # Get the tick properties
        self._xmin = self._RasterList[0].xmin
        self._ymin = self._RasterList[0].ymin
        self._xmax = self._RasterList[0].xmax
        self._ymax = self._RasterList[0].ymax
        self._n_target_ticks = 5
        self.make_ticks()

        self._num_drapes = 0  # Number of drapes in the image.
        # We will increase this everytime we call ax.imshow.

        # Stores the Image instances generated from imshow()
        self._drape_list = []

        self.ax_list = self.make_base_image(self.ax_list)
        print(self.ax_list[0])


    def make_ticks(self):
        """
        This function makes the tick marks and the tick labels.
        It has been optimised so you get nice looking ticks, so you shouldn't have to mess with them after this is called.
        """

        if self._coord_type == "UTM":
            self.tick_xlocs,self.tick_ylocs,self.tick_x_labels,self.tick_y_labels = LSDP.GetTicksForUTMNoInversion(self._BaseRasterFullName,self._xmax,self._xmin,
                             self._ymax,self._ymin,self._n_target_ticks)
        elif self._coord_type == "UTM_km":
            self.tick_xlocs,self.tick_ylocs,self.tick_x_labels,self.tick_y_labels = LSDP.GetTicksForUTMNoInversion(self._BaseRasterFullName,self._xmax,self._xmin,
                             self._ymax,self._ymin,self._n_target_ticks)
            n_hacked_digits = 3
            self.tick_x_labels = LSDP.TickLabelShortenizer(self.tick_x_labels,n_hacked_digits)
            self.tick_y_labels = LSDP.TickLabelShortenizer(self.tick_y_labels,n_hacked_digits)
        else:
            raise ValueError("Sorry, the coordinate type: ", self._coord_type,
                             "is not yet supported")

        print("I made the ticks.")
        print("x labels are: ")
        print(self.tick_x_labels)
        print("x locations are:")
        print(self.tick_xlocs)
        print("y labels are: ")
        print(self.tick_y_labels)
        print("y locations are:")
        print(self.tick_ylocs)

    def add_ticks_to_axis(self,ax):
        """
        This is a low level function for placing the ticks on the active image axis.
        """
        ax.set_xticklabels(self.tick_x_labels)
        ax.set_yticklabels(self.tick_y_labels)
        ax.set_xticks(self.tick_xlocs)
        ax.set_yticks(self.tick_ylocs)
        ax.set_xlabel(self._xaxis_label)
        ax.set_ylabel(self._yaxis_label)

        return ax

    def axis_styler(self,ax_list,axis_style="Normal"):
        """This sets the line width and fonts on the axes.

        Args:
            ax_list (axes objects): the list of axis objects
            axis_style (string): The syle of the axis. See options below.
        """

        if axis_style == "Normal":
            lw = 1              # line width
            ftsz = 10           # Size of tick label font
            tpd = 2             # Tick padding
            label_ftsz = 12     # Fontsize of axis label
        elif axis_style == "Thick":
            lw = 2
            ftsz = 10
            tpd = 2
            label_ftsz = 12
        elif axis_style == "Thin":
            lw = 0.5
            ftsz = 8
            tpd = 1
            label_ftsz = 10
        elif axis_style == "Big":
            lw = 2
            ftsz = 12
            tpd = 3
            label_ftsz = 14
        elif axis_style == "Madhouse":
            # This is just a crazy style to test if the figure is actually recieving these instructions
            lw = 4
            ftsz = 20
            tpd = 3
            label_ftsz = 6
        else:
            print("Using the default axis styling")
            lw = 1
            ftsz = 10
            tpd = 2
            label_ftsz = 12

        for ax in ax_list:
            # Now to fix up the axes
            ax.spines['top'].set_linewidth(lw)
            ax.spines['left'].set_linewidth(lw)
            ax.spines['right'].set_linewidth(lw)
            ax.spines['bottom'].set_linewidth(lw)

            ax.xaxis.label.set_size(label_ftsz)
            ax.yaxis.label.set_size(label_ftsz)

            # This gets all the ticks, and pads them away from the axis so that the corners don't overlap
            ax.tick_params(axis='both', width=lw, pad = tpd, labelsize = ftsz )

        return ax_list


    def make_base_image(self,ax_list):
        """
        This function creates the base image. It creates the axis for the base image,
        further drapes and point data are placed upon this image .
        """

        # We need to initiate with a figure
        #self.ax = self.fig.add_axes([0.1,0.1,0.7,0.7])

        print("This colourmap is: "+ self._RasterList[0]._colourmap)
        im = self.ax_list[0].imshow(self._RasterList[0]._RasterArray, self._RasterList[0]._colourmap, extent = self._RasterList[0].extents, interpolation="nearest")

        # This affects all axes because we set share_all = True.
        #ax.set_xlim(self._xmin,self._xmax)
        #ax.set_ylim(self._ymin,self._ymax)
        self.ax_list[0] = self.add_ticks_to_axis(self.ax_list[0])
        self._drape_list.append(im)

        print("The number of axes are: "+str(len(self._drape_list)))

        print(self.ax_list[0])
        return self.ax_list

    def add_drape_image(self,RasterName,Directory,colourmap = "gray",
                        alpha=0.5,
                        show_colourbar = False,
                        colorbarlabel = "Colourbar", discrete_cmap=False, n_colours=10, norm = "None", modify_raster_values=False, old_values=[], new_values=[], cbar_type=float, NFF_opti = False):

        print("N axes are: "+str(len(self.ax_list)))
        print(self.ax_list[0])

        self.ax_list = self._add_drape_image(self.ax_list,RasterName,Directory,colourmap,alpha,colorbarlabel,discrete_cmap,n_colours,norm,modify_raster_values,old_values,new_values,cbar_type, NFF_opti)
        #print("Getting axis limits in drape function: ")
        #print(self.ax_list[0].get_xlim())


    def _add_drape_image(self,ax_list,RasterName,Directory,
                         colourmap = "gray",
                         alpha=0.5,
                         colorbarlabel = "Colourbar", discrete_cmap=False, n_colours=10, nroma = "None", modify_raster_values = False, old_values=[], new_values = [], cbar_type=float, NFF_opti = False):

        Raster = BaseRaster(RasterName,Directory, NFF_opti = NFF_opti)
        if modify_raster_values == True:
            Raster.replace_raster_values(old_values, new_values)

        if discrete_cmap == True:
            print("N colours: "+str(n_colours))
            colourmap = self.cmap_discretize(colourmap, n_colours)

        self._RasterList.append(Raster)
        self._RasterList[-1].set_colourmap(colourmap)

        # We need to initiate with a figure
        #self.ax = self.fig.add_axes([0.1,0.1,0.7,0.7])
        if(nroma != "None"):
            im = self.ax_list[0].imshow(self._RasterList[-1]._RasterArray, self._RasterList[-1]._colourmap, extent = self._RasterList[0].extents, interpolation="nearest",alpha = alpha, norm = nroma)
        else:
            im = self.ax_list[0].imshow(self._RasterList[-1]._RasterArray, self._RasterList[-1]._colourmap, extent = self._RasterList[0].extents, interpolation="nearest",alpha = alpha)
        # This affects all axes because we set share_all = True.
        #ax.set_xlim(self._xmin,self._xmax)
        #ax.set_ylim(self._ymin,self._ymax)
        self.ax_list[0] = self.add_ticks_to_axis(self.ax_list[0])
        self._drape_list.append(im)

        print("The number of axes are: "+str(len(self._drape_list)))

        if self.colourbar_orientation != "None":
            self.ax_list = self.add_colourbar(self.ax_list,im,self._RasterList[-1],
                                              colorbarlabel = colorbarlabel, discrete=discrete_cmap, n_colours=n_colours, cbar_type=cbar_type)


        return self.ax_list


    def cmap_discretize(self, cmap, N):
        """
        Return a discrete colormap from the continuous colormap cmap.
        From http://scipy.github.io/old-wiki/pages/Cookbook/Matplotlib/ColormapTransformations

        Args:
             cmap: colormap instance, eg. cm.jet.
             N: number of colors.

        Returns:
            discrete colourmap

        Author: FJC

        """

        if type(cmap) == str:
         cmap = get_cmap(cmap)

        colors_i = np.concatenate((np.linspace(0, 1., N), (0.,0.,0.,0.)))
        colors_rgba = cmap(colors_i)
        indices = np.linspace(0, 1., N+1)
        cdict = {}

        for ki,key in enumerate(('red','green','blue')):
         cdict[key] = [ (indices[i], colors_rgba[i-1,ki], colors_rgba[i,ki]) for i in xrange(N+1) ]

        # Return colormap object.
        return _mcolors.LinearSegmentedColormap(cmap.name + "_%d"%N, cdict, 1024)

    def add_colourbar(self,ax_list,im,BaseRaster,colorbarlabel = "Colourbar",discrete=False, n_colours=10, cbar_type=float):
        fig = matplotlib.pyplot.gcf()
        ax_list.append(fig.add_axes([0.1,0.8,0.05,0.2]))
        cbar = plt.colorbar(im,cmap=BaseRaster._colourmap,spacing='uniform', orientation=self.colourbar_orientation,cax=ax_list[-1])

        if discrete==True:
            # change ticks
            self.fix_colourbar_ticks(BaseRaster, cbar, n_colours, cbar_type)

        #Will's changes:
        # Changed rotation of colourbar text to 90 and the labelpad to -75 for "left"

        if self.colourbar_location == 'top':
            ax_list[-1].set_xlabel(colorbarlabel, fontname='Arial',labelpad=5)
        elif self.colourbar_location == 'bottom':
            ax_list[-1].set_xlabel(colorbarlabel, fontname='Arial',labelpad=5)
        elif self.colourbar_location == 'left':
            ax_list[-1].set_ylabel(colorbarlabel, fontname='Arial',labelpad=-75,rotation=90)
        elif self.colourbar_location == 'right':
            ax_list[-1].set_ylabel(colorbarlabel, fontname='Arial',labelpad=10,rotation=270)
        return ax_list

    def fix_colourbar_ticks(self, BaseRaster, cbar,n_colours, cbar_type=float):
        """
        This function takes a discrete colourbar and fixes the ticks so they are
        in the middle of each colour

        Args:
            cbar: the colourbar
        Returns:
            None but fixes ticks

        Author: FJC
        """
        # get the min and the max of the colourbar
        vmin = np.nanmin(BaseRaster._RasterArray)
        vmax = np.nanmax(BaseRaster._RasterArray)
        print vmin, vmax

        # get the additional end spacing for colourbar
        tick_spacing = (vmax-vmin)/(n_colours)
        print tick_spacing
        new_vmin = vmin-(tick_spacing/2)
        new_vmax = vmax+(tick_spacing/2)+tick_spacing

        #get list of tick locations
        tick_locs = np.arange(new_vmin, new_vmax, step=tick_spacing)
        print tick_locs

        # update ticks
        tick_locator = ticker.FixedLocator(tick_locs)
        cbar.locator = tick_locator
        cbar.update_ticks()

        print BaseRaster._RasterArray[np.isnan(BaseRaster._RasterArray) == False]

        # get tick labels
        tick_labels = np.linspace(vmin, vmax, n_colours)
        if cbar_type == int:
            tick_labels = [str(int(x)) for x in tick_labels]
        else:
            tick_labels = [str(x) for x in tick_labels]
        print tick_labels
        cbar.set_ticklabels(tick_labels)

    def add_point_colourbar(self,ax_list,sc,cmap = "cubehelix",colorbarlabel = "Colourbar"):
        fig = matplotlib.pyplot.gcf()
        ax_list.append(fig.add_axes([0.1,0.8,0.2,0.5]))
        cbar = plt.colorbar(sc,cmap=cmap, orientation=self.colourbar_orientation,cax=ax_list[-1])
        #cbar.set_label(colorbarlabel, fontsize=10)


        #Will's changes:
        # Changed rotation of colourbar text to 90 and the labelpad to -75 for "left"

        if self.colourbar_location == 'top':
            ax_list[-1].set_xlabel(colorbarlabel, fontname='Arial',labelpad=5)
        elif self.colourbar_location == 'bottom':
            ax_list[-1].set_xlabel(colorbarlabel, fontname='Arial',labelpad=5)
        elif self.colourbar_location == 'left':
            ax_list[-1].set_ylabel(colorbarlabel, fontname='Arial',labelpad=-75,rotation=90)
        elif self.colourbar_location == 'right':
            ax_list[-1].set_ylabel(colorbarlabel, fontname='Arial',labelpad=10,rotation=270)
        return ax_list


    def add_point_data(self, thisPointData,column_for_plotting = "None",
                       this_colourmap = "cubehelix",colorbarlabel = "Colourbar",
                       scale_points = False,column_for_scaling = "None",
                       scaled_data_in_log = False,
                       max_point_size = 5,
                       min_point_size = 0.5, coulor_log = False, coulor_manual_scale = [], manual_size = 0.5, alpha = 1, minimum_log_scale_cut_off = -10):

        # Get the axis limits to assert after
        this_xlim = self.ax_list[0].get_xlim()
        this_ylim = self.ax_list[0].get_ylim()

        EPSG_string = self._RasterList[0]._EPSGString
        print("I am going to plot some points for you. The EPSG string is:"+EPSG_string)

        # convert to easting and northing
        [easting,northing] = thisPointData.GetUTMEastingNorthing(EPSG_string)

        # check if the column for plotting exists
        this_data = thisPointData.QueryData(column_for_plotting)
        # Log the color if required
        if(coulor_log):
            this_data = np.log10(this_data)
            print("I logged (is it a verb?) your colour data, the minimum is %s and the maximum is %s" %(np.nanmin(this_data), np.nanmax(this_data)))

        # Now the data for scaling. Point size will be scaled by these data

        scale_data = thisPointData.QueryData(column_for_scaling)

        # If there is scaled data, convert to log if that option is selected
        if scaled_data_in_log:
            if len(scale_data) == 0 or len(scale_data) != len(easting):
                scale_data = [0.5]
            else:
                # We need this logic since we can get nans and -Infs from 0 and negative numbers
                scale_data = np.log10(scale_data)
                print("I logged (is it a verb?) your scaled data, the minimum is %s and the maximum is %s but all the values inferior to %s will be %s" %(np.nanmin(scale_data), np.nanmax(scale_data), minimum_log_scale_cut_off, minimum_log_scale_cut_off))
                scale_data[scale_data < minimum_log_scale_cut_off] = minimum_log_scale_cut_off


        # scale the points if you want
        if scale_points == True:
            if len(scale_data) == 0 or len(scale_data) != len(easting):
                point_scale = manual_size
            else:
                max_sd = np.nanmax(scale_data)
                min_sd = np.nanmin(scale_data)

                print("max is: "+str(max_sd)+ " and min is: "+ str(min_sd))

                # now rescale the data. Always a linear scaling.
                new_scale = []
                size_range = max_point_size-min_point_size
                for datum in scale_data:
                    frac = (datum-min_sd)/(max_sd-min_sd)
                    new_size = frac*size_range+min_point_size
                    new_scale.append(new_size)
                ns_array = np.asarray(new_scale)
                point_scale = ns_array

        else:
            point_scale = manual_size

        if len(this_data) == 0 or len(this_data) != len(easting):
            print("I am only plotting the points.")
            sc = self.ax_list[0].scatter(easting,northing,s=point_scale, c="blue",cmap=this_colourmap,edgecolors='none', alpha = alpha)
        else:
            if(coulor_manual_scale != []):
                print("let me rescale the data using your array")
                if(len(coulor_manual_scale) == 2):
                    cNorm  = _mcolors.Normalize(vmin=coulor_manual_scale[0], vmax=coulor_manual_scale[1])
                    scalarMap = _cm.ScalarMappable(norm = cNorm, cmap= this_colourmap)
                    tps_color = scalarMap.to_rgba(this_data)
                    scalarMap.set_array(tps_color)
                    this_colourmap = scalarMap
                    sc = self.ax_list[0].scatter(easting,northing,s=point_scale, c=tps_color,cmap=this_colourmap,edgecolors='none', alpha = alpha)

                else:
                    print("Your coulor_log_manual_scale should be something like [min,max], aborting")
                    quit()
            else:
                sc = self.ax_list[0].scatter(easting,northing,s=point_scale, c=this_data,cmap=this_colourmap,edgecolors='none', alpha = alpha)

        # Annoying but the scatter plot resets the extents so you need to reassert them
        self.ax_list[0].set_xlim(this_xlim)
        self.ax_list[0].set_ylim(this_ylim)

        print("The colourbar orientation for point plotting is: "+self.colourbar_orientation)
        if self.colourbar_orientation != "None":
            print("Let me add a colourbar for your point data")
            self.ax_list = self.add_point_colourbar(self.ax_list,sc,cmap=this_colourmap, colorbarlabel = colorbarlabel)

    def add_text_annotation_from_points(self, thisPointData,column_for_plotting = "None",
                                        selection_criteria = [], PANDEX=False, border_colour='k', text_colour='r', alpha=1):
        """
        This adds annotations to points. Used for annotating basins or sources, for example.
        """

        # A list of text objects
        texts = []

        # Get the axis limits to assert after
        this_xlim = self.ax_list[0].get_xlim()
        this_ylim = self.ax_list[0].get_ylim()

        # Format the bounding box
        bbox_props = dict(boxstyle="circle,pad=0.1", fc="w", ec=border_colour, lw=0.5,alpha = alpha)

        # see if the data column exists
        test_data = thisPointData.QueryData(column_for_plotting, PANDEX=PANDEX)

        if len(test_data) == 0:
            print("There is no data with the column name: "+column_for_plotting)
        else:

            # Thin the data
            if len(selection_criteria) == 1:
                thisPointData.ThinData(column_for_plotting,selection_criteria)
            elif len(selection_criteria) >1:
                thisPointData.ThinDataSelection(column_for_plotting,selection_criteria)

            # get the easting and northing
            EPSG_string = self._RasterList[0]._EPSGString
            print("EPSG_string is: "+EPSG_string)
            [this_easting,this_northing] = thisPointData.GetUTMEastingNorthing(EPSG_string)
            print (this_easting, this_northing)
            thinned_data = thisPointData.QueryData(column_for_plotting, PANDEX=PANDEX)
            print thinned_data

            for idx, data in enumerate(thinned_data):
                texts.append(self.ax_list[0].text(this_easting[idx],this_northing[idx], str(data),fontsize = 8, color= text_colour,alpha=alpha,bbox=bbox_props))
            #print ("I'm adding the text, yo")

        # Annoying but the scatter plot resets the extents so you need to reassert them
        self.ax_list[0].set_xlim(this_xlim)
        self.ax_list[0].set_ylim(this_ylim)

        return texts

    def add_text_annotation_from_shapely_points(self, points, old_values=[], new_values=[], border_colour='k', text_colour='r', alpha=1):
        """
        This adds annotations from a dictionary of shapely points, for annotating basins or sources.
        In the dictionary the keys are the raster values to annotate and the values are the point objects.
        FJC 24/06/17
        """
        from shapely.geometry import Point


        # rewrite with new values if you need to (for basins)
        new_points = {}
        if len(new_values) > 0 and len(old_values) > 0:
            for key, point in points.iteritems():
                for i, j in enumerate(old_values):
                    if (j == key):
                        new_points[int(new_values[i])] = point
            points = new_points

        # A list of text objects
        texts = []

        # Get the axis limits to assert after
        this_xlim = self.ax_list[0].get_xlim()
        this_ylim = self.ax_list[0].get_ylim()

        # Format the bounding box
        bbox_props = dict(boxstyle="circle,pad=0.1", fc="w", ec=border_colour, lw=0.5,alpha = alpha)

        for key, point in points.iteritems():
            x = point.x
            y = point.y
            texts.append(self.ax_list[0].text(point.x, point.y, str(key), fontsize=8, color=text_colour,alpha=alpha,bbox=bbox_props))
            #print ("I'm adding the text, yo")

        # Annoying but the scatter plot resets the extents so you need to reassert them
        self.ax_list[0].set_xlim(this_xlim)
        self.ax_list[0].set_ylim(this_ylim)

        return texts

    def plot_polygon_outlines(self,polygons, colour='black', linewidth=1, alpha = 1):
        """
        This function plots an outline of a series of shapely polygons

        Args:
            ax_list: list of axes
            polygons: dict of shapely polygons

        Author: FJC
        """
        from shapely.geometry import Polygon

        print('Plotting the polygon outlines...')

        for key, poly in polygons.iteritems():
            x,y = poly.exterior.xy
            self.ax_list[0].plot(x,y, c=colour, lw = linewidth, alpha = alpha)

    def plot_filled_polygons(self,polygons, facecolour='blue', edgecolour='black', linewidth=1, alpha=0.5):
        """
        This function plots a series of shapely polygons but fills them in

        Args:
            ax_list: list of axes
            polygons: list of shapely polygons

        Author: FJC
        """
        from shapely.geometry import Polygon
        from descartes import PolygonPatch
        from matplotlib.collections import PatchCollection

        print('Plotting the polygons...')

        patches = []
        for key, poly in polygons.iteritems():
            this_patch = PolygonPatch(poly, fc=facecolour, ec=edgecolour, alpha=alpha)
            self.ax_list[0].add_patch(this_patch)

    def _set_coord_type(self, coord_type):
        """Sets the coordinate type"""
        if coord_type == "UTM":
            self._coord_type = "UTM"
            self._xaxis_label = "Easting (m)"
            self._yaxis_label = "Northing (m)"

        elif coord_type == "UTM_km":
            self._coord_type = "UTM_km"
            self._xaxis_label = "Easting (km)"
            self._yaxis_label = "Northing (km)"

        # Example, do not actually use...
        elif coord_type == "Kruskal–Szekeres":
            self._coord_type = "Kruskal–Szekeres"
            self._xaxis_label = "X"
            self._yaxis_label = "T"

        else:
            raise ValueError("Sorry, the coordinate type: ", coord_type,
                             "is not yet supported")

    def show_plot(self):

        self.fig.show()

    def save_fig(self,fig_width_inches = 4,FigFileName = 'TestFig.png',FigFormat = 'png',Fig_dpi = 100, axis_style = "Normal", transparent=False):


        self.ax_list = self.axis_styler(self.ax_list,axis_style)

        map_aspect_ratio = self._RasterList[0]._RasterAspectRatio
        print("The aspect ratio is: "+str(map_aspect_ratio))

        # We have to make some adjustments for the colourbar labels since if
        # they have lots of digits we need more space.
        # This is a fantastic thing you have to do when you are hard coding the
        # layout of the figure. Don't worry, this will all be worth it when we have awsome
        # figures every time.
        max_cbar_characters = 0
        if self.colourbar_location == "left" or self.colourbar_location == "right":
            print("You have a colourbar on the left or right, I need to check the number of characters in the labels.")
            labels = [item.get_text() for item in self.ax_list[-1].get_yticklabels()]
            print(labels)
            for label in labels:
                if len(label) > max_cbar_characters:
                    max_cbar_characters = len(label)
            print("The longest colourbar label has "+str(max_cbar_characters)+" characters.")



        fig = matplotlib.pyplot.gcf()

        # Now we size the figure. This requires some finessing since we are
        # hard coding the widths of everything
        if max_cbar_characters <= 3:
            cbar_width = 0.2
            cbar_text_width = 0.4   # This is in inches. Because yanks wrote matplotlib.
        else:
            cbar_width = 0.2
            cbar_text_width = 0.4+0.15*(max_cbar_characters-3)   # This is in inches. Because yanks wrote matplotlib.
            print("I'm adjusting the colourbar text width to "+str(cbar_text_width)+" inches")

        fig_size_inches, map_axes, cbar_axes = phelp.MapFigureSizer(fig_width_inches,
                                                              map_aspect_ratio,
                                                              self.colourbar_location,
                                                              cbar_width,
                                                              cbar_text_width)

        fig.set_size_inches(fig_size_inches[0], fig_size_inches[1])
        self.ax_list[0].set_position(map_axes)

        # Annoying but the scatter plot resets the extens so you need to reassert them
        self.ax_list[0].set_xlim(self._xmin,self._xmax)
        self.ax_list[0].set_ylim(self._ymax,self._ymin)

        print("Number of axes are: " + str(len(self.ax_list)))


        if cbar_axes == None:
            del self.ax_list[-1]
        else:
            self.ax_list[-1].set_position(cbar_axes)

        fig.savefig(FigFileName, format=FigFormat, dpi=Fig_dpi, transparent=transparent)

        #self.fig.show()
        #print("The figure format is: " + self.FigFormat)
        #plt.savefig(self.FigFileName,format=self.FigFormat)
        #self.fig.clf()

    def SetRCParams(self,label_size):
        """This sets a load of RC params
        """
        print("I am setting the font size to: "+str(label_size))
        rcParams['font.family'] = 'sans-serif'
        rcParams['font.sans-serif'] = ['arial']
        rcParams['font.size'] = label_size
        rcParams['lines.linewidth']  = 1.5
