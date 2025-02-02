#!/bin/bash
#filename script.sh
# Check if exactly two arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path_to_image1> <path_to_image2>"
    exit 1
fi

IMAGE1_PATH=$1
IMAGE2_PATH=$2

# Validate that the files exist
if [ ! -f "$IMAGE1_PATH" ]; then
    echo "Error: File $IMAGE1_PATH does not exist."
    exit 1
fi

if [ ! -f "$IMAGE2_PATH" ]; then
    echo "Error: File $IMAGE2_PATH does not exist."
    exit 1
fi

# Upload images to the Flask app
echo "Uploading images..."
UPLOAD_RESPONSE=$(curl -s -X POST http://127.0.0.1:5000/upload \
     -F "image1=@$IMAGE1_PATH" \
     -F "image2=@$IMAGE2_PATH")

# Check if the upload was successful
if [[ $(echo "$UPLOAD_RESPONSE" | jq -r '.error') ]]; then
    echo "Error: $(echo "$UPLOAD_RESPONSE" | jq -r '.error')"
    exit 1
fi

# Extract image paths from the JSON response
IMAGE1_UPLOADED_PATH=$(echo "$UPLOAD_RESPONSE" | jq -r '.image1_path')
IMAGE2_UPLOADED_PATH=$(echo "$UPLOAD_RESPONSE" | jq -r '.image2_path')

echo "Images uploaded successfully."
echo "Image 1 Path: $IMAGE1_UPLOADED_PATH"
echo "Image 2 Path: $IMAGE2_UPLOADED_PATH"

# Generate the zoom video
echo "Generating zoom video..."
GENERATE_RESPONSE=$(curl -s -X POST http://127.0.0.1:5000/generate \
     -H "Content-Type: application/json" \
     -d '{
           "image1_path": "'"$IMAGE1_UPLOADED_PATH"'",
           "image2_path": "'"$IMAGE2_UPLOADED_PATH"'",
           "zoom_speed": 0.1,
           "duration": 5,
           "fps": 30
         }')

# Check if the generation was successful
if [[ $(echo "$GENERATE_RESPONSE" | jq -r '.error') ]]; then
    echo "Error: $(echo "$GENERATE_RESPONSE" | jq -r '.error')"
    exit 1
fi

VIDEO_PATH=$(echo "$GENERATE_RESPONSE" | jq -r '.video_path')
echo "Video generated successfully."
echo "Video Path: $VIDEO_PATH"

# Download the video
echo "Downloading video..."
curl -o output.mp4 http://127.0.0.1:5100/download/$(basename "$VIDEO_PATH")

echo "Video downloaded as output.mp4"