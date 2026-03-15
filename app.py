import os
import subprocess
from flask import Flask, request, jsonify, Response, render_template
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/info', methods=['POST'])
def get_video_info():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    ydl_opts = {
        'skip_download': True,
        'format': 'best[ext=mp4]/best',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            
            return jsonify({
                "title": info_dict.get('title', 'Unknown Title'),
                "duration": info_dict.get('duration', 0),
                "thumbnail": info_dict.get('thumbnail', ''),
                "channel": info_dict.get('uploader', 'Unknown Channel'),
                "filesize": info_dict.get('filesize_approx', None) or info_dict.get('filesize', 0),
                "ext": info_dict.get('ext', 'mp4')
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_url = info_dict.get('url')
            
            if not video_url:
                raise Exception("Não foi possível encontrar um link de download direto.")
                
            import urllib.request
            http_headers = info_dict.get('http_headers', {})
            req = urllib.request.Request(video_url, headers=http_headers)
            response = urllib.request.urlopen(req)

            def generate():
                try:
                    while True:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    response.close()

            headers = {
                'Content-Type': response.headers.get('Content-Type', 'video/mp4'),
                'Content-Length': response.headers.get('Content-Length', '')
            }
            # Remove empty headers
            headers = {k: v for k, v in headers.items() if v}

            return Response(generate(), headers=headers)
            
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    # Use environment port for local testing flexibility
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
