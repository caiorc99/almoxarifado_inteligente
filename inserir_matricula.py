import sqlite3

NOME_BANCO = "almoxarifado.db"

def conectar_banco():
    return sqlite3.connect(NOME_BANCO)

def cadastrar_usuario(nome, matricula, cargo, senha=""):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuario (nome, matricula, cargo, senha) VALUES (?, ?, ?, ?)",
            (nome, matricula, cargo, senha),
        )
        conexao.commit()
        print(f"✅ Usuário '{nome}' [{cargo.upper()}] cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        print(f"⚠️ Erro: A matrícula '{matricula}' já está cadastrada.")
    finally:
        conexao.close()

if __name__ == "__main__":
    while True:
        print("\n=== GERENCIADOR DE MATRÍCULAS E ACESSOS ===")
        print("1. Inserir Novo Usuário Manualmente")
        print("2. Inserir Usuários de Teste Automaticamente")
        print("0. Sair")

        op = input("Escolha uma opção: ")

        if op == "1":
            nome = input("Digite o nome completo: ")
            mat = input("Digite a matrícula/RFID: ").strip()
            if nome == "" or mat == "":
                print("❌ Erro: Nome e Matrícula são obrigatórios!")
                continue

            print("\nEscolha o cargo:")
            print("1 - Chão de Fábrica (Usa o Armário)")
            print("2 - Almoxarifado (Administrador Remoto)")
            cargo_op = input("Opção: ")
            
            if cargo_op == "2":
                cargo = "almoxarifado"
                senha = input("Defina uma senha para este Administrador: ").strip()
            else:
                cargo = "chao_de_fabrica"
                senha = ""

            cadastrar_usuario(nome, mat, cargo, senha)

        elif op == "2":
            print("\nInserindo lote de testes...")
            cadastrar_usuario("Carlos Silva", "1001", "chao_de_fabrica")
            # Cria o admin de teste com login 'admin' (matrícula) e senha '1234'
            cadastrar_usuario("Ana Souza (Admin)", "admin", "almoxarifado", "1234")

        elif op == "0":
            break