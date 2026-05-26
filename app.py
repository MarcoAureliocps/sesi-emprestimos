from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3, os, json
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)

DB = os.path.join(os.path.dirname(__file__), 'sesi.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS emprestimos (
            id          TEXT PRIMARY KEY,
            nome        TEXT NOT NULL,
            carrinho    TEXT NOT NULL,
            tipo        TEXT DEFAULT 'professor',
            turma       TEXT,
            obs         TEXT,
            previsao    TEXT,
            dispositivos TEXT NOT NULL,
            data_retirada TEXT NOT NULL,
            data_devolucao TEXT
        );
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT
        );
        INSERT OR IGNORE INTO config VALUES ('pin','1234');
    ''')
    conn.commit()
    conn.close()

# ── FRONTEND ──────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ── API: EMPRÉSTIMOS ──────────────────────────────────
@app.route('/api/emprestimos', methods=['GET'])
def listar_emprestimos():
    conn = get_db()
    rows = conn.execute('SELECT * FROM emprestimos ORDER BY data_retirada DESC').fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            'id': r['id'],
            'nome': r['nome'],
            'carrinho': r['carrinho'],
            'tipo': r['tipo'],
            'turma': r['turma'] or '',
            'obs': r['obs'] or '',
            'previsao': r['previsao'],
            'numeros_dispositivos': json.loads(r['dispositivos']),
            'data_emprestimo': r['data_retirada'],
            'data_devolucao': r['data_devolucao']
        })
    return jsonify(result)

@app.route('/api/registrar', methods=['POST'])
def registrar():
    d = request.json
    nome = d.get('nome','').strip()
    id_  = d.get('id','').strip().upper()
    carrinho = d.get('carrinho','')
    tipo = d.get('tipo','professor')
    turma = d.get('turma','').strip()
    obs = d.get('obs','').strip()
    previsao = d.get('previsao') or None
    numeros = d.get('numeros_dispositivos',[])

    if not nome or not id_ or not numeros:
        return jsonify({'erro':'Campos obrigatórios faltando'}), 400

    MAXIMOS = {'preto':35,'vermelho':35,'cinza':16}
    max_n = MAXIMOS.get(carrinho, 35)
    for n in numeros:
        if not isinstance(n,int) or n < 1 or n > max_n:
            return jsonify({'erro':f'Número {n} fora do range'}), 400

    conn = get_db()
    # checar dispositivos já emprestados
    ativos = conn.execute(
        "SELECT dispositivos FROM emprestimos WHERE carrinho=? AND data_devolucao IS NULL",
        (carrinho,)
    ).fetchall()
    emprestados = []
    for row in ativos:
        emprestados.extend(json.loads(row['dispositivos']))
    conflito = [n for n in numeros if n in emprestados]
    if conflito:
        conn.close()
        return jsonify({'erro':f'Dispositivos já emprestados: {conflito}'}), 409

    # checar se id já tem empréstimo ativo
    ativo = conn.execute(
        "SELECT id FROM emprestimos WHERE id=? AND data_devolucao IS NULL", (id_,)
    ).fetchone()
    if ativo:
        conn.close()
        return jsonify({'erro':'Este responsável já tem empréstimo ativo'}), 409

    conn.execute(
        'INSERT INTO emprestimos VALUES (?,?,?,?,?,?,?,?,?,NULL)',
        (id_, nome, carrinho, tipo, turma, obs, previsao,
         json.dumps(numeros), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return jsonify({'ok':True,'id':id_})

@app.route('/api/devolver/<id_>', methods=['PUT'])
def devolver(id_):
    conn = get_db()
    r = conn.execute('SELECT * FROM emprestimos WHERE id=? AND data_devolucao IS NULL',(id_,)).fetchone()
    if not r:
        conn.close()
        return jsonify({'erro':'Empréstimo não encontrado ou já devolvido'}), 404
    conn.execute(
        'UPDATE emprestimos SET data_devolucao=? WHERE id=?',
        (datetime.now().isoformat(), id_)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok':True})

@app.route('/api/excluir/<id_>', methods=['DELETE'])
def excluir(id_):
    conn = get_db()
    conn.execute('DELETE FROM emprestimos WHERE id=?',(id_,))
    conn.commit()
    conn.close()
    return jsonify({'ok':True})

# ── API: DISPOSITIVOS ATIVOS ──────────────────────────
@app.route('/api/dispositivos-ativos', methods=['GET'])
def dispositivos_ativos():
    conn = get_db()
    rows = conn.execute(
        "SELECT carrinho, dispositivos FROM emprestimos WHERE data_devolucao IS NULL"
    ).fetchall()
    conn.close()
    resultado = {'preto':[],'vermelho':[],'cinza':[]}
    for r in rows:
        nums = json.loads(r['dispositivos'])
        resultado[r['carrinho']].extend(nums)
    return jsonify(resultado)

# ── API: PIN ─────────────────────────────────────────
@app.route('/api/pin/verificar', methods=['POST'])
def verificar_pin():
    d = request.json
    conn = get_db()
    row = conn.execute("SELECT valor FROM config WHERE chave='pin'").fetchone()
    conn.close()
    ok = row and row['valor'] == str(d.get('pin',''))
    return jsonify({'ok': ok})

@app.route('/api/pin/alterar', methods=['POST'])
def alterar_pin():
    d = request.json
    conn = get_db()
    row = conn.execute("SELECT valor FROM config WHERE chave='pin'").fetchone()
    if not row or row['valor'] != str(d.get('pin_atual','')):
        conn.close()
        return jsonify({'erro':'PIN atual incorreto'}), 401
    novo = str(d.get('pin_novo',''))
    if not novo.isdigit() or len(novo) != 4:
        conn.close()
        return jsonify({'erro':'Novo PIN deve ter 4 dígitos'}), 400
    conn.execute("UPDATE config SET valor=? WHERE chave='pin'",(novo,))
    conn.commit()
    conn.close()
    return jsonify({'ok':True})

if __name__ == '__main__':
    init_db()
    print("\n" + "="*50)
    print("  SESI Sumaré - Sistema de Empréstimos")
    print("="*50)
    print("  Acesse em: http://0.0.0.0:5000")
    print("  Na rede:   http://SEU_IP:5000")
    print("  PIN admin: 1234 (altere após o 1º acesso)")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
