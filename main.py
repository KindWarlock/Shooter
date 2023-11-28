import cv2
import numpy as np
import aruco
from game import BaloonsGame
import pygame
from math import sqrt
import matplotlib.pyplot as plt
import config


def openCam():
    # url = "http://192.168.43.1:8080/video"
    url = "/dev/video2"
    _cap = cv2.VideoCapture(url)
    print(_cap.get(cv2.CAP_PROP_FPS))
    if (_cap.isOpened() == False):
        print("Error opening video stream or file")
    return _cap


def getTestAruco():
    _arucoUtils = aruco.ArucoUtils(100)
    _arucoUtils.generateMarkers()
    _image = np.empty((480, 640, 3), dtype='uint8')
    _image.fill(255)
    _arucoUtils.placeMarkers(_image)
    cv2.imshow("Markers", _image)
    cv2.moveWindow('Markers', 2220, 0)
    return _arucoUtils, _image


def detectCircles(frame, minRadius=0, maxRadius=0):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                               param1=50, param2=30, minRadius=minRadius, maxRadius=maxRadius)
    if circles is None:
        return

    circles = np.uint16(np.around(circles))
    return circles


def separateCircles(circles, game, frame):
    offset = 30
    deletedIdx = []
    for i, c in enumerate(circles[0, :]):
        for b in game.baloons:
            xInRange = c[0] > b.pos.x - offset and c[0] < b.pos.x + offset
            yInRange = c[1] > b.pos.y - offset and c[1] < b.pos.y + offset
            rInRange = c[2] > b.size - 5 and c[2] < b.size + 5
            # print(xInRange, yInRange, rInRange)
            if xInRange and yInRange and rInRange:
                deletedIdx.append(i)
                continue
    background = [[b.pos.x, b.pos.y, b.size] for b in game.baloons]
    foreground = np.delete(circles[0], deletedIdx, axis=0)
    # drawing
    for c in foreground:
        cv2.circle(frame, (c[0], c[1]), c[2], (225, 0, 0), 2)
    for c in background:
        cv2.circle(frame, (int(c[0]), int(c[1])), c[2], (0, 255, 0), 2)
    return foreground, background


def detectCollision(rawCircles, game, frame):
    foreground, background = separateCircles(rawCircles, game, frame)
    collided = np.empty(shape=(0, 2), dtype=np.int8)
    for fg in foreground:
        fgX = fg[0]
        fgY = fg[1]
        fgR = fg[2]

        for bg in background:
            bgX = bg[0]
            bgY = bg[1]
            bgR = bg[2]
            dist = sqrt((fgX - bgX) ** 2 + (fgY - bgY) ** 2)
            if dist < (bgR + fgR / 2):
                collided = np.append(collided, [[fgX, fgY]], axis=0)
    # print(collided)
    return collided


def detectStop(currPos, prevPos):
    # print(np.linalg.norm(currPos - prevPos))
    if np.linalg.norm(currPos - prevPos) < 20:
        print('HIT!')
        return True
    return False


def getWarpMatrix(frame, markersImage):
    corners = arucoUtils.detectCorners(frame)
    arucoUtils.outlineMarkers(frame)
    warpMatrix = None
    if type(corners) == np.ndarray:
        # x, y format
        out = np.float32([[0, 0],
                          [0, markersImage.shape[0] - 1],
                          [markersImage.shape[1] - 1,
                           markersImage.shape[0] - 1],
                          [markersImage.shape[1] - 1, 0]])
        # print(corners, out)
        warpMatrix = cv2.getPerspectiveTransform(corners, out)
    else:
        cv2.imshow('Frame', frame)
    return warpMatrix


def findMinDist(collided, prevPos):
    dists = np.linalg.norm(collided - prevPos, axis=1)
    print('prevPos: ', prevPos, ', collided: ',
          collided, ', minDist: ',  dists)
    return np.min(dists), np.argmin(dists)
    # return minDist


def runGame(frame, prevPos):
    game.run()
    # cv2.imshow('Game', game.screen)
    gameImage = cv2.warpPerspective(
        frame, warpMatrix, (640, 480))
    circles = detectCircles(
        gameImage, minRadius=10, maxRadius=game.baloons[0].size + 10)
    minVal = 0

    if type(circles) == np.ndarray:
        # compareBaloons(gameImage, game, circles)

        collided = detectCollision(circles, game, gameImage)
        if np.any(collided):
            minVal, minIdx = findMinDist(collided, prevPos)
            prevPos = collided[minIdx]
            # print(minVal)
            if minVal < 17.5:
                print('Hit!')
                game.popBaloon(prevPos)
                prevPos[:] = 0
            # for currPos in collided:
            #     if detectStop(currPos, prevPos):
            #         game.popBaloon(currPos)
            #         break

    imgdata = pygame.surfarray.array3d(game.screen).swapaxes(0, 1)
    cv2.imshow('Markers', imgdata)

    cv2.imshow('Game', gameImage)
    return prevPos, minVal
    # return prevNumber


def compareBaloons(frame, game, circles):
    baloonsLeft = game.baloons.copy()
    offset = 30
    for b in game.baloons:
        xInRange = np.any(circles[0, :, 0] > b.pos.x -
                          offset) and np.any(circles[0, :, 0] < b.pos.x + offset)
        yInRange = np.any(circles[0, :, 1] > b.pos.y -
                          offset) and np.any(circles[0, :, 1] < b.pos.y + offset)
        # idx = np.where(np.any(xInRange and yInRange))
        if np.any(xInRange and yInRange):
            # print(b.pos.x, b.pos)
            baloonsLeft.remove(b)
        cv2.circle(frame, (int(b.pos.x), int(b.pos.y)), 1, (255, 255, 0), 2)
    baloonPos = []
    for b in baloonsLeft:
        # for b in game.baloons:
        if not game.checkIfBallonOnScreen(b):
            continue
        baloonPos.append([b.pos.x, b.pos.y])
        cv2.circle(frame, (int(b.pos.x), int(b.pos.y)), 1, (0, 0, 0), 2)
        game.popBaloon([b.pos.x, b.pos.y])
    game.updateDebug('Ballons: ', baloonPos)


gameImage = []

arucoUtils, markersImage = getTestAruco()
cap = openCam()
resize_scale = 2
warpMatrix = []
prevNumber = 0

data = []
prevPos = np.array([0, 0], dtype=np.int8)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)

# Lower exposition = lower fps
# cap.set(cv2.CAP_PROP_EXPOSURE, 1)
cap.set(cv2.CAP_PROP_EXPOSURE, 50)


cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
# cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
# mtx, dist, rvecs, tvecs = config.mtx, config.dist, config.rvecs, config.tvecs


game = BaloonsGame()
state = 0

while (cap.isOpened()):
    ret, frame = cap.read()
    if ret:
        # frame = cv2.resize(
        #     frame, (frame.shape[1] // resize_scale, frame.shape[0] // resize_scale))
        # frame = cv2.undistort(frame, mtx, dist, None)

        if state == 0:
            result = getWarpMatrix(frame, markersImage)
            if result is not None:
                warpMatrix = result
                state = 1

        elif state == 1:
            prevPos, dist = runGame(frame, prevPos)
            if dist > 1 and dist < 20:
                data.append(dist)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        elif cv2.waitKey(1) & 0xFF == ord('b'):
            print('Median: ', np.median(data), 'Iqr: ',
                  np.subtract(*np.percentile(data, [75, 25])))
            plt.plot(data)
            plt.show()
    else:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

cap.release()
cv2.destroyAllWindows()
