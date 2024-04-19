from flask import Flask, request, render_template, redirect, url_for, session
import csv
import os
import networkx as nx
import pandas as pd

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Ruta Raiz
@app.route('/')
def index():
    session.pop('username', None)
    return redirect(url_for('login'))

# Ruta de la página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        # Si el usuario ya tiene una sesión, redirigir al dashboard directamente
        return redirect(url_for('dashboard'))

    error = None
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        if verificar_credenciales(usuario, password):
            session['username'] = usuario
            return redirect(url_for('dashboard'))
        else:
            error = 'Credenciales inválidas. Por favor, inténtalo de nuevo.'
    return render_template('login.html', error=error)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Función para verificar las credenciales en el archivo CSV

def verificar_credenciales(usuario, password):
    with open('usuario.csv', 'r') as archivo:
        lector_csv = csv.DictReader(archivo)
        for fila in lector_csv:
            if fila['usuario'] == usuario and fila['password'] == password:
                return True
    return False

def save_search_to_csv(username, query):
     # Verifica si el archivo CSV ya existe
    file_exists = os.path.isfile('search_history.csv')

    # Abre el archivo CSV en modo de escritura, y si no existe, crea uno nuevo
    with open('search_history.csv', 'a', newline='') as csvfile:
        fieldnames = ['username', 'query']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Si el archivo no existe, escribe el encabezado
        if not file_exists:
            writer.writeheader()

        # Escribe la nueva fila con los datos proporcionados
        writer.writerow({'username': username, 'query': query})
        

@app.route('/search', methods=['POST'])
def search():
    username = session['username']
    query = request.form['query']
    save_search_to_csv(username, query)
    # Aquí realizarías la lógica de búsqueda y devolverías los resultados
    # Por ahora, simplemente redirigimos a una página de resultados ficticia
    return redirect(url_for('dashboard'))



# Ruta de la página de éxito después del login
def cargar_datos_busqueda(filename):
    datos_busqueda_usuarios = {}
    with open(filename, 'r') as file:
        lector_csv = csv.DictReader(file)
        for row in lector_csv:
            username = row['username']
            query = row['query']
            if username in datos_busqueda_usuarios:
                datos_busqueda_usuarios[username].append(query)
            else:
                datos_busqueda_usuarios[username] = [query]
    return datos_busqueda_usuarios


def cargar_datos_articulos(filename):
    articulos = {}
    with open(filename, 'r') as file:
        lector_csv = csv.DictReader(file)
        for row in lector_csv:
           articulo = row['articulo']

    return articulos


def procesar_consultas(datos_busqueda_usuarios, session_username):
    grafo = nx.DiGraph()

    if not datos_busqueda_usuarios:
        return nx.pagerank(grafo) 
    consultas_usuario = datos_busqueda_usuarios[session_username]


    for consultas in consultas_usuario:
        for i in range(len(consultas_usuario) - 1):
            query_actual = consultas_usuario[i]
            query_siguiente = consultas_usuario[i + 1]
            if grafo.has_edge(query_actual, query_siguiente):
                grafo[query_actual][query_siguiente]["weight"] += 1
            else:
                grafo.add_edge(query_actual, query_siguiente, weight=1)


    return nx.pagerank(grafo)


def obtener_productos_recomendados(pagerank_productos):
    return sorted(pagerank_productos.items(), key=lambda x: x[1], reverse=True)[:5]

def asignar_anuncios(productos_recomendados):
    total_pagerank = sum(pr for _, pr in productos_recomendados)
    anuncios_por_producto = {}

    for producto, pagerank in productos_recomendados:
        # Reemplaza espacios con guiones bajos
        producto_formato = producto.replace(" ", "_")
        
        # Calcula el número de anuncios proporcional al pagerank
        numero_anuncios = int((pagerank / total_pagerank) * 5)  # 5 es el número total de anuncios aquí, ajusta si necesario
        
        # Lista para guardar las rutas de los anuncios
        anuncios = []
        
        # Crea la ruta del archivo y la añade a la lista de anuncios
        # Utiliza una cadena normal y agrega manualmente una barra
        anuncios.append("./static/img/{}.jpg".format(producto_formato))
        
        # Guarda la lista de anuncios en el diccionario, asociada al producto original
        anuncios_por_producto[producto] = anuncios[0]

    return anuncios_por_producto



# Ejemplo de uso
@app.route('/dashboard')
def dashboard():
    username = session['username']
    # Carga de otros datos necesarios, ejemplos con funciones ficticias
    datos_busqueda_usuarios = cargar_datos_busqueda('search_history.csv')
    pagerank_productos = procesar_consultas(datos_busqueda_usuarios,username)
    productos_recomendados = obtener_productos_recomendados(pagerank_productos)
    anuncios_asignados = asignar_anuncios(productos_recomendados)
    df = pd.read_csv('articles.csv')
    elementos_tienda = df['articulo'].tolist()
 
    
    return render_template('dashboard.html', productos_recomendados=productos_recomendados, elementos_tienda=elementos_tienda,anuncios_asignados=anuncios_asignados)


# Mostrar los productos recomendados

if __name__ == '__main__':
    app.run(debug=True)
