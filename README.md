# HyperXMail: Ferramenta de E-mail Marketing e Rastreamento de Campanhas

HyperXMail é uma aplicação web robusta construída com Flask, projetada para o envio de e-mails em massa, gerenciamento de campanhas e rastreamento detalhado de interações. É uma solução ideal para desenvolvedores e pequenas equipes que precisam de uma ferramenta de e-mail marketing auto-hospedada e personalizável.

## Funcionalidades Principais

- **Envio de E-mail em Massa**: Envie e-mails para um grande número de destinatários usando um servidor SMTP configurado.
- **Rastreamento de Campanhas**: Monitore o desempenho de suas campanhas com rastreamento de aberturas (via pixel) e cliques (via redirecionamento).
- **Relatórios Detalhados**: Visualize relatórios por campanha, incluindo taxas de abertura e de cliques únicos.
- **Editor Rich Text**: Componha e-mails em HTML usando o editor WYSIWYG TinyMCE.
- **Gerenciamento de Templates**: Salve e carregue templates de e-mail para agilizar a criação de campanhas.
- **Suporte a Anexos Seguros**: Envie anexos nos formatos JPG, PNG e PDF, com validação de tipo MIME e limite de tamanho (10MB).
- **Imagens Embutidas**: Incorpore imagens diretamente no corpo do e-mail usando `cid` para uma melhor experiência do usuário.
- **Importação de Destinatários**: Importe listas de e-mails facilmente a partir de arquivos CSV ou adicione-os manualmente.
- **Progresso em Tempo Real**: Acompanhe o progresso do envio de e-mails em tempo real através de WebSockets.
- **Segurança**:
  - **Proteção CSRF**: Integrado com Flask-WTF para prevenir ataques de Cross-Site Request Forgery.
  - **Sanitização de Entradas**: Todo o conteúdo HTML e nomes de arquivos são sanitizados para prevenir ataques de Cross-Site Scripting (XSS).
  - **Limitação de Taxa (Rate Limiting)**: Protege a aplicação contra abuso e ataques de força bruta.

## Arquitetura da Aplicação

A aplicação segue uma arquitetura modular baseada no padrão de fábrica de aplicações (`create_app`) do Flask.

- **Backend**:
  - **Flask**: O micro-framework principal que gerencia as rotas, requisições e a lógica da aplicação.
  - **SQLAlchemy & Flask-SQLAlchemy**: ORM para a interação com o banco de dados.
  - **Alembic & Flask-Migrate**: Gerencia as migrações do esquema do banco de dados.
  - **SocketIO & Flask-SocketIO**: Fornece comunicação bidirecional em tempo real via WebSockets para relatar o progresso do envio.
  - **aiosmtplib & Asyncio**: Utilizado para o envio de e-mails de forma assíncrona, melhorando o desempenho e a concorrência.
  - **python-decouple**: Para gerenciamento de configurações via variáveis de ambiente.

- **Frontend**:
  - **HTML5 / CSS3**: Estrutura e estilo da interface do usuário (sem framework CSS).
  - **JavaScript (Vanilla)**: Manipulação do DOM, interações do usuário e comunicação com o backend via `fetch` e `Socket.IO-client`.
  - **TinyMCE**: Editor de texto rico para a composição de e-mails.

## Estrutura do Banco de Dados

O banco de dados é composto por quatro tabelas principais para armazenar os dados das campanhas e do rastreamento.

- `Campaign`: Armazena informações sobre cada campanha (assunto, mensagem, data de criação).
- `Email`: Registra cada e-mail individual enviado, vinculando-o a uma campanha e a um destinatário. Utiliza um UUID como chave primária para rastreamento.
- `Open`: Registra cada evento de abertura de um e-mail.
- `Click`: Registra cada clique em um link dentro de um e-mail, armazenando a URL de destino.

## Endpoints da API

A aplicação expõe vários endpoints para interações do frontend.

- `GET /`: Renderiza a página principal de envio de e-mails.
- `GET /reports`: Renderiza a página de relatórios.
- `GET /templates`: Retorna uma lista de templates de e-mail salvos em formato JSON.
- `POST /templates`: Salva um novo template de e-mail.
- `POST /send_email`: Inicia o processo de envio de uma campanha de e-mail.
- `GET /api/campaigns`: Retorna uma lista de todas as campanhas criadas.
- `GET /api/reports/<campaign_id>`: Retorna os dados estatísticos de uma campanha específica.
- `GET /track/open/<email_id>`: Endpoint do pixel de rastreamento de aberturas.
- `GET /track/click/<email_id>`: Endpoint de rastreamento de cliques que redireciona para a URL final.

## Instalação

Siga os passos abaixo para configurar e executar o ambiente de desenvolvimento local.

**Pré-requisitos**:
- Python 3.8+
- Um servidor SMTP (ex: Gmail, Office 365, SendGrid, etc.)

**1. Clone o Repositório**
```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_DIRETORIO>
```

**2. Crie e Ative um Ambiente Virtual**
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

**3. Instale as Dependências**
```bash
pip install -r requirements.txt
```

## Configuração

A aplicação utiliza um arquivo `.env` para gerenciar as variáveis de ambiente.

**1. Crie o arquivo `.env`**
Crie um arquivo chamado `.env` na raiz do projeto e adicione as seguintes variáveis:

```env
# Chave secreta para a aplicação Flask (mude para um valor seguro e aleatório)
SECRET_KEY='uma-chave-super-secreta-e-longa'

# URI do Banco de Dados (padrão para SQLite, pode ser alterado para PostgreSQL, etc.)
SQLALCHEMY_DATABASE_URI='sqlite:///tracking.db'

# Configurações do Servidor SMTP
EMAIL_SENDER='seu-email@dominio.com'
EMAIL_PASSWORD='sua-senha-de-app-ou-normal'
SMTP_SERVER='smtp.seu-provedor.com'
SMTP_PORT=587

# Chave da API do TinyMCE (opcional, mas recomendado para remover avisos)
TINYMCE_API_KEY='sua-chave-de-api-do-tinymce'

# (Opcional) Limite de envios por hora
# EMAILS_PER_HOUR=500
```

**2. Configure as Variáveis**
- `SECRET_KEY`: Uma string longa e aleatória usada para proteger sessões e cookies.
- `SQLALCHEMY_DATABASE_URI`: A string de conexão para o banco de dados. O padrão `sqlite:///tracking.db` cria um arquivo de banco de dados SQLite na raiz do projeto.
- `EMAIL_SENDER`: O endereço de e-mail que será usado como remetente.
- `EMAIL_PASSWORD`: A senha para a conta de e-mail. **Atenção**: Para serviços como o Gmail, é necessário gerar uma "Senha de App".
- `SMTP_SERVER`: O endereço do seu servidor SMTP.
- `SMTP_PORT`: A porta do seu servidor SMTP (geralmente 587 para TLS/STARTTLS).
- `TINYMCE_API_KEY`: A chave da API para o editor de texto TinyMCE. Você pode obter uma chave gratuita no site do TinyMCE.

## Execução da Aplicação

**1. Aplique as Migrações do Banco de Dados**
Com o ambiente virtual ativado, execute o seguinte comando para criar as tabelas do banco de dados:
```bash
flask db upgrade
```
Este comando aplica a migração mais recente do banco de dados. Você deve executá-lo sempre que houver novas migrações no diretório `migrations/versions`.

**2. Inicie o Servidor de Desenvolvimento**
```bash
python main.py
```
A aplicação estará disponível em `http://127.0.0.1:5000`.

**Aviso**: O servidor de desenvolvimento do Flask não é recomendado para produção. Para implantação em produção, utilize um servidor WSGI robusto como Gunicorn ou uWSGI.

## Melhorias Futuras

- **Testes Unitários e de Integração**: Expandir a suíte de testes para cobrir todas as funcionalidades críticas, incluindo o envio de e-mails, a lógica da API e a interação com o banco de dados.
- **Autenticação de Usuário**: Implementar um sistema de login para proteger o acesso à ferramenta.
- **Gerenciamento de Listas**: Adicionar funcionalidades para gerenciar listas de contatos de forma mais avançada.
- **Agendamento de Campanhas**: Permitir que os usuários agendem o envio de campanhas para uma data e hora futuras.
