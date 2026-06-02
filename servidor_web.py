import http.server
import json
import socketserver
import urllib.parse
from sistema import (
    atualizar_ferramenta,
    buscar_usuario,
    cadastrar_nova_ferramenta,
    conectar_banco,
    deletar_ferramenta,
    realizar_devolucao,
    realizar_retirada,
)

PORT = 8080

INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Almoxarifado Inteligente - Quantidades</title>
    <style>
        :root {
            --bg-principal: #0a0a0a;
            --bg-card: #141414;
            --bg-input: #1f1f1f;
            --txt-principal: #ffffff;
            --txt-secundario: #a0a0a0;
            --borda: #2d2d2d;
            --borda-foco: #555555;
            --destaque: #ffffff;
            --destaque-txt: #000000;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; transition: all 0.2s ease; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background-color: var(--bg-principal);
            color: var(--txt-principal);
            padding: 40px 20px;
        }

        .container { max-width: 1000px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 40px; }
        header h1 { font-size: 2.2rem; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; }
        header p { color: var(--txt-secundario); }

        .card {
            background-color: var(--bg-card);
            border: 1px solid var(--borda);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }

        h2 { font-size: 1.3rem; margin-bottom: 20px; text-transform: uppercase; border-left: 3px solid var(--destaque); padding-left: 12px; }
        label { display: block; font-size: 0.85rem; color: var(--txt-secundario); margin-bottom: 6px; text-transform: uppercase; }
        p { color: var(--txt-secundario); margin-bottom: 15px; }

        .input-group { display: flex; gap: 12px; margin-bottom: 15px; }
        input {
            flex: 1; background-color: var(--bg-input); color: var(--txt-principal);
            border: 1px solid var(--borda); border-radius: 6px; padding: 12px 16px; font-size: 0.95rem;
        }
        input:focus { outline: none; border-color: var(--borda-foco); background-color: #252525; }

        button {
            background-color: var(--destaque); color: var(--destaque-txt); border: none;
            border-radius: 6px; padding: 12px 24px; font-size: 0.95rem; font-weight: 600; cursor: pointer;
        }
        button:hover { opacity: 0.9; transform: translateY(-1px); }
        button.secundario { background-color: transparent; color: var(--txt-principal); border: 1px solid var(--borda); }
        button.secundario:hover { background-color: var(--bg-input); }
        button.perigo { background-color: #1a1a1a; color: #ff4444; border: 1px solid #331111; }
        button.perigo:hover { background-color: #ff4444; color: #ffffff; }

        table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 10px; }
        th, td { padding: 14px 16px; text-align: left; border-bottom: 1px solid var(--borda); }
        th { background-color: #1a1a1a; color: var(--txt-secundario); font-size: 0.8rem; text-transform: uppercase; }
        tr:hover td { background-color: #171717; }

        .hidden { display: none !important; }
        .badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
        .badge.disponivel { background-color: #1c281c; color: #7cd97c; border: 1px solid #2e4a2e; }
        .badge.retirado { background-color: #2c1a1a; color: #ff8888; border: 1px solid #5a2a2a; }

        #userInfo { display: flex; justify-content: space-between; align-items: center; background-color: #111; border: 1px solid var(--borda); border-radius: 8px; padding: 16px 24px; margin-bottom: 30px; }
        #userInfo span { font-weight: 700; color: var(--destaque); }
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>Almoxarifado Inteligente</h1>
        <p>Controle de Fluxo e Volume de Inventário</p>
    </header>

    <div id="view-login" class="card">
        <h2>Identificação</h2>
        <p>Insira sua matrícula administrativa ou operacional:</p>
        <div class="input-group">
            <input type="text" id="input-matricula" placeholder="Ex: 1001 ou 2002" onkeypress="if(event.key==='Enter') fazerLogin()">
            <button onclick="fazerLogin()">Acessar</button>
        </div>
        <div id="login-erro" style="color: #ff4444;" class="hidden">⚠️ Matrícula inválida.</div>
    </div>

    <div id="view-painel" class="hidden">
        <div id="userInfo">
            <div>Operador: <span id="user-nome">---</span> <span id="user-cargo" style="font-size:0.8rem; padding: 2px 8px; background:#222; border-radius:4px; margin-left:8px; color:#aaa;">---</span></div>
            <button class="secundario" onclick="desconectar()">Sair</button>
        </div>

        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2>Estoque Atual</h2>
                <button class="secundario" onclick="carregarFerramentas()">🔄 Atualizar</button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Ferramenta</th>
                        <th>Localização</th>
                        <th>Qtd em Estoque</th>
                        <th>Status</th>
                        <th style="text-align: right;">Operação por Volume</th>
                    </tr>
                </thead>
                <tbody id="tabela-corpo"></tbody>
            </table>
        </div>

        <div id="bloco-almoxarifado" class="hidden">
            <div class="card">
                <h2 id="titulo-form">Cadastrar Item com Volume</h2>
                <input type="hidden" id="form-id">
                <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 16px; margin-bottom: 20px;">
                    <div>
                        <label>Nome do Ativo</label>
                        <input type="text" id="form-nome" placeholder="Ex: Chave Philips">
                    </div>
                    <div>
                        <label>Gaveta</label>
                        <input type="number" id="form-gaveta" placeholder="Ex: 3">
                    </div>
                    <div>
                        <label>Quantidade Inicial</label>
                        <input type="number" id="form-quantidade" value="1" min="1">
                    </div>
                </div>
                <button id="btn-salvar" onclick="salvarFerramenta()">Salvar Item</button>
                <button id="btn-cancelar" class="secundario hidden" onclick="limparFormulario()">Cancelar</button>
            </div>

            <div class="card">
                <h2>Histórico de Volumes Movimentados</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Operador</th>
                            <th>Ferramenta</th>
                            <th>Data / Hora</th>
                            <th>Qtd</th>
                            <th style="text-align: right;">Ação</th>
                        </tr>
                    </thead>
                    <tbody id="tabela-logs-corpo"></tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
    let usuarioLogado = null;

    async function fazerLogin() {
        const mat = document.getElementById('input-matricula').value.trim();
        if(!mat) return;
        const response = await fetch(`/api/login?matricula=${mat}`);
        const data = await response.json();
        
        if(data.erro) {
            document.getElementById('login-erro').classList.remove('hidden');
        } else {
            usuarioLogado = data;
            document.getElementById('login-erro').classList.add('hidden');
            document.getElementById('view-login').classList.add('hidden');
            document.getElementById('view-painel').classList.remove('hidden');
            document.getElementById('user-nome').innerText = data.nome;
            document.getElementById('user-cargo').innerText = data.cargo === 'almoxarifado' ? 'Admin' : 'Operador';
            
            if(data.cargo === 'almoxarifado') {
                document.getElementById('bloco-almoxarifado').classList.remove('hidden');
                carregarLogs();
            } else {
                document.getElementById('bloco-almoxarifado').classList.add('hidden');
            }
            carregarFerramentas();
        }
    }

    function desconectar() {
        usuarioLogado = null;
        document.getElementById('view-login').classList.remove('hidden');
        document.getElementById('view-painel').classList.add('hidden');
        document.getElementById('input-matricula').value = '';
    }

    async function carregarFerramentas() {
        const response = await fetch('/api/ferramentas');
        const ferramentas = await response.json();
        const tbody = document.getElementById('tabela-corpo');
        tbody.innerHTML = '';

        ferramentas.forEach(f => {
            const [id, nome, status, gaveta, quantidade] = f;
            let acoesHtml = '';
            
            if(usuarioLogado.cargo === 'chao_de_fabrica') {
                acoesHtml = `
                    <div style="display: flex; gap: 6px; justify-content: flex-end; align-items: center;">
                        <input type="number" id="qtd-acao-${id}" value="1" min="1" max="${quantidade || 100}" style="max-width: 70px; padding: 6px 8px;">
                        <button onclick="movimentar(${id}, 'retirar')" style="padding: 6px 12px; font-size:0.85rem;">Retirar</button>
                        <button class="secundario" onclick="movimentar(${id}, 'devolver')" style="padding: 6px 12px; font-size:0.85rem;">Devolver</button>
                    </div>
                `;
            } else {
                acoesHtml = `
                    <div style="text-align: right;">
                        <button class="secundario" onclick="editarFerramenta(${id}, '${nome}', ${gaveta}, ${quantidade})" style="padding: 6px 12px; font-size: 0.8rem;">Editar</button>
                        <button class="perigo" onclick="deletarFerramentaDoEstoque(${id})" style="padding: 6px 12px; font-size: 0.8rem;">Excluir</button>
                    </div>
                `;
            }

            const badgeClass = quantidade > 0 ? 'disponivel' : 'retirado';
            const badgeTexto = quantidade > 0 ? 'Em Estoque' : 'Esgotado';

            tbody.innerHTML += `
                <tr>
                    <td><code>#${id}</code></td>
                    <td><strong>${nome}</strong></td>
                    <td>Gaveta ${gaveta}</td>
                    <td><strong>${quantidade} un</strong></td>
                    <td><span class="badge ${badgeClass}">${badgeTexto}</span></td>
                    <td>${acoesHtml}</td>
                </tr>
            `;
        });
    }

    async function movimentar(id, acao) {
        const qtdInput = document.getElementById(`qtd-acao-${id}`);
        const qtd = parseInt(qtdInput.value) || 1;

        const response = await fetch('/api/movimentacao', {
            method: 'POST',
            body: JSON.stringify({ id_usuario: usuarioLogado.id, nome_usuario: usuarioLogado.nome, id_ferramenta: id, acao: acao, quantidade: qtd })
        });
        const resData = await response.json();
        if (resData.erro) alert(resData.erro);
        
        carregarFerramentas();
    }

    async function carregarLogs() {
        const response = await fetch('/api/logs');
        const logs = await response.json();
        const tbody = document.getElementById('tabela-logs-corpo');
        tbody.innerHTML = '';
        logs.forEach(l => {
            const acaoMarcada = l[3] === 'retirou' 
                ? `<span style="color:#ff8888; font-weight:600;">⚠️ RETIROU</span>` 
                : `<span style="color:#7cd97c; font-weight:600;">✅ DEVOLVEU</span>`;
            tbody.innerHTML += `
                <tr>
                    <td>${l[0]}</td>
                    <td><strong>${l[1]}</strong></td>
                    <td style="color: var(--txt-secundario); font-size:0.85rem;">${l[2]}</td>
                    <td>${l[4]} un</td>
                    <td style="text-align: right;">${acaoMarcada}</td>
                </tr>
            `;
        });
    }

    async function salvarFerramenta() {
        const id = document.getElementById('form-id').value;
        const nome = document.getElementById('form-nome').value;
        const gaveta = document.getElementById('form-gaveta').value;
        const quantidade = document.getElementById('form-quantidade').value;
        
        if(!nome || !gaveta || !quantidade) return alert('Preencha os dados!');

        await fetch('/api/salvar-ferramenta', { 
            method: 'POST', 
            body: JSON.stringify({ id, nome, gaveta, quantidade }) 
        });
        
        limparFormulario();
        carregarFerramentas();
        carregarLogs();
    }

    function editarFerramenta(id, nome, gaveta, quantidade) {
        document.getElementById('form-id').value = id;
        document.getElementById('form-nome').value = nome;
        document.getElementById('form-gaveta').value = gaveta;
        document.getElementById('form-quantidade').value = quantidade;
        
        document.getElementById('titulo-form').innerText = "Modificar Item";
        document.getElementById('btn-cancelar').classList.remove('hidden');
    }

    async function deletarFerramentaDoEstoque(id) {
        if(confirm("Remover este item permanente?")) {
            await fetch('/api/deletar-ferramenta', { method: 'POST', body: JSON.stringify({ id }) });
            carregarFerramentas();
            carregarLogs();
        }
    }

    function limparFormulario() {
        document.getElementById('form-id').value = '';
        document.getElementById('form-nome').value = '';
        document.getElementById('form-gaveta').value = '';
        document.getElementById('form-quantidade').value = '1';
        document.getElementById('titulo-form').innerText = "Cadastrar Item com Volume";
        document.getElementById('btn-cancelar').classList.add('hidden');
    }
</script>
</body>
</html>
"""

class AlmoxarifadoAPIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url_parseada = urllib.parse.urlparse(self.path)
        
        if url_parseada.path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(INTERFACE_HTML.encode('utf-8'))
            return
            
        if url_parseada.path == "/api/login":
            parametros = urllib.parse.parse_qs(url_parseada.query)
            matricula = parametros.get('matricula', [''])[0]
            usuario = buscar_usuario(matricula)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resposta = {"id": usuario[0], "nome": usuario[1], "cargo": usuario[2]} if usuario else {"erro": "Invalido"}
            self.wfile.write(json.dumps(resposta).encode('utf-8'))
            return

        if url_parseada.path == "/api/ferramentas":
            conexao = conectar_banco()
            cursor = conexao.cursor()
            # MODIFICADO: Busca também a coluna quantidade
            cursor.execute("SELECT id, nome, status, gaveta, quantidade FROM ferramenta")
            ferramentas = cursor.fetchall()
            conexao.close()
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(ferramentas).encode('utf-8'))
            return

        if url_parseada.path == "/api/logs":
            conexao = conectar_banco()
            cursor = conexao.cursor()
            # MODIFICADO: Busca também a quantidade movimentada no histórico
            cursor.execute('''
                SELECT usuario.nome, ferramenta.nome, item.data_hora, item.acao, item.quantidade_movimentada 
                FROM item
                INNER JOIN usuario ON item.usuario_id = usuario.id
                INNER JOIN ferramenta ON item.ferramenta_id = ferramenta.id
                ORDER BY item.data_hora DESC
            ''')
            logs = cursor.fetchall()
            conexao.close()
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(logs).encode('utf-8'))
            return

        super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        dados = json.loads(post_data.decode('utf-8'))

        if self.path == "/api/movimentacao":
            id_usuario = dados['id_usuario']
            nome_usuario = dados['nome_usuario']
            id_ferramenta = dados['id_ferramenta']
            acao = dados['acao']
            quantidade = int(dados['quantidade'])

            if acao == 'retirar':
                res = realizar_retirada(id_usuario, nome_usuario, id_ferramenta, quantidade)
            elif acao == 'devolver':
                res = realizar_devolucao(id_usuario, nome_usuario, id_ferramenta, quantidade)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        if self.path == "/api/salvar-ferramenta":
            id_f = dados.get('id')
            nome = dados['nome']
            gaveta = int(dados['gaveta'])
            quantidade = int(dados['quantidade'])

            if id_f:
                atualizar_ferramenta(int(id_f), nome, gaveta, quantidade)
            else:
                cadastrar_nova_ferramenta(nome, gaveta, quantidade)

            self.responder_sucesso()
            return

        if self.path == "/api/deletar-ferramenta":
            id_f = int(dados['id'])
            deletar_ferramenta(id_f)
            self.responder_sucesso()
            return

    def responder_sucesso(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "sucesso"}).encode('utf-8'))

with socketserver.TCPServer(("", PORT), AlmoxarifadoAPIHandler) as httpd:
    print(f"🚀 Servidor com controle de Volume rodando em: http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor finalizado.")