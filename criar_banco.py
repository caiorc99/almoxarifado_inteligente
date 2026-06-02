import sqlite3  # importa o módulo nativo do Python para interagir com o banco de dados SQLite.

# Define a função principal responsável por estruturar o nosso banco de dados
def inicializar_banco():
    # Cria a conexão com o arquivo 'almoxarifado.db'. Se o arquivo não existir, ele é criado na hora
    conexao = sqlite3.connect("almoxarifado.db")
    # Cria um cursor, que funciona como um "intermediário" para enviar comandos SQL no banco.
    cursor = conexao.cursor()

    # Executa a criação da tabela 'usuario' incluindo o campo 'cargo'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            matricula TEXT UNIQUE NOT NULL,
            cargo TEXT NOT NULL DEFAULT 'chao_de_fabrica' -- 'almoxarifado' ou 'chao_de_fabrica'
        )
    ''')

    # Executa a criação da tabela 'ferramenta', com a coluna 'quantidade' para controle de volume
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS ferramenta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            status TEXT DEFAULT 'disponivel',
            gaveta INTEGER NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 1
        )
    ''')

    # Executa a criação da tabela 'item', que funciona como o histórico (log) de movimentações incluindo a quantidade
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            ferramenta_id INTEGER,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
            acao TEXT NOT NULL,
            quantidade_movimentada INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id),
            FOREIGN KEY (ferramenta_id) REFERENCES ferramenta(id)
        )
    ''')

    # Confirma e salva permanentemente no arquivo as alterações feitas no banco de dados.
    conexao.commit()
    # Fecha a conexão com o banco de dados para liberar memória e evitar corrupção de arquivo.
    conexao.close()
    # Mostra a mensagem de sucesso no terminal.
    print("Banco de dados e tabelas criados/atualizados com sucesso com suporte a volumes!")

# Verifica se este arquivo .py está sendo executado diretamente pelo usuário.
if __name__ == "__main__":
    # Chama a função para criar e configurar o banco de dados.
    inicializar_banco()