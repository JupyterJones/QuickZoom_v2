#!/mnt/HDD500/QuickZoom/env/bin/python
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, make_response, redirect, url_for
import os
import cv2
import numpy as np
import uuid
from PIL import Image
from moviepy.editor import (
    VideoFileClip, ImageClip, ColorClip, CompositeVideoClip,
    AudioFileClip, ImageSequenceClip
)
from moviepy.editor import ImageSequenceClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import glob
import random
import shutil
import base64   
import io
import numpy as np
import subprocess
import json
import datetime
from icecream import ic
import re
import gc
import sys
import psutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Set custom GC thresholds
#gc.set_threshold(500, 8, 8)


UPLOAD_FOLDER = 'static/upload/'
VIDEO_FOLDER = 'static/videos/'
TEXT_FILES_DIR = 'static/TEXT/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs('static/vids', exist_ok=True)
def add_title_image(video_path, hex_color = "#A52A2A"):
    hex_color=random.choice(["#A52A2A","#ad1f1f","#16765c","#7a4111","#9b1050","#8e215d","#2656ca"])
    # Define the directory path
    directory_path = "temp"
    # Check if the directory exists
    if not os.path.exists(directory_path):
        # If not, create it
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")
    else:
        print(f"Directory '{directory_path}' already exists.") 
    # Load the video file and title image
    video_clip = VideoFileClip(video_path)
    print(video_clip.size)
    # how do i get the width and height of the video
    width, height = video_clip.size
    get_duration = video_clip.duration
    print(get_duration, width, height)
    title_image_path = "static/assets/port-hole.png"
    # Set the desired size of the padded video (e.g., video width + padding, video height + padding)
    padded_size = (width + 50, height + 50)

    # Calculate the position for centering the video within the larger frame
    x_position = (padded_size[0] - video_clip.size[0]) / 2
    y_position = (padded_size[1] - video_clip.size[1]) / 2
    #hex_color = "#09723c"
    # Remove the '#' and split the hex code into R, G, and B components
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    # Create an RGB tuple
    rgb_tuple = (r, g, b)

    # Create a blue ColorClip as the background
    blue_background = ColorClip(padded_size, color=rgb_tuple)

    # Add the video clip on top of the red background
    padded_video_clip = CompositeVideoClip([blue_background, video_clip.set_position((x_position, y_position))])
    padded_video_clip = padded_video_clip.set_duration(video_clip.duration)
    #title_image_path = "/home/jack/Desktop/EXPER/static/assets/Title_Image02.png"
    # Load the title image
    title_image = ImageClip(title_image_path)

    # Set the duration of the title image
    title_duration = video_clip.duration
    title_image = title_image.set_duration(title_duration)

    print(video_clip.size)
    # Position the title image at the center and resize it to fit the video dimensions
    #title_image = title_image.set_position(("left", "top"))
    title_image = title_image.set_position((0, -5))
    #video_clip.size = (620,620)
    title_image = title_image.resize(padded_video_clip.size)

    # Position the title image at the center and resize it to fit the video dimensions
    #title_image = title_image.set_position(("center", "center")).resize(video_clip.size)

    # Create a composite video clip with the title image overlay
    composite_clip = CompositeVideoClip([padded_video_clip, title_image])
    # Limit the length to video duration
    composite_clip = composite_clip.set_duration(video_clip.duration)
    # Load a random background music
    mp3_files = glob.glob("static/music/*.mp3")
    random.shuffle(mp3_files)

    # Now choose a random MP3 file from the shuffled list
    mp_music = random.choice(mp3_files)
    get_duration = AudioFileClip(mp_music).duration
    # Load the background music without setting duration
    music_clip = AudioFileClip(mp_music)
    # Fade in and out the background music
    #music duration is same as video
    music_clip = music_clip.set_duration(video_clip.duration)
    # Fade in and out the background music
    fade_duration = 1.0
    music_clip = music_clip.audio_fadein(fade_duration).audio_fadeout(fade_duration)
    # Set the audio of the composite clip to the background music
    composite_clip = composite_clip.set_audio(music_clip)
    uid = uuid.uuid4().hex
    output_path = f'static/videos/final_output3{uid}.mp4'
    # Export the final video with the background music
    composite_clip.write_videofile(output_path)
    mp4_file =  f"static/vids/Ready_Post_{uid}.mp4"
    shutil.copyfile(output_path, mp4_file) 
    temp_vid="static/videos/temp.mp4"
    shutil.copyfile(output_path, temp_vid)    
    print(mp4_file)
    VIDEO = output_path
    return VIDEO


# Route to serve uploaded images
@app.route('/')
def index():
    return render_template('index.html')

# Route to work with text
@app.route('/index2')
def index2():
    return render_template('index2.html')    

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    file = request.files['image']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    return jsonify({'filepath': filepath})

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    image_path = data['image_path']
    points = data['points']
    zoom_level = float(data['zoom'])  # Convert zoom_level to float
    
    output_video = os.path.join(VIDEO_FOLDER, 'zoom_animation.mp4')
    create_zoom_video(image_path, points, zoom_level, output_video)
    return jsonify({'video_path': output_video})

# Function to create zoom effect on a single point



def generate_frames(image_path, points, zoom_level, num_frames):
    """
    Generator function to yield frames one at a time.
    This avoids storing all frames in memory at once.
    """
    img = cv2.imread(image_path)
    h, w, _ = img.shape
    point = points[0]
    cx, cy = int(point[0] * w), int(point[1] * h)

    # Define the sharpening kernel
    sharpening_kernel = np.array([[0, -1, 0],
                                  [-1, 5, -1],
                                  [0, -1, 0]])

    for i in range(num_frames):
        alpha = (i / num_frames) ** 2  # Slow zoom at start, faster at end
        zoom_factor = 1 + alpha * zoom_level

        # Define the cropping region
        x1 = max(cx - int(w / (2 * zoom_factor)), 0)
        y1 = max(cy - int(h / (2 * zoom_factor)), 0)
        x2 = min(cx + int(w / (2 * zoom_factor)), w)
        y2 = min(cy + int(h / (2 * zoom_factor)), h)

        cropped = img[y1:y2, x1:x2]
        resized = cv2.resize(cropped, (w, h))

        # Apply sharpening to every 5th frame
        if i % 5 == 0:
            resized = cv2.filter2D(resized, -1, sharpening_kernel)

        # Yield the frame
        yield resized

        # Clean up intermediate variables
        del cropped, resized

        # Trigger garbage collection periodically
        if i % 50 == 0:
            gc.collect()

@app.route('/create_zoom_video', methods=['POST'])
def create_zoom_video_route():
    """
    Flask route to handle video creation requests.
    """
    try:
        # Parse input data
        data = request.json
        image_path = data.get('image_path')
        points = data.get('points')  # List of points (e.g., [[0.5, 0.5]])
        zoom_level = data.get('zoom_level', 2.0)  # Default zoom level
        output_video = data.get('output_video', 'output.mp4')

        # Validate inputs
        if not image_path or not points:
            return jsonify({"error": "Missing required parameters"}), 400

        # Number of frames for the video
        num_frames = 500

        # Generate frames using the generator
        frames_generator = generate_frames(image_path, points, zoom_level, num_frames)

        # Create video from frames
        process = psutil.Process()  # For memory profiling
        video = ImageSequenceClip(
            [cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames_generator], fps=30
        )
        video.write_videofile(output_video, codec='libx264')

        # Log memory usage after video creation
        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        print(f"Memory usage after video creation: {memory_usage:.2f} MB")

        # Final garbage collection
        gc.collect()

        return jsonify({"message": "Video created successfully", "output_video": output_video}), 200

    except Exception as e:
        # Handle errors gracefully
        return jsonify({"error": str(e)}), 500
def create_zoom_video(image_path, points, zoom_level, output_video):
    img = cv2.imread(image_path)
    h, w, _ = img.shape
    frames = []
    num_frames = 500
    
    # Only using the first point
    point = points[0]
    cx, cy = int(point[0] * w), int(point[1] * h)
    
    # Define the sharpening kernel
    sharpening_kernel = np.array([[0, -1, 0],
                                  [-1, 5,-1],
                                  [0, -1, 0]])

    for i in range(num_frames):
        #alpha = i / num_frames
        alpha = (i / num_frames) ** 2  # This makes the zoom slower at the start and faster at the end

        zoom_factor = 1 + alpha * zoom_level
        
        # Define the cropping region
        x1 = max(cx - int(w / (2 * zoom_factor)), 0)
        y1 = max(cy - int(h / (2 * zoom_factor)), 0)
        x2 = min(cx + int(w / (2 * zoom_factor)), w)
        y2 = min(cy + int(h / (2 * zoom_factor)), h)
        cropped = img[y1:y2, x1:x2]
        resized = cv2.resize(cropped, (w, h))
        
        # Apply sharpening to every 5th frame
        if i % 5 == 0:  # Sharpen every 5th frame (adjust as needed)
            resized = cv2.filter2D(resized, -1, sharpening_kernel)
        
        frames.append(resized)
    
    # Save as video
    video = ImageSequenceClip([cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames], fps=30)
    video.write_videofile(output_video, codec='libx264')
    add_title_image(video_path=output_video)


@app.route('/video/<filename>')
def video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)
#-------------------------

# Path to the uploads and output folders
UPLOAD_FOLDER = 'static/uploads/'
OUTPUT_FOLDER = 'static/uploads/'

@app.route('/video_edit')
def video_edit():
    return render_template('video_edit.html')

@app.route('/trim-video', methods=['POST'])
def trim_video():
    start_time = float(request.form['startTime'])
    end_time = float(request.form['endTime'])
    input_video = 'static/use.mp4'
    output_video = 'static/bash_vids/trimmed_video.mp4'

    try:
        # Log the trimming process
        ic(f"Trimming video from {start_time} to {end_time}")
         
        # Use MoviePy to trim the video
        ffmpeg_extract_subclip(input_video, start_time, end_time, targetname=output_video)
        return redirect(url_for('video_edit'))

    except Exception as e:
        print(f"Error trimming video: {str(e)}")
        return f"Error: {str(e)}", 500
@app.route('/reverse_video', methods=['POST', 'GET'])
def reverse_video():
    try:
        # Define paths
        input_video = 'static/video_resources/forward.mp4'
        temp_dir = 'static/temp/'
        final_output_dir = 'static/video_history/'
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(final_output_dir, exist_ok=True)

        # Step 1: Slow down the input video
        slow_video = os.path.join(temp_dir, 'slow_video.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', input_video,
            '-filter:v', 'scale=512x768,setpts=2.0*PTS',
            '-an', '-y', slow_video
        ], check=True)

        # Step 2: Reverse the slowed video
        reverse_slow_video = os.path.join(temp_dir, 'reverse_slow_video.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', slow_video,
            '-vf', 'reverse', '-af', 'areverse',
            '-y', reverse_slow_video
        ], check=True)

        # Step 3: Concatenate slow and reverse videos
        joined = os.path.join(temp_dir, 'joined.mp4')
        with open(os.path.join(temp_dir, 'file_list1.txt'), 'w') as f:
            f.write(f"file '{slow_video[12:]}'\nfile '{reverse_slow_video[12:]}'\n")
        subprocess.run([
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', os.path.join(temp_dir, 'file_list1.txt'),
            '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
            '-y', joined
        ], check=True)

        # Step 4: Reverse the concatenated video
        joined_reverse = os.path.join(temp_dir, 'joined_reverse.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', joined,
            '-vf', 'reverse', '-af', 'areverse',
            '-y', joined_reverse
        ], check=True)

        # Step 5: Concatenate joined and reversed joined videos
        final = os.path.join(temp_dir, 'final.mp4')
        with open(os.path.join(temp_dir, 'file_list2.txt'), 'w') as f:
            f.write(f"file '{joined[12:]}'\nfile '{joined_reverse[12:]}'\n")
        subprocess.run([
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', os.path.join(temp_dir, 'file_list2.txt'),
            '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
            '-y', final
        ], check=True)

        # Step 6: Add a border overlay
        border_image = 'static/assets/512x768.png'
        final_with_border = os.path.join(temp_dir, 'final_with_border.mp4')
        if os.path.exists(border_image):
            subprocess.run([
                'ffmpeg', '-hide_banner', '-i', final, '-i', border_image,
                '-filter_complex', "[1:v]scale=iw:ih[border];[0:v][border]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2:format=auto",
                '-c:a', 'copy', '-y', final_with_border
            ], check=True)
        else:
            raise FileNotFoundError(f"Border file '{border_image}' not found!")

        # Step 7: Add background music to the video with no sound
        music_files = [os.path.join('static/music/', f) for f in os.listdir('static/music/') if f.endswith('.mp3')]
        if not music_files:
            raise FileNotFoundError("No background music files found in the specified directory!")
        music_file = random.choice(music_files)
        final_temp = os.path.join(temp_dir, 'FINAL_TEMP.mp4')

        # Add background music to the video (no existing audio in the video)
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', final_with_border, '-i', music_file,
            '-filter_complex', "[1:a]volume=0.5[a1]",  # Adjust volume of the music
            '-map', '0:v', '-map', '[a1]', '-shortest', '-c:v', 'copy', '-y', final_temp
        ], check=True)


        # Step 8: Save the final video with timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        final_filename = os.path.join(final_output_dir, f'{timestamp}_FINAL.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', final_temp,
            '-g', '48', '-keyint_min', '48', '-movflags', '+faststart',
            '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-preset', 'fast',
            '-crf', '23', '-c:a', 'aac', '-b:a', '128k', '-y', final_filename
        ], check=True)

        # Cleanup intermediate files
        intermediate_files = [slow_video, reverse_slow_video, joined, joined_reverse, final, final_with_border, final_temp]
        for file in intermediate_files:
            if os.path.exists(file):
                os.remove(file)
        src =final_filename
        dest ='static/use.mp4'
        shutil.copy(src, dest)
        return redirect(url_for('video_edit'))

    except Exception as e:
        return f"An error occurred: {str(e)}"


@app.route('/reverse_videom', methods=['POST', 'GET'])
def reverse_videom():
    try:
        # Define paths
        input_video = 'static/video_resources/forward.mp4'
        temp_dir = 'static/temp/'
        final_output_dir = 'static/video_history/'
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(final_output_dir, exist_ok=True)

        # Step 1: Slow down the input video
        slow_video = os.path.join(temp_dir, 'slow_video.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', input_video,
            '-filter:v', 'scale=512x820,setpts=2.0*PTS',
            '-an', '-y', slow_video
        ], check=True)

        # Step 2: Reverse the slowed video
        reverse_slow_video = os.path.join(temp_dir, 'reverse_slow_video.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', slow_video,
            '-vf', 'reverse', '-af', 'areverse',
            '-y', reverse_slow_video
        ], check=True)

        # Step 3: Concatenate slow and reverse videos
        joined = os.path.join(temp_dir, 'joined.mp4')
        with open(os.path.join(temp_dir, 'file_list1.txt'), 'w') as f:
            f.write(f"file '{slow_video[12:]}'\nfile '{reverse_slow_video[12:]}'\n")
        subprocess.run([
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', os.path.join(temp_dir, 'file_list1.txt'),
            '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
            '-y', joined
        ], check=True)

        # Step 4: Reverse the concatenated video
        joined_reverse = os.path.join(temp_dir, 'joined_reverse.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', joined,
            '-vf', 'reverse', '-af', 'areverse',
            '-y', joined_reverse
        ], check=True)

        # Step 5: Concatenate joined and reversed joined videos
        final = os.path.join(temp_dir, 'final.mp4')
        with open(os.path.join(temp_dir, 'file_list2.txt'), 'w') as f:
            f.write(f"file '{joined[12:]}'\nfile '{joined_reverse[12:]}'\n")
        subprocess.run([
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', os.path.join(temp_dir, 'file_list2.txt'),
            '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
            '-y', final
        ], check=True)

        # Step 6: Add a border overlay
        border_image = 'static/assets/512x820.png'
        final_with_border = os.path.join(temp_dir, 'final_with_border.mp4')
        if os.path.exists(border_image):
            subprocess.run([
                'ffmpeg', '-hide_banner', '-i', final, '-i', border_image,
                '-filter_complex', "[1:v]scale=iw:ih[border];[0:v][border]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2:format=auto",
                '-c:a', 'copy', '-y', final_with_border
            ], check=True)
        else:
            raise FileNotFoundError(f"Border file '{border_image}' not found!")

        # Step 7: Add background music to the video with no sound
        music_files = [os.path.join('static/music/', f) for f in os.listdir('static/music/') if f.endswith('.mp3')]
        if not music_files:
            raise FileNotFoundError("No background music files found in the specified directory!")
        music_file = random.choice(music_files)
        final_temp = os.path.join(temp_dir, 'FINAL_TEMP.mp4')

        # Add background music to the video (no existing audio in the video)
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', final_with_border, '-i', music_file,
            '-filter_complex', "[1:a]volume=0.7[a1]",  # Adjust volume of the music
            '-map', '0:v', '-map', '[a1]', '-shortest', '-c:v', 'copy', '-y', final_temp
        ], check=True)


        # Step 8: Save the final video with timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        final_filename = os.path.join(final_output_dir, f'{timestamp}_FINAL.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', final_temp,
            '-g', '48', '-keyint_min', '48', '-movflags', '+faststart',
            '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-preset', 'fast',
            '-crf', '23', '-c:a', 'aac', '-b:a', '128k', '-y', final_filename
        ], check=True)

        # Cleanup intermediate files
        intermediate_files = [slow_video, reverse_slow_video, joined, joined_reverse, final, final_with_border, final_temp]
        for file in intermediate_files:
            if os.path.exists(file):
                os.remove(file)
        src =final_filename
        dest ='static/use.mp4'
        shutil.copy(src, dest)
        return redirect(url_for('video_edit'))

    except Exception as e:
        return f"An error occurred: {str(e)}"



@app.route('/reverse_videos', methods=['POST', 'GET'])
def reverse_videos():
    try:
        # Define paths
        input_video = 'static/video_resources/forward.mp4'
        temp_dir = 'static/temp/'
        final_output_dir = 'static/video_history/'
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(final_output_dir, exist_ok=True)

        # Step 1: Slow down the input video
        slow_video = os.path.join(temp_dir, 'slow_video.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', input_video,
            '-filter:v', 'scale=512x700,setpts=2.0*PTS',
            '-an', '-y', slow_video
        ], check=True)

        # Step 2: Reverse the slowed video
        reverse_slow_video = os.path.join(temp_dir, 'reverse_slow_video.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', slow_video,
            '-vf', 'reverse', '-af', 'areverse',
            '-y', reverse_slow_video
        ], check=True)

        # Step 3: Concatenate slow and reverse videos
        joined = os.path.join(temp_dir, 'joined.mp4')
        with open(os.path.join(temp_dir, 'file_list1.txt'), 'w') as f:
            f.write(f"file '{slow_video}'\nfile '{reverse_slow_video}'\n")
        subprocess.run([
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', os.path.join(temp_dir, 'file_list1.txt'),
            '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
            '-y', joined
        ], check=True)

        # Step 4: Reverse the concatenated video
        joined_reverse = os.path.join(temp_dir, 'joined_reverse.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', joined,
            '-vf', 'reverse', '-af', 'areverse',
            '-y', joined_reverse
        ], check=True)

        # Step 5: Concatenate joined and reversed joined videos
        final = os.path.join(temp_dir, 'final.mp4')
        with open(os.path.join(temp_dir, 'file_list2.txt'), 'w') as f:
            f.write(f"file '{joined}'\nfile '{joined_reverse}'\n")
        subprocess.run([
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', os.path.join(temp_dir, 'file_list2.txt'),
            '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
            '-y', final
        ], check=True)

        # Step 6: Add a border overlay
        border_image = 'static/assets/512x700.png'
        final_with_border = os.path.join(temp_dir, 'final_with_border.mp4')
        if os.path.exists(border_image):
            subprocess.run([
                'ffmpeg', '-hide_banner', '-i', final, '-i', border_image,
                '-filter_complex', "[1:v]scale=iw:ih[border];[0:v][border]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2:format=auto",
                '-c:a', 'copy', '-y', final_with_border
            ], check=True)
        else:
            raise FileNotFoundError(f"Border file '{border_image}' not found!")

        # Step 7: Add background music to the video with no sound
        music_files = [os.path.join('static/music/', f) for f in os.listdir('static/music/') if f.endswith('.mp3')]
        if not music_files:
            raise FileNotFoundError("No background music files found in the specified directory!")
        music_file = random.choice(music_files)
        final_temp = os.path.join(temp_dir, 'FINAL_TEMP.mp4')

        # Add background music to the video (no existing audio in the video)
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', final_with_border, '-i', music_file,
            '-filter_complex', "[1:a]volume=0.7[a1]",  # Adjust volume of the music
            '-map', '0:v', '-map', '[a1]', '-shortest', '-c:v', 'copy', '-y', final_temp
        ], check=True)


        # Step 8: Save the final video with timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        final_filename = os.path.join(final_output_dir, f'{timestamp}_FINAL.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', final_temp,
            '-g', '48', '-keyint_min', '48', '-movflags', '+faststart',
            '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-preset', 'fast',
            '-crf', '23', '-c:a', 'aac', '-b:a', '128k', '-y', final_filename
        ], check=True)

        # Cleanup intermediate files
        intermediate_files = [slow_video, reverse_slow_video, joined, joined_reverse, final, final_with_border, final_temp]
        for file in intermediate_files:
            if os.path.exists(file):
                os.remove(file)
        src =final_filename
        dest ='static/use.mp4'
        shutil.copy(src, dest)
        return redirect(url_for('video_edit'))

    except Exception as e:
        return f"An error occurred: {str(e)}"


@app.route('/upload_mp4_video')
def upload_mp4_video():
    return render_template('upload_mp4.html')
@app.route('/upload_mp4', methods=['POST'])
def upload_mp4():
    uploaded_file = request.files['videoFile']
    if uploaded_file.filename != '':
        # Save the uploaded file to a directory or process it as needed
        # For example, you can save it to a specific directory:
        uploaded_file.save('static/video_resources/forward.mp4')
        #                   /' + uploaded_file.filename)
        VIDEO='static/video_resources/forward.mp4'
        #use a uuid and copy 'to static/video_history'
        shutil.copy('static/video_resources/forward.mp4', 'static/video_history/' + str(uuid.uuid4()) + '.mp4')
        return render_template('upload_mp4.html',VIDEO=VIDEO)
    else:
        VIDEO='static/video_resources/forward.mp4'
        return render_template('upload_mp4.html',VIDEO=VIDEO)
@app.route('/get_videos', methods=['GET', 'POST'])
def get_videos():
    video_files = glob.glob("static/video_history/*.mp4")
    video_files = sorted(video_files, key=os.path.getmtime, reverse=True)
    return render_template("get_videos.html", video_files=video_files)

@app.route('/delete_videos', methods=['POST'])
def delete_videos():
    videos_to_delete = request.form.getlist('videos_to_delete')  # Get selected videos

    if not videos_to_delete:
        flash("No videos selected for deletion.", "warning")
        return redirect(url_for('get_videos'))

    for video_path in videos_to_delete:
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"Deleted: {video_path}")  # Debugging log
            else:
                print(f"File not found: {video_path}")
        except Exception as e:
            print(f"Error deleting {video_path}: {str(e)}")

    flash(f"Deleted {len(videos_to_delete)} video(s).", "success")
    return redirect(url_for('get_videos'))   
#---------------------------------------

# sanitize filename
def sanitize_filename(filename):
    """Removes special characters from a filename, keeping only alphanumeric characters, underscores, and extensions."""
    filename = filename.strip().replace(" ", "_")  # Replace spaces with underscores
    filename = re.sub(r"[^\w\-.]", "", filename)  # Keep only letters, numbers, underscore, dot, and hyphen
    return filename
#create a text file
@app.route('/create_text_file', methods=['GET', 'POST'])
def create_text_file():
    if request.method == 'POST':
        print("Received request to create a text file.")
        # Get the text content from the textarea
        text_content = request.form.get('textarea_content')
        print(f"Text content for file: {text_content}")

        #use first 20 letters of text content
        text_file_name = text_content[:20]
        filename = text_file_name
        file_name=sanitize_filename(filename)+'.txt'
        # Create the file path
        text_file_path = os.path.join('static/TEXT', file_name)

        # Write the text content to the file
        with open(text_file_path, 'w') as file:
            file.write(text_content)
        print(f"Text file created at {text_file_path}")

        return render_template('text_file_created.html', text_file_path=text_file_path, text_content=text_content)

    return render_template('create_text_file.html')



def save_text_to_file(filename, text):
    try:
        with open(os.path.join(TEXT_FILES_DIR, filename), "w") as file:
            file.write(text)
    except Exception as e:
        print(f"An error occurred while saving file '{filename}': {e}")

UPLOAD_FOLDER = 'static/TEXT'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/read_text_file/<filename>')
def read_text_file(filename):
    # Ensure the filename is safe
    safe_filename = os.path.basename(filename)  # Prevent directory traversal
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return render_template("TEXT.html", text=text, filename=safe_filename)
    else:
        return "File not found", 404

# list and read a directory of text files in static/TEXT
@app.route('/list_text_files')
def list_text_files():
    text_files = os.listdir(TEXT_FILES_DIR)
    return render_template('list_text_files.html', text_files=text_files)
# Define path for videos and temp export

#---------------------------------------

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

@app.route("/zoom_effect", methods=["GET", "POST"])
def zoom_effect():
    video_path = None
    if request.method == "POST":
        # Ensure both images are provided
        if "image1" not in request.files or "image2" not in request.files:
            return "Both image1 and image2 must be provided", 400
        
        # Save uploaded images
        image1 = request.files["image1"]
        image2 = request.files["image2"]
        image1_path = os.path.join(UPLOAD_FOLDER, secure_filename(image1.filename))
        image2_path = os.path.join(UPLOAD_FOLDER, secure_filename(image2.filename))
        image1.save(image1_path)
        image2.save(image2_path)

        # Get parameters from the form
        transition_style = request.form.get("transition_style")
        duration = int(request.form.get("duration", 5))
        fps = int(request.form.get("fps", 30))

        # Generate the video
        output_path = os.path.join(OUTPUT_FOLDER, "output.mp4")
        if transition_style == "infinite_zoom":
            generate_infinite_zoom(image1_path, image2_path, output_path, duration=duration, fps=fps)
        elif transition_style == "pixel_sorting":
            generate_pixel_sorting(image1_path, image2_path, output_path, duration=duration, fps=fps)

        # Add a title frame to the video
        
        titled_video_path=add_title_image(video_path=output_path, hex_color="#A52A2A")
        #titled_video_path = os.path.join(OUTPUT_FOLDER, "titled_output.mp4")
        # Save copies of the last two generations
        shutil.copy(output_path, os.path.join(OUTPUT_FOLDER, "last_generation_no_title.mp4"))
        shutil.copy(titled_video_path, os.path.join(OUTPUT_FOLDER, "last_generation_with_title.mp4"))

    # Render the template with the video paths
    return render_template(
        "zoom_effect.html",
        video=video_path,
        last_no_title=os.path.join(OUTPUT_FOLDER, "last_generation_no_title.mp4"),
        last_with_title=os.path.join(OUTPUT_FOLDER, "last_generation_with_title.mp4")
    )
# Route to download the generated video
@app.route("/download/<filename>", methods=["GET"])
def download_video(filename):
    video_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(video_path):
        return "File not found", 404
    return send_file(video_path, as_attachment=True)
@app.route('/speed_up', methods=['POST', 'GET'])
def speed_up():
    try:
        # Define paths
        input_video = 'static/video_resources/forward.mp4'
        temp_dir = 'static/temp/'
        final_output_dir = 'static/video_history/'
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(final_output_dir, exist_ok=True)

        # Step 1: Slow down the input video
        speed_video = os.path.join(temp_dir, 'speed_video.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', input_video,
            '-filter:v', 'scale=512x820,setpts=.5*PTS',
            '-an', '-y', speed_video
        ], check=True)
        # Step 6: Add a border overlay
        border_image = 'static/assets/512x820.png'
        final_with_border = os.path.join(temp_dir, 'speed_with_border.mp4')
        if os.path.exists(border_image):
            subprocess.run([
                'ffmpeg', '-hide_banner', '-i', speed_video, '-i', border_image,
                '-filter_complex', "[1:v]scale=iw:ih[border];[0:v][border]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2:format=auto",
                '-c:a', 'copy', '-y', final_with_border
            ], check=True)
        else:
            raise FileNotFoundError(f"Border file '{border_image}' not found!")

        # Step 7: Add background music to the video with no sound
        music_files = [os.path.join('static/music/', f) for f in os.listdir('static/music/') if f.endswith('.mp3')]
        if not music_files:
            raise FileNotFoundError("No background music files found in the specified directory!")
        music_file = random.choice(music_files)
        final_temp = os.path.join(temp_dir, 'speed_TEMP.mp4')

        # Add background music to the video (no existing audio in the video)
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', final_with_border, '-i', music_file,
            '-filter_complex', "[1:a]volume=0.7[a1]",  # Adjust volume of the music
            '-map', '0:v', '-map', '[a1]', '-shortest', '-c:v', 'copy', '-y', final_temp
        ], check=True)


        # Step 8: Save the final video with timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        final_filename = os.path.join(final_output_dir, f'{timestamp}_FINAL.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i', final_temp,
            '-g', '48', '-keyint_min', '48', '-movflags', '+faststart',
            '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-preset', 'fast',
            '-crf', '23', '-c:a', 'aac', '-b:a', '128k', '-y', final_filename
        ], check=True)

        '''
        # Cleanup intermediate files
        intermediate_files = [speed_video, final_filename, joined, joined_reverse, final, final_with_border, final_temp]
        for file in intermediate_files:
            if os.path.exists(file):
                os.remove(file)
        '''
        src =final_filename
        dest ='static/use.mp4'
        shutil.copy(src, dest)
        return redirect(url_for('video_edit'))

    except Exception as e:
        return f"An error occurred: {str(e)}"

#--
TEXT_FILES_DIR = "static/TEXT" 
# Index route to display existing text files and create new ones
@app.route("/edit_text", methods=["GET", "POST"])
def edit_text():

    if request.method == "POST":
        filename = request.form["filename"]
        text = request.form["text"]
        save_text_to_file(filename, text)
        return redirect(url_for("edit_text"))
    else:
        # Path to the file containing list of file paths
        text_files = os.listdir(TEXT_FILES_DIR)
        text_directory='static/TEXT'
        files = sorted(text_files, key=lambda x: os.path.getmtime(os.path.join(text_directory, x)), reverse=True)
        #files=glob.glob('static/TEXT/*.txt')
        print(f'files 1: {files}')  
        # Call the function to list files by creation time
        #files = list_files_by_creation_time(files)
        print(f'files 2: {files}')
        return render_template("edit_text.html", files=files)
 # Route to edit a text file
@app.route("/edit/<filename>", methods=["GET", "POST"])
def edit(filename):
    if request.method == "POST":
        text = request.form["text"]
        save_text_to_file(filename, text)
        return redirect(url_for("index"))
    else:
        text = read_text_from_file(filename)
        return render_template("edit.html", filename=filename, text=text)
# Route to delete a text file
@app.route("/delete/<filename>")
def delete(filename):
    filepath = os.path.join(TEXT_FILES_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"File deleted: {filename}")
    return redirect(url_for("index"))

def read_text_from_file(filename):
    filepath = os.path.join(TEXT_FILES_DIR, filename)
    with open(filepath, "r") as file:
        text = file.read()
        print(f"Text read from file: {filename}")
        return text
def list_files_by_creation_time(file_paths):
    """
    List files by their creation time, oldest first.
    
    Args:
    file_paths (list): List of file paths.
    
    Returns:
    list: List of file paths sorted by creation time.
    """
    # Log the start of the function
    print('Listing files by creation time...')
    
    # Create a dictionary to store file paths and their creation times
    file_creation_times = {}
    
    # Iterate through each file path
    for file_path in file_paths:
        # Get the creation time of the file
        try:
            creation_time = os.path.getctime(file_path)
            # Store the file path and its creation time in the dictionary
            file_creation_times[file_path] = creation_time
        except FileNotFoundError:
            # Log a warning if the file is not found
            print(f'File not found: {file_path}')
    
    # Sort the dictionary by creation time
    sorted_files = sorted(file_creation_times.items(), key=lambda x: x[1],reverse=True)
    
    # Extract the file paths from the sorted list
    sorted_file_paths = [file_path for file_path, _ in sorted_files]
    
    # Log the end of the function
    print('File listing complete.')
    
    # Return the sorted file paths
    return sorted_file_paths     
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
