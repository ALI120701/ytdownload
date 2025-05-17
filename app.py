from flask import Flask, request, jsonify, send_from_directory, abort
import yt_dlp
import os
import threading
import time
import uuid

app = Flask(__name__)

# Directory to store downloaded videos
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Cleanup delay in seconds (e.g., 10 minutes)
CLEANUP_DELAY = 600

# Store info about downloaded files and their cleanup timers
downloaded_files = {}

def schedule_file_cleanup(filepath):
    def cleanup():
        time.sleep(CLEANUP_DELAY)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Deleted file: {filepath}")
        except Exception as e:
            print(f"Error deleting file {filepath}: {e}")

    threading.Thread(target=cleanup, daemon=True).start()

@app.route('/api/video_info', methods=['POST'])
def video_info():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    ydl_opts = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            return jsonify({'error': f'Failed to extract info: {str(e)}'}), 500

    formats = [
        {
            'format_id': f['format_id'],
            'ext': f['ext'],
            'resolution': f.get('resolution'),
            'filesize': f.get('filesize'),
            'acodec': f.get('acodec'),
            'vcodec': f.get('vcodec')
        }
        for f in info['formats']
    ]

    return jsonify({
        'title': info.get('title'),
        'thumbnail': info.get('thumbnail'),
        'formats': formats
    })

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    format_id = data.get('format_id')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # Generate unique filename to avoid collisions
    unique_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_FOLDER, f'{unique_id}.%(ext)s')

    ydl_opts = {
        'format': format_id if format_id else 'best',
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

    # Find the downloaded file path
    ext = info.get('ext', 'mp4')
    filename = f"{unique_id}.{ext}"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'Downloaded file not found'}), 500

    # Schedule file cleanup after delay
    schedule_file_cleanup(filepath)

    # Store the file info for possible future use (optional)
    downloaded_files[unique_id] = filepath

    download_url = f'/download/{filename}'

    return jsonify({'downloadUrl': download_url})

@app.route('/download/<path:filename>', methods=['GET'])
def serve_file(filename):
    # Security check: prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(400)

    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
