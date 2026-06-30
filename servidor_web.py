import http.server
import json
import socketserver
import urllib.parse
import sistema 

PORT = 8081

INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Almoxarifado Inteligente - ESP32 Control</title>
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
            background-color: var(--bg-principal); color: var(--txt-principal); padding: 40px 20px;
        }
        .container { max-width: 1100px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 40px; }
        header h1 { font-size: 2.2rem; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; }
        .card { background-color: var(--bg-card); border: 1px solid var(--borda); border-radius: 12px; padding: 30px; margin-bottom: 30px; }
        h2 { font-size: 1.3rem; margin-bottom: 20px; text-transform: uppercase; border-left: 3px solid var(--destaque); padding-left: 12px; }
        label { display: block; font-size: 0.85rem; color: var(--txt-secundario); margin-bottom: 6px; text-transform: uppercase; }
        input, select {
            width: 100%; background-color: var(--bg-input); color: var(--txt-principal);
            border: 1px solid var(--borda); border-radius: 6px; padding: 12px 16px; font-size: 0.95rem; margin-bottom: 10px;
        }
        button {
            background-color: var(--destaque); color: var(--destaque-txt); border: none;
            border-radius: 6px; padding: 12px 24px; font-size: 0.95rem; font-weight: 600; cursor: pointer;
        }
        button:hover { opacity: 0.9; }
        button.secundario { background-color: transparent; color: var(--txt-principal); border: 1px solid var(--borda); }
        button.perigo { background-color: #1a1a1a; color: #ff4444; border: 1px solid #331111; }
        button.perigo:hover { background-color: #ff4444; color: #ffffff; }
        table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 10px; }
        th, td { padding: 14px 16px; text-align: left; border-bottom: 1px solid var(--borda); }
        th { background-color: #1a1a1a; color: var(--txt-secundario); font-size: 0.8rem; text-transform: uppercase; }
        .hidden { display: none !important; }
        .badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
        .badge.reutilizavel { background-color: #1c281c; color: #7cd97c; border: 1px solid #2e4a2e; }
        .badge.consumivel { background-color: #2a2015; color: #ffb86c; border: 1px solid #44301a; }
        #userInfo { display: flex; justify-content: space-between; align-items: center; background-color: #111; border: 1px solid var(--borda); border-radius: 8px; padding: 16px 24px; margin-bottom: 30px; }
        #userInfo span { font-weight: 700; color: var(--destaque); }
        
        /* Abas de Login */
        .login-tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { flex: 1; padding: 12px; background: #111; border: 1px solid var(--borda); color: var(--txt-secundario); border-radius: 6px; font-weight: bold; cursor: pointer; }
        .tab-btn.active { background: var(--destaque); color: var(--destaque-txt); border-color: var(--destaque); }
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>Almoxarifado Inteligente ESP32</h1>
        <p>Controle Automatizado de Insumos por Balança e Sensores de Porta</p>
        <div id="peso-live" style="margin-top: 15px; font-weight: bold; color: #ffb86c;">⚖️ Peso Ativo do Armário: <span id="peso-val">0.0</span>g</div>
    </header>

    <div id="view-login" class="card" style="max-width: 500px; margin: 0 auto 30px auto;">
        <div class="login-tabs">
            <button id="tab-op" class="tab-btn active" onclick="alternarAba('operador')"> Operador (Chão de Fábrica)</button>
            <button id="tab-adm" class="tab-btn" onclick="alternarAba('admin')"> Administrador (Sala)</button>
        </div>

        <div id="form-login-operador">
            <h2>Identificação do Operador</h2>
            <label>Matrícula ou Proximidade RFID</label>
            <input type="text" id="input-matricula" placeholder="Aproxime a Tag RFID ou digite a Matrícula">
            <button onclick="fazerLoginOperador()" style="width: 100%; margin-top: 10px;">Entrar no Sistema</button>
        </div>

        <div id="form-login-admin" class="hidden">
            <h2>Login Administrativo Remoto</h2>
            <label>Usuário / Matrícula Admin</label>
            <input type="text" id="input-admin-user" placeholder="Ex: admin">
            <label>Senha de Acesso</label>
            <input type="password" id="input-admin-pass" placeholder="••••••••">
            <button onclick="fazerLoginAdmin()" style="width: 100%; margin-top: 10px;">Autenticar Admin</button>
        </div>

        <div id="login-erro" style="color: #ff4444; margin-top: 15px; text-align: center;" class="hidden">⚠️ Credenciais incorretas ou não localizadas.</div>
    </div>

    <div id="view-painel" class="hidden">
        <div id="userInfo">
            <div>Usuário Conectado: <span id="user-nome">---</span> (<span id="user-cargo">---</span>)</div>
            <button class="secundario" onclick="desconectar()">Sair / Desconectar</button>
        </div>

        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2>Inventário de Itens</h2>
                <button class="secundario" onclick="carregarFerramentas()">🔄 Atualizar Dados</button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Descrição do Ativo</th>
                        <th>Localização</th>
                        <th>Saldo Estoque</th>
                        <th>Categoria</th>
                        <th style="text-align: right;">Ação</th>
                    </tr>
                </thead>
                <tbody id="tabela-corpo"></tbody>
            </table>
        </div>

        <div id="bloco-almoxarifado" class="hidden">
            <div class="card">
                <h2 id="titulo-form">Gerenciar Cadastro de Item</h2>
                <input type="hidden" id="form-id">
                <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 16px; margin-bottom: 20px;">
                    <div>
                        <label>Nome do Item</label>
                        <input type="text" id="form-nome" placeholder="Ex: Porca Sextavada 1/4">
                    </div>
                    <div>
                        <label>Gaveta Fís.</label>
                        <input type="number" id="form-gaveta" placeholder="Ex: 2">
                    </div>
                    <div>
                        <label>Qtd / Volume</label>
                        <input type="number" step="0.1" id="form-quantidade" value="10">
                    </div>
                    <div>
                        <label>Categoria</label>
                        <select id="form-tipo">
                            <option value="reutilizavel">Reutilizável (Porta 1)</option>
                            <option value="consumivel">Consumível (Porta 2 / Peso)</option>
                        </select>
                    </div>
                </div>
                <button id="btn-salvar" onclick="saveFerramenta()">Gravar Dados</button>
                <button id="btn-cancelar" class="secundario hidden" onclick="limparFormulario()">Cancelar</button>
            </div>

            <div class="card">
                <h2>Histórico Consolidado de Auditoria</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Colaborador</th>
                            <th>Item Retirado</th>
                            <th>Data / Horário</th>
                            <th>Volume</th>
                            <th style="text-align: right;">Evento</th>
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
    let abaAtual = 'operador';

    function alternarAba(aba) {
        abaAtual = aba;
        document.getElementById('login-erro').classList.add('hidden');
        if (aba === 'operador') {
            document.getElementById('tab-op').classList.add('active');
            document.getElementById('tab-adm').classList.remove('active');
            document.getElementById('form-login-operador').classList.remove('hidden');
            document.getElementById('form-login-admin').classList.add('hidden');
        } else {
            document.getElementById('tab-op').classList.remove('active');
            document.getElementById('tab-adm').classList.add('active');
            document.getElementById('form-login-operador').classList.add('hidden');
            document.getElementById('form-login-admin').classList.remove('hidden');
        }
    }

    // Monitora constantemente o RFID e o peso do ESP32
    setInterval(async () => {
        const resPeso = await fetch('/api/peso-atual');
        const dataPeso = await resPeso.json();
        document.getElementById('peso-val').innerText = dataPeso.peso.toFixed(2);

        // Só tenta logar via RFID se estiver na aba do operador e deslogado
        if (!usuarioLogado && abaAtual === 'operador') {
            const response = await fetch('/api/check-rfid');
            const data = await response.json();
            if (data.tag) {
                document.getElementById('input-matricula').value = data.tag;
                fazerLoginOperador();
            }
        }
    }, 800);

    async function fazerLoginOperador() {
        const mat = document.getElementById('input-matricula').value.trim();
        if(!mat) return;
        const response = await fetch(`/api/login?matricula=${mat}`);
        const data = await response.json();
        
        if(data.erro) {
            document.getElementById('login-erro').classList.remove('hidden');
        } else {
            entrarNoPainel(data);
        }
    }

    async function fazerLoginAdmin() {
        const user = document.getElementById('input-admin-user').value.trim();
        const pass = document.getElementById('input-admin-pass').value.trim();
        
        if(!user || !pass) return alert("Preencha o usuário e a senha!");

        const response = await fetch('/api/login-admin', {
            method: 'POST',
            body: JSON.stringify({ usuario: user, senha: pass })
        });
        const data = await response.json();

        if (data.erro) {
            document.getElementById('login-erro').classList.remove('hidden');
        } else {
            entrarNoPainel(data);
        }
    }

    function entrarNoPainel(data) {
        usuarioLogado = data;
        document.getElementById('login-erro').classList.add('hidden');
        document.getElementById('view-login').classList.add('hidden');
        document.getElementById('view-painel').classList.remove('hidden');
        document.getElementById('user-nome').innerText = data.nome;
        document.getElementById('user-cargo').innerText = data.cargo === 'almoxarifado' ? 'Administrador' : 'Chão de Fábrica';
        
        if(data.cargo === 'almoxarifado') {
            document.getElementById('bloco-almoxarifado').classList.remove('hidden');
            carregarLogs();
        } else {
            document.getElementById('bloco-almoxarifado').classList.add('hidden');
        }
        carregarFerramentas();
    }

    function desconectar() {
        usuarioLogado = null;
        document.getElementById('view-login').classList.remove('hidden');
        document.getElementById('view-painel').classList.add('hidden');
        document.getElementById('input-matricula').value = '';
        document.getElementById('input-admin-user').value = '';
        document.getElementById('input-admin-pass').value = '';
        alternarAba('operador');
    }

    async function carregarFerramentas() {
        const response = await fetch('/api/ferramentas');
        const ferramentas = await response.json();
        const tbody = document.getElementById('tabela-corpo');
        tbody.innerHTML = '';

        ferramentas.forEach(f => {
            const [id, nome, status, gaveta, quantidade, tipo] = f;
            let acoesHtml = '';
            
            if(usuarioLogado.cargo === 'chao_de_fabrica') {
                acoesHtml = `
                    <div style="text-align: right;">
                        <button onclick="solicitarAbertura(${id})" style="padding: 8px 16px; background-color: #222; color: #fff; border: 1px solid #444;">🔓 Solicitar Abertura</button>
                    </div>
                `;
            } else {
                acoesHtml = `
                    <div style="text-align: right;">
                        <button class="secundario" onclick="editarFerramenta(${id}, '${nome}', ${gaveta}, ${quantidade}, '${tipo}')" style="padding: 6px 12px; font-size: 0.8rem;">Modificar</button>
                        <button class="perigo" onclick="deletarItem(${id})" style="padding: 6px 12px; font-size: 0.8rem;">Excluir</button>
                    </div>
                `;
            }

            const badgeStyle = tipo === 'consumivel' ? 'consumivel' : 'reutilizavel';
            const displayQtd = tipo === 'consumivel' ? `${quantidade} un` : (quantidade > 0 ? "Disponível" : "Indisponível");

            tbody.innerHTML += `
                <tr>
                    <td><code>#${id}</code></td>
                    <td><strong>${nome}</strong></td>
                    <td>Gaveta ${gaveta}</td>
                    <td>${displayQtd}</td>
                    <td><span class="badge ${badgeStyle}">${tipo}</span></td>
                    <td>${acoesHtml}</td>
                </tr>
            `;
        });
    }

    async function solicitarAbertura(id) {
        const response = await fetch('/api/movimentacao', {
            method: 'POST',
            body: JSON.stringify({ id_usuario: usuarioLogado.id, id_ferramenta: id })
        });
        const resData = await response.json();
        if (resData.erro) {
            alert("❌ Erro: " + resData.erro);
        } else {
            alert("✅ Sucesso: " + resData.sucesso);
        }
        carregarFerramentas();
    }

    async function carregarLogs() {
        const response = await fetch('/api/logs');
        const logs = await response.json();
        const tbody = document.getElementById('tabela-logs-corpo');
        tbody.innerHTML = '';
        logs.forEach(l => {
            const tagAcao = l[3] === 'retirou' 
                ? `<span style="color:#ffb86c; font-weight:600;">RETIROU</span>` 
                : `<span style="color:#7cd97c; font-weight:600;">DEVOLVEU</span>`;
            tbody.innerHTML += `
                <tr>
                    <td>${l[0]}</td>
                    <td><strong>${l[1]}</strong></td>
                    <td style="color: var(--txt-secundario); font-size:0.85rem;">${l[2]}</td>
                    <td>${l[4]} un</td>
                    <td style="text-align: right;">${tagAcao}</td>
                </tr>
            `;
        });
    }

    async function saveFerramenta() {
        const id = document.getElementById('form-id').value;
        const nome = document.getElementById('form-nome').value;
        const gaveta = document.getElementById('form-gaveta').value;
        const quantidade = document.getElementById('form-quantidade').value;
        const tipo = document.getElementById('form-tipo').value;
        
        if(!nome || !gaveta) return alert('Campos obrigatórios ausentes!');

        await fetch('/api/salvar-ferramenta', { 
            method: 'POST', 
            body: JSON.stringify({ id, nome, gaveta, quantidade, tipo }) 
        });
        
        limparFormulario();
        carregarFerramentas();
        carregarLogs();
    }

    function editarFerramenta(id, nome, gaveta, quantidade, tipo) {
        document.getElementById('form-id').value = id;
        document.getElementById('form-nome').value = nome;
        document.getElementById('form-gaveta').value = gaveta;
        document.getElementById('form-quantidade').value = quantidade;
        document.getElementById('form-tipo').value = tipo;
        
        document.getElementById('titulo-form').innerText = "Atualizar Configurações do Item";
        document.getElementById('btn-cancelar').classList.remove('hidden');
    }

    async function deletarItem(id) {
        if(confirm("Deseja expurgar este item permanentemente do banco relacional?")) {
            await fetch('/api/deletar-ferramenta', { method: 'POST', body: JSON.stringify({ id }) });
            carregarFerramentas();
            carregarLogs();
        }
    }

    function limparFormulario() {
        document.getElementById('form-id').value = '';
        document.getElementById('form-nome').value = '';
        document.getElementById('form-gaveta').value = '';
        document.getElementById('form-quantidade').value = '1.0';
        document.getElementById('titulo-form').innerText = "Gerenciar Cadastro de Item";
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
            usuario = sistema.buscar_usuario(matricula)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            if usuario:
                resposta = {"id": usuario[0], "nome": usuario[1], "cargo": usuario[2]}
            else:
                resposta = {"erro": "Invalido"}
                sistema.enviar_comando_hardware("ACESSO_NEGADO")
                
            self.wfile.write(json.dumps(resposta).encode('utf-8'))
            return

        if url_parseada.path == "/api/check-rfid":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            tag = sistema.obter_e_limpar_tag()
            self.wfile.write(json.dumps({"tag": tag}).encode('utf-8'))
            return

        if url_parseada.path == "/api/peso-atual":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            peso = sistema.obter_peso_atual()
            self.wfile.write(json.dumps({"peso": peso}).encode('utf-8'))
            return

        if url_parseada.path == "/api/ferramentas":
            conexao = sistema.conectar_banco()
            cursor = conexao.cursor()
            cursor.execute("SELECT id, nome, status, gaveta, quantidade, tipo FROM ferramenta")
            ferramentas = cursor.fetchall()
            conexao.close()
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(ferramentas).encode('utf-8'))
            return

        if url_parseada.path == "/api/logs":
            conexao = sistema.conectar_banco()
            cursor = conexao.cursor()
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

        # NOVA ROTA: Tratamento de Login Administrativo com Senha Relacional
        if self.path == "/api/login-admin":
            user = dados.get('usuario', '')
            passw = dados.get('senha', '')
            
            admin_usuario = sistema.buscar_administrador_por_senha(user, passw)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            if admin_usuario:
                resposta = {"id": admin_usuario[0], "nome": admin_usuario[1], "cargo": admin_usuario[2]}
            else:
                resposta = {"erro": "Acesso Administrativo Recusado"}
                
            self.wfile.write(json.dumps(resposta).encode('utf-8'))
            return

        if self.path == "/api/movimentacao":
            id_usuario = dados['id_usuario']
            id_ferramenta = dados['id_ferramenta']
            
            res = sistema.preparar_e_abrir_porta_hardware(id_usuario, id_ferramenta)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        if self.path == "/api/salvar-ferramenta":
            id_f = dados.get('id', '')
            nome = dados['nome']
            gaveta = int(dados['gaveta'])
            quantidade = float(dados['quantidade'])
            tipo = dados.get('tipo', 'reutilizavel')

            if id_f and str(id_f).strip() != "":
                sistema.atualizar_ferramenta(int(id_f), nome, gaveta, quantidade, tipo)
            else:
                sistema.cadastrar_nova_ferramenta(nome, gaveta, quantity=quantidade, tipo=tipo) # Corrigido nome de parâmetro interno se houver

            self.responder_sucesso()
            return

        if self.path == "/api/deletar-ferramenta":
            id_f = int(dados['id'])
            sistema.deletar_ferramenta(id_f)
            self.responder_sucesso()
            return

    def responder_sucesso(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "sucesso"}).encode('utf-8'))

with socketserver.TCPServer(("", PORT), AlmoxarifadoAPIHandler) as httpd:
    print(f"🚀 Servidor Web integrado rodando na porta {PORT} em sincronia com o ESP32!")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Encerrando Servidor.")