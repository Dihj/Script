#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  CFT Downloading Data from IRIDL script

@author: Dihj
"""

from PyQt5 import QtWidgets, uic
import sys
import os
import requests
from PyQt5.QtCore import QThread, pyqtSignal
import datetime

class DownloadDataApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("Download_data.ui", self)

        # Define available options for dropdowns
        #self.years = [str(year) for year in range(1960, 2026)]
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().strftime('%b') 
        self.years = [str(year) for year in range(1960, current_year + 1)] 
        self.months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        self.predictors = ["SST", "HGP850", "HGP500", "U850", "U200", "V850", "V200", "MSLP"]

        # Populate dropdowns
        self.firstYearCombo.addItems(self.years)
        self.lastYearCombo.addItems(self.years)
        self.prevMonthCombo.addItems(self.months)

        # Set default values
        self.firstYearCombo.setCurrentIndex(self.firstYearCombo.findText('1961'))
        self.lastYearCombo.setCurrentIndex(self.lastYearCombo.findText(str(current_year)))
        self.prevMonthCombo.setCurrentIndex(self.prevMonthCombo.findText(current_month))

        # Populate list widget for multiple predictors
        self.predictorListWidget.addItems(self.predictors)
        self.predictorListWidget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        # Adjust width of the predictor list widget
        self.predictorListWidget.setFixedWidth(150)  # Tight width

        # Connect buttons
        self.downloadButton.clicked.connect(self.download_data)
        self.exitButton.clicked.connect(self.close)
        self.browseButton.clicked.connect(self.browse_directory)

    def browse_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.downloadDirInput.setText(directory)

    def download_data(self):
        # Get selected values
        selected_items = self.predictorListWidget.selectedItems()
        predictors = [item.text() for item in selected_items]
        first_year = self.firstYearCombo.currentText()
        last_year = self.lastYearCombo.currentText()
        prev_month = self.prevMonthCombo.currentText()
        download_dir = self.downloadDirInput.text()

        # Validate directory
        if not download_dir:
            self.statusLabel.setText("Please select a valid download directory.")
            return

        # Define predictor URLs
        predictors_urls = {
            "SST": f"https://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCDC/.ERSST/.version5/.sst/T/({prev_month}%20{first_year}-{last_year})/RANGEEDGES/T/12/STEP/data.nc",
            "HGP850": f"https://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.MONTHLY/.Intrinsic/.PressureLevel/.phi/P/(850)/VALUES/T/({prev_month}%20{first_year}-{last_year})/RANGEEDGES/T/12/STEP/data.nc",
            "HGP500": f"https://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.MONTHLY/.Intrinsic/.PressureLevel/.phi/P/(500)/VALUES/T/({prev_month}%20{first_year}-{last_year})/RANGEEDGES/T/12/STEP/data.nc",
            #"HGP500": f"https://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.MONTHLY/.Intrinsic/.PressureLevel/.phi/P/(500)/VALUES/T/($PREV_MONTH%20$FIRST_YEAR-$PREV_YEAR)/RANGEEDGES/T/12/STEP/data.nc",
            "U850": f"https://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.MONTHLY/.Intrinsic/.PressureLevel/.u/P/(850)/VALUES/T/({prev_month}%20{first_year}-{last_year})/RANGEEDGES/T/12/STEP/data.nc",
            "U200": f"https://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.MONTHLY/.Intrinsic/.PressureLevel/.u/P/(200)/VALUES/T/({prev_month}%20{first_year}-{last_year})/RANGEEDGES/T/12/STEP/data.nc",
            "V850": f"https://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.MONTHLY/.Intrinsic/.PressureLevel/.v/P/(850)/VALUES/T/({prev_month}%20{first_year}-{last_year})/RANGEEDGES/T/12/STEP/data.nc",
            "V200": f"https://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.MONTHLY/.Intrinsic/.PressureLevel/.v/P/(200)/VALUES/T/({prev_month}%20{first_year}-{last_year})/RANGEEDGES/T/12/STEP/data.nc",
            "MSLP": f"https://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP-NCAR/.CDAS-1/.MONTHLY/.Intrinsic/.MSL/.pressure/T/({prev_month}%20{first_year}-{last_year})/RANGEEDGES/T/12/STEP/data.nc"
            # Add here another predictors if you want. 
        }

        # Create a directory for downloads
        os.makedirs(download_dir, exist_ok=True)

        # Set up progress bar
        self.progressBar.setValue(0)
        self.statusLabel.setText("Downloading...")

        # Start downloading in a separate thread to keep UI responsive
        self.downloader = MultiPredictorDownloader(predictors, prev_month, first_year, last_year, download_dir, predictors_urls, self.statusLabel)
        self.downloader.progress_signal.connect(self.update_progress)
        self.downloader.start()

    def update_progress(self, progress):
        self.progressBar.setValue(progress)


class MultiPredictorDownloader(QThread):
    progress_signal = pyqtSignal(int)

    def __init__(self, predictors, prev_month, first_year, last_year, download_dir, predictors_urls, status_label):
        super().__init__()
        self.predictors = predictors
        self.prev_month = prev_month
        self.first_year = first_year
        self.last_year = last_year
        self.download_dir = download_dir
        self.predictors_urls = predictors_urls
        self.status_label = status_label

    def run(self):
        total_predictors = len(self.predictors)
        downloaded_count = 0

        for predictor in self.predictors:
            if predictor in self.predictors_urls:
                url = self.predictors_urls[predictor]
                file_name = os.path.join(self.download_dir, f"{predictor}_{self.prev_month}_{self.first_year}-{self.last_year}.nc")

                try:
                    response = requests.get(url, stream=True)
                    total_length = int(response.headers.get('content-length', 0))
                    with open(file_name, "wb") as file:
                        downloaded = 0
                        for data in response.iter_content(chunk_size=1024):
                            downloaded += len(data)
                            file.write(data)
                            progress = int(downloaded / total_length * 100) if total_length > 0 else 100
                            self.progress_signal.emit(progress)
                    
                    downloaded_count += 1
                    self.status_label.setText(f"Downloaded: {file_name}")
                except requests.exceptions.RequestException as e:
                    self.status_label.setText(f"Error downloading {predictor}: {e}")
        
        # Final status update
        if downloaded_count == total_predictors:
            self.status_label.setText("All downloads completed successfully!")
        else:
            self.status_label.setText(f"Downloaded {downloaded_count}/{total_predictors} predictors.")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DownloadDataApp()
    window.show()
    sys.exit(app.exec_())
