import sqlite3

def inicializar_banco():
    conexao = sqlite3.connect("almoxarifado.db")
    cursor = conexao.cursor()

    # Adicionado o campo 'senha' com valor padrão vazio
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            matricula TEXT UNIQUE NOT NULL,
            cargo TEXT NOT NULL DEFAULT 'chao_de_fabrica', -- 'almoxarifado' ou 'chao_de_fabrica'
            senha TEXT DEFAULT ''
        )
    ''')

    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS ferramenta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            status TEXT DEFAULT 'disponivel',
            gaveta INTEGER NOT NULL,
            quantidade REAL NOT NULL DEFAULT 1.0,
            tipo TEXT NOT NULL DEFAULT 'reutilizavel'
        )
    ''')

    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            ferramenta_id INTEGER,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
            acao TEXT NOT NULL,
            quantidade_movimentada REAL NOT NULL DEFAULT 1.0,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id),
            FOREIGN KEY (ferramenta_id) REFERENCES ferramenta(id)
        )
    ''')

    conexao.commit()
    conexao.close()
    print("✅ Banco de dados atualizado com suporte a senhas administrativas!")

if __name__ == "__main__":
    inicializar_banco()