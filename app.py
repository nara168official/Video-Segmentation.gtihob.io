from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
import math

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SEGMENTS_FOLDER'] = 'segments'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv'}
app.config['MAX_CONTENT_LENGTH'] = 5000 * 1024 * 1024  # 5000MB limit

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SEGMENTS_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def split_video(input_path, segment_duration):
    """Split video into segments of specified duration (in seconds)"""
    clip = VideoFileClip(input_path)
    duration = clip.duration
    segments = []
    
    # Calculate number of segments needed
    num_segments = math.ceil(duration / segment_duration)
    
    # Create segments
    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, duration)
        
        segment = clip.subclip(start_time, end_time)
        output_path = os.path.join(
            app.config['SEGMENTS_FOLDER'],
            f"{os.path.splitext(os.path.basename(input_path))[0]}_part{i+1}.mp4"
        )
        segment.write_videofile(output_path, codec='libx264', audio_codec='aac')
        segments.append(output_path)
    
    clip.close()
    return segments

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Get segment duration from form (default to 60 seconds)
        segment_duration = int(request.form.get('duration', 60))
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Split video
        segments = split_video(filepath, segment_duration)
        
        # Prepare segment data for template
        segment_data = [
            {
                'name': os.path.basename(seg),
                'path': seg
            } for seg in segments
        ]
        
        return render_template('results.html', 
                             original=filename,
                             segments=segment_data)
    
    return redirect(request.url)

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['SEGMENTS_FOLDER'], 
                             filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)