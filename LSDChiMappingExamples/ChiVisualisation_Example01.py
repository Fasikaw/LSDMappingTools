"""
    This contains a series of examples for chi plotting to be used with 
    the chi_mapping_tool. 
    
    Simon Mudd and Fiona Clubb, June 2017
    
    Released under GPL3
    

"""

import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')



import matplotlib.pyplot as plt
import matplotlib
from matplotlib import rcParams


"""
    IMPORTANT: You must call this function from a lower level driectory
    where both LSDPlottingTools and LSDMapFigure are in the python path!
    
    That is, it will not work if you call it from outside the directory structure. 
    
"""
import LSDPlottingTools as LSDP
from LSDMapFigure.PlottingRaster import MapFigure
import LSDMapFigure.PlottingHelpers as PlotHelp
#import LSDPlottingTools.LSDMap_VectorTools as LSDMap_VT


def ExampleOne_PartOne_SimpleHillshade(DataDirectory,Base_file):
    """
    This function makes a shaded relief plot of the DEM with the basins coloured
    by the basin ID.

    WORK IN PROGRESS - NEED TO GET LABELLING OR A COLOUR BAR WORKING

    Args:
        DataDirectory (str): the data directory with the m/n csv files
        fname_prefix (str): The prefix for the m/n csv files
        size_format (str): Can be "big" (16 inches wide), "geomorphology" (6.25 inches wide), or "ESURF" (4.92 inches wide) (defualt esurf).
        FigFormat (str): The format of the figure. Usually 'png' or 'pdf'. If "show" then it calls the matplotlib show() command.

    Returns:
        Shaded relief plot with the basins coloured by basin ID

    Author: FJC
    """
    # specify the figure size and format
    #size_format='ESURF'
    #FigFormat = 'png'
    fig_size_inches = 12
    ax_style = "Normal"
    
    # Get the filenames you want    
    BackgroundRasterName = Base_file+"_hs.bil"    
    DrapeRasterName = Base_file+".bil"

    # clear the plot
    plt.clf() 
    
    # this is where we want the colourbar
    cbar_loc = "right"
    
    # set up the base image and the map
    MF = MapFigure(BackgroundRasterName, DataDirectory,coord_type="UTM_km",colourbar_location = cbar_loc)
    MF.add_drape_image(DrapeRasterName,DataDirectory,colourmap = "jet", alpha = 0.6, colorbarlabel = "Elevation (m)")
    
    # Save the image
    ImageName = DataDirectory+"Xian_example1.png" 
    MF.save_fig(fig_width_inches = fig_size_inches, FigFileName = ImageName, axis_style = ax_style, Fig_dpi = 250)

def ExampleOne_PartTwo_PrintBasins(DataDirectory,fname_prefix):
    """
    This function makes a shaded relief plot of the DEM with the basins coloured
    by the basin ID.

    WORK IN PROGRESS - NEED TO GET LABELLING OR A COLOUR BAR WORKING

    Args:
        DataDirectory (str): the data directory with the m/n csv files
        fname_prefix (str): The prefix for the m/n csv files
        size_format (str): Can be "big" (16 inches wide), "geomorphology" (6.25 inches wide), or "ESURF" (4.92 inches wide) (defualt esurf).
        FigFormat (str): The format of the figure. Usually 'png' or 'pdf'. If "show" then it calls the matplotlib show() command.

    Returns:
        Shaded relief plot with the basins coloured by basin ID

    Author: FJC
    """
    #import modules
    from LSDMapFigure.PlottingRaster import MapFigure

    # Set up fonts for plots
    label_size = 10
    rcParams['font.family'] = 'sans-serif'
    rcParams['font.sans-serif'] = ['arial']
    rcParams['font.size'] = label_size
    size_format  = "geomorphology"
    
    # set figure sizes based on format
    if size_format == "geomorphology":
        fig_width_inches = 6.25
    elif size_format == "big":
        fig_width_inches = 16
    else:
        fig_width_inches = 4.92126

    # get the basin IDs to make a discrete colourmap for each ID
    BasinDF = PlotHelp.ReadBaselevelKeysCSV(DataDirectory,fname_prefix)

    basin_keys = list(BasinDF['baselevel_key'])
    basin_keys = [float(x) for x in basin_keys]

    basin_junctions = list(BasinDF['baselevel_junction'])
    basin_junctions = [float(x) for x in basin_junctions]

    print ('Basin keys are: ')
    print basin_keys

    # get a discrete colormap
    cmap = plt.cm.jet

    # going to make the basin plots - need to have bil extensions.
    print("I'm going to make the basin plots. Your topographic data must be in ENVI bil format or I'll break!!")

    # get the rasters
    raster_ext = '.bil'
    #BackgroundRasterName = fname_prefix+raster_ext
    HillshadeName = fname_prefix+'_hs'+raster_ext
    BasinsName = fname_prefix+'_AllBasins'+raster_ext
    print (BasinsName)

    # create the map figure
    MF = MapFigure(HillshadeName, DataDirectory,coord_type="UTM_km", colourbar_location='bottom')
    # add the basins drape
    MF.add_drape_image(BasinsName, DataDirectory, colourmap = cmap, alpha = 0.8, colorbarlabel='Basin ID', discrete_cmap=True, n_colours=len(basin_keys), show_colourbar = True, modify_raster_values=True, old_values=basin_junctions, new_values=basin_keys, cbar_type = int)
    # add the basin outlines
    Basins = LSDP.GetBasinOutlines(DataDirectory, fname_prefix)
    MF.plot_polygon_outlines(Basins, linewidth=0.8)

    FigFormat = "png"
    ImageName = DataDirectory+fname_prefix+'_basin_keys.'+FigFormat
    MF.save_fig(fig_width_inches = fig_width_inches, FigFileName = ImageName, FigFormat=FigFormat, Fig_dpi = 300) # Save the figure
    
    
def ExampleOne_PartThree_PrintBasinsWithLabels(DataDirectory, fname_prefix):
    """
    This function makes a shaded relief plot of the DEM with the basins coloured
    by the basin ID.

    Args:
        DataDirectory (str): the data directory with the m/n csv files
        fname_prefix (str): The prefix for the m/n csv files
        size_format (str): Can be "big" (16 inches wide), "geomorphology" (6.25 inches wide), or "ESURF" (4.92 inches wide) (defualt esurf).
        FigFormat (str): The format of the figure. Usually 'png' or 'pdf'. If "show" then it calls the matplotlib show() command.

    Returns:
        Shaded relief plot with the basins coloured by basin ID

    Author: FJC
    """

    FigFormat = "png"
    size_format = "geomorphology"

    #import modules
    # from LSDMapFigure.PlottingRaster import MapFigure
    # from LSDMapFigure.PlottingRaster import BaseRaster
    # import LSDPlottingTools.LSDMap_VectorTools as LSDMap_VT
    # import LSDPlottingTools.LSDMap_PointTools as LSDMap_PT

    # Set up fonts for plots
    label_size = 10
    rcParams['font.family'] = 'sans-serif'
    rcParams['font.sans-serif'] = ['arial']
    rcParams['font.size'] = label_size

    # set figure sizes based on format
    if size_format == "geomorphology":
        fig_width_inches = 6.25
    elif size_format == "big":
        fig_width_inches = 16
    else:
        fig_width_inches = 4.92126



    # get the basin IDs to make a discrete colourmap for each ID
    BaseLevelDF = PlotHelp.ReadBaselevelKeysCSV(DataDirectory, fname_prefix)

    baselevel_keys = list(BaseLevelDF['baselevel_key'])
    baselevel_keys = [float(x) for x in baselevel_keys]

    baselevel_junctions = list(BaseLevelDF['baselevel_junction'])
    baselevel_junctions = [float(x) for x in baselevel_junctions]

    print ('Basin keys are: ')
    print baselevel_keys

    # get a discrete colormap
    cmap = plt.cm.jet

    # going to make the basin plots - need to have bil extensions.
    print("I'm going to make the basin plots. Your topographic data must be in ENVI bil format or I'll break!!")

    # get the rasters
    raster_ext = '.bil'
    #BackgroundRasterName = fname_prefix+raster_ext
    HillshadeName = fname_prefix+'_hs'+raster_ext
    BasinsName = fname_prefix+'_AllBasins'+raster_ext
    print (BasinsName)

    # create the map figure
    # We set colourbar location to none since we are labelling the figures
    MF = MapFigure(HillshadeName, DataDirectory,coord_type="UTM_km", colourbar_location='none')

    # add the basins drape
    MF.add_drape_image(BasinsName, DataDirectory, colourmap = cmap, alpha = 0.8, colorbarlabel='Basin ID', discrete_cmap=True, n_colours=len(baselevel_keys), show_colourbar = True, modify_raster_values=True, old_values=baselevel_junctions, new_values=baselevel_keys, cbar_type = int)

    # add the basin outlines
    Basins = LSDP.GetBasinOutlines(DataDirectory, fname_prefix)
    MF.plot_polygon_outlines(Basins, linewidth=0.8)

    # add the basin labelling
    Points = LSDP.GetPointWithinBasins(DataDirectory, fname_prefix)
    MF.add_text_annotation_from_shapely_points(Points, text_colour='k', old_values = baselevel_junctions, new_values = baselevel_keys)

    # Save the figure
    ImageName = DataDirectory+fname_prefix+'_basin_keys.'+FigFormat
    MF.save_fig(fig_width_inches = fig_width_inches, FigFileName = ImageName, FigFormat=FigFormat, Fig_dpi = 300)    
    