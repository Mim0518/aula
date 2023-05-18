from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
import serial
import emociones as em
import mysql.connector

app = Flask(__name__)

# Configuración de la conexión a la base de datos
db_config = {
    'user': 'admin',
    'password': 'admin',
    'host': 'localhost',
    'database': 'aula_inteligente'
}

# Configuración del puerto serial
serial_port = 'COM6'  # Cambiar al puerto serial correcto

# Scheduler
scheduler = BackgroundScheduler()


@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        if request.form.get('Iniciar'):
            codigo_maestro = request.form.get('codigo')
            materia = request.form.get('materia')
            dia, mes, anio, hora = formated_date()
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(buffered=True)
            query = "INSERT INTO clase (codigo_maestro, materia, dia, mes, anio, hora) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (codigo_maestro, materia, dia, mes, anio, hora)
            cursor.execute(query, values)
            conn.commit()
            query = "SELECT id FROM clase WHERE codigo_maestro = %s AND materia = %s AND dia = %s AND mes = %s " \
                    "AND anio = %s AND hora = %s"
            cursor.execute(query, (codigo_maestro, materia, dia, mes, anio, hora))
            result = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            redirected = redirect(url_for('clase'))
            redirected.set_cookie('id', str(result))
            return redirected
    elif request.method == 'GET':
        return render_template('inicio.html')


@app.route('/clase', methods=['POST', 'GET'])
def clase():
    id_uso = request.cookies.get('id', 1)
    if request.method == 'GET':
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(buffered=True)
        query = "SELECT * FROM lecturas WHERE clase_id = %s"
        cursor.execute(query, (id_uso,))
        lecturas = cursor.fetchall()
        cursor.close()
        conn.close()
        # Comprobar si el trabajo ya está en el programador
        if 'leer_datos' not in [job.id for job in scheduler.get_jobs()]:
            scheduler.add_job(leer_datos, 'interval', seconds=5, id='leer_datos', kwargs={'claseid': id_uso})
            scheduler.start()
        return render_template("clase.html", lecturas=lecturas)
    elif request.method == 'POST':
        if request.form.get('ax'):
            redirected = redirect(url_for('clase'))
            redirected.set_cookie('id', id_uso)
            return redirected
        else:
            scheduler.shutdown(wait=False)
            return redirect('/')


def formated_date():
    now = datetime.now()
    dia = now.strftime("%d")
    mes = now.strftime("%m")
    anio = now.strftime("%Y")
    hora = now.strftime("%H:%M")
    return dia, mes, anio, hora


def read_temperature():
    # Inicializar la conexión con el puerto serial
    ser = serial.Serial(serial_port, 9600)
    # Leer la temperatura desde el puerto serial
    pretemp = ser.read(5)
    temperature = str(pretemp, 'utf-8')
    ser.close()
    return temperature


# Estoy sembrando el terror
def leer_datos(claseid):
    now = datetime.now()
    emotion = em.emotion_detection()
    temperatura = read_temperature()
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(buffered=True)
    sql = "INSERT INTO lecturas (clase_id, hora, emocion, temperatura) VALUES (%s, %s, %s, %s)"
    values = (claseid, now.strftime("%H:%M:%S"), emotion, temperatura)
    cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()


# Reportes
@app.route('/reportes', methods=['POST', 'GET'])
def reportes():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(buffered=True)

    if request.method == 'POST':
        # Obtén los valores del formulario
        materia = request.form.get('materia')
        dia = request.form.get('dia')
        hora = request.form.get('hora')

        # Ejecuta las consultas a la base de datos para obtener las estadísticas requeridas
        query = """
        SELECT emocion, COUNT(emocion) AS count
        FROM lecturas
        JOIN clase ON lecturas.clase_id = clase.id
        WHERE clase.materia = %s AND clase.dia = %s 
        GROUP BY emocion
        ORDER BY count DESC
        LIMIT 1
        """
        cursor.execute(query, (materia, dia))
        emocion_mas_registrada = cursor.fetchone()

        query = """
        SELECT AVG(temperatura)
        FROM lecturas
        JOIN clase ON lecturas.clase_id = clase.id
        WHERE clase.materia = %s AND clase.dia = %s 
        """
        cursor.execute(query, (materia, dia))
        temperatura_promedio = cursor.fetchone()
        # Consulta las materias disponibles
        cursor.execute("SELECT DISTINCT materia FROM clase")
        materias_disponibles = [row[0] for row in cursor.fetchall()]

        # Consulta los días disponibles
        cursor.execute("SELECT DISTINCT dia FROM clase")
        dias_disponibles = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        # Pasar los resultados a la plantilla
        return render_template("reportes.html", emocion_mas_registrada=emocion_mas_registrada,
                               temperatura_promedio=temperatura_promedio, materias_disponibles=materias_disponibles,
                               dias_disponibles=dias_disponibles)

    elif request.method == 'GET':
        # Consulta las materias disponibles
        cursor.execute("SELECT DISTINCT materia FROM clase")
        materias_disponibles = [row[0] for row in cursor.fetchall()]

        # Consulta los días disponibles
        cursor.execute("SELECT DISTINCT dia FROM clase")
        dias_disponibles = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return render_template('reportes.html', materias_disponibles=materias_disponibles,
                               dias_disponibles=dias_disponibles)


if __name__ == '__main__':
    app.run()
