import cv2
import numpy as np
import aruco
from game import BaloonsGame
import pygame
from math import sqrt
import matplotlib.pyplot as plt
import config


def openCam():
    url = "http://192.168.1.39:8080/video"
    # url = "/dev/video2"
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
    cv2.imshow("Game", _image)
    # cv2.moveWindow('Markers', 2220, 0)
    return _arucoUtils, _image


def detectCircles(frame, minRadius=0, maxRadius=0):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                               param1=50, param2=25, minRadius=minRadius, maxRadius=maxRadius)
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


def getColorMask(frame):
    yellow = [[20, 30, 30], [35, 255, 255]]
    green = [[40, 30, 30], [75, 255, 255]]

    # Красный присутствует на обеих границах
    red_low = [[0, 30, 30], [15, 255, 255]]
    red_high = [[160, 30, 30], [179, 255, 255]]
    blue = [[80, 30, 30], [130, 255, 255]]

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask_yellow = cv2.inRange(hsv, yellow[0], yellow[1])
    mask_red = cv2.bitwise_or(cv2.inRange(
        hsv, red_low[0], red_low[1]), cv2.inRange(hsv, red_high[0], red_high[1]))
    mask_blue = cv2.inRange(hsv, blue[0], blue[1])
    mask_green = cv2.inRange(hsv, green[0], green[1])
    return mask_yellow, mask_red, mask_blue, mask_green


def getWarpMatrix(frame, markersImage):
    corners = arucoUtils.detectCorners(frame)
    arucoUtils.outlineMarkers(frame)
    warpMatrix = None

    cv2.imshow('Frame', frame)

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
    # print('prevPos: ', prevPos, ', collided: ',
    #   collided, ', minDist: ',  dists)
    return np.min(dists), np.argmin(dists)
    # return minDist


def runGame(frame, prevPos):
    game.run()
    # cv2.imshow('Game', game.screen)
    gameImage = cv2.warpPerspective(
        frame, warpMatrix, (640, 480))
    circles = detectCircles(
        gameImage, minRadius=17, maxRadius=game.baloons[0].size + 10)
    minVal = 0

    if type(circles) == np.ndarray:
        # compareBaloons(gameImage, game, circles)

        collided = detectCollision(circles, game, gameImage)
        if np.any(collided):
            minVal, minIdx = findMinDist(collided, prevPos)
            prevPos = collided[minIdx]
            # print(minVal)
            if minVal < 17.5:
                game.popBaloon(prevPos)
                prevPos[:] = 0
            # for currPos in collided:
            #     if detectStop(currPos, prevPos):
            #         game.popBaloon(currPos)
            #         break

    imgdata = pygame.surfarray.array3d(game.screen).swapaxes(0, 1)
    cv2.imshow('Game', imgdata)

    cv2.imshow('Game (Camera)', gameImage)
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


def preprocess(frame):
    rgb_planes = cv2.split(frame)

    result_planes = []
    result_norm_planes = []
    for plane in rgb_planes:
        dilated_img = cv2.dilate(plane, np.ones((7, 7), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        norm_img = cv2.normalize(
            diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        result_planes.append(diff_img)
        result_norm_planes.append(norm_img)

    result_norm = cv2.merge(result_norm_planes)
    return result_norm


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
        frame = cv2.resize(
            frame, (frame.shape[1] // resize_scale, frame.shape[0] // resize_scale))
        # frame = cv2.undistort(rawframe, config.mtx, config.dist, None)

        if state == 0:
            result = getWarpMatrix(frame, markersImage)
            if result is not None:
                warpMatrix = result
                cv2.imshow('Original', frame)

                frame = cv2.warpPerspective(
                    frame, warpMatrix, (640, 480))
                cv2.imshow('Warped', frame)
                state = 1

        elif state == 1:
            frame = preprocess(frame)
            cv2.imshow('Raw', frame)

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
