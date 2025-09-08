# main.py
"""Ponto de entrada principal para a aplicação Flask.

Este script inicializa e executa a aplicação web. Ele cria a instância da aplicação
utilizando a factory `create_app` e inicia o servidor de desenvolvimento do Flask
integrado com o SocketIO.

Para executar a aplicação:
    $ python main.py

O servidor será iniciado em modo de depuração, escutando em todas as interfaces
de rede (0.0.0.0) na porta 5000.
"""
import logging
from app import create_app, socketio

# A configuração do logging é feita dentro de create_app para centralização.
# Obtemos o logger aqui apenas para a mensagem de inicialização.
logger = logging.getLogger(__name__)

# Cria a instância da aplicação e do SocketIO usando a factory.
# Isso permite que o Flask CLI e outras ferramentas encontrem a instância `app`.
app, socketio = create_app()


if __name__ == "__main__":
    """Ponto de entrada para execução direta do script.

    Inicia o servidor de desenvolvimento Flask com suporte a SocketIO.
    O modo de depuração (`debug=True`) é ativado para facilitar o desenvolvimento,
    habilitando o recarregamento automático e o depurador interativo.

    A opção `allow_unsafe_werkzeug=True` é usada para contornar uma verificação
    de segurança do Werkzeug em ambientes de desenvolvimento, mas não deve ser
    usada em produção.
    """
    logger.info("Iniciando o servidor Flask com SocketIO na porta 5000...")
    socketio.run(app, debug=True, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
