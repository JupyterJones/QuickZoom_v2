import cv2
import numpy as np
from sys import argv
import subprocess



def blend_images(image1, image2):
    # Set video parameters
    frame_rate = 30  # Frames per second
    duration_image1 = 2  # seconds
    transition_duration = 4  # seconds
    duration_image2 = 3  # seconds
    total_duration = duration_image1 + transition_duration + duration_image2

    # Calculate number of frames for each section
    num_frames_image1 = frame_rate * duration_image1
    num_frames_transition = frame_rate * transition_duration
    num_frames_image2 = frame_rate * duration_image2

    # Get dimensions of images
    height, width, _ = image1.shape

    # Prepare video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('static/videos/spinn.mp4', fourcc, frame_rate, (width, height))

    # Write first image
    for _ in range(num_frames_image1):
        out.write(image1)

    # Transition effect
    for i in range(num_frames_transition):
        # Calculate the rotation angle
        angle = (i / num_frames_transition) * 360

        # Get the rotation matrix
        M = cv2.getRotationMatrix2D((width // 2, height // 2), angle, 1.0)
        rotated_image1 = cv2.warpAffine(image1, M, (width, height))
        
        # Blend the images
        alpha = i / num_frames_transition
        blended = cv2.addWeighted(rotated_image1, 1 - alpha, image2, alpha, 0)

        out.write(blended)

    # Write second image
    for _ in range(num_frames_image2):
        out.write(image2)

    # Release video writer
    out.release()
if __name__ == '__main__':    
    image1_path = argv[1]
    image2_path = argv[2]
    image1 = cv2.imread(image1_path)
    image2 = cv2.imread(image2_path)
    blend_images(image1, image2)
    subprocess.call(['vlc', 'static/videos/spinn.mp4'])   