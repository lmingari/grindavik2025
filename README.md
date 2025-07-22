# FALL3D forecasting workflow using GFS data
This is the CWL workflow for a FALL3D forecast of ash dispersal using GFS data.
The workflow performs multiple tasks, including:

* Define the FALL3D model configuration
* Get weather forecasts (GFS data)
* Pre-process GFS data (concatenate and convert from grib to netCDF)
* Run FALL3D in parallel
* Generate plots

# Running the workflow

## Prerequisites
In order to execute the workflow, you need to install the necessary Python packages.
For example, you can create a virtual environment `venv` using pip:
```console
python -m venv venv
```
Then, you need to activate it:
```console
source venv/bin/activate
```
Once your virtual environment is active, you can use pip to install all the packages listed in your `requirements.txt` file.
```console
pip install -r requirements.txt
```

## Running the workflow
A CWL runner is required for running the workflow. 
In the previous step, we've already installed `cwltool`, a Python Open Source project maintained by the CWL community.

Some steps of the workflow are executed in a Docker container by default.
In order to disable Docker, execute the workflow using:
```console
cwltool --no-container workflow.cwl arguments.yml
```
Just two files are required:
* `workflow.cwl`: The workflow definition
* `arguments.yml`: List of user inputs

## Configuring the workflow
In order to configure the execution, you have to provide a few inputs editing
the `arguments.yml` file:
```
# Eruption parameters
volcano: Grindavik         # Volcano name
lat_vent: 63.899996        # Volcano latitude
lon_vent: -22.350001       # Volcano longitude
date: '20250616'           # Reference date (date_ref)
start_time: 2              # Start time in hours since date_ref at 00:00 
end_time: 4                # End time in hours since date_ref at 00:00 

# Model configuration
meteo_database: 'GFS'      # Meteorological driver
initial_condition: 'NONE'  # Initial condition
west_lon: 14.0             # Domain limits
east_lon: 16.0
south_lat: 36.5
north_lat: 38.5
dx: 0.1                    # Resolution (longitudes)
dy: 0.1                    # Resolution (latitudes)
nlevels: 10                # Nuumber of model levels

# GFS configuration: 
resolution: 0.25           # Resolution of GFS data (0.25 or 0.5)
step: 1                    # Temporal resolution of GFS data

# MPI configuration
nx: 2                      # Number of MPI processes
ny: 1                      # along each dimensions for
nz: 1                      # for a parallel run

# Plot configuration
keys:                      # Variables and times to be plotted
  - tephra_col_mass
  - tephra_cloud_top
times:
  - 1
  - 3
```
