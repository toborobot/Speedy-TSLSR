import cv2
import numpy as np
from . import utils

def __findCircles(mask):
    """
        Finds circles from mask and returns HoughCircles
    """
    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1, 100, param1=30, param2=50)
    return circles

def __filterRedColor(image_hsv):
    """
        Filters the red color from image_hsv and returns mask.
    """
    mask1 = cv2.inRange(image_hsv, np.array([0, 100, 65]), np.array([10, 255, 255]))
    mask2 = cv2.inRange(image_hsv, np.array([155, 100, 70]), np.array([179, 255, 255]))
    mask = mask1 + mask2
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2,2)))
    mask = cv2.Canny(mask, 50, 100)
    mask = cv2.GaussianBlur(mask, (13, 13), 0)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2,2)))
    return mask

def __extract_sign_roi(image, circle):
    """
        @circle => (x, y, r)
        Extracts roi from image and returns the roi
    """
    x, y, r = circle
    rn = int(r - (r/4.5))
    rect = [(x - rn), (y - rn), (x + rn), (y + rn)]
    return image[rect[1]:rect[3], rect[0]:rect[2]]

def __bound_contours(roi):
    """
        returns modified roi(non-destructive) and rectangles that founded by the algorithm.
        @roi region of interest to find contours
        @return (roi, rects)
    """

    roi_copy = roi.copy()
    roi_hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
    # filter black color
    mask1 = cv2.inRange(roi_hsv, np.array([0, 0, 0]), np.array([180, 255, 125]))
    mask1 = cv2.morphologyEx(mask1, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    mask1 = cv2.Canny(mask1, 100, 300)
    mask1 = cv2.GaussianBlur(mask1, (1, 1), 0)
    mask1 = cv2.Canny(mask1, 100, 300)

    # mask1 = cv2.morphologyEx(mask1, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))

    # Find contours for detected portion of the image
    im2, cnts, hierarchy = cv2.findContours(mask1.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5] # get largest five contour area
    rects = []
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        x, y, w, h = cv2.boundingRect(approx)
        if h >= 15:
            # if height is enough
            # create rectangle for bounding
            rect = (x, y, w, h)
            rects.append(rect)
            cv2.rectangle(roi_copy, (x, y), (x+w, y+h), (0, 255, 0), 1);

    return (roi_copy, rects)

def extractDigits(roi):
    mroi, rects = __bound_contours(roi)
    digits = []
    for (x, y, w, h) in utils.eliminate_child_rects(rects):
        digits.append(roi[y : y + h, x : x + w])

    return digits

def tslsr(image):
    """
        Takes an image then returns (mask, circles, rois for each circle)
    """
    image_hsv = cv2.cvtColor(cv2.GaussianBlur(image, (7, 7), 0), cv2.COLOR_BGR2HSV)
    mask = __filterRedColor(image_hsv)
    circles = __findCircles(mask)
    rois = []
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            rois.append(__extract_sign_roi(image, (x, y, r)))

    return (mask, circles, rois)
