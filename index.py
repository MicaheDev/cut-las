import os
from flask import Flask, request, jsonify, send_file
import laspy
import numpy as np
from io import BytesIO
import time  # Importa el módulo time para gestionar el retraso

app = Flask(__name__)

def cortar_nube_por_mitad(las_file_path, stage_type):
    # Crear un nuevo archivo .las para cada mitad
    mitad_superior_file = las_file_path.replace('.las', '_mitad_superior.las')
    mitad_inferior_file = las_file_path.replace('.las', '_mitad_inferior.las')

    # Leemos el archivo original
    in_file = laspy.read(las_file_path)
    header = in_file.header

    # Calcular la mitad de la nube en el eje y
    mitad_y = np.median(in_file.y)

    # Filtrar puntos por encima y por debajo de la mitad en el eje y
    mitad_superior = in_file.points[in_file.y >= mitad_y]
    mitad_inferior = in_file.points[in_file.y < mitad_y]

    # Crear instancias de laspy.LasData para cada mitad
    las_superior = laspy.LasData(header)
    las_inferior = laspy.LasData(header)

    # Modificar las coordenadas de las mitades
    las_superior.points = mitad_superior
    las_inferior.points = mitad_inferior

    # Simular un retraso adicional para el tipo "functional"
    if stage_type.lower() == "functional":
        time.sleep(5)  # Ajusta el valor según sea necesario

    # Escribir los archivos LAS
    las_superior.write(mitad_superior_file)
    las_inferior.write(mitad_inferior_file)

    return mitad_superior_file, mitad_inferior_file

@app.route('/recortar_nube', methods=['POST'])
def recortar_nube():
    try:
        # Verificar si se recibe un archivo .las en la solicitud POST
        if 'file' not in request.files:
            return jsonify({'error': 'No se ha proporcionado ningún archivo .las'}), 400

        archivo = request.files['file']

        if archivo.filename == '':
            return jsonify({'error': 'Nombre de archivo no válido'}), 400

        if archivo and archivo.filename.endswith('.las'):
            # Verificar si se proporciona el parámetro "stage-type"
            stage_type = request.args.get('stageType', 'geometrical')

            # Obtén la ruta al directorio de trabajo actual
            directorio_actual = os.getcwd()

            # Crea el directorio si no existe
            directorio_guardado = os.path.join(directorio_actual, 'archivos_guardados')
            if not os.path.exists(directorio_guardado):
                os.makedirs(directorio_guardado)

            # Guarda el archivo .las en el servidor
            archivo_path = os.path.join(directorio_guardado, archivo.filename)
            archivo.save(archivo_path)

            # Realizar el recorte y obtener los archivos de las mitades
            mitad_superior, mitad_inferior = cortar_nube_por_mitad(archivo_path, stage_type)

            # Eliminar el archivo original
            os.remove(archivo_path)

            # Devolver la mitad inferior como respuesta para su descarga
            return send_file(
                mitad_inferior, 
                as_attachment=True, 
                download_name='mitad_inferior.las', 
                mimetype='application/octet-stream'
            )

        else:
            return jsonify({'error': 'Formato de archivo no admitido, se esperaba un archivo .las'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
