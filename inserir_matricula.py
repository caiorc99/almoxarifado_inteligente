import sqlite3

# Nome do arquivo do banco que você criou no primeiro script
NOME_BANCO = "almoxarifado.db"


def conectar_banco():
    """Abre a conexão com o arquivo de banco de dados existente."""
    return sqlite3.connect(NOME_BANCO)


def cadastrar_usuario(nome, matricula, cargo):
    """Conecta no banco e insere um novo usuário com sua matrícula e cargo."""
    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        # Executa o comando SQL incluindo o novo campo 'cargo' na tabela 'usuario'
        cursor.execute(
            "INSERT INTO usuario (nome, matricula, cargo) VALUES (?, ?, ?)",
            (nome, matricula, cargo),
        )

        # Confirma e salva a inserção de forma permanente no arquivo .db
        conexao.commit()
        print(f"✅ Usuário '{nome}' [{cargo.upper()}] cadastrado com sucesso!")

    except sqlite3.IntegrityError:
        # O SQLite aciona esse erro automaticamente se a matrícula já existir (regra do UNIQUE)
        print(f"⚠️ Erro: A matrícula '{matricula}' já está cadastrada no sistema.")

    finally:
        # Fecha a conexão para liberar o arquivo do banco de dados
        conexao.close()


# =====================================================================
# INTERFACE VIA TERMINAL para você inserir as matrículas
# =====================================================================
if __name__ == "__main__":
    print("=== CADASTRO COM CONTROLE DE CARGOS ===")

    while True:
        print("\n1. Cadastrar Usuário Manualmente")
        print("2. Inserir Usuários de Teste Automaticamente")
        print("0. Sair")

        op = input("Escolha uma opção: ")

        if op == "1":
            nome = input("Digite o nome completo do funcionário: ")
            mat = input("Digite a matrícula/RFID do funcionário: ").strip()
            
            # Validação simples para não aceitar campos em branco
            if nome == "" or mat == "":
                print("❌ Erro: Nome e Matrícula não podem ficar em branco!")
                continue

            print("\nEscolha o cargo:")
            print("1 - Chão de Fábrica")
            print("2 - Almoxarifado")
            cargo_op = input("Opção: ")
            
            # Se digitar 2 vira almoxarifado, qualquer outra coisa define como chao_de_fabrica por padrão
            cargo = "almoxarifado" if cargo_op == "2" else "chao_de_fabrica"
            
            cadastrar_usuario(nome, mat, cargo)

        elif op == "2":
            print("\nInserindo lote de testes com cargos diferentes...")
            # Criando um de cada cargo para você testar os dois menus diferentes no sistema.py
            cadastrar_usuario("Carlos Silva", "1001", "chao_de_fabrica")
            cadastrar_usuario("Ana Souza (Admin)", "2002", "almoxarifado")

        elif op == "0":
            print("Encerrando o programa de cadastro. Até logo!")
            break
        else:
            print("Opção inválida! Tente novamente.")