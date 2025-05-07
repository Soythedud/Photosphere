import cv2 as cv
import numpy as np
import os
from datetime import datetime

# === Calibration Parameters ===
board_size = (9, 6)  # The number of inner corners (cols, rows) in the checkerboard
square_size = 1.0  # Size of each square in your checkerboard (in some unit like cm or inches)

# Prepare object points based on the real world coordinates of the checkerboard squares
objp = np.zeros((board_size[0] * board_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2)

objpoints = []  # 3D points in world space
imgpoints = []  # 2D points in image space

# === Create Output Directory ===
session_timestamp = datetime.now().strftime("session_%Y%m%d_%H%M%S")
output_dir = os.path.join("captured_images", session_timestamp)
os.makedirs(output_dir, exist_ok=True)

# === Open Webcam ===
cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot access the webcam.")
    exit()

# === Capture Loop ===
print("📸 Press 'c' to capture a checkerboard frame.")
print("💾 Press 'q' to calibrate and undistort.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    found, corners = cv.findChessboardCorners(gray, board_size, None)

    # Draw chessboard corners on the frame
    display = frame.copy()
    if found:
        cv.drawChessboardCorners(display, board_size, corners, found)
        cv.putText(display, "✅ Checkerboard detected", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        cv.putText(display, "❌ Checkerboard NOT detected", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Show the frame with detected corners
    cv.imshow("Checkerboard Detection", display)

    # Capture frame when 'c' is pressed
    key = cv.waitKey(1) & 0xFF
    if key == ord('c') and found:
        objpoints.append(objp.copy())  # Add 3D object points (real-world coordinates)
        imgpoints.append(corners)  # Add 2D image points (detected corners)
        print(f"📸 Captured frame {len(objpoints)}")

    # Calibrate when 'q' is pressed
    if key == ord('q'):
        if len(objpoints) < 5:
            print("❌ Not enough calibration images. Capture at least 5.")
        else:
            print("🔧 Performing calibration...")
            ret, K, D, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

            if ret:
                print("\n🎯 Calibration complete!")
                print("\n📌 Camera Matrix (K):\n", K)
                print("\n📌 Distortion Coefficients (D):\n", D.ravel())

                # Option to save calibration
                save = input("\n💾 Save calibration to 'camera_params.npz'? (y/n): ").strip().lower()
                if save == 'y':
                    np.savez("camera_params.npz", K=K, D=D)
                    print("✅ Saved calibration to 'camera_params.npz'")
            else:
                print("❌ Calibration failed.")
        
        break  # Exit the loop once calibration is complete

# === Cleanup ===
cap.release()
cv.destroyAllWindows()
