# Email Sender 

Este é um aplicativo Flask para envio de e-mails em massa com suporte a anexos (imagens e PDFs) e imagens embutidas no corpo do e-mail. Ele possui uma interface web futurista e inclui validações de segurança, como limite de envio, autenticação e sanitização de entradas.

## Funcionalidades

- Envio de e-mails em massa via SMTP.
- Suporte a anexos (imagens e PDFs) com limite de tamanho (10MB).
- Imagens embutidas no corpo do e-mail usando `cid`.
- Interface web com tema futurista para compor e enviar e-mails.
- Validação de e-mails e sanitização de entradas com `bleach`.
- Limite de envio (500 e-mails por hora) usando `Flask-Limiter`.
- Autenticação via token de API.
- Registro de e-mails enviados para evitar duplicatas (`sent_emails.log`).

## Estrutura do Projeto

email_sender/
│
├── app/
│   ├── init.py        # Inicialização do app Flask
│   ├── config.py          # Configurações centralizadas
│   ├── email_utils.py     # Funções relacionadas ao envio de e-mails
│   ├── routes.py          # Definição das rotas do Flask
│   └── templates.py       # Template HTML para a interface web
│
├── main.py                # Arquivo principal para executar o app
├── requirements.txt       # Dependências do projeto
└── README.md              # Instruções de uso


## Pré-requisitos

- Python 3.8 ou superior
- Um servidor SMTP (ex.: Office 365, Gmail)
- Credenciais SMTP (e-mail e senha)

## Instalação

1. Clone o repositório:

   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd email_sender

2. Crie um ambiente virtual e ative-o:

python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

3. Instale as dependências:

pip install -r requirements.txt

4. Configure as variáveis de ambiente em um arquivo .env:

EMAIL_SENDER=seu-email@dominio.com
EMAIL_PASSWORD=sua-senha
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
API_TOKEN=seu-token-secreto
SECRET_KEY=sua-chave-secreta

EMAIL_SENDER: E-mail que será usado para enviar os e-mails.
EMAIL_PASSWORD: Senha do e-mail (para Office 365, pode ser uma senha de aplicativo).
SMTP_SERVER: Servidor SMTP (ex.: smtp.office365.com para Office 365).
SMTP_PORT: Porta do servidor SMTP (geralmente 587 para TLS).
API_TOKEN: Token para autenticação na API.
SECRET_KEY: Chave secreta para o Flask (use uma string aleatória).


Como Usar
1. Execute o aplicativo:

python main.py
O servidor será iniciado em http://127.0.0.1:5000

2. Acesse a interface web em um navegador: URL: http://127.0.0.1:5000

3. Preencha o formulário na interface:

Destinatários: Digite e-mails manualmente (pressione Enter para adicionar) ou carregue um arquivo CSV com uma lista de e-mails (um por linha).
Assunto: Insira o assunto do e-mail.
CC e CCO: (Opcional) Adicione e-mails em cópia ou cópia oculta, separados por vírgulas.
Mensagem: Escreva a mensagem (suporta HTML, como <img> para imagens embutidas).
Anexos: Clique em "ANEXAR AO TEXTO" para adicionar imagens ou PDFs (máximo 10MB por arquivo).
CSV: (Opcional) Carregue um arquivo CSV com e-mails.

4. Clique em "ENVIAR SINAL" para enviar os e-mails.

Um log será exibido na interface com o progresso do envio.
Um arquivo sent_emails.log será criado para registrar os e-mails enviados e evitar duplicatas.

Exemplo de Uso

1. Enviar um e-mail com uma imagem embutida:
Assunto: Teste de E-mail
Mensagem: Olá, veja nossa campanha: <img src="cid:image0" alt="campanha.png">
Anexos: Selecione a imagem campanha.png.
CSV: Carregue um arquivo emails.csv com:

usuario1@dominio.com
usuario2@dominio.com

2. Clique em "ENVIAR SINAL". O e-mail será enviado para os destinatários listados, com a imagem embutida no corpo.

Notas

Limites: O aplicativo limita o envio a 500 e-mails por hora para evitar abuso.
Anexos: Imagens são embutidas no corpo do e-mail usando cid, enquanto PDFs são anexados normalmente.
Segurança: As entradas são sanitizadas com bleach para evitar ataques XSS. A autenticação via token é obrigatória.
Logs: Logs detalhados são gerados tanto no console quanto na interface web para facilitar a depuração.

Solução de Problemas

Erro de autenticação SMTP:
Verifique se as credenciais no arquivo .env estão corretas.
Para Office 365, pode ser necessário usar uma senha de aplicativo em vez da senha padrão.

Anexo .htm aparece no e-mail:
Este problema foi corrigido usando uma estrutura MIME simplificada (alternative com related). Se persistir, teste em outro cliente de e-mail (ex.: Gmail) para confirmar se é específico do Outlook.

E-mails não são enviados:
Verifique os logs no console e na interface para identificar o erro.
Certifique-se de que o servidor SMTP está acessível e que o limite de 500 e-mails por hora não foi excedido.

Contribuições
Sinta-se à vontade para abrir issues ou pull requests com melhorias ou correções!

Licença
Este projeto é licenciado sob a MIT License.

Autor: SuperGrok
