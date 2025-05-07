import cv2
import numpy as np
import time
import os

# Wide FOV camera matrix (fisheye shape)
K_wide = np.array([
    [1596.34409, 0.0, 955.733346],
    [0.0, 1963.27331, 544.754985],
    [0.0, 0.0, 1.0]
])
D_wide = np.array([
    -0.854219699, -1.28299539, -0.0371297352, 0.00396044482, 5.67983356
])

# Fully undistorted calibration
K_narrow = np.array([
    [999.560015, 0.0, 959.698507],
    [0.0, 1121.38327, 547.053694],
    [0.0, 0.0, 1.0]
])
D_narrow = np.array([
    -0.557454645, -0.326774637, -0.0142731950, -0.00156834809, 1.87705883
])

alpha = 0.4  # Blending factor: 0 = undistorted, 1 = full fisheye

# Blend both sets of camera parameters
K = (1 - alpha) * K_narrow + alpha * K_wide
D = (1 - alpha) * D_narrow + alpha * D_wide

cap = cv2.VideoCapture(0)
balance = 0.5

# Global variables for remap (map1, map2)
map1, map2 = None, None

# List to store captured images for stitching
captured_images = []

# Flag to track if the process has started
started = False

# Function to capture a screenshot every 2 seconds
def capture_screenshot():
    global map1, map2
    ret, frame = cap.read()
    if ret:
        h, w = frame.shape[:2]
        if map1 is None or map1.shape[:2] != frame.shape[:2]:
            new_K, _ = cv2.getOptimalNewCameraMatrix(K, D, (w, h), balance, (w, h))
            map1, map2 = cv2.initUndistortRectifyMap(K, D, None, new_K, (w, h), cv2.CV_16SC2)

        undistorted = cv2.remap(frame, map1, map2, interpolation=cv2.INTER_LINEAR)
        captured_images.append(undistorted)
        print("Screenshot captured.")
    else:
        print("Failed to capture image.")

# Main loop
start_time = time.time()
while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    if map1 is None or map1.shape[:2] != frame.shape[:2]:
        new_K, _ = cv2.getOptimalNewCameraMatrix(K, D, (w, h), balance, (w, h))
        map1, map2 = cv2.initUndistortRectifyMap(K, D, None, new_K, (w, h), cv2.CV_16SC2)

    undistorted = cv2.remap(frame, map1, map2, interpolation=cv2.INTER_LINEAR)
    cv2.imshow("Undistorted Image", undistorted)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('s') and not started:
        print("Starting the image capture process...")
        started = True
        start_time = time.time()
    if key == ord('q'):
        print("Exiting...")
        break

    if started and time.time() - start_time >= 2:
        capture_screenshot()
        start_time = time.time()

cap.release()
cv2.destroyAllWindows()

# Stitch captured images
if len(captured_images) > 1:
    stitcher = cv2.Stitcher_create()
    status, panorama = stitcher.stitch(captured_images)

    if status == cv2.Stitcher_OK:
        cv2.imwrite("panorama.jpg", panorama)
        print("Panorama created and saved.")
    else:
        print("Stitching failed with error code", status)
else:
    print("Not enough images for stitching.")

# Convert panorama to 360-degree photosphere
if os.path.exists("panorama.jpg"):
    panorama = cv2.imread("panorama.jpg")
    h, w = panorama.shape[:2]
    fov = 360

    theta = np.linspace(0, 2 * np.pi, w)
    phi = np.linspace(0, np.pi, h)

    x = np.outer(np.sin(phi), np.sin(theta))
    y = np.outer(np.sin(phi), np.cos(theta))
    z = np.outer(np.cos(phi), np.ones_like(theta))

    spherical_projection = np.zeros_like(panorama)

    for i in range(h):
        for j in range(w):
            xi = np.clip(int((x[i, j] + 1) * (w / 2)), 0, w - 1)
            yi = np.clip(int((y[i, j] + 1) * (h / 2)), 0, h - 1)
            spherical_projection[i, j] = panorama[yi, xi]

    cv2.imwrite("360_photosphere.jpg", spherical_projection)
    print("360 Photosphere created and saved.")
else:
    print("Panorama file not found.")



