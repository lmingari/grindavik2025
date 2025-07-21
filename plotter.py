#!/usr/bin/env python

import numpy as np
import xarray as xr
import logging
import argparse
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import cartopy.crs as crs
import cartopy.feature as cfeature
from PIL import Image
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PLOT")

plt.rcParams.update({'font.size': 8})

units = {
    'kg/m2':      'kg~m^{-2}',
    'g/m2':       'g~m^{-2}',
    'g/m3':       'g~m^{-3}',
    'DU':         'DU',
    'm (a.s.l.)': 'm',
    'm':          'm',
    }

def create_map():
    proj_pc = crs.PlateCarree()
    proj    = crs.Mercator(central_longitude=-10, min_latitude=50, max_latitude=75)
    fig, ax = plt.subplots( subplot_kw={'projection': proj} )
    #
    # Add map features
    #
    BORDERS = cfeature.NaturalEarthFeature(
            scale     = '10m',
            category  = 'cultural',
            name      = 'admin_0_countries',
            edgecolor = 'gray',
            facecolor = 'none'
            )
    LAND = cfeature.NaturalEarthFeature(
            'physical', 'land', '10m',
            edgecolor = 'none',
            facecolor = 'lightgrey',
            alpha     = 0.8
            )
    ax.add_feature(LAND,zorder=0)
    ax.add_feature(BORDERS, linewidth=0.4)
    ###
    ### Add grid lines
    ###
    gl = ax.gridlines(
        crs         = proj_pc,
        draw_labels = True,
        linewidth   = 0.5,
        color       = 'gray',
        alpha       = 0.5,
        linestyle   = '--')
    gl.top_labels    = False
    gl.right_labels  = False
    gl.ylabel_style  = {'rotation': 90}

    return (fig,ax)

def get_colormap(key):
    ###
    ### Define colormap
    ###
    cmap = plt.cm.RdYlBu_r
    return cmap

def get_label(da):
    label = da.long_name.replace("_", " ").capitalize()
    if da.units in units:
        unit = units[da.units]
        label = fr"{label} [${unit}$]"
    else:
        unit = da.units
        label = f"{label} [{unit}]"
    return label

def add_logo(ax, fname):
    image_data = Image.open(fname)
    image_box = OffsetImage(image_data, zoom=0.2)
    anno_box = AnnotationBbox(image_box, 
        xy=(0, 1), 
        xycoords='axes fraction', 
        box_alignment=(0, 1), 
        frameon=False)
    ax.add_artist(anno_box)

def main(args):
    setMin    = False
    plotVent  = False
    autoScale = True
    plotVent  = False
    hasTime   = False
    ###
    ### Set mininmum level
    ###
    if args.minval is not None: setMin = True
    ###
    ### Automatic scale
    ###
    if args.levels is not None: autoScale = False
    ###
    ### Plot vent
    ###
    if args.lat is not None and args.lon is not None: plotVent = True
    ###
    ### Redefine levels
    ###
    if not autoScale:
        levels = sorted(args.levels)
        if setMin:
            levels = [args.minval] + [i for i in levels if i > args.minval]
    ###
    ### Read file/data
    ###
    ds = xr.open_dataset(args.netcdf)
    if args.key in ds: 
        da = ds[args.key]
    else:
        logger.info(f"Variable {args.key} not found. Nothing to do")
        return
    ###
    ### Check time
    ###
    if 'time' in da.dims: hasTime = True
    ###
    ### Indexing dataarray
    ###
    dims = ['time', 'lev', 'bin', 'fl', 'layer']
    d = {dim: 0 for dim in dims if dim in da.dims}
    if hasTime:
        nt = ds.sizes['time']
        it = args.time%nt
        d['time'] = it
        time_fmt = ds.isel(time=it)['time'].dt.strftime("%d/%m/%Y %H:%M").item()
    da = da[d]
    ###
    ### Work with a 2-d array da(lat,lon)
    ###
    if ["lat","lon"] != sorted(da.dims): 
        logger.info(f"Incorrect dimensions for {args.key}. Nothing to do")
        return
    ###
    ### Generate map
    ###
    fig, ax = create_map()
    ###
    ### Add vent location
    ###
    if plotVent: ax.plot(args.lon,args.lat,color='red',marker='^')
    ###
    ### Add title
    ###
    if hasTime: ax.set_title(time_fmt, loc='right')
    ###
    ### Contours plot
    ###
    cmap = get_colormap(args.key)
    args_dict = {
            "cmap": cmap,
            "extend": 'max',
            "transform": crs.PlateCarree()
            }
    if not autoScale: 
        args_dict['levels'] = levels
        args_dict['norm'] = BoundaryNorm(levels,cmap.N)
    fc = ax.contourf(da.lon,da.lat,da,**args_dict)
    ###
    ### Generate colorbar
    ###
    label = get_label(da)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes(
        position='bottom',
        size="3%", 
        pad=0.4,
        axes_class=plt.Axes)
    cbar = fig.colorbar(fc, 
        orientation='horizontal',
        label = label,
        cax=cax)
    ##
    ## Add logo
    ##
    add_logo(ax,"/home/lmingari/fall3d/iceland/CSIC.png")
    ###
    ### Output plot
    ###
    fname_plt = f'{args.key}_{d["time"]:03d}.png'
    plt.savefig(fname_plt,dpi=200,bbox_inches='tight')

if __name__ == "__main__":
    ###
    ### Argument parser
    ###
    parser=argparse.ArgumentParser(description="Plot FALL3D output")
    parser.add_argument("--key",    metavar='variable',  required=True, help='Variable name in netCDF file') 
    parser.add_argument("--netcdf", metavar='file',      required=True, help='FALL3D output file in netCDF format')
    parser.add_argument("--minval", metavar='minimum',   type=float, help='Minimum value in the scale')
    parser.add_argument("--levels", metavar='list',      type=float, nargs='+', help='Minimum value in the scale')
    parser.add_argument('--lat',    metavar='latitude',  type=float, help='Volcano latitude')
    parser.add_argument('--lon',    metavar='longitude', type=float, help='Volcano longitude')
    parser.add_argument("--time",   metavar='step',      type=int,   default = -1, help='Time step index')
    args=parser.parse_args()
    ###
    ### Main program
    ###
    logger.info(f"Plotting {args.key}...")
    main(args)
    logger.info("Done!")
