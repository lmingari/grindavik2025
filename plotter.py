#!/usr/bin/env python

import argparse
import xarray as xr
import logging
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from mpl_toolkits.axes_grid1 import make_axes_locatable
import cartopy.crs as crs
import cartopy.feature as cfeature
from PIL import Image

plt.rcParams.update({'font.size': 8})

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PLOTTER")

# Time format
FMT_TIME = "%Y-%m-%d %H:%MZ"

# Default units
DEF_UNITS = {
    'kg/m2':      'kg~m^{-2}',
    'g/m2':       'g~m^{-2}',
    'g/m3':       'g~m^{-3}',
    'DU':         'DU',
    'm (a.s.l.)': 'm',
    'm':          'm',
    }

class MapImage:
    def __init__(self,ncfile):
        self.key      = None
        self.it       = None
        self.time_fmt = None
        self.data     = None
        ###
        ### Open netcdf
        ###
        self.ds = xr.open_dataset(ncfile)
        self.nt = self.ds.sizes['time']
        ###
        ### Create plot
        ###
        self.fig, self.ax = self._create_map()

    def load(self,key,time):
        self.key = key
        #
        if key in self.ds:
            da = self.ds[key]
        else:
            logger.info(f"Variable {key} not found. Nothing to do")
            return
        ###
        ### Indexing dataarray
        ###
        dims = ['time', 'lev', 'bin', 'fl', 'layer']
        d = {dim: 0 for dim in dims if dim in da.dims}
        if 'time' in da.dims:
            it = time%self.nt
            d['time'] = it
            self.it  = it
            self.time_fmt = self.ds.isel(time=it)['time'].dt.strftime(FMT_TIME).item()
        ###
        ### Get data
        ###
        self.data = da[d]
        ###
        ### Work with a 2-d array da(lat,lon)
        ###
        if ["lat","lon"] != sorted(self.data.dims): 
            logger.info(f"Incorrect dimensions for {args.key}. Nothing to do")
            return

    def plot(self):
        ax  = self.ax
        fig = self.fig
        #
        autoScale = False
        #
        label  = self._get_label()
        cmap   = self._get_colormap()
        levels = self._get_levels()
        ###
        ### Configure plot
        ###
        args_dict = {
                "cmap": cmap,
                "extend": 'max',
                "transform": crs.PlateCarree(),
                }
        if not autoScale: 
            args_dict['levels'] = levels
            args_dict['norm'] = BoundaryNorm(levels,cmap.N)
        ###
        ### Create plot
        ###
        fc = ax.contourf(self.data.lon,self.data.lat,self.data,**args_dict)
        ###
        ### Generate colorbar
        ###
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

    def add_title(self):
        ###
        ### Add title
        ###
        if self.it is not None: self.ax.set_title(self.time_fmt, loc='right')

    def add_marker(self,lon,lat):
        ###
        ### Add vent location
        ###
        self.ax.plot(lon,lat,
            color='red',
            marker='^',
            zorder = 4,
            alpha = 0.5,
            transform=crs.PlateCarree())

    def add_logo(self,fname):
        ###
        ### Add logo
        ###
        image_data = Image.open(fname)
        image_box = OffsetImage(image_data, zoom=0.2)
        anno_box = AnnotationBbox(image_box, 
            xy=(0, 1), 
            xycoords='axes fraction', 
            box_alignment=(0, 1), 
            frameon=False)
        self.ax.add_artist(anno_box)
 
    def save(self):
        """
        Save a map as a png image
        """
        if self.it is None:
            fname = f"{self.key}.png"
        else:
            fname = f"{self.key}_{self.it:03}.png"

        logger.info(f"Saving {fname}")
        ##
        ## Save output file
        ##
        plt.savefig(fname,dpi=200,bbox_inches='tight')

    def _get_label(self):
        label_raw = self.data.long_name
        units_raw = self.data.units
        #
        label = label_raw.replace("_", " ")
        if units_raw in DEF_UNITS:
            units = DEF_UNITS[units_raw]
            label = fr"{label} [${units}$]"
        else:
            label = f"{label} [{units_raw}]"
        return label

    def _get_colormap(self):
        ###
        ### Define colormap
        ###
        cmap = plt.cm.RdYlBu_r
        return cmap

    def _get_levels(self):
        levels = [1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        return levels
 
    def _create_map(self):
        proj = crs.Mercator(
            central_longitude=-10, 
            min_latitude=50, 
            max_latitude=75)
        fig, ax = plt.subplots( subplot_kw={'projection': proj} )
        ###
        ### Add map features
        ###
        BORDERS = cfeature.NaturalEarthFeature(
                scale     = '50m',
                category  = 'cultural',
                name      = 'admin_0_countries',
                edgecolor = 'gray',
                facecolor = 'none'
                )
        LAND = cfeature.NaturalEarthFeature(
                'physical', 'land', '50m',
                edgecolor = 'none',
                facecolor = 'lightgrey',
                alpha     = 0.8
                )
        ax.add_feature(LAND)
        ax.add_feature(BORDERS, linewidth=0.4)
        ###
        ### Add grid lines
        ###
        gl = ax.gridlines(
            crs         = crs.PlateCarree(),
            draw_labels = True,
            linewidth   = 0.5,
            color       = 'gray',
            alpha       = 0.5,
            linestyle   = '--')
        gl.top_labels    = False
        gl.right_labels  = False
        gl.ylabel_style  = {'rotation': 90}
        return (fig,ax)

def main(args):
    addVolcano = True
    addLogo    = True
    #
    if args.lat is None or args.lon is None: addVolcano = False
    if args.logo is None: addLogo = False
    #
    c = MapImage(args.netcdf)
    c.load(args.key, args.time)
    c.plot()
    if addVolcano: c.add_marker(args.lon,args.lat)
    if addLogo: c.add_logo(args.logo)
    c.add_title()
    c.save()

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(description="Plot a map from a NetCDF file")
    parser.add_argument("--netcdf", metavar='file',      type=str,   help="Path to NetCDF file", required=True)
    parser.add_argument("--key",    metavar='variable',  type=str,   help="Variable name in NetCDF", required=True)
    parser.add_argument('--lat',    metavar='latitude',  type=float, help='Volcano latitude')
    parser.add_argument('--lon',    metavar='longitude', type=float, help='Volcano longitude')
    parser.add_argument("--time",   metavar='stepIndex', type=int,   help='Time step index', default = -1)
    parser.add_argument("--logo",   metavar='file',      type=str,   help='Logo image')
    args = parser.parse_args()

    logger.info("Creating map output file...")
    main(args)
    logger.info("Done!")
