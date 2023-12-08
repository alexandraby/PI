from flask import Flask, render_template, request, redirect, url_for, abort, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash 

app = Flask(__name__, static_folder='static')


def row_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

#estabelecer a conexão com o bd;

def get_db_connection():
    conn = sqlite3.connect('banco_de_dados.db')
    conn.row_factory = row_factory
    return conn


def drop_table():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('DROP TABLE IF EXISTS publicacoes')
    db.commit()
    db.close()


def create_table():
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def setup_publicacoes_table():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('DROP TABLE IF EXISTS publicacoes')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publicacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conteudo TEXT NOT NULL,
            categoria TEXT NOT NULL
        )
    ''')
    db.commit()
    db.close()


categorias_e_publicacoes = {
    'acao': [],
    'aventura': [],
    'drama': [],
    'sci-fi': [],
    'romance': [],
    'fantasia': [],
    'sobrenatural': [],
    'suspense': [],
    'AU': []
}

id_counter = 0
publicacoes = []


def agrupar_publicacoes_por_categoria(publicacoes):
    categorias_publicacoes = {}
    for publicacao in publicacoes:
        categoria = publicacao["categoria"]
        if categoria not in categorias_publicacoes:
            categorias_publicacoes[categoria] = []
        categorias_publicacoes[categoria].append(publicacao)
    return categorias_publicacoes


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/index.html')
def pagina_inicial():
    return render_template('index.html')


@app.route('/cadastro.html')
def cadastro():
    return render_template('cadastro.html')


@app.route('/login.html')
def logar():
    return render_template('login.html')

#@app.route('/login', methods=['POST'], endpoint='login_usuario')
#def login():
   # try:
     #   data = request.get_json()
      #  email = data.get('email')
       # senha_digitada = data.get('senha')

        #conn = sqlite3.connect('usuarios.db')
        #cursor = conn.cursor()

        #cursor.execute('SELECT * FROM usuario WHERE email = ?', (email,))
        #usuario = cursor.fetchone()

        #conn.close()

        #if usuario and check_password_hash(usuario[3], senha_digitada):
         #   print("Login bem-sucedido")
          #  return jsonify({"success": True, "message": "Login bem-sucedido."})
        #else:
         #   print("Credenciais inválidas")
         #   return jsonify({"success": False, "message": "Credenciais inválidas. Por favor, verifique seu e-mail e senha."})

   # except Exception as e:
       #print(f"Erro durante o login: {str(e)}")
        #return jsonify({"success": False, "message": "Erro durante o login. Por favor, tente novamente."}) 


@app.route('/Publicacoes.html')
def publicacoes_page():
    mostrar_formulario = True
    return render_template('publicacoes.html', publicacoes=publicacoes, mostrar_formulario=mostrar_formulario)


@app.route('/categorias.html')
def categorias():
    return render_template('categorias.html')


@app.route('/minhaspublicacoes.html')
def minhas_publicacoes():
    
    categorias = ['Ação', 'Aventura', 'Drama', 'Fantasia', 'Misterio', 'Romance', 'Sobrenatural']



    return render_template('minhas.publicacoes.html', categorias=categorias, publicacoes=publicacoes)


@app.route('/cadastrar', methods=['POST'], endpoint='cadastrar_usuario')
def cadastrar():
    try:
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        # Hash da senha antes de armazenar no banco de dados
        senha_hash = generate_password_hash(senha, method='pbkdf2:sha256')

        conn = sqlite3.connect('usuarios.db')
        cursor = conn.cursor()

        # Verifica se o e-mail já está cadastrado
        cursor.execute('SELECT * FROM usuario WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "E-mail já cadastrado. Por favor, escolha outro e-mail."})

        # Insere o novo usuário no banco de dados
        cursor.execute('INSERT INTO usuario (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha_hash))

        conn.commit()
        conn.close()

        print(f'Usuário cadastrado: Nome: {nome}, E-mail: {email}, Senha: {senha_hash}')

        # Redireciona para a página home após o cadastro bem-sucedido
        return redirect(url_for('home'))

    except Exception as e:
        # Log de exceção
        print(f"Erro durante o cadastro: {str(e)}")
        return jsonify({"success": False, "message": "Erro durante o cadastro. Por favor, tente novamente."})


@app.route('/cadastro', methods=['GET'])
def exibir_formulario_cadastro():
    return render_template('cadastro.html')


@app.route('/publicacoes/<categoria>')
def publicacoes_por_categoria(categoria):
    categorias_publicacoes = agrupar_publicacoes_por_categoria(publicacoes)
    return render_template('publicacoes.html', categorias_publicacoes=categorias_publicacoes, categoria_selecionada=categoria)


@app.route('/publicar', methods=['POST'])
def publicar():
    global id_counter
    global publicacoes
    global categorias_e_publicacoes

    novo_conteudo = request.form['conteudo']
    categoria = request.form['categoria']

    nova_publicacao = {
        'id': id_counter + 1,
        'conteudo': novo_conteudo,
        'categoria': categoria
    }

    id_counter += 1
    publicacoes.append(nova_publicacao)

    if categoria not in categorias_e_publicacoes:
        categorias_e_publicacoes[categoria] = []

    categorias_e_publicacoes[categoria].append(nova_publicacao)

    # Atualiza as publicações no contexto do template

    # Conectar ao banco de dados
    db = get_db_connection()
    cursor = db.cursor()

    # Inserir a nova publicação no banco de dados
    cursor.execute('INSERT INTO publicacoes (conteudo, categoria) VALUES (?, ?)', (novo_conteudo, categoria))

    # Commit e fechar a conexão
    db.commit()
    db.close()

    return render_template('publicacoes.html', categorias_publicacoes=categorias_e_publicacoes, categoria_selecionada=categoria)

from flask import request, jsonify

@app.route('/editar_publicacao/<int:publicacao_id>', methods=['POST'])
def editar_publicacao(publicacao_id):
    novo_conteudo = request.form.get('conteudo')
    nova_categoria = request.form.get('categoria')

    resultado = editar_publicacao_no_banco(publicacao_id, novo_conteudo, nova_categoria)

    if resultado:
        return jsonify({'mensagem': 'Publicação editada com sucesso', 'publicacaoId': publicacao_id, 'conteudo': novo_conteudo, 'categoria': nova_categoria})
    else:
        return jsonify({'erro': 'Falha ao editar publicação'}), 500

def encontrar_publicacao_por_id(publicacao_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM publicacoes WHERE id = ?', (publicacao_id,))
    publicacao = cursor.fetchone()
    conn.close()
    return publicacao

# Função para editar uma publicação no banco de dados
def editar_publicacao_no_banco(publicacao_id, novo_conteudo, nova_categoria):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verifica se a publicação existe
    cursor.execute('SELECT * FROM publicacoes WHERE id = ?', (publicacao_id,))
    publicacao = cursor.fetchone()

    if publicacao:
        # Atualiza os campos
        cursor.execute('UPDATE publicacoes SET conteudo = ?, categoria = ? WHERE id = ?', 
                       (novo_conteudo, nova_categoria, publicacao_id))
        conn.commit()
        conn.close()
        return jsonify({'mensagem': 'Publicação editada com sucesso'})
   

@app.route('/editar/<int:publicacao_id>', methods=['POST'])
def editar(publicacao_id):
    if request.method == 'POST':
        novo_conteudo = request.form['conteudoEdicao']

        # Atualizar a publicação no banco de dados
        db = get_db_connection()
        cursor = db.cursor()

        # Substitua 'publicacoes' pelo nome real da sua tabela
        cursor.execute('UPDATE publicacoes SET conteudo = ? WHERE id = ?', (novo_conteudo, publicacao_id))

        db.commit()
        db.close()

        # Retornar sucesso como JSON
        return jsonify(success=True)
    else:
        return jsonify(success=False, error="Método inválido para esta rota"), 400


@app.route('/excluir_publicacao/<int:publicacao_id>', methods=['POST'])
def excluir_publicacao(publicacao_id):
    global publicacoes

    # Encontrar a publicação pelo ID
    publicacao = next((p for p in publicacoes if p['id'] == publicacao_id), None)

    if publicacao:
        publicacoes.remove(publicacao)
        return redirect(url_for('minhas_publicacoes'))
    else:
        abort(404)



@app.route('/api/get_publicacoes')
def get_publicacoes():
    return {'publicacoes': publicacoes}


if __name__ == '__main__':
    drop_table()
    create_table()
    setup_publicacoes_table()
    app.run(debug=True)
