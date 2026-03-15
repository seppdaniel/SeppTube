# SeppTube Downloader

SeppTube é uma aplicação web para baixar vídeos do YouTube em alta qualidade (.mp4). O projeto evoluiu de um simples script Python de 2023 para uma solução completa com interface baseada em Glassmorphism, totalmente responsiva e otimizada para Desktop e Mobile.

## Funcionalidades

- *Design*: Interface translúcida com animações suaves e modo escuro.
- *Responsividade*: Layout que se adapta perfeitamente a computadores, tablets e celulares.
- **Download**: 
  - No *Desktop*: Abre a janela nativa de "Salvar como..." para você escolher o destino.
  - No *Mobile*: Download direto para a pasta padrão do dispositivo.
- *Motor*: Utiliza `yt-dlp` para extração rápida e estável de vídeos.
- *Segurança*: Suporte a cookies para evitar bloqueios de bot.

## Como Rodar Localmente (Windows)

Para rodar o projeto no seu computador, você não precisa configurar nada manualmente. Siga estes passos:

1. Baixe ou clone este repositório.
2. Localize o arquivo `start.bat` na pasta raiz.
3. Dê um clique duplo no `start.bat`.
   - O script criará automaticamente um ambiente virtual (`venv`).
   - Instalará todas as dependências necessárias.
   - Iniciará o servidor Flask.
4. Abra seu navegador e acesse: `http://127.0.0.1:5000`

## Tecnologias Utilizadas

- **Backend**: Python, Flask, yt-dlp.
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (ES6+).

## Notas sobre Deployment (Cloud)

Este projeto está configurado para deploy com o **Render**. 
> [!OBS]
> Devido às políticas restritivas do YouTube contra IPs de datacenters, o download em servidores cloud pode exigir a configuração de `cookies.txt` atualizados nas variáveis de ambiente/secret files do servidor. Para uso sem restrições, a execução **local** é recomendada.

---
Desenvolvido por Daniel Sepp
