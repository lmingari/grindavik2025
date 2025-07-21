#!/usr/bin/env cwl-runner
cwlVersion: v1.2
$namespaces:
  s: https://schema.org/
s:softwareVersion: 0.0.1
schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf

$graph:
  - id: config
    class: CommandLineTool
    baseCommand: ["fill_template.py"]
    inputs:
      template:
        type: string
        inputBinding: {prefix: --template}
      initial_condition:
        type: "#main/InitialCondition"
        inputBinding: {prefix: --INITIAL}
      meteo_database:
        type: "#main/MeteoDatabase"
        inputBinding: {prefix: --METEO_DATABASE}
      meteo:
        type: string
        inputBinding: {prefix: --METEO_FILE}
      dictionary:
        type: string?
        inputBinding: {prefix: --METEO_DICTIONARY}
      restart:
        type: string?
        inputBinding: {prefix: --RESTART_FILE}
      levels:
        type: string?
        inputBinding: {prefix: --LEVELS_FILE}
      date:
        type: string?
        inputBinding: {prefix: --date}
      start_time:
        type: float
        inputBinding: {prefix: --START_TIME}
      end_time:
        type: float
        inputBinding: {prefix: --END_TIME}
      west_lon:
        type: float
        inputBinding: {prefix: --LONMIN}
      east_lon:
        type: float
        inputBinding: {prefix: --LONMAX}
      north_lat:
        type: float
        inputBinding: {prefix: --LATMAX}
      south_lat:
        type: float
        inputBinding: {prefix: --LATMIN}
      dx:
        type: float
        inputBinding: {prefix: --DX}
      dy:
        type: float
        inputBinding: {prefix: --DY}
      nlevels:
        type: int
        inputBinding: {prefix: --NZ}
      lon_vent:
        type: float
        inputBinding: {prefix: --LONV}
      lat_vent:
        type: float
        inputBinding: {prefix: --LATV}
      elevation_vent:
        type: float
        inputBinding: {prefix: --ELEVATION}
    outputs:
      inp:
        type: File
        outputBinding:
          glob: "*.inp"

  - id: gfs_times
    class: CommandLineTool
    baseCommand: ["gfs_times.py"]
    inputs:
      reference_date:
        type: string
        inputBinding: {prefix: --date}
      hmin:
        type: float
        inputBinding: {prefix: --hinit}
      hmax:
        type: float
        inputBinding: {prefix: --hend}
      step:
        type: int?
        inputBinding: {prefix: --step}
    outputs:
      cycle:
        type: int
        outputBinding:
          glob: gfs.json
          loadContents: true
          outputEval: $(JSON.parse(self[0].contents).cycle)
      date:
        type: string
        outputBinding:
          glob: gfs.json
          loadContents: true
          outputEval: $(JSON.parse(self[0].contents).date)
      tmin:
        type: int
        outputBinding:
          glob: gfs.json
          loadContents: true
          outputEval: $(JSON.parse(self[0].contents).tmin)
      tmax:
        type: int
        outputBinding:
          glob: gfs.json
          loadContents: true
          outputEval: $(JSON.parse(self[0].contents).tmax)
    stdout: gfs.json
    requirements:
      InlineJavascriptRequirement: {}

  - id: gfs
    class: CommandLineTool
    baseCommand: ["gfs.py"]
    inputs:
      date:
        type: string
        inputBinding: {prefix: --date}
      lonmin:
        type: float
        inputBinding:
          prefix: --lon
          position: 1
      lonmax:
        type: float
        inputBinding: 
          position: 2
      latmin:
        type: float
        inputBinding: 
          prefix: --lat
          position: 3
      latmax:
        type: float
        inputBinding: 
          position: 4
      tmin:
        type: int
        inputBinding: 
          prefix: --time
          position: 5
      tmax:
        type: int
        inputBinding: 
          position: 6
      resolution:
        type: float
        inputBinding: {prefix: --res}
      cycle:
        type: int
        inputBinding: {prefix: --cycle}
      step:
        type: int
        inputBinding: {prefix: --step}
    outputs:
      gribs:
        type: File[]
        outputBinding:
          glob: "*.f???"

  - id: gfs_table
    class: ExpressionTool
    inputs:
      resolution: float
    outputs:
      nlev: int
      levels: float[]
    expression: |
      ${
          var selectedList;
          var res = inputs.resolution;
          if (res === 0.5) {
              selectedList = [1000,975,950,925,900,875,850,825,800,775,750,725,700,675,650,625,600,575,550,525,500,475,450,425,400,375,350,325,300,275,250,225,200,175,150,125,100,70,50,40,30,20,15,10,7,5,3,2,1,0.7,0.4,0.2,0.1,0.07,0.04,0.02,0.01];
          } else {
              selectedList = [1000,975,950,925,900,850,800,750,700,650,600,550,500,450,400,350,300,250,200,150,100,70,50,40,30,20,15,10,7,5,3,2,1,0.7,0.4,0.2,0.1,0.07,0.04,0.02,0.01];
          }
          return { 
              levels: selectedList,
              nlev: selectedList.length
          };
      }
    requirements:
      InlineJavascriptRequirement: {}

  - id: grib2nc
    class: CommandLineTool
    baseCommand: sh
    arguments: ["grib2nc.sh"]
    inputs:
      gribs:
        type: File[]
        inputBinding: {position: 1}
      nlev: int
      levels: float[]
    outputs:
      netcdf:
        type: File
        outputBinding:
          glob: "*.nc"
    stdout: stdout.wgrib
    hints:
      DockerRequirement:
        dockerPull: docker.io/lmingari/wgrib2-minimal:1.0
    requirements:
      InlineJavascriptRequirement: {}
      InitialWorkDirRequirement:
        listing:
          - entryname: table.gfs
            entry: |
              $lev_type  100:lev:pressure level:mb:0.01
              $nlev      $(inputs.nlev)
              $levs      $(inputs.levels.join())
          - entryname: grib2nc.sh
            entry: |
              #!/bin/bash
              variables="HGT|TMP|RH|UGRD|VGRD|VVEL|PRES|PRATE|LAND|HPBL|SFCR"
              levels="([0-9]*[.])?[0-9]+ mb|surface|2 m above ground|10 m above ground"
              for file in "$@"; do
                  echo "Processing $file"
                  wgrib2 $file \
                    -match ":(\${variables}):" \
                    -match ":(\${levels}):" \
                    -nc_table "table.gfs" \
                    -append \
                    -nc3 \
                    -netcdf \
                    gfs.nc                    
              done

  - id: runner
    class: CommandLineTool
    label: Run FALL3D model
    baseCommand: mpirun
    arguments:
      - prefix: -n
        valueFrom: $(inputs.nx * inputs.ny * inputs.nz)
      - "Fall3d.x"
    inputs:
      task:
        type: string
        default: all
        inputBinding: {position: 0}
      inp: 
        type: File
        inputBinding: {position: 1}
      nx:
        type: int
        inputBinding: {position: 2}
      ny:
        type: int
        inputBinding: {position: 3}
      nz:
        type: int
        inputBinding: {position: 4}
      meteo: File
    outputs:
      stdout:
        type: stdout
      stderr:
        type: stderr
      log:
        type: File
        outputBinding:
          glob: "*.Fall3d.log"
      res:
        type: File
        outputBinding:
          glob: "*.res.nc"
      rst:
        type: File[]
        outputBinding:
          glob: "*.rst.nc"
    stdout: fall3d.out
    stderr: fall3d.err
    requirements:
      InlineJavascriptRequirement: {}
      InitialWorkDirRequirement:
        listing:
          - $(inputs.inp)
          - $(inputs.meteo)

  - id: plotter
    class: CommandLineTool
    baseCommand: ["plotter.py"]
    inputs:
      key:
        type: string
        inputBinding: {prefix: --key}
      netcdf:
        type: File
        inputBinding: {prefix: --netcdf}
      minval:
        type: float?
        inputBinding: {prefix: --minval}
      levels:
        type: float[]?
        inputBinding: {prefix: --levels}
      lat:
        type: float?
        inputBinding: {prefix: --lat}
      lon:
        type: float?
        inputBinding: {prefix: --lon}
      time:
        type: int?
        inputBinding: {prefix: --time}
    outputs:
      png:
        type: File
        outputBinding: {glob: "*.png"}   

  - id: gather_files
    class: ExpressionTool
    inputs:
      folder_name: string
      figs: File[]
      gribs: File[]
      rst: File[]
    outputs:
      collected_folder: Directory
    expression: |
      ${
          var dir = {
              "class": "Directory",
              "basename": inputs.folder_name,
              "listing": inputs.figs.concat(inputs.gribs,inputs.rst)
          };
          return {"collected_folder": dir};
      }
    requirements:
      InlineJavascriptRequirement: {}

  - id: main
    class: Workflow
    label: FALL3D forecast driven by GFS
    inputs:
      volcano: string
      lat_vent: float
      lon_vent: float
      elevation_vent: float
      date: string
      start_time: float
      end_time: float
      meteo_database: 
        type: "#main/MeteoDatabase"
      initial_condition:
        type: "#main/InitialCondition"
      restart: string
      west_lon: float
      east_lon: float
      north_lat: float
      south_lat: float
      dx: float
      dy: float
      nlevels: int
      # GFS inputs
      resolution: float
      step: int
      # MPI inputs
      nx: int
      ny: int
      nz: int
      # Plot inputs
      times: int[]
      keys: string[]
      levels: float[]
      basepath: 
        type: string
        default: "/home/lmingari/fall3d/iceland"
    outputs: 
      folder:
        type: Directory
        outputSource: create_folder/collected_folder
    steps:
      configure:
        run: "#config"
        in:
          template: 
            source: basepath
            valueFrom: $(self + "/template.inp")
          meteo: 
            source: gfs_netcdf/netcdf
            valueFrom: $(self.basename)
          meteo_database: meteo_database
          date: date
          start_time: start_time
          end_time: end_time
          west_lon: west_lon
          east_lon: east_lon
          north_lat: north_lat
          south_lat: south_lat
          dx: dx
          dy: dy
          nlevels: nlevels
          initial_condition: initial_condition
          restart: restart
          lon_vent: lon_vent
          lat_vent: lat_vent
          elevation_vent: elevation_vent
        out: [inp]
      gfs_times:
        run: "#gfs_times"
        in:
          reference_date: date
          hmin: start_time
          hmax: end_time
        out: [cycle,date,tmin,tmax]
      gfs_gribs:
        run: "#gfs"
        in:
          date: gfs_times/date
          tmin: gfs_times/tmin
          tmax: gfs_times/tmax
          cycle: gfs_times/cycle
          lonmin: west_lon
          lonmax: 
            source: east_lon
            valueFrom: $(self + inputs.resolution)
          latmin: south_lat
          latmax:
            source: north_lat 
            valueFrom: $(self + inputs.resolution)
          resolution: resolution
          step: step
        out: [gribs]
      gfs_levels:
        run: "#gfs_table"
        in:
          resolution: resolution
        out: [nlev,levels]
      gfs_netcdf:
        run: "#grib2nc"
        in:
          gribs: gfs_gribs/gribs
          nlev: gfs_levels/nlev
          levels: gfs_levels/levels
        out: [netcdf]
      run_fall3d:
        run: "#runner"
        in:
          inp: configure/inp
          nx: nx
          ny: ny
          nz: nz
          meteo: gfs_netcdf/netcdf
        out: [log,res,rst]
      plot_maps:
        run: "#plotter"
        scatter: [time,key]
        scatterMethod: flat_crossproduct
        in:
          key: keys
          time: times
          netcdf: run_fall3d/res
          lon: lon_vent
          lat: lat_vent
          levels: levels
        out: [png]
      create_folder:
        run: "#gather_files"
        in:
          figs: plot_maps/png
          gribs: gfs_gribs/gribs
          rst: run_fall3d/rst
          folder_name: date
        out: [collected_folder]
    requirements:
      StepInputExpressionRequirement: {}
      InlineJavascriptRequirement: {}
      ScatterFeatureRequirement: {}
      NetworkAccess:
        networkAccess: true
      SchemaDefRequirement:
        types:
          - name: MeteoDatabase
            type: enum
            symbols:
              - GFS
              - WRF
              - ERA5
          - name: InitialCondition
            type: enum
            symbols:
              - NONE
              - RESTART
              - INSERTION
