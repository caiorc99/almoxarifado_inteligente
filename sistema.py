import sqlite3
import time
import serial # Reativado para comunicação com o Hardware físico

NOME_BANCO = "almoxarifado.db"

# Tenta estabelecer conexão com o Arduino na porta especificada.
try:
    arduino = serial.Serial('COM3', 9600, timeout=1) 
    print("🔌 Conexão Serial com o leitor RFID estabelecida com sucesso!")
except Exception as e:
    arduino = None 
    print("⚠️ Hardware RFID não detectado ou porta ocupada. Operando em modo de emulação por digitação.")

def conectar_banco():
    return sqlite3.connect(NOME_BANCO)

def buscar_usuario(matricula):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    matricula_limpa = str(matricula).strip().upper()
    cursor.execute("SELECT id, nome, cargo FROM usuario WHERE matricula = ?", (matricula_limpa,))
    usuario = cursor.fetchone()
    conexao.close()
    return usuario # Retorna (id, nome, cargo) ou None

# =====================================================================
# FUNÇÕES EXCLUSIVAS DO ALMOXARIFADO (DASHBOARD, CREATE, UPDATE, DELETE)
# =====================================================================

def dashboard_movimentacoes():
    """Mostra quem pegou o que, quando pegou e o histórico completo."""
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute('''
        SELECT usuario.nome, ferramenta.nome, item.data_hora, item.acao, item.quantidade_movimentada 
        FROM item
        INNER JOIN usuario ON item.usuario_id = usuario.id
        INNER JOIN ferramenta ON item.ferramenta_id = ferramenta.id
        ORDER BY item.data_hora DESC
    ''')
    dados = cursor.fetchall()
    conexao.close()
    
    print("\n📊 === DASHBOARD DE MOVIMENTAÇÕES ===")
    if not dados:
        print("Nenhuma movimentação registrada ainda.")
    for linha in dados:
        print(f"👤 {linha[0]} | 🔧 {linha[1]} | 📅 {linha[2]} | Qtd: {linha[4]} | Action: {linha[3].upper()}")

# 💡 CORRIGIDO: Agora aceita explicitamente a quantidade vinda da WEB ou do Terminal
def cadastrar_nova_ferramenta(nome, gaveta, quantidade=1):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO ferramenta (nome, gaveta, quantidade) VALUES (?, ?, ?)", (nome, gaveta, quantidade))
    conexao.commit()
    conexao.close()
    print(f"✅ Ferramenta '{nome}' ({quantidade} un) adicionada ao estoque na gaveta {gaveta}!")

# 💡 CORRIGIDO: Agora atualiza explicitamente a quantidade vinda da WEB ou do Terminal
def atualizar_ferramenta(id_f, novo_nome, nova_gaveta, nova_quantidade):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("UPDATE ferramenta SET nome = ?, gaveta = ?, quantidade = ? WHERE id = ?", (novo_nome, nova_gaveta, nova_quantidade, id_f))
    conexao.commit()
    conexao.close()
    print("✅ Dados da ferramenta atualizados com sucesso!")

def deletar_ferramenta(id_f):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM ferramenta WHERE id = ?", (id_f,))
    conexao.commit()
    conexao.close()
    print("❌ Ferramenta removida do estoque!")

# =====================================================================
# FUNÇÕES DO CHÃO DE FÁBRICA / REGRAS DE RETIRADA POR QUANTIDADE
# =====================================================================

def visualizar_prazos_e_status():
    """Funcionário do chão de fábrica vê o que está disponível e os volumes."""
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, status, gaveta, quantidade FROM ferramenta")
    ferramentas = cursor.fetchall()
    conexao.close()
    print("\n🔧 === STATUS DO ESTOQUE COMPLETO ===")
    for f in ferramentas:
        print(f"ID: {f[0]} | Item: {f[1]} | Qtd Disp: {f[4]} un | Status: {f[2]} | Local: Gaveta {f[3]}")

def realizar_retirada(id_usuario, nome_usuario, id_ferramenta, qtd_solicitada=1):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT nome, status, gaveta, quantidade FROM ferramenta WHERE id = ?", (id_ferramenta,))
    ferramenta = cursor.fetchone()
    
    if not ferramenta:
        print("❌ Erro: Ferramenta não encontrada no banco!")
        conexao.close()
        return {"erro": "Ferramenta não encontrada!"}
        
    qtd_atual = ferramenta[3]
    
    if qtd_atual < qtd_solicitada:
        print(f"❌ Erro: Quantidade solicitada indisponível! Estoque atual: {qtd_atual}")
        conexao.close()
        return {"erro": f"Quantidade indisponível! Estoque atual: {qtd_atual}"}

    nova_qtd = qtd_atual - qtd_solicitada
    novo_status = 'retirada' if nova_qtd == 0 else 'disponivel'

    cursor.execute("UPDATE ferramenta SET quantidade = ?, status = ? WHERE id = ?", (nova_qtd, novo_status, id_ferramenta))
    cursor.execute("INSERT INTO item (usuario_id, ferramenta_id, acao, quantidade_movimentada) VALUES (?, ?, 'retirou', ?)", (id_usuario, id_ferramenta, qtd_solicitada))
    
    conexao.commit()
    conexao.close()
    print(f"✨ Retirada concluída! Gaveta {ferramenta[2]} liberada para {nome_usuario} pegar {qtd_solicitada} un.")
    return {"sucesso": f"Retirada de {qtd_solicitada} unidade(s) concluída!"}

def realizar_devolucao(id_usuario, nome_usuario, id_ferramenta, qtd_devolvida=1):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
    cursor.execute("SELECT quantidade FROM ferramenta WHERE id = ?", (id_ferramenta,))
    ferramenta = cursor.fetchone()
    
    if not ferramenta:
        print("❌ Erro: Ferramenta inválida.")
        conexao.close()
        return {"erro": "Ferramenta não encontrada!"}
        
    nova_qtd = ferramenta[0] + qtd_devolvida

    cursor.execute("UPDATE ferramenta SET quantidade = ?, status = 'disponivel' WHERE id = ?", (nova_qtd, id_ferramenta))
    cursor.execute("INSERT INTO item (usuario_id, ferramenta_id, acao, quantidade_movimentada) VALUES (?, ?, 'devolveu', ?)", (id_usuario, id_ferramenta, qtd_devolvida))
    
    conexao.commit()
    conexao.close()
    print(f"✨ Devolução de {qtd_devolvida} unidade(s) do item ID {id_ferramenta} registrada por {nome_usuario}.")
    return {"sucesso": f"Devolução de {qtd_devolvida} unidade(s) registrada!"}

# =====================================================================
# MENUS DE ACESSO COMPLETOS PARA INTERFACE VIA TERMINAL
# =====================================================================

def menu_almoxarifado(id_user, nome_user):
    while True:
        print(f"\n🛠️ PAINEL ADMINISTRATIVO - ALMOXARIFADO | Login: {nome_user}")
        print("1. Ver Dashboard de Movimentações (Quem pegou / Devoluções)")
        print("2. Cadastrar Novo Item no Estoque")
        print("3. Atualizar Item Existente")
        print("4. Deletar Item do Estoque")
        print("0. Desconectar")
        
        op = input("Escolha a operação: ")
        if op == "1":
            dashboard_movimentacoes()
        elif op == "2":
            nome = input("Nome do item/ferramenta: ")
            gaveta = int(input("Número da gaveta física: "))
            qtd = int(input("Quantidade de itens: "))
            cadastrar_nova_ferramenta(nome, gaveta, qtd)
        elif op == "3":
            id_f = int(input("ID do item que deseja alterar: "))
            nome = input("Novo Nome: ")
            gaveta = int(input("Nova Gaveta: "))
            qtd = int(input("Nova Quantidade Total: "))
            atualizar_ferramenta(id_f, nome, gaveta, qtd)
        elif op == "4":
            id_f = int(input("ID do item para DELETAR para sempre: "))
            deletar_ferramenta(id_f)
        elif op == "0":
            break

def menu_chao_de_fabrica(id_user, nome_user):
    while True:
        print(f"\n🏭 PAINEL OPERACIONAL - CHÃO DE FÁBRICA | Login: {nome_user}")
        print("1. Visualizar Ferramentas e Status de Devolução")
        print("2. Pegar/Retirar um Item")
        print("3. Devolver um Item")
        print("0. Desconectar")
        
        op = input("Escolha a operação: ")
        if op == "1":
            visualizar_prazos_e_status()
        elif op == "2":
            visualizar_prazos_e_status()
            id_f = int(input("Digite o ID do item que vai retirar: "))
            qtd = int(input("Quantidade que deseja retirar: "))
            realizar_retirada(id_user, nome_user, id_f, qtd)
        elif op == "3":
            id_f = int(input("Digite o ID do item que está devolvendo: "))
            qtd = int(input("Quantidade que está devolvendo: "))
            realizar_devolucao(id_user, nome_user, id_f, qtd)
        elif op == "0":
            break

# =====================================================================
# FUNÇÃO AUXILIAR PARA ESCUTAR O LEITOR RFID FÍSICO
# =====================================================================
def ler_tag_rfid_serial():
    if not arduino:
        return None
    try:
        arduino.reset_input_buffer()
        time.sleep(0.5)
        if arduino.in_waiting > 0:
            linha = arduino.readline().decode('utf-8').strip()
            if linha:
                print(f"📡 Tag RFID capturada via Serial: {linha}")
                return linha
    except Exception as e:
        print(f"Erro ao ler dados da Serial: {e}")
    return None

if __name__ == "__main__":
    while True:
        print("\n=========================================")
        print("   SISTEMA DE CONTROLE DE ALMOXARIFADO   ")
        print("=========================================")
        if arduino:
            print(" [Aproxime seu cartão RFID físico do leitor]")
        print("Ou digite a matrícula manualmente para entrar (ou 'sair'):")
        
        entrada = ler_tag_rfid_serial()
        if not entrada:
            entrada = input("Acesso / Matrícula: ").strip()
            
        if entrada.lower() == 'sair':
            break
            
        usuario = buscar_usuario(entrada)
        if usuario:
            id_user, nome_user, cargo = usuario
            print(f"\n🔓 Acesso Concedido! Bem-vindo, {nome_user}.")
            if cargo == "almoxarifado":
                menu_almoxarifado(id_user, nome_user)
            elif cargo == "chao_de_fabrica":
                menu_chao_de_fabrica(id_user, nome_user)
        else:
            if entrada != "":
                print("❌ Erro: Usuário ou Cartão não cadastrado no sistema!")