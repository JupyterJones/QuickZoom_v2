- Customizable music and frame for video output.

### Requirements:
- Python 3.9+
- Linux (other OS should work with minor adjustments)

### Installation Steps:

1. **Clone the repository**:
   ```bash
   git clone git@github.com:JupyterJones/QuickZoom_v2.git


QuickZoom_v2 is a small Flask application that allows you to quickly zoom into an image and save the zoom animation as an MP4. The app also enables you to add a customizable music background and a frame to the video. It has been tested on Linux systems.
Features:

    Upload an image and select zoom points.
    Apply a smooth zoom effect on the selected points.
    Save the zoom effect as an MP4 file.
    Add a customizable music track (MP3) and frame to the video.
    Customizable music and frame for video output.

Requirements:

    Python 3.9+
    Linux (other OS should work with minor adjustments)

Installation Steps:

    Clone the repository:

git clone git@github.com:JupyterJones/QuickZoom_v2.git

Navigate into the project folder:

cd QuickZoom_v2

Create a Python virtual environment:

python3 -m venv env

Activate the virtual environment: On Linux or macOS:

source env/bin/activate

On Windows:

env\Scripts\activate

Install the dependencies:

python -m pip install --no-cache-dir -r requirements.txt

Run the Flask application:

    python app.py

    The application will be available at http://127.0.0.1:5000.

How to Use:

    Upload an Image: Navigate to the homepage (/), and upload the image you wish to zoom in on.
    Select Zoom Points: Click three points on the image to specify where the zoom effect should focus.
    Adjust Zoom Level: Use the provided input to control the level of zoom.
    Generate Video: Once the points and zoom level are set, the app will generate a video of the zoom effect.
    Add Music and Frame: After the zoom video is generated, a background music (MP3) and customizable frame will be added to the video.
    Download Video: After processing, you can download the final video with the applied zoom, frame, and music.

Customization:

    Frame and Music: The frame and background music (MP3) are customizable. You can place your music files in the static/music/ folder and frame images in the static/assets/ folder.
    Zoom Animation: The zoom effect can be adjusted by modifying the zoom algorithm in the code.

Troubleshooting:

    Ensure that all dependencies are installed correctly using the requirements.txt.
    Make sure your virtual environment is active (source env/bin/activate).
    If you encounter issues with libraries like OpenCV or MoviePy, consider updating or reinstalling them.

Contributing:

Feel free to open issues or submit pull requests if you'd like to contribute improvements or fix bugs.
License:

This project is open-source and available under the MIT License.
