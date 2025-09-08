"""Módulo de configuração da aplicação.

Este arquivo centraliza todas as configurações da aplicação. As configurações
são carregadas de variáveis de ambiente usando a biblioteca `python-decouple`,
o que permite uma separação clara entre o código e as configurações de
implantação.

Para definir uma variável, crie um arquivo `.env` na raiz do projeto ou
exporte as variáveis de ambiente no seu shell.

Exemplo de `.env`:
    SECRET_KEY='sua_chave_secreta_aqui'
    SQLALCHEMY_DATABASE_URI='sqlite:///meu_banco.db'
    EMAIL_SENDER='seu_email@provedor.com'
    EMAIL_PASSWORD='sua_senha_de_email'
"""

from decouple import config
import os


class Config:
    """Classe que contém as configurações da aplicação.

    As variáveis são definidas como atributos de classe, permitindo fácil
    acesso em toda a aplicação (ex: `app.config['SECRET_KEY']`).
    """

    # Chave secreta para o Flask, usada para assinar sessões e tokens de CSRF.
    # É crucial para a segurança. Um valor padrão aleatório é gerado se não for definido.
    SECRET_KEY = config("SECRET_KEY", default=os.urandom(24).hex())

    # URI de conexão com o banco de dados.
    # Exemplo para PostgreSQL: 'postgresql://user:password@host/dbname'
    # O padrão é um banco de dados SQLite chamado 'tracking.db'.
    SQLALCHEMY_DATABASE_URI = config(
        "SQLALCHEMY_DATABASE_URI", default="sqlite:///tracking.db"
    )
    # Desativa o rastreamento de modificações do SQLAlchemy para economizar recursos.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Configurações de E-mail ---
    # Endereço de e-mail usado como remetente.
    # Fornece um valor padrão para facilitar a execução de testes sem
    # dependências externas ou variáveis de ambiente.
codex/analise-o-repositorio-btgqea
    EMAIL_SENDER = config("EMAIL_SENDER", default="test@example.com")
    # Senha do e-mail do remetente. Para serviços como Gmail, use uma "Senha de App".
    EMAIL_PASSWORD = config("EMAIL_PASSWORD", default="test-password")

    codex/analise-o-repositorio-z8y2o9
    EMAIL_SENDER = config("EMAIL_SENDER", default="test@example.com")
    # Senha do e-mail do remetente. Para serviços como Gmail, use uma "Senha de App".
    EMAIL_PASSWORD = config("EMAIL_PASSWORD", default="test-password")

    EMAIL_SENDER = config('EMAIL_SENDER', default='test@example.com')
    # Senha do e-mail do remetente. Para serviços como Gmail, use uma "Senha de App".
    EMAIL_PASSWORD = config('EMAIL_PASSWORD', default='test-password')
    main
main
    # Endereço do servidor SMTP.
    SMTP_SERVER = config("SMTP_SERVER", default="smtp.office365.com")
    # Porta do servidor SMTP (587 é comum para STARTTLS).
    SMTP_PORT = config("SMTP_PORT", default=587, cast=int)

    # --- Limites de Envio ---
    # Número máximo de e-mails que podem ser enviados por hora.
    EMAILS_PER_HOUR = config("EMAILS_PER_HOUR", default=500, cast=int)
    # Calcula o intervalo em segundos entre cada e-mail para respeitar o limite por hora.
    SECONDS_PER_EMAIL = 3600 / EMAILS_PER_HOUR

    # Chave da API para o editor de texto rico TinyMCE.
    # Obtenha uma chave no site do TinyMCE para remover avisos.
    TINYMCE_API_KEY = config("TINYMCE_API_KEY", default="no-api-key")

    # Tamanho máximo permitido para anexos de e-mail, em bytes. (Padrão: 10 MB)
    MAX_ATTACHMENT_SIZE = config(
        "MAX_ATTACHMENT_SIZE", default=10 * 1024 * 1024, cast=int
    )

    # --- Configurações de Segurança dos Cookies ---
    # Garante que os cookies de sessão só sejam enviados sobre HTTPS.
    # Defina como True em produção.
    SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
    # Impede que o cookie de sessão seja acessado por JavaScript no lado do cliente.
    SESSION_COOKIE_HTTPONLY = True
    # Define a política de SameSite para cookies para mitigar ataques CSRF.
    SESSION_COOKIE_SAMESITE = "Lax"
