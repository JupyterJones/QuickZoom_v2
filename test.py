from flask import Flask, request, render_template, send_file
import os
import cv2
import numpy as np
from moviepy.editor import ImageSequenceClip

app = Flask(__name__)

# Temporary directory to store uploaded files
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to generate the infinite zoom effect
def generate_infinite_zoom(image1_path, image2_path, output_path, zoom_speed=0.05, duration=4, fps=30):
    img1 = cv2.imread(image1_path)
    img2 = cv2.imread(image2_path)
    h, w = img1.shape[:2]

    frames = []
    total_frames = int(duration * fps)

    # Zoom in phase
    for i in range(total_frames // 2):
        zoom_factor = 1 + zoom_speed * i
        frame = zoom_image(img1, zoom_factor)
        frames.append(frame)

    # Transition phase
    frames.append(zoom_image(img2, zoom_factor))  # Switch to second image

    # Zoom out phase
    for i in range(total_frames // 2, 0, -1):
        zoom_factor = 1 + zoom_speed * i
        frame = zoom_image(img2, zoom_factor)
        frames.append(frame)

    frames_rgb = [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) for frame in frames]
    clip = ImageSequenceClip(frames_rgb, fps=fps)
    clip.write_videofile(output_path, codec="libx264")

# Helper function to zoom into an image
def zoom_image(image, zoom_factor):
    h, w = image.shape[:2]
    new_h, new_w = int(h / zoom_factor), int(w / zoom_factor)
    top = (h - new_h) // 2
    left = (w - new_w) // 2
    cropped = image[top:top+new_h, left:left+new_w]
    resized = cv2.resize(cropped, (w, h))
    return resized

# Function to generate the pixel sorting transition
def generate_pixel_sorting(image1_path, image2_path, output_path, duration=5, fps=30):
    img1 = cv2.imread(image1_path)
    img2 = cv2.imread(image2_path)
    h, w = img1.shape[:2]

    frames = []
    total_frames = int(duration * fps)

    for i in range(total_frames):
        # Create a copy of the first image
        frame = img1.copy()

        # Sort pixels horizontally based on brightness
        progress = i / total_frames
        sorted_rows = int(h * progress)
        for row in range(sorted_rows):
            frame[row] = frame[row][frame[row][:, 0].argsort()]

        # Blend with the second image
        alpha = progress
        blended_frame = cv2.addWeighted(frame, 1 - alpha, img2, alpha, 0)
        frames.append(blended_frame)

    frames_rgb = [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) for frame in frames]
    clip = ImageSequenceClip(frames_rgb, fps=fps)
    clip.write_videofile(output_path, codec="libx264")

# Route to render the HTML form
@app.route("/", methods=["GET", "POST"])
def index():
    video_path = None
    if request.method == "POST":
        if "image1" not in request.files or "image2" not in request.files:
            return "Both image1 and image2 must be provided", 400

        image1 = request.files["image1"]
        image2 = request.files["image2"]

        # Save images to the upload folder
        image1_path = os.path.join(UPLOAD_FOLDER, image1.filename)
        image2_path = os.path.join(UPLOAD_FOLDER, image2.filename)
        image1.save(image1_path)
        image2.save(image2_path)

        # Get parameters from the form
        transition_style = request.form.get("transition_style")
        duration = int(request.form.get("duration", 5))
        fps = int(request.form.get("fps", 30))

        # Generate the video
        output_path = os.path.join(UPLOAD_FOLDER, "output.mp4")
        if transition_style == "infinite_zoom":
            generate_infinite_zoom(image1_path, image2_path, output_path, duration=duration, fps=fps)
        elif transition_style == "pixel_sorting":
            generate_pixel_sorting(image1_path, image2_path, output_path, duration=duration, fps=fps)

        # Pass the video path to the template
        video_path = output_path

    return render_template("zoom_effect.html", video=video_path)

# Route to download the generated video
@app.route("/download/<filename>", methods=["GET"])
def download_video(filename):
    video_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(video_path):
        return "File not found", 404
    return send_file(video_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5100)