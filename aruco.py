import cv2
import numpy as np


class ArucoUtils:
    def __init__(self, size: int, markersDictionary: dict = cv2.aruco.DICT_4X4_50):
        self.size = size
        self.availableMarkers = markersDictionary
        self.markers = []
        self.ids = [4, 7, 13, 24]
        self.detectedMarkers = {"Ids": np.array([]), "Corners": np.array([])}
        self.offset = 3

        # self.detectedCorners = np.array([])
        # self.detectedIds = np.array([])

    def _generateMarker(self, idx: int):
        marker = np.zeros((self.size, self.size, 1), dtype="uint8")
        markersDict = cv2.aruco.getPredefinedDictionary(self.availableMarkers)
        markersDict.generateImageMarker(idx, self.size, marker)
        return marker

    def generateMarkers(self):
        for i in self.ids:
            self.markers.append(self._generateMarker(i))

    def placeMarkers(self, image):
        size = self.size + self.offset
        image[self.offset:size, self.offset:size] = self.markers[0]
        image[-size:-self.offset, -size:-
              self.offset] = self.markers[2]
        image[self.offset:size, -size:-
              self.offset] = self.markers[1]
        image[-size:-self.offset, self.offset:size] = self.markers[3]

    def detectCorners(self, image):
        self._detectMarkers(image)
        if type(self.detectedMarkers["Ids"]) == np.ndarray and len(self.detectedMarkers["Ids"]) == len(self.ids):
            allCorners = self.detectedMarkers["Corners"]
            print(allCorners)
            return np.array([allCorners[0][0][0], allCorners[3][0][3], allCorners[2][0][2], allCorners[1][0][1]])
        return None

    def _detectMarkers(self, image):
        greyImg = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        detectorParams = cv2.aruco.DetectorParameters()
        markersDict = cv2.aruco.getPredefinedDictionary(self.availableMarkers)
        detector = cv2.aruco.ArucoDetector(markersDict, detectorParams)
        rejectedImgPoints = np.array([])
        self.detectedMarkers["Corners"], self.detectedMarkers["Ids"], rejectedImgPoints = detector.detectMarkers(
            greyImg)
        self.detectedMarkers["Corners"] = np.array(
            self.detectedMarkers["Corners"])
        if type(self.detectedMarkers["Ids"]) == np.ndarray:
            self._sortMarkers()
        return rejectedImgPoints

    def outlineMarkers(self, image):
        cv2.aruco.drawDetectedMarkers(
            image, self.detectedMarkers["Corners"], self.detectedMarkers["Ids"])

    def _sortMarkers(self):
        sortedIds = self.detectedMarkers["Ids"].argsort(0)[
            :, 0]
        self.detectedMarkers["Ids"] = self.detectedMarkers["Ids"][sortedIds]
        self.detectedMarkers["Corners"] = self.detectedMarkers["Corners"][sortedIds]
