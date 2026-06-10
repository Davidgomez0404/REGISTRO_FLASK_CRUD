from flask import Flask, session, flash, redirect, render_template, request
from werkzeug.security import check_password_hash,generate_password_hash
from dotenv import load_dotenv
import os, sqlite3, requests, datetime

load_dotenv()

app=Flask(__name__)
app.secret_key=os.getenv('secreto')

def create_table():
    conexion = sqlite3.connect('users.db')
    cursor = conexion.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   nombre TEXT,
                   email TEXT UNIQUE,
                   password_hash TEXT,
                   fecha_registro DATE,
                   inicio_sesion DATE
                   )''')
    conexion.commit()
    conexion.close()
    conexion = sqlite3.connect('favoritos.db')
    cursor = conexion.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS favoritos(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   email TEXT,
                   name TEXT,
                   image TEXT
                   )''')
    conexion.commit()
    conexion.close()

#===RUTAS===
@app.route('/')
def home():
    return render_template('home.html')

@app.errorhandler(404)
def error_404(e):
    return render_template('404.html'),404

#===REGISTRO===

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        if not nombre or not password or not email:
            flash("Campos vacios")
            return redirect('/register')
        conexion = sqlite3.connect('users.db')
        cursor = conexion.cursor()
        cursor.execute('''SELECT * FROM users WHERE email =?''', (email,))
        usuario = cursor.fetchone()
        if usuario:
            flash("Usuario previamente registrado")
            conexion.close()
            return redirect('/register')
        password_hash = generate_password_hash(password)
        fecha_registro = datetime.datetime.now()
        inicio_sesion = ""
        cursor.execute('''INSERT INTO users (nombre, email, password_hash, fecha_registro, inicio_sesion) VALUES(?,?,?,?,?)''', 
                       (nombre, email, password_hash, fecha_registro, inicio_sesion))
        conexion.commit()
        flash("Registro exitoso")
        session['nombre'] = nombre
        session['email'] = email
        conexion.close()
        return redirect('/dashboard')
    return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        if not password or not email:
            flash("Campos vacios")
            return redirect('/login')
        conexion = sqlite3.connect('users.db')
        cursor = conexion.cursor()
        cursor.execute('''SELECT * FROM users WHERE email =?''', (email,))
        usuario = cursor.fetchone()

        if not usuario:
            flash("Usuario no encontrado")
            conexion.close()
            return redirect('/login')
        if usuario:
            if check_password_hash(usuario[3], password):
                inicio_sesion = datetime.datetime.now()
                cursor.execute('''UPDATE users SET inicio_sesion=? WHERE email =?''', (inicio_sesion, email))
                conexion.commit()
                session['email'] = email
                session['nombre'] = usuario[1]
                flash("Inicio de sesion exitoso")
                conexion.close()
                return redirect('/dashboard')
            else:
                flash("Contraseña incorrecta")
                return redirect('/login')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('email'):
        flash("Debes iniciar sesion")
        return redirect('/login')
    conexion = sqlite3.connect('users.db')
    cursor = conexion.cursor()
    cursor.execute('''SELECT fecha_registro, inicio_sesion FROM users WHERE email =?''', (session['email'],))
    fechas = cursor.fetchone()
    conexion.close()

    url = "https://futuramaapi.com/api/characters"
    respuesta = requests.get(url, timeout=5)
    data = respuesta.json()
    personajes = data['items'][:10]
    return render_template('dashboard.html', personajes=personajes, fecha_registro = fechas[0], inicio_sesion = fechas[1])

#===FAVORITOS CRUD===
@app.route('/favoritos', methods=['POST', 'GET'])
def favoritos():
    if not session.get('email'):
        flash("Debes iniciar sesion")
        return redirect('/login')
    conexion = sqlite3.connect('favoritos.db')
    cursor = conexion.cursor()
    if request.method == 'POST':
        name = request.form['name']
        image = request.form['image']

        cursor.execute('''SELECT COUNT(*) FROM favoritos WHERE email =?''', (session['email'],))
        total_favoritos = cursor.fetchone()

        if total_favoritos[0] >= 5:
            flash("Maximo 5 favoritos")
            conexion.close()
            return redirect('/favoritos')

        cursor.execute('''INSERT INTO favoritos (name, image, email) VALUES(?,?,?)''', (name, image, session['email']))
        conexion.commit()
        conexion.close()

        return redirect('/favoritos')
    
    cursor.execute('''SELECT id, name, image FROM favoritos WHERE email =?''', (session['email'],))
    favoritos = cursor.fetchall()
    conexion.close()
    return render_template('favoritos.html', favoritos=favoritos)

@app.route('/borrar', methods=['POST'])
def borrar():
    if not session.get('email'):
        flash("Debes iniciar sesion")
        return redirect('login')
    
    p_id = request.form['p_id']

    conexion = sqlite3.connect('favoritos.db')
    cursor = conexion.cursor()
    cursor.execute('''DELETE FROM favoritos WHERE id=? AND email=?''', (p_id, session['email'],))
    conexion.commit()
    conexion.close()
    return redirect('/favoritos')

@app.route('/actualizar', methods=['POST'])
def actualizar():
    if not session.get('email'):
        flash("Debes iniciar sesion")
        return redirect('/login')

    p_id = request.form['p_id']
    name = request.form['name'].strip()

    if not name:
        flash("Nombre vacio")
        return redirect('/favoritos')

    conexion = sqlite3.connect('favoritos.db')
    cursor = conexion.cursor()
    cursor.execute('''UPDATE favoritos SET name=? WHERE email=? AND id=?''', (name, session['email'], p_id))

    conexion.commit()
    conexion.close()
    return redirect('/favoritos')

#===CIERRE DE SESION===
@app.route('/cerrarsesion')
def cerrarsesion():
    session.clear()
    flash("Has cerrado sesion")
    return redirect('/login')


create_table()
#===INICIO APP===
if __name__ == '__main__':
    app.run(debug=True)