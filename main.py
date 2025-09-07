# main.py
import logging
from app import create_app, socketio

# --- A configuração do logging foi movida para dentro de create_app ---
# É uma boa prática configurar o logging junto com a criação da app.
# Mantemos apenas a obtenção do logger aqui para a mensagem de inicialização.
logger = logging.getLogger(__name__)

# Cria a instância da aplicação para que o Flask CLI possa encontrá-la.
app, socketio = create_app()

# O ponto de entrada da aplicação
if __name__ == "__main__":
    logger.info("Iniciando o servidor Flask com SocketIO na porta 5000...")
    # O debug=True é ótimo para desenvolvimento, mas lembre-se de
    # desativá-lo em produção.
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)