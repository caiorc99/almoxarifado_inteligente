# Documentação do Sistema de Almoxarifado Inteligente com Integração RFID e Controle de Acesso

## 1. Descrição Geral do Projeto

O Sistema de Almoxarifado Inteligente é uma solução de engenharia de software e hardware projetada para automatizar, auditar e restringir o fluxo de ferramentas em ambientes industriais ou laboratoriais. Integrando o banco de dados relacional SQLite com a plataforma microcontrolada Arduino via comunicação serial, o sistema substitui a entrada manual de credenciais pela leitura física de tags de identificação por radiofrequência (RFID - MFRC522).

Uma das principais características da arquitetura é o Controle de Acesso Baseado em Papéis (RBAC - Role-Based Access Control). Ao aproximar um cartão ou chaveiro RFID do leitor do armário, o sistema identifica o operador no banco de dados e determina suas permissões de acordo com duas categorias de cargos:
Trabalhador do Chão de Fábrica: Possui perfil operacional restrito. Suas ações são limitadas à visualização do inventário atual de ferramentas, status de disponibilidade e execução de rotinas supervisionadas de retirada e devolução de itens.
Trabalhador do Almoxarifado (Administrador): Possui perfil de gestão integral. Tem acesso a um painel de auditoria (Dashboard de Movimentações) que exibe o histórico consolidado de transações em tempo real (identificação do operador, ferramenta manipulada, timestamp da ação e tipo de evento), além de permissões irrestritas de CRUD (Criação, Leitura, Atualização e Deleção) na tabela de inventário de ferramentas.

O software foi construído com mecanismos de tolerância a falhas. Caso o circuito físico do Arduino esteja desconectado ou inacessível no barramento serial, o sistema emite um alerta informativo no terminal e chaveia automaticamente para o Modo de Simulação. Neste cenário, as portas e leituras lógicas são emuladas via teclado, garantindo que o ciclo de vida do software e os testes de banco de dados não sejam interrompidos pela ausência do hardware.

---

## 2. Tecnologias e Arquitetura

A arquitetura do projeto é dividida em três camadas fundamentais:

Camada de Dados (Back-end / Persistência):** Utiliza a biblioteca nativa `sqlite3` do Python para gerenciar o arquivo de banco de dados relacional `almoxarifado.db`. A estrutura de dados conta com integridade referencial por meio de chaves estrangeiras (Foreign Keys) e restrições de unicidade (Unique Constraints).
Camada de Comunicação e Controle (Middleware):** Desenvolvida em Python 3, utiliza a biblioteca `pyserial` para estabelecer comunicação serial assíncrona bidirecional (via USB) com o microcontrolador a uma taxa de transmissão de 9600 bauds.
Camada de Hardware (Física):** Composta por um microcontrolador da família ATmega (Arduino Uno, Nano ou Mega), um módulo leitor RFID MFRC522 operando via barramento SPI (Serial Peripheral Interface) e módulos de relés eletromecânicos acionados por portas digitais configuradas como saída (Output) para o controle de travas solenoides de gavetas.

---

## 3. Guia de Instalação e Configuração

Para implantar o sistema no ambiente de desenvolvimento local, siga as instruções abaixo.

### 3.1. Preparação do Ambiente Python
Certifique-se de possuir o Python 3.10 ou superior instalado no sistema operacional. No terminal do seu ambiente ou editor de código (como o VS Code), instale a biblioteca de comunicação com o hardware executando o seguinte comando:

```bash
pip install pyserial
