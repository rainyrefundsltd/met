
# Tweaked from https://github.com/MetOffice/weather_datahub_utilities/blob/main/atmospheric_order_download/cda_download.py
# Script to fetch met office data

from datetime import datetime
import inspect
import requests
import sys
import time
import traceback
import os
from config import MET_OFFICE_API_KEY

class MetFileImporter:
    def __init__(self):

        # Initialize variables
        self.MODEL_LIST = ["mo-uk-latlon"]
        self.BASE_URL = "https://data.hub.api.metoffice.gov.uk/atmospheric-models/1.0.0"
        self.fillgaps = False
        self.verbose = False
        self.debugMode = False
        self.perfMode = True
        self.printUrl = True
        self.retryCount = 3
        self.verifySSL = True
        self.order = "dailyrainfallaccumulation" # This is the name of the order on the MET Office portal
        self.useEnhancedApi = True
        self.run = "08"  # Time when model is released (8am UTC)
        self.numFilesPerOrder = 0

        # File drop location
        self.baseFolder = "data/met_forecasts"
        os.makedirs(self.baseFolder, exist_ok=True)

        # Request header including API (from .env file)
        self.requestHeaders = {'apikey': MET_OFFICE_API_KEY}
        print(f"MET OFFICE API KEY IN FETCH DATA: {MET_OFFICE_API_KEY}")


    def get_order_details(self):

        if self.perfMode:
            print("PM ", inspect.stack()[0][3], " started")
            pmstart = datetime.now()

        details = None

        actualHeaders = {"Accept": "application/json"}
        actualHeaders.update(self.requestHeaders)

        url = self.BASE_URL + "/orders/" + self.order + "/latest"
        if self.useEnhancedApi:
            url = url + "?detail=MINIMAL"
            url = url + "&runfilter=" + self.run

        try:
            req = requests.get(url, headers=actualHeaders, verify=self.verifySSL)
            req.raise_for_status()
        except Exception as exc:
            print("EXCEPTION: get_order_details failed first time")
            print(traceback.format_exc())
            print(exc)
            time.sleep(5)
            try:
                req = requests.get(url, headers=actualHeaders, verify=self.verifySSL)
                req.raise_for_status()
            except Exception as exctwo:
                print("EXCEPTION: get_order_details failed second time")
                print(exctwo)
                sys.exit(8)

        if self.printUrl == True:
            print("get_order_details: ", url)
            if url != req.url:
                print("redirected to: ", req.url)

        if req.status_code != 200:
            print(
                "ERROR: Unable to load details for order : ",
                self.order,
                " status code: ",
                req.status_code,
            )
            print("Headers: ", req.headers)
            print("Text: ", req.text)
            print("URL:", url)
            sys.exit(6)
        else:
            details = req.json()

        if self.perfMode:
            pmend = datetime.now()
            delta = round((pmend - pmstart).total_seconds() * 1000)
            print(
                "PM ",
                inspect.stack()[0][3],
                " executed in ",
                str(delta),
                "ms",
                "API URL:",
                url,
            )

        return details

    def get_model_runs(self):

        modelRuns = {}

        if self.perfMode:
            print("PM ", inspect.stack()[0][3], " started")
            pmstart = datetime.now()

        runHeaders = {"Accept": "application/json"}
        runHeaders.update(self.requestHeaders)

        for model in self.MODEL_LIST:
            requrl = self.BASE_URL + "/runs/" + model + "?sort=RUNDATETIME"

            for loop in range(self.retryCount):
                if self.perfMode:
                    print("PM ", inspect.stack()[0][3], " model=", model, " started ")
                    pmstart2 = datetime.now()

                try:
                    reqr = requests.get(requrl, headers=runHeaders, verify=self.verifySSL)
                    reqr.raise_for_status()
                except Exception as exc:
                    print("EXCEPTION: get_model_runs failed first time")
                    print(traceback.format_exc())
                    print(exc)
                    time.sleep(5)
                    try:
                        reqr = requests.get(requrl, headers=runHeaders, verify=self.verifySSL)
                        reqr.raise_for_status()
                    except Exception as exctwo:
                        print("EXCEPTION: get_model_runs failed second time")
                        print(exctwo)
                        #                   raise SystemError(exctwo)
                        sys.exit(9)

                if self.perfMode:
                    pmend2 = datetime.now()
                    delta2 = round((pmend2 - pmstart2).total_seconds() * 1000)
                    print(
                        "PM ",
                        inspect.stack()[0][3],
                        " model=",
                        model,
                        " executed in ",
                        str(delta2),
                        "ms",
                        "API URL:",
                        requrl,
                    )

                if self.printUrl == True:
                    print("get_model_runs: ", requrl)
                    if requrl != reqr.url:
                        print("redirected to: ", reqr.url)

                if reqr.status_code != 200:
                    print(
                        "ERROR:  Unable to get latest run for model: "
                        + model
                        + " status code: ",
                        reqr.status_code,
                    )
                    if loop != (self.retryCount - 1):
                        time.sleep(10)
                        continue
                    else:
                        print("ERROR:  Ran out of retries to get latest run for model: ")
                        break

                rundetails = reqr.json()
                rawlatest = rundetails["completeRuns"]
                modelRuns[model] = rawlatest[0]["run"] + ":" + rawlatest[0]["runDateTime"]
                break
            # endFor=True

        if self.perfMode:
            pmend = datetime.now()
            delta = round((pmend - pmstart).total_seconds() * 1000)
            print("PM ", inspect.stack()[0][3], " executed in ", str(delta), "ms")

        return modelRuns

    def get_files_by_run(self, order):

        # Break down the files in to those needed for each run
        filesByRun = {}
        filesByRun[self.run] = []
        fc = 0
        for f in order["orderDetails"]["files"]:
            fileId = f["fileId"]
            if "_+" + self.run in fileId:
                filesByRun[self.run].append(fileId)
                fc += 1
                if self.numFilesPerOrder > 0 and fc >= self.numFilesPerOrder:
                    break

        return filesByRun

    @staticmethod
    def backoff_time_calculator(self, count, limit):
        # fails limit values 5 and 30 used for get_order_file and get_my_orders respectively
        if limit == 5:
            match count:
                case 1:
                    return 5
                case 2:
                    return 10
                case 3:
                    return 15
                case 4:
                    return 30
        elif limit == 30:
            if count <= 5:
                return 1
            elif 5 < count <= 20:
                return count / 2
            elif 20 < count <= 30:
                return 30

    def get_order_file(
            self,
            fileId,
            guidFileNames,
            folder,
            start,
            backdatedDate,
    ):
        # If file id is too long or random file names required generate a uuid for the file name

        urlMod = ""
        global debugMode
        global perfMode
        global workerThreadsWaiting

        if len(fileId) > 100 or guidFileNames:
            local_filename = folder + "/" + str(uuid.uuid4()) + ".grib2"
        else:
            local_filename = folder + "/" + fileId + ".grib2"

        ttfb = 0

        if backdatedDate != "":
            if debugMode == True:
                print("DEBUG: We are in backdated Date mode for the date: " + backdatedDate)
            fileId = fileId.replace("+", backdatedDate)
            if debugMode == True:
                print("DEBUG: New fileID is: " + fileId)

        url = requests.utils.quote(self.BASE_URL + "/orders/" + self.order + "/latest/" + fileId + "/data", safe=': /')

        if self.debugMode == True:
            urlMod = input(
                "Order: "
                + self.order
                + " File:"
                + fileId
                + "\n"
                + "Enter y to mimic a receive failure on file - 'go' to run to end> "
            )
            # If you put go all further runs will automatically go through
            if urlMod == "go":
                self.debugMode = False
            if self.debugMode == True and urlMod == "y":
                url = (
                        self.BASE_URL
                        + "/orders/"
                        + self.order
                        + "/latest/"
                        + fileId
                        + urlMod
                        + "/data"
                )

        actualHeaders = {"Accept": "application/x-grib"}
        actualHeaders.update(self.requestHeaders)

        if perfMode:
            pmstart3 = datetime.now()

        failLimit = 30
        failCount = 0
        MyThread = threading.current_thread()
        MyThreadName = MyThread.name

        if self.verbose:
            print("get_order_file: ", MyThreadName, " Terminate value ", terminate)

        while True:

            with requests.get(url, headers=actualHeaders, allow_redirects=True, stream=True, verify=self.verifySSL) as r:

                if r.url.find("--") != -1:
                    if self.verbose:
                        print("-- found in redirect: ", r.url)

                if self.printUrl == True:
                    print("get_order_file: ", url)
                    if url != r.url:
                        print("redirected to: ", r.url)

                if self.perfMode:
                    pmend3 = datetime.now()
                    delta3 = round((pmend3 - pmstart3).total_seconds() * 1000)
                    if delta3 > int(self.perfTime) * 1000:
                        print("PM ", url, " executed in ", str(delta3) + "ms")

                if r.status_code != 200:
                    failCount += 1
                    print("ERROR: File download failed " + str(failCount) + " time(s).")
                    print("Headers: ", r.headers)
                    print("Text: ", r.text)
                    print("URL:", url)
                    print("Redirected URL:", r.url)

                if r.status_code == 200:
                    if self.verbose:
                        print("get_order_file: Status code 200 - writing file with content length ", len(r.content))

                    # Record time to first byte
                    ttfb = start + r.elapsed.total_seconds()

                    if os.path.exists(local_filename) == True:
                        if self.fillGaps == True:
                            if self.verbose:
                                print("File: ", local_filename, " has already been downloaded")
                            break
                        else:
                            os.remove(local_filename)

                    with open(local_filename, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                        f.close()

                    break

        return [ttfb, local_filename]

    def download_worker(self, downloadTask):
        try:
            # Extract task details
            fileId = downloadTask["fileId"]
            folder = downloadTask["folder"]
            headers = downloadTask["requestHeaders"]

            # Construct download URL and file path
            download_url = f"{downloadTask['baseUrl']}/orders/{downloadTask['orderName']}/latest/{fileId}/data".replace(
                "+", "%2B") # encoding error with + signs
            file_path = os.path.join(folder, f"{fileId}.grib2")  # Customize file naming as needed

            # Make the API call and save the file
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()  # Check for HTTP errors

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            if self.verbose:
                print(f"Downloaded file {fileId} to {file_path}")
        except Exception as e:
            print(f"Error downloading file {fileId}: {e}")


    def download_files(self, filesByRun):

        # Create folder to save files

        if self.verbose:
            print("Starting downloads")

        if self.perfMode:
            print("PM Download starting")
            pmstart = datetime.now()

        # Process each file sequentially
        for fileId in filesByRun[self.run]:
            downloadTask = {
                "baseUrl": self.BASE_URL,
                "requestHeaders": self.requestHeaders,
                "orderName": self.order,
                "fileId": fileId,
                "guidFileNames": False,
                "folder": self.baseFolder,
                "responseLog": [],
                "downloadErrorLog": [],
                "backdatedDate": '',
            }

            # Call the worker directly to process the download
            self.download_worker(downloadTask)

        if self.perfMode:
            pmend = datetime.now()
            delta = round((pmend - pmstart).total_seconds() * 1000)
            print("PM Download executed in ", str(delta), "ms")

        if self.verbose:
            print("Downloads complete")



if __name__ == "__main__":
    
    # Start class
    client = MetFileImporter()

    # Get the model runs available
    runs_dict = client.get_model_runs()

    # Get the order details
    order = client.get_order_details()

    # Get the files for this run
    files = client.get_files_by_run(order)

    # Check whether the run is already in the folder
    client.download_files(files)