## analyse_knickpoints.py
##=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
## This scripts takes in the Mchi files with the knickpoint information
## and creates various plots.  User specifies a threshold knickpoint magnitude
## (difference in MChi between the upstream and downstream segments)
## MChi file is read in using pandas
##
## I'm writing this at midnight so here is a panda:
##             ,,,         ,,,
##          ;"   ^;     ;'   ",
##          ;    s$$$$$$$s     ;
##          ,  ss$$$$$$$$$$s  ,'
##          ;s$$$$$$$$$$$$$$$
##          $$$$$$$$$$$$$$$$$$
##         $$$$P""Y$$$Y""W$$$$$
##         $$$$  p"$$$"q  $$$$$
##         $$$$  .$$$$$.  $$$$
##           $$DcaU$$$$$$$$$$
##            "Y$$$"*"$$$Y"
##               "$b.$$"
##
##
## Knickpoint plots:
## 1. For each basin, it looks at the relationship between the flow distance
## (distance from the basin outlet) and the elevation of the knickpoints
## 2. Knickpoint magnitude vs elevation
##
## IDEAS TO ADD TO PLOTS:
## - Colour points by lithology (import USGS lithologies). Theory predicts that
## - the knickpoints of all the tributaries should be at the same elevation. How does
## lithology affect this?
## - Normalise flow distance by channel length/drainage area (chi coordinate)
## - Different marker for convex/concave knickpoints
## - Plots for along the mountain front: Distance from N - S along the Sierras. How
## does the elevation of the knickpoints vary as you move from N - S?
##
##=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
## Authors: FJC, BG
## 02/06/17
##=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

#set backend to run on server
import matplotlib
matplotlib.use('Agg')

#import modules
from matplotlib import pyplot as plt
import numpy as np
import os
import matplotlib
import pandas
from LSDPlottingTools import LSDMap_PointTools as PointTools
from LSDPlottingTools import LSDMap_KnickpointPlotting as KP
from LSDPlottingTools import statsutilities as lst

def read_MChi_file(DataDirectory, csv_name):
    """
    This function reads in the MChi file using pandas - the data is raw, I'll add processing functions
    file structure:
    latitude longitude elevation	flow distance	drainage area	diff ratio sign	source_key	basin_key
    FJC/BG 29/03/17
    """
    df = pandas.read_csv(DataDirectory+csv_name, sep=",")
    return df

def get_data_columns_from_csv(DataDirectory, csv_name, columns):
    """
    This function returns lists of specified column names from the MChi csv file.
    Must be strings equal to the column headers.
    FJC 29/03/17
    """
    column_lists = []
    df = read_MChi_file(DataDirectory, csv_name)
    for column_name in columns:
        print("I'm returning the "+column_name+" values as a list")
        column_values = list(df[column_name])
        column_lists.append(column_values)
    return column_lists

def make_cumulative_plot(DataDirectory, csv_name):
    print("Now printing the cumulative plot")
    sorted_data = read_MChi_file(DataDirectory, csv_name)
    temp_count = 0
    x_cumul, y_cumul = np.unique(sorted_data[:,11],return_counts= True)
    #y_cumul = np.unique(sorted_data[:,11],return_counts= True)
    for i in range(1,x_cumul.size):
        y_cumul[i] = y_cumul[i]+y_cumul[i-1]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x_cumul, y_cumul, 'k--', linewidth=1)

    print("Saving the Cumulative plot")
    # tidy up the figure
    ax.grid(True)
    ax.set_title('Cumulative step histograms')
    ax.set_xlabel('kinckpoint value')
    ax.set_ylabel('Cumulative %')
    #ax.set_ylim(0,100)
    ax.set_xlim(0,sorted_data[:,11].max())
    write_name = "kp_cumulative"
    file_ext = "png"
    plt.savefig(DataDirectory+write_name+"."+file_ext,dpi=300)
    plt.clf()

    #### Elevation against Knickpoints ####
def plot_knickpoint_elevations(DataDirectory, csv_name, kp_type = "diff"):
    """
    This function creates a plot of knickpoint elevations against magnitude
    FJC 29/03/17, modified from code by BG.
    """
    # read in the data from the csv to lists
    elevation = get_data_column_from_csv(DataDirectory, csv_name, kp_threshold, "elevation")
    kp_data = get_data_column_from_csv(DataDirectory, csv_name, kp_threshold, kp_type)

    # plot the figure
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(kp_data, elevation, 'k+', linewidth=0.5)
    ax.grid(True)
    ax.set_title('Elevation against knickpoint value')
    ax.set_xlabel('Knickpoint '+kp_type)
    ax.set_ylabel('Elevation (m)')
    #ax.set_ylim(0,100)
    ax.set_xlim(0,1000)
    write_name = "knickpoint_elevation_"+kp_type
    file_ext = "png"
    plt.savefig(DataDirectory+write_name+"."+file_ext,dpi=300)
    plt.clf()

def return_outlier(df,data = "diff", thresh=3.5):
    """
    Returns a boolean array with True if points are outliers and False
    otherwise.

    Parameters:
    -----------
        points : An numobservations by numdimensions array of observations
        thresh : The modified z-score to use as a threshold. Observations with
            a modified z-score (based on the median absolute deviation) greater
            than this value will be classified as outliers.

    Returns:
    --------
        mask : A numobservations-length boolean array.

    References:
    ----------
        Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
        Handle Outliers", The ASQC Basic References in Quality Control:
        Statistical Techniques, Edward F. Mykytka, Ph.D., Editor.
    """
    points = df[data]
    if len(points.shape) == 1:
        points = points[:,None]
    median = np.median(points, axis=0)
    diff = np.sum((points - median)**2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation
    msk =  modified_z_score > thresh
    df = df[msk]
    return df

def knickpoint_plots_for_basins(DataDirectory, csv_name, kp_type = "diff"):
    """
    This function creates subplots of knickpoint characteristics for each individual
    basin. kp_type define if you want the ratio data or the differencee data (diff by default).
    FJC 29/03/17
    """
    # read in data from the csv to lists
    columns = ["elevation", "flow distance", "drainage area", kp_type, "sign", "basin_key"]
    column_lists = get_data_columns_from_csv(DataDirectory, csv_name, columns)
    print(len(column_lists))
    elevation = column_lists[0]
    flow_distance = column_lists[1]
    drainage_area = column_lists[2]
    kp_data = column_lists[3]
    kp_sign = column_lists[4]
    basin_id = column_lists[5]
    #list_of_lists = zip(elevation,flow_distance,basin_id)
    #print column_lists

    # loop through and get a plot for each basin id
    ids = set(basin_id)
    for id in ids:
        print("This basin id/key is: "+str(id))
        these_lists = [(a,b,c,d,e,f) for (a,b,c,d,e,f) in zip(elevation,flow_distance,drainage_area,kp_data,kp_sign,basin_id) if f == id]
        this_elev, this_distance, this_area, this_magnitude, this_sign, this_id = zip(*these_lists)

        fig,ax = plt.subplots(figsize=(10,12))
        #ax = ax.ravel()
        #for i in range(len(ax)):
        ax.scatter(this_distance,this_elev,facecolors="None", edgecolors="k", s=this_magnitude)
        ax.set_xlabel('Flow distance (m)')
        ax.set_ylabel('Elevation (m)')

        write_name = "knickpoint_plots_basin_"
        file_ext = "png"
        plt.savefig(DataDirectory+write_name+str(id)+"."+file_ext,dpi=100)
        plt.close()

def select_main_basin(pd):
    """
    Function that takes a dataframe from the knickpoint anaysis tool and mask it on the main basin

    Args:
    pd = pandas dataframe to mask

    Returns:
    The new pandas dataframe sorted/masked

    Author: Yes
    """
    basins_count =  pd.groupby("basin_key")["basin_key"].count()
    maxi =basins_count[basins_count == basins_count.max()]
    biggest_basin = maxi.index.values[0]
    pd = pd[pd["basin_key"] == biggest_basin]
    return pd

def sort_ratio_0_data(pd, mode = "extract"):
    """
    Function that separate from the dataset the data where the ratio = -9999 meaning that it included a /0 (aka a very flat area).

    Args:
    pd = pandas dataframe to mask
    mode (str): "extract" for returning a new DF with these values (default)
                "delete" for returning a dataframe without these values
    Returns:
        The new pandas dataframe selected

    Author: BG
    """
    if(mode =="extract"):
        pd = pd[pd["ratio"] == -9999]
    else:
        if(mode == "delete"):
            pd = pd[pd["ratio"] != -9999]
        else:
            print("Invalid mode argument for the sort_ratio_0_data function, please put mode = extract or delete")
            quit()
    return pd

def load_Point_Tool(thing):
    """
    Returns a PointTools object from a csv_file or a pandas dataframe (automatically detects the type)

    Author:
        PointTools object
    """
    if(isinstance(thing, pandas.DataFrame)):
        PointData = PointTools.LSDMap_PointData(thing,data_type ="pandas", PANDEX = True)
    else:
        if(isinstance(thing, str)):
            if(thing[-3:] == "csv"):
                tdf = read_MChi_file(thing)
                PointData = PointTools.LSDMap_PointData(tdf,data_type ="pandas", PANDEX = True)
            else:
                print("Hum, your file does not exists or your pandas is not a pandas (then what is it???), anyway I am aborting")
                quit()
    return PointData


def knickpoint_plotter_by_basin(name ,DataDirectory, save_name = "kn_by_Basins", kp_type = "diff", FigFormat='pdf', processed = False):
    """
    Function to test LSDMap_KnickpointPlotting

    Args:
        DataDirectory (str): the data directory of the chi csv file
        DEM_prefix (str): DEM name without extension
        kp_type (string): select the type of knickpoint data you want (diff vs ratio).
        processed (bool): Switch on to directly give a pandas dataframe to plots
        pd_name (string or pandas dataframe): Name of this theoretical pandas dataframe

    Returns:
        Plot of knickpoint (diff or ratio) for each basin

    Author: FJC
    """


    # read in the raw csv file
    PointData = load_Point_Tool(name)

    # get the basin keys
    basin = PointData.QueryData('basin_key')
    basin = [int(x) for x in basin]
    Basin = np.asarray(basin)
    basin_keys = np.unique(Basin)
    print('There are %s basins') %(len(basin_keys))

    # loop through each basin and make the figure
    for basin_key in basin_keys:
        FileName = save_name+"_KP_elevations_%s.%s" %(str(basin_key),FigFormat)
        KP.plot_knickpoint_elevations(PointData, DataDirectory, basin_key, kp_type, FileName, FigFormat)

if __name__ == "__main__":

    DataDirectory = '/home/s1675537/PhD/DataStoreBoris/GIS/Data/Carpathian/knickpoint/'
    baseName = "Buzau"
    dfp = read_MChi_file(DataDirectory,baseName+"_KsnKn.csv")
    river_net = read_MChi_file(DataDirectory,baseName+"_MChiSegmented.csv")
    dfp = select_main_basin(dfp)
    flat_values = sort_ratio_0_data(dfp, mode = "extract")
    dfp = sort_ratio_0_data(dfp, mode = "delete")


    ######## I am binning the elevation using an interval to test

    Z_interval = []
    interval = 100
    rangelev = interval
    while(rangelev<dfp.elevation.max()):
        Z_interval.append(rangelev)
        rangelev += interval
    binned_by_Z = lst.binning_PD(dfp,column = "elevation",values =  Z_interval)
    #KP.pdf_from_bin(binned_by_Z, DataDirectory, column = "elevation", size_format = "ESURF")
    KP.pdf_from_bin_one_col(binned_by_Z, DataDirectory, column = "elevation", size_format = "ESURF", combine_diff_sign = True, argsort = True)
        #KP.plot_pdf_diff_ratio(dfp, DataDirectory, saveName = "pdf_Z_bin_"+each.keys, save_fmt = ".png", size_format = "ESURF",  xlim = [])
    ######## done

    ######## I am selecting the outliers for each lists

    binned_by_Z_Outliers = lst.add_outlier_column_to_PD(binned_by_Z, column = ["diff", "ratio"], threshold =[2,2])

    ZOUT = pandas.concat(binned_by_Z_Outliers)

    #ZOUT = ZOUT[ZOUT['diff_outlier']]
    ZOUT = ZOUT[ZOUT['ratio_outlier']]



    #Loading the pt
    PTZOUT = load_Point_Tool(ZOUT)
    PT = load_Point_Tool(dfp) # If you need actual pointdata
    #PTflat = load_Point_Tool(flat_values)
    PTriver = load_Point_Tool(river_net)
    KP.plot_outliers_x_vs_diff_ratio(PTZOUT,PT, DataDirectory,x_col = "elevation", saveName = "Outliers_bin_Z_ratio_int_"+str(interval), save_fmt = ".png", size_format = "ESURF", log_data = False, ylim_diff = [0,500])

    ########### Now binning by Source key ################

    binned_by_S = lst.binning_PD(dfp,column = "source_key",values =  "unique")
    binned_by_S_outliers = lst.add_outlier_column_to_PD(binned_by_Z, column = ["diff", "ratio"], threshold =[2,2])
    SOUT = pandas.concat(binned_by_S_outliers)
    PTSOUT = load_Point_Tool(SOUT)
    #KP.plot_outliers_x_vs_diff_ratio(PTZOUT,PT, DataDirectory,x_col = "source_key", saveName = "Outliers_bin_S", save_fmt = ".png", size_format = "ESURF", log_data = False, ylim_diff = [0,500])

    ############################################## I am too lazy to delete the following code but I don't need it for the moment
    quit()



    ######## binned by DA
    binned_by_DA = lst.binning_PD(dfp,column = "drainage area",values =  "auto_power_10")
    is_created = True
    tet_lines = 0
    PTBD = {}

    for key in binned_by_DA.keys():
        binned_by_DA[key] = lst.add_outlier_column_to_PD(binned_by_DA[key], column = ["diff", "ratio"], threshold =[3.6,3.6])
        binned_by_DA[key] = binned_by_DA[key][binned_by_DA[key]["diff_outlier"]]
        binned_by_DA[key] = binned_by_DA[key][binned_by_DA[key]["ratio_outlier"]]
        #PTBD[key] = load_Point_Tool(binned_by_DA[key])
        #PTt = load_Point_Tool(binned_by_DA[key])
        #KP.plot_diff_ratio(PTt, DataDirectory, saveName = "OUTLIERS_test_bin_"+str(key), save_fmt = ".png", size_format = "ESURF", log_data = True)
    ############ dine




    #PTO = load_Point_Tool(dfpo)
    #KP.plot_diff_ratio(PTO, DataDirectory, saveName = "OUTLIERS_diff_ratio_test", save_fmt = ".png", size_format = "ESURF", log_data = True )
    #KP.plot_outliers_vs_others(PT, PTBD,DataDirectory,saveName = "OUTLIERS_diff_ratio_test", save_fmt = ".png", size_format = "ESURF", log_data = True )
    KP.plot_basic_DA(PT, DataDirectory, save_fmt = ".png", size_format = "ESURF", log_data = True )
    KP.plot_basic_FD(PT, DataDirectory, save_fmt = ".png", size_format = "ESURF", log_data = True)
    KP.plot_basic_Z(PT, DataDirectory, save_fmt = ".png", size_format = "ESURF", log_data = True)
    #select = dfp[dfp["elevation"]<600]
    #select = select[select["elevation"]>500]
    #PTS = load_Point_Tool(select)
    #KP.map_custom()
    #KP.map_knickpoint_sign(PT, DataDirectory, baseName, Time_in_name = False, river_network = PTriver)
    #KP.map_knickpoint_sign(PTflat, DataDirectory, baseName, Time_in_name = False, river_network = PTriver, saveName = "flat_", size = 0.1)
    KP.map_knickpoint_diff_sized_colored_ratio(PTS, DataDirectory, baseName, river_network = PTriver, log = True, saveName = "500_700")
    kp_type = "diff" # every knickpoint below this will be erased
    FigFormat = 'png'
    #knickpoint_plots_for_basins(DataDirectory,csv_name, kp_type)

    #knickpoint_plotter_by_basin(dfp, DataDirectory,kp_type=kp_type,FigFormat=FigFormat)