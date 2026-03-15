import os
import re
import urllib.request
from flask import Flask, request, jsonify, Response, render_template
from flask_cors import CORS
import yt_dlp

# ─────────────────────── Error helper ───────────────────────
# Errors that mean the production server (Render.com datacenter
# IP) is being blocked by YouTube's bot-detection.
_BOT_DETECTION_SIGNALS = [
    'Sign in to confirm',
    'confirm you\'re not a bot',
    'This helps protect our community',
    'bot',
]

_MAINTENANCE_MSG = (
    "A versão online está temporariamente em manutenção.<br>"
    "A versão local está funcionando perfeitamente! <br>"
    "Bons downloads!"
)

_ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
_YT_PREFIX_RE = re.compile(r'^ERROR:\s*\[youtube\]\s*[a-zA-Z0-9_-]+:\s*')


def parse_ydl_error(exc) -> str:
    """Return a clean, localised error string from a yt-dlp exception."""
    raw = str(exc)
    clean = _ANSI_RE.sub('', raw)
    clean = _YT_PREFIX_RE.sub('', clean)

    # Bot-detection / sign-in required → maintenance message
    if any(sig.lower() in clean.lower() for sig in _BOT_DETECTION_SIGNALS):
        return _MAINTENANCE_MSG

    if 'DRM protected' in clean:
        return "Este vídeo é protegido por DRM (Direitos Autorais) e não pode ser baixado."
    if 'Video unavailable' in clean:
        return "Este vídeo está indisponível."

    return clean
# ─────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)

# Use absolute path so the file is always found regardless of working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_PATH = os.path.join(BASE_DIR, 'cookies.txt')


def sanitize_cookies_file():
    """
    Re-writes the cookies.txt to ensure it is in valid Netscape format.
    This fixes issues caused by the Render Secret Files UI adding invisible
    characters (BOM) or extra whitespace when pasting content.
    """
    if not os.path.exists(COOKIES_PATH):
        return

    try:
        with open(COOKIES_PATH, 'r', encoding='utf-8-sig') as f:  # utf-8-sig strips BOM
            lines = f.readlines()

        # Strip leading/trailing whitespace from each line
        lines = [line.strip() for line in lines]

        # Remove leading blank lines
        while lines and not lines[0]:
            lines.pop(0)

        # Ensure the first line is the required Netscape header
        if not lines or not lines[0].startswith('# Netscape HTTP Cookie File'):
            lines.insert(0, '# Netscape HTTP Cookie File')

        with open(COOKIES_PATH, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')

        print("[SeppTube] cookies.txt sanitized successfully.")
    except Exception as e:
        print(f"[SeppTube] Could not sanitize cookies.txt: {e}")

# Sanitize cookie file on startup
sanitize_cookies_file()

def get_ydl_opts(extra=None):
    """Build base yt-dlp options, adding cookies if available."""
    opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': False,       # Enable verbose for debugging in server logs
        'no_warnings': False,
        # Use android + web clients. 'tv' and 'mweb' cause false DRM
        # errors on YouTube Shorts and have been removed.
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        },
    }
    if os.path.exists(COOKIES_PATH):
        opts['cookiefile'] = COOKIES_PATH
    if extra:
        opts.update(extra)
    return opts

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/debug')
def debug():
    """Endpoint to help diagnose cookie file issues on the server."""
    cookie_exists = os.path.exists(COOKIES_PATH)
    cookie_preview = None
    cookie_size = None
    if cookie_exists:
        cookie_size = os.path.getsize(COOKIES_PATH)
        try:
            with open(COOKIES_PATH, 'r', encoding='utf-8') as f:
                first_lines = [f.readline() for _ in range(3)]
            cookie_preview = [repr(line) for line in first_lines]
        except Exception as e:
            cookie_preview = [f"Error reading: {e}"]
    return jsonify({
        "base_dir": BASE_DIR,
        "cookies_path": COOKIES_PATH,
        "cookies_exists": cookie_exists,
        "cookies_size_bytes": cookie_size,
        "first_3_lines_repr": cookie_preview
    })

@app.route('/api/info', methods=['POST'])
def get_video_info():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts({'skip_download': True})) as ydl:
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
        return jsonify({"error": parse_ydl_error(e)}), 500

@app.route('/api/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_url = info_dict.get('url')

            if not video_url:
                raise Exception("Não foi possível encontrar um link de download direto.")

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
            headers = {k: v for k, v in headers.items() if v}

            return Response(generate(), headers=headers)

    except Exception as e:
        return parse_ydl_error(e), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
