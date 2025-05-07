import cv2
import os
import shutil
import subprocess
from PIL import Image

# Setup directories
image_dir = "hugin_images"
output_dir = "hugin_output"
os.makedirs(image_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# Clean old images
for folder in [image_dir, output_dir]:
    for f in os.listdir(folder):
        file_path = os.path.join(folder, f)
        if os.path.isfile(file_path):
            os.remove(file_path)

# Initialize webcams
cam1 = cv2.VideoCapture(1)  # Webcam 1
cam2 = cv2.VideoCapture(2)  # Webcam 2

# Number of images to capture per camera
captures_cam1 = 3  # 3 images from Webcam 1
captures_cam2 = 3  # 3 images from Webcam 2
index = 0

# Define the compass angle steps for 0° to 180° (3 steps for each webcam)
angle_steps_cam1 = [0, 60, 120]  # For Webcam 1 (3 images)
angle_steps_cam2 = [0, 60, 120]  # For Webcam 2 (3 images)

# Display function with compass overlay
def show_feed(f1, f2, angle):
    combined = cv2.hconcat([f1, f2])
    cv2.putText(combined, f"Angle: {angle}°", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Camera Feeds", combined)

# Image viewer function
def show_360_viewer(image_path):
    try:
        img = Image.open(image_path)
        img.show()
    except Exception as e:
        print(f"Error opening 360 Viewer: {e}")

captured_images = []

while True:
    ret1, frame1 = cam1.read()
    ret2, frame2 = cam2.read()
    if not ret1 or not ret2:
        print("Error reading camera feeds.")
        break

    # Show the feed with compass overlay
    if index < len(angle_steps_cam1):  # Capture images for Webcam 1
        angle = angle_steps_cam1[index]
        show_feed(frame1, frame2, angle)
    elif index < len(angle_steps_cam1) + len(angle_steps_cam2):  # Capture images for Webcam 2
        angle = angle_steps_cam2[index - len(angle_steps_cam1)]
        show_feed(frame1, frame2, angle)
    else:
        show_feed(frame1, frame2, "Done")

    key = cv2.waitKey(1) & 0xFF

    # Capture the images
    if key == ord('c') and index < len(angle_steps_cam1) + len(angle_steps_cam2):
        if index < len(angle_steps_cam1):
            angle = angle_steps_cam1[index]
        else:
            angle = angle_steps_cam2[index - len(angle_steps_cam1)]

        s_path = os.path.join(image_dir, f"s{index+1}_{angle}.jpg")
        c_path = os.path.join(image_dir, f"c{index+1}_{angle}.jpg")
        cv2.imwrite(s_path, frame1)
        cv2.imwrite(c_path, frame2)
        print(f"Captured: {s_path}, {c_path}")
        captured_images.extend([s_path, c_path])
        index += 1

    # Press 'q' to exit and launch Hugin
    elif key == ord('q'):
        print("Exiting and launching Hugin...")
        break

    # Press 'x' to quit without stitching
    elif key == ord('x'):
        print("Early exit without stitching.")
        cam1.release()
        cam2.release()
        cv2.destroyAllWindows()
        exit()

cv2.destroyAllWindows()
cam1.release()
cam2.release()

# Launch Hugin GUI manually with the captured images
hugin_command = ["hugin"] + captured_images
try:
    subprocess.run(hugin_command)
except Exception as e:
    print("Failed to launch Hugin:", e)