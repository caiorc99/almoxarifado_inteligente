import sqlite3

NOME_BANCO = "almoxarifado.db"


def consultar_matricula(matricula_procurada):
    # 1. Conecta ao banco de dados existente
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()

    # 2. Executa a busca garantindo que a matrícula seja tratada como TEXTO (com aspas)
    cursor.execute(
        "SELECT id, nome, matricula FROM usuario WHERE matricula = ?",
        (str(matricula_procurada),),
    )
    usuario = cursor.fetchone()

    conexao.close()
    return usuario


def listar_todos_os_usuarios():
    """Função para listar tudo o que existe na tabela de usuários."""
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()

    cursor.execute("SELECT id, nome, matricula FROM usuario")
    usuarios = cursor.fetchall()

    conexao.close()
    return usuarios


# =====================================================================
# EXECUÇÃO DO TESTE de CONSULTA
# =====================================================================
if __name__ == "__main__":
    print("=== TELA DE CONSULTA DE MATRÍCULAS ===")

    # PASSO 1: Mostrar tudo o que REALMENTE está salvo no banco
    print("\n1. Verificando quem está cadastrado no banco de dados...")
    todos = listar_todos_os_usuarios()

    if not todos:
        print(
            "⚠️ O banco está VAZIO! Nenhuma matrícula foi encontrada na tabela 'usuario'."
        )
        print("-> Rode o arquivo 'inserir_matricula.py' primeiro!")
    else:
        print("Usuários encontrados no arquivo .db:")
        for u in todos:
            print(f"   - ID: {u[0]} | Nome: {u[1]} | Matrícula: {u[2]}")

        # PASSO 2: Testar a busca individual
        print("\n2. Testando a busca por uma matrícula específica...")
        mat = input("Digite uma matrícula para buscar (Ex: 1001): ")

        resultado = consultar_matricula(mat)

        if resultado:
            print(
                f"✅ Encontrado com sucesso! ID: {resultado[0]} | Nome: {resultado[1]} | Matrícula: {resultado[2]}"
            )
        else:
            print(
                f"❌ Erro: A matrícula '{mat}' NÃO foi encontrada no sistema."
            )