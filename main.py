# main.py
import logging
from app import create_app, socketio

# --- A configuração do logging foi movida para dentro de create_app ---
# É uma boa prática configurar o logging junto com a criação da app.
# Mantemos apenas a obtenção do logger aqui para a mensagem de inicialização.
logger = logging.getLogger(__name__)

# O ponto de entrada da aplicação
if __name__ == "__main__":
    logger.info("Criando a instância da aplicação Flask...")
    app, socketio = create_app()
    
    # Adicionamos uma verificação para garantir que a app foi criada com sucesso
    if app:
        logger.info("Iniciando o servidor Flask com SocketIO na porta 5000...")
        # O debug=True é ótimo para desenvolvimento, mas lembre-se de 
        # desativá-lo em produção.
        socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
    else:
        logger.error("Falha ao criar a aplicação Flask. Encerrando.")