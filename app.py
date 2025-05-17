from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/api/video_info', methods=['POST'])
def video_info():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    ydl_opts = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = [
        {
            'format_id': f['format_id'],
            'ext': f['ext'],
            'resolution': f.get('resolution'),
            'filesize': f.get('filesize'),
        }
        for f in info['formats']
    ]

    return jsonify({
        'title': info.get('title'),
        'thumbnail': info.get('thumbnail'),
        'formats': formats
    })

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
