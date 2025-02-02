#spin.py
import cv2
import numpy as np
from moviepy.editor import ImageSequenceClip
from sys import argv

def create_spinning_frames(image1, image2, num_frames=60):
    frames = []
    height, width = image1.shape[:2]
    
    for i in range(num_frames):
        # Calculate the angle of rotation
        # For the first half of the frames, rotate progressively
        # For the second half, the rotation should be a reverse effect from the second image
        angle1 = (360 * (i / (num_frames - 1))) if i < (num_frames // 2) else 360
        angle2 = 360 - angle1  # This makes the second image rotate in reverse

        # Spin the first image
        matrix1 = cv2.getRotationMatrix2D((width / 2, height / 2), angle1, 1)
        spun_image1 = cv2.warpAffine(image1, matrix1, (width, height))

        # Spin the second image
        matrix2 = cv2.getRotationMatrix2D((width / 2, height / 2), angle2, 1)
        spun_image2 = cv2.warpAffine(image2, matrix2, (width, height))

        # Blend the images - at first more of image1 and at last more of image2
        alpha = 1 - (i / (num_frames - 1))
        blended_frame = cv2.addWeighted(spun_image1, alpha, spun_image2, 1 - alpha, 0)
        
        frames.append(blended_frame)

    return frames

def main(image_path1, image_path2, output_path):
    # Load the images
    image1 = cv2.imread(image_path1)
    image2 = cv2.imread(image_path2)

    # Ensure the images are the same size
    if image1.shape != image2.shape:
        image1 = cv2.resize(image1, (image2.shape[1], image2.shape[0]))

    # Create spinning frames
    frames = create_spinning_frames(image1, image2)

    # Write the frames into a video
    clip = ImageSequenceClip(frames, fps=24)
    clip.write_videofile(output_path, codec='libx264')

if __name__ == "__main__":
    image_path1 = argv[1]  # Path to the first image
    image_path2 = argv[2]  # Path to the second image
    output_path = 'static/videos/spinning_transition.mp4'  # Output path for the video

    main(image_path1, image_path2, output_path)