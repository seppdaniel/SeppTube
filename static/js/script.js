document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('video-url');
    const fetchBtn = document.getElementById('fetch-btn');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorBox = document.getElementById('error-message');
    const videoInfo = document.getElementById('video-info');
    
    // Video elements
    const videoThumbnail = document.getElementById('video-thumbnail');
    const videoTitle = document.getElementById('video-title');
    const videoChannel = document.getElementById('video-channel').querySelector('span');
    const videoDuration = document.getElementById('video-duration').querySelector('span');
    
    // Download elements
    const downloadBtn = document.getElementById('download-btn');
    const progressContainer = document.getElementById('download-progress-container');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressText = document.getElementById('progress-text');

    let currentVideoData = null;

    // Format duration helper (seconds to MM:SS)
    const formatDuration = (secs) => {
        const h = Math.floor(secs / 3600);
        const m = Math.floor((secs % 3600) / 60);
        const s = Math.floor(secs % 60);
        const pad = (num) => num.toString().padStart(2, '0');
        return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
    };

    // Format bytes helper
    const formatBytes = (bytes) => {
        if (!bytes || bytes === 0) return 'Tamanho desconhecido';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    fetchBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) {
            showError('Por favor, insira um link do YouTube válido.');
            return;
        }

        // Reset UI
        errorBox.classList.add('hidden');
        videoInfo.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');
        progressContainer.classList.add('hidden');
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '<i class="fa-solid fa-download"></i> Salvar e Baixar Vídeo';

        try {
            const response = await fetch('/api/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erro ao buscar informações do vídeo.');
            }

            currentVideoData = data;
            currentVideoData.originalUrl = url;

            // Populate UI
            videoThumbnail.src = data.thumbnail;
            videoTitle.textContent = data.title;
            videoChannel.textContent = data.channel;
            videoDuration.textContent = formatDuration(data.duration);
            
            loadingSpinner.classList.add('hidden');
            videoInfo.classList.remove('hidden');
            
        } catch (error) {
            loadingSpinner.classList.add('hidden');
            showError(error.message);
        }
    });

    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') fetchBtn.click();
    });

    const showError = (msg) => {
        errorBox.textContent = msg;
        errorBox.classList.remove('hidden');
    };

    downloadBtn.addEventListener('click', async () => {
        if (!currentVideoData || !currentVideoData.originalUrl) return;

        // Generate a clean suggested filename
        const safeTitle = currentVideoData.title.replace(/[<>:"/\\|?*]+/g, '_').trim();
        const suggestedName = `${safeTitle}.${currentVideoData.ext || 'mp4'}`;

        // Verify if File System Access API is supported (Desktop only)
        if (window.showSaveFilePicker) {
            let fileHandle;
            try {
                fileHandle = await window.showSaveFilePicker({
                    suggestedName: suggestedName,
                    types: [{
                        description: 'Video File',
                        accept: { 'video/mp4': ['.mp4'] },
                    }],
                });
            } catch (err) {
                if (err.name !== 'AbortError') {
                    console.error(err);
                    showError('Erro ao abrir a janela de "Salvar como...".');
                }
                return; // User canceled the save dialog
            }

            // Ready to download via streaming (Desktop)
            downloadBtn.disabled = true;
            progressContainer.classList.remove('hidden');
            progressBarFill.style.width = '0%';
            progressText.textContent = 'Iniciando download...';
            progressBarFill.style.animation = 'none';

            try {
                const response = await fetch(`/api/download?url=${encodeURIComponent(currentVideoData.originalUrl)}`);
                if (!response.ok) {
                    throw new Error('Falha ao iniciar o streaming do download.');
                }

                const writableStream = await fileHandle.createWritable();
                
                const reader = response.body.getReader();
                const contentLength = response.headers.get('Content-Length') || currentVideoData.filesize;
                
                let receivedLength = 0;

                while(true) {
                    const { done, value } = await reader.read();
                    
                    if (done) break;

                    await writableStream.write(value);
                    receivedLength += value.length;

                    if (contentLength && contentLength > 0) {
                        const percent = (receivedLength / contentLength) * 100;
                        progressBarFill.style.width = `${percent}%`;
                        progressText.textContent = `Pocessando... ${Math.round(percent)}%`;
                    } else {
                        progressBarFill.style.width = `100%`;
                        progressBarFill.style.animation = `pulse 1.5s infinite alternate`;
                        progressText.textContent = `Processando... (${formatBytes(receivedLength)})`;
                    }
                }

                await writableStream.close();
                completeUI();

            } catch (err) {
                console.error(err);
                progressText.textContent = 'Erro durante o download.';
                progressText.style.color = 'var(--error-color)';
                downloadBtn.disabled = false;
            }
        } else {
            // Mobile Fallback: Standard browser download
            // On mobile, showSaveFilePicker is not supported.
            // We'll redirect or use a hidden anchor to trigger standard behavior.
            downloadBtn.disabled = true;
            downloadBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Baixando...';
            
            const downloadUrl = `/api/download?url=${encodeURIComponent(currentVideoData.originalUrl)}`;
            
            // Note: Standard download doesn't easily show detailed JS progress 
            // but is the most compatible way for Mobile.
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = suggestedName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            // On mobile, we can't track exact completion of the browser's internal download,
            // so we'll just wait a bit and show a success message.
            setTimeout(() => {
                completeUI();
            }, 3000);
        }
    });

    const completeUI = () => {
        progressBarFill.style.width = '100%';
        progressBarFill.style.animation = 'none';
        progressBarFill.parentElement.style.background = 'var(--success-color)';
        progressText.textContent = 'Download concluído com sucesso!';
        progressText.style.color = 'var(--success-color)';
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '<i class="fa-solid fa-check"></i> Concluído';
    };
});
