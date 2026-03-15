@echo off
echo ==========================================
echo Inicializando o SeppTube Web App - Backend
echo ==========================================

IF NOT EXIST venv (
    echo Criando ambiente virtual...
    python -m venv venv
)

echo Ativando ambiente virtual...
call venv\Scripts\activate

echo Atualizando dependencias necesarias (isso corrigira problemas de conexao com o YouTube)...
pip install -U -r requirements.txt

echo.
echo ==========================================
echo Servidor Iniciado! Acesse no navegador:
echo http://127.0.0.1:5000
echo ==========================================
python app.py

pause
