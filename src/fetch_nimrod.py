
"""
Script to pull the nimrod data pulled in the data folder in this repo. This should be pulled prior 
to running this script.
"""

import io
import tarfile
from datetime import datetime, timezone
import pandas as pd
import logging
import os
from collections import defaultdict
import numpy as np
import gzip
import shutil
import nimrod # https://github.com/richard-thomas/MetOffice_NIMROD
from typing import Literal
from dateutil.relativedelta import relativedelta
from pyproj import Transformer
from config import NIMROD_STATIONS

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# one-time transformer WGS84 → BNG (EPSG:27700)
_wgs84_to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)

# Env
BASE_DIR = os.path.join(os.getcwd(),"data/dap.ceda.ac.uk/badc/ukmo-nimrod/data/composite/uk-1km")

class fetchNimrod:

    def __init__(self, coords, start_datetime_utc, end_datetime_utc, csv_path, method="composite"):

        # Initialize variables
        assert method in ["composite","closest"], "method must be 'closest' or 'composite'"
        self.coords = coords
        self.start_datetime_utc = start_datetime_utc
        self.end_datetime_utc = end_datetime_utc
        self.method = method
        logger.info(f"Parameters: {self.__dict__}\n")

        # Create list of days that need to be analysed
        df = self._get_files_df_()
        logger.info(f"Files to be queried :{df["fn"]}\n")
        
        # Define location of dump path
        self.dump_path = os.path.join(BASE_DIR, "temp")

        # Loop through files and get required data from each
        df2 = self._loop_through_files_(df)
        del df

        # Convert dataframe to hourly to get accumulated precip values
        hourly_acc_df = self._get_hourly_accumulated_rainfall_(df2)

        # Output to csv
        hourly_acc_df.to_csv(csv_path)
        logger.info(f"Dropped csv: {csv_path}")


    @staticmethod
    def _split_by_year_(dates_array):
        
        """ Split a 1-D array of datetime.date objects into sub-arrays by year."""
        groups = defaultdict(list)
        for dt in dates_array:
            groups[dt.year].append(dt)
        # convert lists to numpy arrays (preserving order)
        return { year: np.array(dts, dtype=object)
                for year, dts in sorted(groups.items()) }

    @staticmethod
    def _get_date_from_fn_(fn):
        """Find the correct date given file name"""
        try:
            dt = pd.to_datetime(fn.split(".")[0].split("_")[2],format="%Y%m%d").tz_localize("utc")
        except IndexError as e:
            raise IndexError(f"Error parsing date '{fn}': {e}") from e
        logger.debug(f"Converted {fn} -> {dt}")
        return dt
    
    def _get_files_df_(self):
        """Get the zip files in the base folder that need to be queried"""
        # Create range for dates in between start and end dates
        range = pd.date_range(start=start_datetime_utc, end=end_datetime_utc,tz="utc")
        logger.info(f"Date range: {range}\n")

        # Split array into dict by years
        yearly = self._split_by_year_(range)

        # Create arr to add file and dates to
        arr = []

        # Loop through year folder in BASE_DIR and add neccessary filepaths
        for year in yearly.keys():
            
            # Get dirs in year folder
            dirs = os.listdir(os.path.join(BASE_DIR, str(year)))
            logger.debug(f"Process {year} files: {dirs}")

            # Get dates for all files in the year folder and create a df, ignore html files
            for fn in dirs:
                if fn.split(".")[-1] != "html":
                    dt = self._get_date_from_fn_(fn)
                    arr.append((dt, os.path.join(BASE_DIR, str(year), fn)))

        # Create df
        df = pd.DataFrame(arr,columns=["date","fn"]).sort_values(by=["date"]).set_index("date",drop=True)

        # Only keep rows within the given start and end datetimes (utc)
        df_range = pd.DataFrame(range,columns=["range"])
        df2 = df.reset_index().merge(df_range,left_on="date",right_on="range",how="right").drop(columns="range").dropna()

        return df2

    @staticmethod
    def _decompress_tar_folder_(tar_path, extract_path, date):
        """
        Decompresses a tar folder to the specified directory.

        :param tar_path: Path to the tar file.
        :param extract_path: Directory where the contents will be extracted.
        """
        
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)
        
        with tarfile.open(tar_path, 'r:*') as tar:
            tar.extractall(path=extract_path)
            logger.info(f"Extracted all files to temp folder for {str(date)}")


    @staticmethod
    def _get_datetime_from_filename_(fn):
        """Get datetime from .dat.gz file"""
        return pd.to_datetime(fn.split("_")[2],format="%Y%m%d%H%M").tz_localize("utc")
    
    @staticmethod
    def _read_nimrod_gz_(path):
        """
        Read a Met Office NIMROD .dat.gz file and return:
        - nim:   the Nimrod object (with all header fields)
        - data:  a 2D numpy array of rainfall in mm/hr
        """
        # 1) Open the gzipped file for binary reading
        with gzip.open(path, 'rb') as f:
            nim = nimrod.Nimrod(f)           # parses header + payload
        
        # 2) Convert the flat int16 array into a 2D grid
        arr = np.frombuffer(nim.data, dtype=np.int16)
        arr = arr.reshape((nim.nrows, nim.ncols))
        
        # 3) Scale values: stored as (mm/hr) * 32, per NIMROD spec
        rainfall = arr.astype(np.float32) / 32.0  # yields mm/hr :contentReference[oaicite:1]{index=1}

        return nim, rainfall


    @staticmethod
    def clear_folder(path):
        """
        Delete all files and subdirectories in `path`, but keep `path` itself.
        """
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                # recursively delete a subdirectory
                shutil.rmtree(full_path)
            else:
                # delete a file or symlink
                os.remove(full_path)
        logger.info(f"Cleared temp folder")


    def _loop_through_files_(self,df):
        
        """Takes the file dataframe and decompresses them one by one into the temp folder for analysis"""
        
        # Create inital arr & delete contents of temp folder
        arr = []
        self.clear_folder(self.dump_path)

        # Loop through required file paths
        for _, row in df.iterrows():
            
            # Dump the contents of the file into the temp folder
            self._decompress_tar_folder_(row["fn"], self.dump_path, row.date.date())

            # Loop through the contents of the temp folder and use the nimrod package to read
            for file in os.listdir(self.dump_path):
                
                # Get dt from filename
                dt = self._get_datetime_from_filename_(file)

                # Get the precipitation rate from the file and add it and the datetime to the array
                if self.method == "composite":
                    precip_arr = self.get_precip_rates(os.path.join(self.dump_path, file))
                elif self.method == "closest":
                    precip_arr = self.get_precip_rates_from_closest_station(os.path.join(self.dump_path, file))

                # Append the required data to the inital arr
                arr.append((dt, *precip_arr))

            # Delete the contents of the temp folder
            self.clear_folder(self.dump_path)
        
        # Combine arr with coords and dates to get a df result
        df = pd.DataFrame(arr, columns=["date"] + [f"{[coord[0],coord[1]]}" for coord in self.coords]).sort_values(by=["date"])

        return df

    def get_precip_rates(
        self,
        path: str,
        crs_in: Literal["WGS84", "grid"] = "WGS84",
    ) -> np.ndarray:
        """
        Sample precipitation rates (mm/hr) from a NIMROD .dat.gz file at
        self.coords, but if the file can’t be read, return N/A for all points.

        Parameters
        ----------
        path
            Path to the gzipped NIMROD .dat file.
        crs_in
            Coordinate system of self.coords:
            - "WGS84": coords are (latitude, longitude) in EPSG:4326.
            - "grid": coords are already (x, y) in the same CRS as the NIMROD grid (BNG).

        Returns
        -------
        rates : np.ndarray, shape (N,)
            Precipitation (mm/hr) at each coordinate, or np.nan if the file fails to load.
        """
        # prepare coords array and output shape
        pts = np.asarray(self.coords, dtype=float)
        if pts.ndim != 2 or pts.shape[1] != 2:
            raise ValueError(f"coords must be shape (N,2), got {pts.shape}")
        N = pts.shape[0]

        # 1) Try to load the grid + rainfall array (mm/hr); on fail return all NaNs
        try:
            nim, rainfall = self._read_nimrod_gz_(path)
        except Exception:
            return np.full(N, np.nan, dtype=float)

        # 2) project if needed
        if crs_in == "WGS84":
            lats, lons = pts[:, 0], pts[:, 1]
            xs, ys = _wgs84_to_bng.transform(lons, lats)
        else:
            xs, ys = pts[:, 0], pts[:, 1]

        # 3) compute integer column & row indices
        cols = np.round((xs - nim.x_left) / nim.x_pixel_size).astype(int)
        rows = np.round((nim.y_top - ys) / nim.y_pixel_size).astype(int)

        # 4) mask out-of-bounds
        valid = (
            (rows >= 0) & (rows < nim.nrows) &
            (cols >= 0) & (cols < nim.ncols)
        )

        # 5) build output array of NaNs, then fill valid entries
        rates = np.full(N, np.nan, dtype=float)
        if valid.any():
            vals = rainfall[rows[valid], cols[valid]]
            # any negative value indicates no-data → NaN
            vals = np.where(vals < 0, np.nan, vals)
            rates[valid] = vals

        return rates


    def get_precip_rates_from_closest_station(
        self,
        path: str,
        crs_in: Literal["WGS84", "grid"] = "WGS84",
    ) -> np.ndarray:
        """
        Sample precipitation rates (mm/hr) from a NIMROD .dat.gz file at
        the coordinates of the nearest NIMROD station to each input point.

        Parameters
        ----------
        path
            Path to the gzipped NIMROD .dat file.
        crs_in
            Coordinate system of self.coords:
              - "WGS84": coords are (latitude, longitude) in EPSG:4326.
              - "grid": coords are already (x, y) in British National Grid (EPSG:27700).

        Returns
        -------
        rates : np.ndarray, shape (N,)
            Precipitation (mm/hr) at the nearest station for each input coord.
            Out-of-bounds or no-data → np.nan.
        """
        # 1) load the grid + rainfall array (mm/hr)
        nim, rainfall = self._read_nimrod_gz_(path)

        # 2) get input points
        pts = np.asarray(self.coords, dtype=float)
        if pts.ndim != 2 or pts.shape[1] != 2:
            raise ValueError(f"coords must be shape (N,2), got {pts.shape}")

        # 3) project pts to grid CRS if needed
        if crs_in == "WGS84":
            lats, lons = pts[:, 0], pts[:, 1]
            xs, ys = _wgs84_to_bng.transform(lons, lats)
        else:
            xs, ys = pts[:, 0], pts[:, 1]

        # 4) load station coords and project to grid CRS
        names = list(NIMROD_STATIONS.keys())
        stat_lats = np.array([NIMROD_STATIONS[n]["lat"] for n in names])
        stat_lons = np.array([NIMROD_STATIONS[n]["lon"] for n in names])

        if crs_in == "WGS84":
            xs_s, ys_s = _wgs84_to_bng.transform(stat_lons, stat_lats)
        else:
            # if user coordinates are already in grid CRS, assume stations are too
            xs_s, ys_s = stat_lats, stat_lons  # unlikely, but falls back

        # 5) find nearest station for each point
        #    compute squared distances between each pt and each station
        dx = xs[:, None] - xs_s[None, :]
        dy = ys[:, None] - ys_s[None, :]
        nearest_idx = np.argmin(dx*dx + dy*dy, axis=1)  # shape (N,)

        # 6) turn station grid coords into row/col once
        #    note: nim.x_left, nim.y_top, nim.x_pixel_size, nim.y_pixel_size
        cols_s = np.round((xs_s - nim.x_left) / nim.x_pixel_size).astype(int)
        rows_s = np.round((nim.y_top - ys_s) / nim.y_pixel_size).astype(int)

        # 7) build output array of NaNs, then fill from station pixels
        N = pts.shape[0]
        rates = np.full(N, np.nan, dtype=float)

        # mask stations that are actually in bounds
        valid_stat = (
            (rows_s >= 0) & (rows_s < nim.nrows) &
            (cols_s >= 0) & (cols_s < nim.ncols)
        )

        # for each point, if its nearest station is in bounds, grab the rain value
        for i, stat_i in enumerate(nearest_idx):
            if valid_stat[stat_i]:
                val = rainfall[rows_s[stat_i], cols_s[stat_i]]
                # negative → no-data
                rates[i] = float(val)
                # rates[i] = np.nan if val < 0 else float(val)

        return rates

    @staticmethod
    def _get_hourly_accumulated_rainfall_(df):
        """Convert 5-minute mm/hr precip rate data into hourly accumulated rainfall, returns NaN where appropriate"""
        
        # Reset index
        df = df.set_index("date")

        # 1) compute the hourly mean (will average whatever values *are* there)
        df_h = df.resample("h").mean()

        # 2) count how many non-NA samples each hour had
        counts = df.resample("h").count()

        # 3) wherever counts < 12, force the mean to NaN, return NaN if we don't have 25% of the data for a given hour
        df_h[counts < 9] = np.nan

        # 4) shift the index to label each hour by its end time
        df_h.index = df_h.index + pd.Timedelta(hours=1)

        return df_h





if __name__ == "__main__":

    # Get coords from coords csv
    # df = pd.read_csv("data/csvs/random_uk_land_coords.csv", index_col=0)
    # coords_arr = []
    # for _, row in df.iterrows():
    #     coords_arr.append((float(row["lat"]), float(row["long"])))

    # Use coords from festival list
    coords_arr = [
        (52.826829, 0.652),                         # Houghton
        (51.49988, -0.29109),                       # Waterworks
        (51.1586418151855, -2.58320236206054),      # Glasonbury
        (55.8477254, -4.2344144),                   # TRNSMT
        (50.435834, -5.03676),                      # Boardmasters
        (53.869932, -1.379663),                     # Leeds Festival
        (51.46367, -0.985466),                      # Reading Festival
        (50.706523, -1.284858),                     # Isle of Wight Festival
        (50.639106, -2.208773),                     # Camp Bestival
        (52.842018, -1.354528)                      # Download Festival
    ]

    # Create start and end datetimes, loop through summer dates from 2004
    for year in range(2014,2024 + 1):
        
        # Get summer dates for the year in question
        start_datetime_utc = datetime(year, 4, 1, tzinfo=timezone.utc)
        end_datetime_utc = datetime(year, 9, 30, tzinfo=timezone.utc)
        csv_path = os.path.join(os.getcwd(), f"data/csvs/nimrod_festival_actuals_{str(year)}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv")

        # Initiate class and save csv
        cls = fetchNimrod(coords_arr, start_datetime_utc, end_datetime_utc, csv_path)

    # --------------------------------------

    # start_time_utc = 8
    # end_time_utc = 19

    # df = pd.read_csv(os.path.join(os.getcwd(), "data/csvs", "nimrod_clostest_station_actuals_2023.csv"))
    # df = df.rename(columns={df.columns[0]:"date"})
    # df["date"] = pd.to_datetime(df["date"])
    # df["hour"] = [hr.hour for hr in df["date"]]
    # df = df[(df["hour"] >= start_time_utc) & (df["hour"] <= end_time_utc)]

    # df_count = pd.DataFrame(df.set_index("date").resample('D').count().iloc[:,1])

    # date_arr = []

    # for date, row in df_count.iterrows():
    #     if row.iloc[0] == (end_time_utc - start_time_utc + 1):
    #         date_arr.append(date)

    # df = df.drop(columns=["hour"]).set_index("date",drop=True)
    # df["day"] = [d.date() for d in df.index]
    # df_sum = df.groupby("day").sum()

    # splice_arr = []
    # for date, row in df_sum.iterrows():
    #     if pd.Timestamp(date).tz_localize("utc") in date_arr:
    #         splice_arr.append("T")
    #     else:
    #         splice_arr.append("F")

    # df_sum["Inc"] = splice_arr
    # df = df_sum[df_sum["Inc"] == "T"].drop(columns=["Inc"])
    # df.to_csv(os.path.join(os.getcwd(), "data/csvs/2023_rearranged_closest_station.csv"))