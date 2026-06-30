import sqlite3
import time
import serial
import threading

NOME_BANCO = "almoxarifado.db"

ULTIMA_TAG_LIDA = None
PESO_ATUAL_BALANCA = 0.0

# VARIÁVEIS DE CONTROLE DE TRANSAÇÃO DO HARDWARE
TRANSACAO_ATIVA = False          # Indica se há uma retirada aguardando fechamento de porta
TIPO_ITEM_TRANSACAO = None       # 'porcas' ou 'alicate'
PESO_INICIAL_TRANSACAO = 0.0     # Guarda o peso antes da abertura da gaveta 2
ID_FERRAMENTA_TRANSACAO = None
ID_USUARIO_TRANSACAO = None

try:
    # Configurado com o Baudrate de 115200 enviado pelo ESP32
    arduino = serial.Serial("COM3", 115200, timeout=0.1)
    print("🔌 Conexão Serial com o hardware ESP32 (115200 baud) estabelecida com sucesso!")
except Exception as e:
    arduino = None
    print("⚠️ Hardware ESP32 não detectado na COM3. Operando em modo de emulação por digitação.")

def conectar_banco():
    return sqlite3.connect(NOME_BANCO)

def buscar_usuario(matricula):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    matricula_limpa = str(matricula).strip().upper()
    cursor.execute("SELECT id, nome, cargo FROM usuario WHERE matricula = ?", (matricula_limpa,))
    usuario = cursor.fetchone()
    conexao.close()
    return usuario

def buscar_administrador_por_senha(login, senha):
    """Busca um usuário administrador que coincida com o login (matrícula) e senha digitados."""
    conexao = conectar_banco()
    cursor = conexao.cursor()
    login_limpo = str(login).strip()
    senha_limpa = str(senha).strip()
    
    cursor.execute(
        "SELECT id, nome, cargo FROM usuario WHERE matricula = ? AND senha = ? AND cargo = 'almoxarifado'", 
        (login_limpo, senha_limpa)
    )
    usuario = cursor.fetchone()
    conexao.close()
    return usuario # Retorna (id, nome, cargo) ou None

def enviar_comando_hardware(comando):
    """Envia uma string de comando formatada para o ESP32 via Serial."""
    if arduino and arduino.is_open:
        try:
            msg = f"{comando}\n".encode('utf-8')
            arduino.write(msg)
            print(f"📟 [Python -> ESP32]: {comando}")
        except Exception as e:
            print(f"❌ Erro ao enviar comando para o hardware: {e}")

def finalizar_retirada_porcas_por_peso(peso_final):
    """Calcula a quantidade de porcas retiradas após a gaveta ser fechada."""
    global TRANSACAO_ATIVA, PESO_INICIAL_TRANSACAO, ID_FERRAMENTA_TRANSACAO, ID_USUARIO_TRANSACAO
    
    peso_retirado = PESO_INICIAL_TRANSACAO - peso_final
    if peso_retirado < 0:
        peso_retirado = 0.0
        
    # Lógica enviada: 1 porca = 6.6g
    quantidade_retirada = round(peso_retirado / 6.6)
    
    print(f"⚖️ [BALANÇA] Peso Inicial: {PESO_INICIAL_TRANSACAO}g | Peso Final: {peso_final}g")
    print(f"⚖️ [BALANÇA] Peso Diferença: {peso_retirado}g -> Quantidade Calculada: {quantidade_retirada} porcas.")
    
    if quantidade_retirada > 0:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        # Pega a quantidade atual no estoque
        cursor.execute("SELECT nome, quantidade FROM ferramenta WHERE id = ?", (ID_FERRAMENTA_TRANSACAO,))
        f_dados = cursor.fetchone()
        
        if f_dados:
            nome_f, qtd_estoque = f_dados
            nova_qtd = max(0.0, qtd_estoque - quantidade_retirada)
            novo_status = 'retirada' if nova_qtd == 0 else 'disponivel'
            
            # Atualiza estoque e insere no histórico (log)
            cursor.execute("UPDATE ferramenta SET quantidade = ?, status = ? WHERE id = ?", (nova_qtd, novo_status, ID_FERRAMENTA_TRANSACAO))
            cursor.execute("INSERT INTO item (usuario_id, ferramenta_id, acao, quantidade_movimentada) VALUES (?, ?, 'retirou', ?)", 
                           (ID_USUARIO_TRANSACAO, ID_FERRAMENTA_TRANSACAO, quantidade_retirada))
            conexao.commit()
            print(f"📦 [Estoque Atualizado] {quantidade_retirada} un de '{nome_f}' debitadas do inventário.")
        conexao.close()
    else:
        print("⚠️ Nenhuma porca foi retirada (variação de peso insignificante).")
        
    # Limpa estado da transação
    TRANSACAO_ATIVA = False

def finalizar_retirada_alicate_visao():
    """Aciona a rotina de Visão Computacional após a gaveta do alicate ser fechada."""
    global TRANSACAO_ATIVA, ID_FERRAMENTA_TRANSACAO, ID_USUARIO_TRANSACAO
    
    print("👁️ [VISÃO COMPUTACIONAL] Porta 1 Fechada. Iniciando análise de câmera para o Alicate...")
    
    # Executa a baixa padrão de 1 unidade para a ferramenta monitorada
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT nome, quantidade FROM ferramenta WHERE id = ?", (ID_FERRAMENTA_TRANSACAO,))
    f_dados = cursor.fetchone()
    
    if f_dados:
        nome_f, qtd_estoque = f_dados
        nova_qtd = max(0.0, qtd_estoque - 1.0)
        novo_status = 'retirada' if nova_qtd == 0 else 'disponivel'
        
        cursor.execute("UPDATE ferramenta SET quantidade = ?, status = ? WHERE id = ?", (nova_qtd, novo_status, ID_FERRAMENTA_TRANSACAO))
        cursor.execute("INSERT INTO item (usuario_id, ferramenta_id, acao, quantidade_movimentada) VALUES (?, ?, 'retirou', 1.0)", 
                       (ID_USUARIO_TRANSACAO, ID_FERRAMENTA_TRANSACAO))
        conexao.commit()
        print(f"📦 [Estoque Atualizado] 1 un de '{nome_f}' (Alicate) confirmada por monitoramento de porta.")
        
    conexao.close()
    TRANSACAO_ATIVA = False

def escutar_arduino_loop():
    """Thread em segundo plano que monitora as mensagens textuais do ESP32."""
    global ULTIMA_TAG_LIDA, PESO_ATUAL_BALANCA, TRANSACAO_ATIVA
    while arduino and arduino.is_open:
        try:
            if arduino.in_waiting > 0:
                linha = arduino.readline().decode("utf-8", errors="ignore").strip()
                if linha:
                    # Captura de Tags RFID
                    if linha.startswith("TAG:"):
                        ULTIMA_TAG_LIDA = linha.replace("TAG:", "").strip().upper()
                        print(f"\n📡 Tag RFID lida via Serial: {ULTIMA_TAG_LIDA}")
                        
                    # Monitoramento constante do peso em gramas
                    elif linha.startswith("PESO:"):
                        try:
                            PESO_ATUAL_BALANCA = float(linha.replace("PESO:", "").strip())
                        except ValueError:
                            pass
                            
                    # Evento de fechamento da Porta 1 (Alicate / Visão Computacional)
                    elif linha == "PORTA_1_FECHADA":
                        print("🚪 Notificação do Hardware: PORTA_1_FECHADA")
                        if TRANSACAO_ATIVA and TIPO_ITEM_TRANSACAO == 'alicate':
                            finalizar_retirada_alicate_visao()
                            
                    # Evento de fechamento da Porta 2 (Balança / Porcas)
                    elif linha == "PORTA_2_FECHADA":
                        print("🚪 Notificação do Hardware: PORTA_2_FECHADA")
                        if TRANSACAO_ATIVA and TIPO_ITEM_TRANSACAO == 'porcas':
                            finalizar_retirada_porcas_por_peso(PESO_ATUAL_BALANCA)
                            
                    # Strings Informativas de Setup do ESP32
                    elif linha in ["SISTEMA_PRONTO", "BALANCA_PRONTA", "CALIBRACAO_FIXA_ATIVA"]:
                        print(f"🤖 [ESP32 Status]: {linha}")
        except Exception as e:
            print(f"Erro na leitura da linha serial: {e}")
            time.sleep(0.1)
        time.sleep(0.02)

# Inicializa a Thread de escuta contínua do Hardware
if arduino:
    thread_serial = threading.Thread(target=escutar_arduino_loop, daemon=True)
    thread_serial.start()

def obter_e_limpar_tag():
    global ULTIMA_TAG_LIDA
    tag = ULTIMA_TAG_LIDA
    ULTIMA_TAG_LIDA = None 
    return tag

def obter_peso_atual():
    return PESO_ATUAL_BALANCA

# =====================================================================
# LÓGICA DE INTERAÇÃO DISPARADA PELA INTERFACE WEB
# =====================================================================

def preparar_e_abrir_porta_hardware(id_usuario, id_ferramenta):
    """
    Identifica o tipo de item no banco e envia o comando de abertura correto para o ESP32,
    salvando as métricas iniciais para computação posterior no fechamento da porta.
    """
    global TRANSACAO_ATIVA, TIPO_ITEM_TRANSACAO, PESO_INICIAL_TRANSACAO, ID_FERRAMENTA_TRANSACAO, ID_USUARIO_TRANSACAO
    
    if TRANSACAO_ATIVA:
        return {"erro": "Existe uma operação pendente no armário físico. Feche a porta aberta primeiro!"}
        
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT nome, tipo, quantidade FROM ferramenta WHERE id = ?", (id_ferramenta,))
    item = cursor.fetchone()
    conexao.close()
    
    if not item:
        return {"erro": "Item selecionado inválido ou não cadastrado."}
        
    nome_f, tipo_f, qtd_atual = item
    
    # Vincula dados ao gerenciador de transação atual
    ID_USUARIO_TRANSACAO = id_usuario
    ID_FERRAMENTA_TRANSACAO = id_ferramenta
    TRANSACAO_ATIVA = True
    
    # MAPEAMENTO SEGUNDO ESPECIFICAÇÃO:
    # Se o nome ou tipo corresponder a porcas/consumível -> Porta 2 (Balança)
    if tipo_f == 'consumivel' or "porca" in nome_f.lower():
        TIPO_ITEM_TRANSACAO = 'porcas'
        PESO_INICIAL_TRANSACAO = PESO_ATUAL_BALANCA   # Salva o peso atual antes de retirar
        
        # Se estiver em modo de emulação (sem ESP32), simula um peso inicial fictício superior
        if not arduino:
            PESO_INICIAL_TRANSACAO = 500.0 
            
        print(f"🔓 [COMANDO] Iniciando transação de Porcas. Peso antes da abertura: {PESO_INICIAL_TRANSACAO}g")
        enviar_comando_hardware("ABRIR:2")
        return {"sucesso": f"Gaveta das Porcas (Porta 2) Liberada! Aguardando a retirada de insumos e o fechamento da porta."}
        
    # Se corresponder a ferramenta/reutilizavel -> Porta 1 (Alicate)
    else:
        TIPO_ITEM_TRANSACAO = 'alicate'
        print(f"🔓 [COMANDO] Iniciando transação de Alicate. Aguardando verificação por câmera posterior.")
        enviar_comando_hardware("ABRIR:1")
        return {"sucesso": f"Compartimento do Alicate (Porta 1) Liberado! Retire a ferramenta e feche a porta para auditoria visual."}

# Mantido funções padrões para CRUD administrativo via Web
def cadastrar_nova_ferramenta(nome, gaveta, quantidade, tipo):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO ferramenta (nome, status, gaveta, quantidade, tipo) VALUES (?, 'disponivel', ?, ?, ?)", (nome, gaveta, quantidade, tipo))
    conexao.commit()
    conexao.close()

def atualizar_ferramenta(id_f, nome, gaveta, quantidade, tipo):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("UPDATE ferramenta SET nome = ?, gaveta = ?, quantidade = ?, tipo = ? WHERE id = ?", (nome, gaveta, quantidade, tipo, id_f))
    conexao.commit()
    conexao.close()

def deletar_ferramenta(id_f):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM ferramenta WHERE id = ?", (id_f,))
    conexao.commit()
    conexao.close()