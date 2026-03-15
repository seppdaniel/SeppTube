from pytube import YouTube
from tqdm import tqdm
import re

def progress_bar(stream, chunk, bytes_remaining):
    current = stream.filesize - bytes_remaining
    completed = int(current * 100 / stream.filesize)
    tqdm.write(f'Concluído {completed}%')

def download_video(video_link):
    try:
        yt = YouTube(video_link, on_progress_callback=progress_bar)
        ys = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        if ys is None:
            print("Nenhuma resolução de vídeo adequada encontrada para download.")
            return
        
        valid_title = re.sub(r'[<>:"/\\|?*]', '_', yt.title)
        download_path = f'./{valid_title}.mp4'  # Alterando o caminho para a pasta local
        
        with tqdm(total=ys.filesize, unit='B', unit_scale=True, ncols=100, bar_format='{l_bar}{bar}|') as t:
            ys.download(download_path)
            t.write(f'Download concluído: {yt.title}')
    
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

# Link direto para o vídeo que será baixado
video_link = "https://youtu.be/Jyg-9I0ZL2Q?si=8HAY717_hGPowzIN"
download_video(video_link)
