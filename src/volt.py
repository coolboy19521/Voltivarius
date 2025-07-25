import cv2
import numpy
import imutils

nothing = lambda x: 0

class ColorDetector:
    def Process(self, Frame, Color, Draw = (1, 1), Action = 1, Tresh = 500, X = (640, 0), Y = (480, 0)):
        Hsv = cv2.cvtColor(Frame, cv2.COLOR_BGR2HSV)
        Centers, Areas = [], []

        MaskColor = cv2.inRange(Hsv, Color[0], Color[1])

        Contours = cv2.findContours(MaskColor, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        Contours = imutils.grab_contours(Contours)

        Angle = []

        for Contour in Contours:
            Area = cv2.contourArea(Contour)
            if (Area > Tresh):
                cv2.drawContours(Frame, [Contour], -1, (0, 255, 0), 2)
                M = cv2.moments(Contour)
                Areas.append(Area)
                CenterX = int(M["m10"] / M["m00"])
                CenterY = int(M["m01"] / M["m00"])

                Centers.append((CenterX, CenterY))

                if (Draw):
                    cv2.circle(Frame, (CenterX, CenterY), 7, (0, 0, 0), -1)
                    cv2.line(Frame, (250, 250), (CenterX, CenterY), (0, 0, 0), 2)

                if (Action and CenterX < X[0] and CenterX > X[1] and CenterY < Y[0] and CenterY > Y[1]):
                    Angle = [90, 0]

        return Frame, Centers, Angle, Areas
    
class DataMaker:
    def PrepareWindow(self):
        cv2.namedWindow("Trackbars")

        cv2.createTrackbar("L - H", "Trackbars", 0, 179, nothing)
        cv2.createTrackbar("L - S", "Trackbars", 0, 255, nothing)
        cv2.createTrackbar("L - V", "Trackbars", 0, 255, nothing)
        cv2.createTrackbar("U - H", "Trackbars", 179, 179, nothing)
        cv2.createTrackbar("U - S", "Trackbars", 255, 255, nothing)
        cv2.createTrackbar("U - V", "Trackbars", 255, 255, nothing)

    def BruteForce(self, Frame):
        Frame = cv2.flip(Frame, 1)

        hsv = cv2.cvtColor(Frame, cv2.COLOR_BGR2HSV)

        l_h = cv2.getTrackbarPos("L - H", "Trackbars")
        l_s = cv2.getTrackbarPos("L - S", "Trackbars")
        l_v = cv2.getTrackbarPos("L - V", "Trackbars")
        u_h = cv2.getTrackbarPos("U - H", "Trackbars")
        u_s = cv2.getTrackbarPos("U - S", "Trackbars")
        u_v = cv2.getTrackbarPos("U - V", "Trackbars")

        lower_range = numpy.array([l_h, l_s, l_v])
        upper_range = numpy.array([u_h, u_s, u_v])

        mask = cv2.inRange(hsv, lower_range, upper_range)

        res = cv2.bitwise_and(Frame, Frame, mask=mask)

        mask_3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        stacked = numpy.hstack((mask_3, Frame, res))

        cv2.imshow('Trackbars', cv2.resize(stacked, None, fx=0.4, fy=0.4))

        return ((l_h, l_s, l_v), (u_h, u_s, u_v))