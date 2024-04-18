from flask import Flask, request, render_template, redirect, url_for, session
import csv
import os
import networkx as nx
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'
# Ruta de la página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        if verificar_credenciales(usuario, password):
            # Si las credenciales son correctas, redirigir a la página de éxito
            session['username'] = usuario
            
            return redirect(url_for('dashboard'))
        else:
            error = 'Credenciales inválidas. Por favor, inténtalo de nuevo.'
    return render_template('login.html', error=error)

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


def calcular_pagerank(datos_busqueda_usuarios):
    grafo = nx.DiGraph()
    for username, queries in datos_busqueda_usuarios.items():
        for i in range(len(queries) - 1):
            query_actual = queries[i]
            query_siguiente = queries[i + 1]
            if grafo.has_edge(query_actual, query_siguiente):
                grafo[query_actual][query_siguiente]["weight"] += 1
            else:
                grafo.add_edge(query_actual, query_siguiente, weight=1)
    return nx.pagerank(grafo)

# Función para obtener los productos recomendados
def obtener_productos_recomendados(pagerank_productos):
    return sorted(pagerank_productos.items(), key=lambda x: x[1], reverse=True)[:6]

# Ejemplo de uso
@app.route('/dashboard')
def dashboard():
    datos_busqueda_usuarios = cargar_datos_busqueda('search_history.csv')
    pagerank_productos = calcular_pagerank(datos_busqueda_usuarios)
    productos_recomendados = obtener_productos_recomendados(pagerank_productos)
    return render_template('dashboard.html', productos_recomendados=productos_recomendados)




# Mostrar los productos recomendados

if __name__ == '__main__':
    app.run(debug=True)
