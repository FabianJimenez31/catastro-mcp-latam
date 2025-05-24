"""
Aplicación principal del microservicio REST para el MCP de Catastro Geográfico Inteligente.

Este módulo configura y ejecuta la aplicación Flask que sirve la API REST
para consultas catastrales a partir de direcciones.

Autor: Fabián Jiménez
Licencia: MIT
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS

# Importar controladores
from api.controllers.catastro_controller import catastro_bp, init_services

def create_app(test_config=None):
    """
    Crea y configura la aplicación Flask.
    
    Args:
        test_config: Configuración para pruebas (opcional)
        
    Returns:
        Aplicación Flask configurada
    """
    # Crear y configurar la aplicación
    app = Flask(__name__, instance_relative_config=True)
    
    # Configuración por defecto
    app.config.from_mapping(
        SECRET_KEY='dev',
        GOOGLE_MAPS_API_KEY=os.environ.get('GOOGLE_MAPS_API_KEY'),
        CATASTRO_DATA_PATH=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                        'data/bogota/TPREDIO.csv')
    )
    
    # Cargar configuración de prueba si se proporciona
    if test_config is None:
        # Cargar configuración de instancia, si existe
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Cargar configuración de prueba
        app.config.from_mapping(test_config)
    
    # Asegurar que existe el directorio de instancia
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Habilitar CORS
    CORS(app)
    
    # Inicializar servicios
    with app.app_context():
        init_services(app)
    
    # Registrar blueprints
    app.register_blueprint(catastro_bp)
    
    # Ruta de inicio
    @app.route('/')
    def index():
        return jsonify({
            "name": "Catastro Geográfico Inteligente API",
            "version": "1.0.0",
            "description": "API REST para consulta de información catastral a partir de direcciones",
            "endpoints": [
                "/api/catastro/geocode",
                "/api/catastro/predio/direccion",
                "/api/catastro/predio/coordenadas",
                "/api/catastro/pois/cercanos",
                "/api/catastro/consulta/completa"
            ],
            "documentation": "/docs"
        })
    
    # Ruta para verificar estado
    @app.route('/health')
    def health():
        return jsonify({
            "status": "ok",
            "message": "El servicio está funcionando correctamente"
        })
    
    # Manejador de errores 404
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "success": False,
            "error": "Recurso no encontrado",
            "message": "La ruta solicitada no existe en esta API"
        }), 404
    
    # Manejador de errores 500
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({
            "success": False,
            "error": "Error interno del servidor",
            "message": "Ocurrió un error al procesar la solicitud"
        }), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
