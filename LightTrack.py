import numpy as np
import cv2, cv
from matplotlib import pyplot as plt
import matplotlib.image as mpimg
import scipy.ndimage as ndimage
import socket
import os.path as path

def nothing(x):
    pass

threshMin = 210
threshMax = 255
minSize = 400
cv2.namedWindow("Vision Window", cv2.WINDOW_NORMAL)

#con = np.zeros((240,300,3), np.uint8) usded to make a black blank image

fourcc = cv.CV_FOURCC('X', 'V', 'I', 'D')
recording = False

#robots ip address
UDP_IP = "10.12.43.2"
#UDP_IP = "127.0.0.1"
UDP_PORT = 1130
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

video ="http://10.12.43.11/mjpg/video.mjpg"
#video = 'Team 1986 Robot POV 2014 with Field View PIP.mp4'
#video = 'recording 4.avi'
image = 'image3.jpg'
ret = False

# create trackbars 
cv2.createTrackbar('B/W min','Vision Window',0,255,nothing)
cv2.createTrackbar('B/W max','Vision Window',0,255,nothing)
cv2.createTrackbar('Size','Vision Window',0,1000,nothing)


while not ret:
    cv2.imshow("Vision Window", con)
    
    cap = cv2.VideoCapture(video)
    
    ret = cap.isOpened()

    if ret:
        ret, img = cap.read()
    key = cv2.waitKey(20)
    
    if key == 27: # exit on ESC
        break

numObjects = 0
kernel = np.ones((7,7),np.uint8)

while(1):
    threshMin = cv2.getTrackbarPos('B/W min','Vision Window')
    threshMax = cv2.getTrackbarPos('B/W max','Vision Window')
    minSize = cv2.getTrackbarPos('Size','Vision Window')
    
    centerPoints = []
    if not cap.isOpened():
        break
    
    #we get the image from the camera
    ret, img = cap.read()
    ret, orgImg = cap.read()

    
    #img = cv2.imread(image)#un comment if you want to proccess just an image instead
    
    height, width, depth = img.shape
    #here we blur the image for easier proccessing, gets rid of noise from teh camera itself
    #img = cv2.medianBlur(img,7)
    
    #Color Thresholding code to find color
    #hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    #COLOR_MIN = np.array([20, 80, 80],np.uint8)
    #COLOR_MAX = np.array([40, 255, 255],np.uint8)
    #frame_threshed = cv2.inRange(hsv_img, COLOR_MIN, COLOR_MAX)
    
    #here we convert it to black and white since we only are looking for brightness it is easier
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    #here we set up the zones which a indivual pixle has to be in order to be shown or not
    
    
    #here make the image comlpetely black and white, no other colors exist using the set up variables above
    binary = cv2.threshold(gray, threshMin, threshMax, cv2.THRESH_BINARY)[1]
    
    #binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.dilate(binary,kernel,iterations = 1)
    #here we dectect the objects in the image and put them into an arry
    contours, hierarchy = cv2.findContours(binary,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    
    #outlining the contours
    #cv2.drawContours(gray,contours,-1,(0,255,0),3)  
    
    try:
        #this finds how many objects are in the picture
        numObjects = len(contours)
    except:
        numObjects = 0
       
    #initalize our filter array
    filteredContours = []
    
    #here we use a convexHull to even out the images then we remove any that are too small
    
    for i in range(0, numObjects):
        cnt = contours[i]
        hull = cv2.convexHull(cnt)
        if (cv2.arcLength(hull,True) > minSize):
            filteredContours.append(hull)
    
    #height filtering
    heightFilteredContours = []
    centCNT = []
    
    for i in range(0,len(filteredContours)):
        cnt = filteredContours[i]
        
        inside = False
        for i2 in range (0, height):
            if (cv2.pointPolygonTest(cnt, (width/2, i2 -1), False) > 0):
                inside = True
                
        if inside:
            centCNT.append(cnt)
            
        maxCnt = tuple(cnt[cnt[:,:,1].argmax()][0])
        y = maxCnt[1]
        if (y<(height)):
            heightFilteredContours.append(cnt)
        
    #leftmost = tuple(cnt[cnt[:,:,0].argmin()][0])
    #rightmost = tuple(cnt[cnt[:,:,0].argmax()][0])
    #topmost = tuple(cnt[cnt[:,:,1].argmin()][0])
    #bottommost = tuple(cnt[cnt[:,:,1].argmax()][0])
    
    #this finds the exact center of the object in the 0 place
    x = 0
    y = 0
    
    #here  we combine our filered image with the orgional image so we know what it sees.
    cv2.drawContours(img,centCNT,-1,(255,0,0),-1)
    cv2.drawContours(binary,contours,-1,(255,0,0),-1)
    #this just helps us by labeling and finding the center points of each contour
    
    heightFilteredContours = centCNT
    
    if (len(heightFilteredContours) != 0):
        if (len(heightFilteredContours) != 0):  
            for i in range(0,len(heightFilteredContours)): 
                M = cv2.moments(heightFilteredContours[i])
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
                centerPoints.append((i,x))
                centerPoints.append((i,y))
                center = (x,y)
                radius = 10
                cv2.circle(img,center,radius,(0,255,0),2)    
                cv2.putText(img, str(i+1), (x-5,y+5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (0,0,0), 4, cv2.CV_AA)
                cv2.putText(img, str(i+1), (x-5,y+5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (255,255,255), 1, cv2.CV_AA) 
    #ndimage.binary_fill_holes(binary, structure=np.ones((5,5))).astype(int)
    
    if recording:
        cv2.circle(img, (10,10), 10, (0,0,255), -1)
        cv2.putText(img, "rec...", (22,15), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.6, (255,255,255), 4, cv2.CV_AA) 
        cv2.putText(img, "rec...", (22,15), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.6, (0,0,0), 1, cv2.CV_AA) 
    
    cv2.line(img, (width/2, 0), (width/2, height),(0,0,255), 2)
    
    cv2.imshow("Vision Window", img)
    #cv2.imshow("binary", binary)
    
    goalHot = (len(centCNT) > 0)
    
    sock.sendto(str(goalHot), (UDP_IP, UDP_PORT))   
     
    key = cv2.waitKey(20)
    key2 = 0
    
    #end the video stream
    if key == 27: # exit on ESC
        break
    
    #tell you the x axis if the first object
    if key == ord('x'):
        print(x)
        
    #tell you the y axis if the first object
    if (key == ord('y')):
        print(y)
        
    if (key == ord('r')) or (recording == True):
        fname = path.realpath(__doc__) + "\\"
        
        if recording == False:
            newFileName = "recording.avi"
            exist  = path.isfile(fname + newFileName)
            
            i = 1
            while(exist):
                newFileName = "recording " + str(i) + ".avi"
                exist  = path.isfile(fname + newFileName)
                i += 1
                
            out = cv2.VideoWriter(newFileName, fourcc, 15.0, (width, height))
        out.write(orgImg)
        recording = True
    if (key == ord('q')):
        out.release()
        recording = False 
    #pause the video
    if (key == ord('p')):
        while True:
            key2 = cv2.waitKey(20)
            if key2 == ord('p'):
                break
            if key2 == 27: # exit on ESC
                break
            if key2 == ord('n'):
                try:
                    print(len(filteredContours))
                except:
                    print("no Contours")
                     #tell you the x axis if the first object
            if key2 == ord('x'):
                print(x)
            if key2 == ord('t'):
                print(centerPoints)
                
            #tell you the y axis if the first object
            if (key2 == ord('y')):
                print(y)
    if key2 == 27:
        break
    #show how many objects are on the screen currently
    if key == ord('n'):
        try:
            print(len(filteredContours))
        except:
            print("no Contours")
try:
    out.release()
except:
    pass
cap.release()
cv2.destroyAllWindows()


