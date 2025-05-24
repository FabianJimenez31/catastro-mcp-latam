"""
Controlador para el microservicio REST de Catastro Geográfico Inteligente.

Este módulo implementa los endpoints de la API REST y la lógica de negocio
para la consulta de información catastral a partir de direcciones.

Autor: Fabián Jiménez
Licencia: MIT
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple

from flask import Blueprint, request, jsonify, current_app

# Importar modelos y servicios
from api.models.catastro import CatastroService
from api.utils.geocode import GeocodingService

# Crear blueprint para las rutas de catastro
catastro_bp = Blueprint('catastro', __name__, url_prefix='/api/catastro')

# Inicializar servicios
geocoder = None
catastro_service = None

def init_services(app):
    """
    Inicializa los servicios necesarios para el controlador.
    
    Args:
        app: Aplicación Flask
    """
    global geocoder, catastro_service
    
    # Obtener configuración
    google_api_key = app.config.get('GOOGLE_MAPS_API_KEY')
    data_path = app.config.get('CATASTRO_DATA_PATH')
    
    # Inicializar servicios
    geocoder = GeocodingService(google_api_key)
    catastro_service = CatastroService(data_path, google_api_key)


# Endpoints de la API

@catastro_bp.route('/geocode', methods=['POST'])
def geocode_address():
    """
    Geocodifica una dirección para obtener coordenadas.
    
    Request:
        {
            "direccion": "Calle 147 #11-10",
            "ciudad": "Bogotá",
            "pais": "Colombia"
        }
    
    Response:
        {
            "success": true,
            "coordinates": {
                "lat": 4.7281,
                "lng": -74.0332
            },
            "formatted_address": "Calle 147 #11-10, Bogotá, Colombia"
        }
    """
    data = request.get_json()
    
    if not data or 'direccion' not in data:
        return jsonify({
            "success": False,
            "error": "Se requiere una dirección para geocodificar"
        }), 400
    
    direccion = data.get('direccion')
    ciudad = data.get('ciudad', '')
    pais = data.get('pais', '')
    
    # Construir dirección completa
    direccion_completa = direccion
    if ciudad:
        direccion_completa += f", {ciudad}"
    if pais:
        direccion_completa += f", {pais}"
    
    # Geocodificar dirección
    geocode_result = geocoder.geocode_address(direccion_completa)
    
    # Extraer datos relevantes
    location_data = geocoder.extract_location_data(geocode_result)
    
    return jsonify(location_data)


@catastro_bp.route('/predio/direccion', methods=['POST'])
def find_predio_by_address():
    """
    Busca información catastral de un predio por dirección.
    
    Request:
        {
            "direccion": "Calle 147 #11-10",
            "ciudad": "Bogotá",
            "pais": "Colombia"
        }
    
    Response:
        {
            "success": true,
            "predio": {
                "chip": "AAA0045TEMS",
                "numero_predial": "110010145072100090011000000000",
                "direccion": "CL 65G BIS A SUR 77I 09",
                "barrio": "LA ESTACION BOSA",
                "area_terreno": 108.0,
                "area_construida": 175.9,
                "uso_codigo": "014",
                "uso_descripcion": "Dotacional Público",
                "estrato": 3,
                "anio_construccion": "1987",
                "valor_catastral": 1250000000.0
            }
        }
    """
    data = request.get_json()
    
    if not data or 'direccion' not in data:
        return jsonify({
            "success": False,
            "error": "Se requiere una dirección para buscar el predio"
        }), 400
    
    direccion = data.get('direccion')
    ciudad = data.get('ciudad', '')
    pais = data.get('pais', '')
    
    # Construir dirección completa
    direccion_completa = direccion
    if ciudad:
        direccion_completa += f", {ciudad}"
    if pais:
        direccion_completa += f", {pais}"
    
    # Buscar predio por dirección
    resultado = catastro_service.find_predio_by_address(direccion_completa)
    
    return jsonify(resultado)


@catastro_bp.route('/predio/coordenadas', methods=['POST'])
def find_predio_by_coordinates():
    """
    Busca información catastral de un predio por coordenadas.
    
    Request:
        {
            "lat": 4.7281,
            "lng": -74.0332
        }
    
    Response:
        {
            "success": true,
            "predio": {
                "chip": "AAA0045TEMS",
                "numero_predial": "110010145072100090011000000000",
                "direccion": "CL 65G BIS A SUR 77I 09",
                "barrio": "LA ESTACION BOSA",
                "area_terreno": 108.0,
                "area_construida": 175.9,
                "uso_codigo": "014",
                "uso_descripcion": "Dotacional Público",
                "estrato": 3,
                "anio_construccion": "1987",
                "valor_catastral": 1250000000.0
            }
        }
    """
    data = request.get_json()
    
    if not data or 'lat' not in data or 'lng' not in data:
        return jsonify({
            "success": False,
            "error": "Se requieren coordenadas (lat, lng) para buscar el predio"
        }), 400
    
    lat = data.get('lat')
    lng = data.get('lng')
    
    # Buscar predio por coordenadas
    resultado = catastro_service.find_nearest_predio(lat, lng)
    
    return jsonify(resultado)


@catastro_bp.route('/pois/cercanos', methods=['POST'])
def find_nearby_pois():
    """
    Busca puntos de interés cercanos a unas coordenadas.
    
    Request:
        {
            "lat": 4.7281,
            "lng": -74.0332,
            "radius": 500
        }
    
    Response:
        {
            "success": true,
            "pois": [
                {
                    "tipo": "Colegio",
                    "nombre": "Colegio Distrital",
                    "distancia": 120.5,
                    "direccion": "Calle 65 #10-45"
                },
                ...
            ]
        }
    """
    data = request.get_json()
    
    if not data or 'lat' not in data or 'lng' not in data:
        return jsonify({
            "success": False,
            "error": "Se requieren coordenadas (lat, lng) para buscar POIs cercanos"
        }), 400
    
    lat = data.get('lat')
    lng = data.get('lng')
    radius = data.get('radius', 500)
    
    # Buscar POIs cercanos
    resultado = catastro_service.find_nearby_pois(lat, lng, radius)
    
    return jsonify(resultado)


@catastro_bp.route('/consulta/completa', methods=['POST'])
def consulta_completa():
    """
    Realiza una consulta completa de información catastral a partir de una dirección.
    
    Request:
        {
            "direccion": "Calle 147 #11-10",
            "ciudad": "Bogotá",
            "pais": "Colombia"
        }
    
    Response:
        {
            "success": true,
            "direccion": {
                "original": "Calle 147 #11-10, Bogotá, Colombia",
                "formateada": "Calle 147 #11-10, Bogotá, Colombia"
            },
            "coordenadas": {
                "lat": 4.7281,
                "lng": -74.0332
            },
            "predio": {
                "chip": "AAA0045TEMS",
                "numero_predial": "110010145072100090011000000000",
                "direccion": "CL 65G BIS A SUR 77I 09",
                "barrio": "LA ESTACION BOSA",
                "area_terreno": 108.0,
                "area_construida": 175.9,
                "uso_codigo": "014",
                "uso_descripcion": "Dotacional Público",
                "estrato": 3,
                "anio_construccion": "1987",
                "valor_catastral": 1250000000.0
            },
            "pois_cercanos": [
                {
                    "tipo": "Colegio",
                    "nombre": "Colegio Distrital",
                    "distancia": 120.5,
                    "direccion": "Calle 65 #10-45"
                },
                ...
            ]
        }
    """
    data = request.get_json()
    
    if not data or 'direccion' not in data:
        return jsonify({
            "success": False,
            "error": "Se requiere una dirección para la consulta"
        }), 400
    
    direccion = data.get('direccion')
    ciudad = data.get('ciudad', '')
    pais = data.get('pais', '')
    
    # Construir dirección completa
    direccion_completa = direccion
    if ciudad:
        direccion_completa += f", {ciudad}"
    if pais:
        direccion_completa += f", {pais}"
    
    # 1. Geocodificar dirección
    geocode_result = geocoder.geocode_address(direccion_completa)
    location_data = geocoder.extract_location_data(geocode_result)
    
    if not location_data.get('success'):
        return jsonify(location_data)
    
    # 2. Buscar predio por coordenadas
    lat = location_data['coordinates']['lat']
    lng = location_data['coordinates']['lng']
    predio_result = catastro_service.find_nearest_predio(lat, lng)
    
    if not predio_result.get('success'):
        return jsonify({
            "success": False,
            "error": "No se encontró información catastral para la dirección proporcionada",
            "direccion": {
                "original": direccion_completa,
                "formateada": location_data.get('formatted_address', direccion_completa)
            },
            "coordenadas": location_data['coordinates']
        })
    
    # 3. Buscar POIs cercanos
    pois_result = catastro_service.find_nearby_pois(lat, lng)
    
    # 4. Construir respuesta completa
    respuesta = {
        "success": True,
        "direccion": {
            "original": direccion_completa,
            "formateada": location_data.get('formatted_address', direccion_completa)
        },
        "coordenadas": location_data['coordinates'],
        "predio": predio_result['predio'],
        "pois_cercanos": pois_result.get('pois', [])
    }
    
    return jsonify(respuesta)


# Funciones para el MCP

def geocodificar_direccion(direccion, ciudad, pais):
    """
    Geocodifica una dirección para el MCP.
    
    Args:
        direccion: Dirección a geocodificar
        ciudad: Ciudad de la dirección
        pais: País de la dirección
        
    Returns:
        Diccionario con coordenadas y dirección confirmada
    """
    # Construir dirección completa
    direccion_completa = direccion
    if ciudad:
        direccion_completa += f", {ciudad}"
    if pais:
        direccion_completa += f", {pais}"
    
    # Geocodificar dirección
    geocode_result = geocoder.geocode_address(direccion_completa)
    location_data = geocoder.extract_location_data(geocode_result)
    
    if location_data.get('success'):
        return {
            "coordenadas": location_data['coordinates'],
            "direccion_confirmada": True
        }
    else:
        return {
            "coordenadas": None,
            "direccion_confirmada": False
        }


def buscar_predio_por_coordenadas(coordenadas):
    """
    Busca información de un predio por coordenadas para el MCP.
    
    Args:
        coordenadas: Diccionario con lat y lng
        
    Returns:
        Información del predio
    """
    if not coordenadas:
        return {"predio_info": None}
    
    lat = coordenadas['lat']
    lng = coordenadas['lng']
    
    resultado = catastro_service.find_nearest_predio(lat, lng)
    
    if resultado.get('success'):
        return {"predio_info": resultado['predio']}
    else:
        return {"predio_info": None}


def buscar_pois_cercanos(coordenadas):
    """
    Busca POIs cercanos a unas coordenadas para el MCP.
    
    Args:
        coordenadas: Diccionario con lat y lng
        
    Returns:
        Lista de POIs cercanos y texto formateado
    """
    if not coordenadas:
        return {
            "pois_cercanos": [],
            "pois_cercanos_texto": "No hay información disponible"
        }
    
    lat = coordenadas['lat']
    lng = coordenadas['lng']
    
    resultado = catastro_service.find_nearby_pois(lat, lng)
    
    if resultado.get('success') and resultado.get('pois'):
        pois = resultado['pois']
        
        # Formatear texto para MCP
        pois_texto = ""
        for poi in pois:
            pois_texto += f"- {poi['tipo']}: {poi['nombre']} ({poi['distancia']}m)\n"
        
        return {
            "pois_cercanos": pois,
            "pois_cercanos_texto": pois_texto
        }
    else:
        return {
            "pois_cercanos": [],
            "pois_cercanos_texto": "No se encontraron puntos de interés cercanos"
        }


def reiniciar_slots():
    """
    Reinicia los slots para una nueva consulta en el MCP.
    
    Returns:
        Valores iniciales para los slots
    """
    return {
        "direccion": None,
        "ciudad": None,
        "pais": None,
        "direccion_completa": None,
        "direccion_confirmada": False,
        "coordenadas": None,
        "predio_info": None,
        "pois_cercanos": None,
        "pois_cercanos_texto": None
    }
