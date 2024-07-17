import os
from flask import Flask, request, render_template, redirect, url_for, flash, session
import datetime
import psycopg2
import requests

app = Flask(__name__)
app.secret_key = "mysecretkey"

# Configuración de conexión para PostgreSQL
conn_str = {
    "host": "dpg-cqarlkuehbks73de8dlg-a.oregon-postgres.render.com",
    "database": "bdfisitweet",
    "user": "grupo_app",
    "password": "4fPiWKsmtrNfCeHEEo2jBVIP7jvLGAn3"
}
@app.route('/')
def home():
    return redirect(url_for('login_render'))

# Conexión a la base de datos PostgreSQL
try:
    mydb = psycopg2.connect(**conn_str)
    print("Conexión exitosa a la base de datos PostgreSQL")
except Exception as e:
    print(f"No se pudo conectar a la base de datos PostgreSQL: {e}")

@app.route('/registro-usuario')
def registro_usuario():
    return render_template('registro-usuario.html')

@app.route('/agregar-usuario', methods=['POST'])
def agregar_usuario():
    if request.method == 'POST':
        try:
            nombre = request.form['nombre']
            apellido = request.form['apellido']
            correo = request.form['correo']
            codigo = request.form['codigo']

            cursor = mydb.cursor()
            query = "INSERT INTO alumnos (nombre, apellido, correo, codigo) VALUES (%s, %s, %s, %s)"
            values = (nombre, apellido, correo, codigo)
            cursor.execute(query, values)
            mydb.commit()
            cursor.close()

            flash('Usuario agregado de manera correcta: {}'.format(nombre))
        except Exception as e:
            flash("Error al realizar el registro: {}".format(e))

    return render_template('registro-usuario.html')

@app.route('/login-face')
def login_render():
    return render_template('loginFace.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        codigo = request.form['codigo']
        cursor = mydb.cursor()
        query = "SELECT * FROM alumnos WHERE correo = %s AND codigo = %s"
        values = (correo, codigo)
        cursor.execute(query, values)
        alumno = cursor.fetchone()
        cursor.close()

        if alumno:
            fecha = str(datetime.datetime.now())

            try:
                cursor = mydb.cursor()
                idAlumno = alumno[0]

                query = "INSERT INTO logs (idAlumno, fecha) VALUES (%s, %s)"
                values = (idAlumno, fecha)
                cursor.execute(query, values)
                cursor.close()

                session['logged_in'] = True
                session['usuario_id'] = alumno[0]
                session['nombre'] = alumno[1]
                flash("Inicio de sesión exitoso!")
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f"Error al registrar Log: {e}")
        else:
            flash("Error de autenticación")

    return render_template('loginFace.html')

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('logged_in', None)
    session.pop('usuario_id', None)
    session.pop('nombre', None)
    flash("Sesión cerrada correctamente.")
    return redirect(url_for('Index'))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' in session:
        idAlumno = session['usuario_id']

        # Llamada al microservicio de publicaciones
        try:
            publicaciones_response = requests.get(f'http://posts_service:5001/publicaciones/{idAlumno}')
            sesiones_response = requests.get(f'http://posts_service:5001/sesiones/{idAlumno}')

            publicaciones = publicaciones_response.json()
            sesiones = sesiones_response.json()
        except Exception as e:
            flash(f"Error al obtener datos de publicaciones: {e}")
            publicaciones = []
            sesiones = []

        cursor = mydb.cursor()
        query = "SELECT nombre, apellido, correo FROM alumnos WHERE idAlumno = %s"
        cursor.execute(query, (idAlumno,))
        usuario = cursor.fetchone()
        cursor.close()

        return render_template('dashboard.html', publicaciones=publicaciones, sesiones=sesiones, usuario=usuario)
    else:
        flash("Debe iniciar sesión para acceder al dashboard.")
        return redirect(url_for('login_render'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
