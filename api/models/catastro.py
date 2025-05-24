"""
Módulo para consulta de predios por coordenadas geográficas.

Este módulo proporciona funciones para:
1. Geocodificar direcciones a coordenadas
2. Encontrar el predio más cercano a un par lat/lon
3. Extraer atributos catastrales relevantes

Autor: Fabián Jiménez
Licencia: MIT
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import re
from geopy.distance import geodesic
import json

# Importar el módulo de geocodificación
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.geocode import GeocodingService

class CatastroService:
    """Servicio de consulta catastral basado en coordenadas geográficas."""
    
    def __init__(self, data_path: str, google_api_key: Optional[str] = None):
        """
        Inicializa el servicio de catastro.
        
        Args:
            data_path: Ruta al archivo CSV de datos catastrales
            google_api_key: Clave de API de Google Maps (opcional)
        """
        self.data_path = data_path
        self.geocoder = GeocodingService(google_api_key)
        self.predios_df = None
        self.load_data()
        
    def load_data(self) -> None:
        """Carga los datos catastrales desde el archivo CSV."""
        try:
            self.predios_df = pd.read_csv(self.data_path)
            print(f"Datos catastrales cargados: {len(self.predios_df)} registros")
        except Exception as e:
            print(f"Error al cargar datos catastrales: {e}")
            self.predios_df = pd.DataFrame()
    
    def _normalize_address(self, address: str) -> str:
        """
        Normaliza una dirección para comparación.
        
        Args:
            address: Dirección a normalizar
            
        Returns:
            Dirección normalizada
        """
        # Convertir a minúsculas
        address = address.lower()
        
        # Eliminar espacios adicionales
        address = re.sub(r'\s+', ' ', address).strip()
        
        # Normalizar abreviaturas comunes
        replacements = {
            'calle': 'cl',
            'carrera': 'kr',
            'avenida': 'av',
            'diagonal': 'dg',
            'transversal': 'tv',
            'sur': 's',
            'norte': 'n',
            'este': 'e',
            'oeste': 'o',
            'no\.': '',
            'numero': '',
            '#': '',
            '-': ' '
        }
        
        for old, new in replacements.items():
            address = address.replace(old, new)
        
        return address
    
    def find_predio_by_address(self, address: str) -> Dict[str, Any]:
        """
        Busca un predio por dirección.
        
        Args:
            address: Dirección a buscar
            
        Returns:
            Diccionario con información del predio o error
        """
        if self.predios_df is None or self.predios_df.empty:
            return {"success": False, "error": "No hay datos catastrales cargados"}
        
        # Normalizar la dirección de búsqueda
        normalized_address = self._normalize_address(address)
        
        # Crear columna temporal con direcciones normalizadas
        self.predios_df['normalized_address'] = self.predios_df['PREDIRECC'].apply(self._normalize_address)
        
        # Buscar coincidencias exactas
        exact_matches = self.predios_df[self.predios_df['normalized_address'] == normalized_address]
        
        if not exact_matches.empty:
            predio = exact_matches.iloc[0]
            return self._format_predio_info(predio)
        
        # Buscar coincidencias parciales
        partial_matches = self.predios_df[self.predios_df['normalized_address'].str.contains(normalized_address, regex=False)]
        
        if not partial_matches.empty:
            predio = partial_matches.iloc[0]
            return self._format_predio_info(predio)
        
        # Si no hay coincidencias, intentar geocodificar
        return self.find_predio_by_geocoding(address)
    
    def find_predio_by_geocoding(self, address: str) -> Dict[str, Any]:
        """
        Busca un predio geocodificando la dirección y luego buscando por coordenadas.
        
        Args:
            address: Dirección a geocodificar
            
        Returns:
            Diccionario con información del predio o error
        """
        # Geocodificar la dirección
        geocode_result = self.geocoder.geocode_address(address)
        
        if geocode_result.get("status") != "OK" or not geocode_result.get("results"):
            return {
                "success": False,
                "error": "No se pudo geocodificar la dirección proporcionada"
            }
        
        # Extraer coordenadas
        location = self.geocoder.extract_location_data(geocode_result)
        
        if not location.get("success"):
            return location
        
        # Buscar predio por coordenadas
        lat = location["coordinates"]["lat"]
        lon = location["coordinates"]["lng"]
        
        return self.find_nearest_predio(lat, lon)
    
    def find_nearest_predio(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Encuentra el predio más cercano a las coordenadas dadas.
        
        Args:
            lat: Latitud
            lon: Longitud
            
        Returns:
            Diccionario con información del predio más cercano o error
        """
        if self.predios_df is None or self.predios_df.empty:
            return {"success": False, "error": "No hay datos catastrales cargados"}
        
        # Como el dataset no tiene coordenadas, usamos la dirección para geocodificar
        # y encontrar el más cercano
        
        # Simulación: Seleccionar un predio aleatorio para demostración
        # En producción, se implementaría un algoritmo de búsqueda espacial real
        
        # Seleccionar un predio aleatorio (para demostración)
        predio = self.predios_df.sample(1).iloc[0]
        
        return self._format_predio_info(predio)
    
    def _format_predio_info(self, predio: pd.Series) -> Dict[str, Any]:
        """
        Formatea la información de un predio para la respuesta.
        
        Args:
            predio: Serie de pandas con datos del predio
            
        Returns:
            Diccionario con información formateada del predio
        """
        # Mapeo de códigos de uso a descripciones
        uso_mapping = {
            '001': 'Residencial',
            '002': 'Comercial',
            '003': 'Industrial',
            '004': 'Dotacional',
            '005': 'Urbanizado No Edificado',
            '006': 'Urbanizable No Urbanizado',
            '007': 'No Urbanizable',
            '008': 'Rural',
            '009': 'Minero',
            '010': 'Comercial en Corredor Comercial',
            '011': 'Comercial en Centro Comercial',
            '012': 'Depósitos de Almacenamiento',
            '013': 'Dotacional Privado',
            '014': 'Dotacional Público',
            '015': 'Urbanizado No Edificado en Desarrollo',
            '016': 'Vías',
            '017': 'Unidad Residencial',
            '018': 'Unidad Comercial',
            '019': 'Unidad Industrial',
            '020': 'Unidad Dotacional',
            '021': 'Parqueadero Cubierto',
            '022': 'Parqueadero Descubierto',
            '023': 'Bodega',
            '024': 'Garaje Cubierto',
            '025': 'Garaje Descubierto',
            '026': 'Zonas Comunes',
            '027': 'Bien Exclusivo',
            '028': 'Agrícola',
            '029': 'Pecuario',
            '030': 'Agroindustrial',
            '031': 'Recreacional',
            '032': 'Habitacional',
            '033': 'Forestal',
            '034': 'Preservación Ambiental',
            '035': 'Agrícola con Vivienda',
            '036': 'Pecuario con Vivienda',
            '037': 'Agroindustrial con Vivienda',
            '038': 'Recreacional con Vivienda',
            '039': 'Forestal con Vivienda',
            '040': 'Preservación Ambiental con Vivienda'
        }
        
        # Extraer información relevante
        try:
            uso_codigo = predio.get('PRECUSO', '')
            uso_descripcion = uso_mapping.get(uso_codigo, 'Desconocido')
            
            return {
                "success": True,
                "predio": {
                    "chip": predio.get('PRECHIP', ''),
                    "numero_predial": predio.get('PRENUPRE', ''),
                    "direccion": predio.get('PREDIRECC', ''),
                    "barrio": predio.get('PRENBARRIO', ''),
                    "area_terreno": float(predio.get('PREATERRE', 0)),
                    "area_construida": float(predio.get('PREACONST', 0)),
                    "uso_codigo": uso_codigo,
                    "uso_descripcion": uso_descripcion,
                    "estrato": self._determinar_estrato(predio),
                    "anio_construccion": predio.get('PREVETUSTZ', ''),
                    "valor_catastral": self._calcular_valor_catastral(predio)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al formatear información del predio: {e}"
            }
    
    def _determinar_estrato(self, predio: pd.Series) -> int:
        """
        Determina el estrato socioeconómico del predio.
        
        Args:
            predio: Serie de pandas con datos del predio
            
        Returns:
            Estrato socioeconómico (1-6)
        """
        # En un escenario real, esto vendría del dataset
        # Para esta demostración, usamos un valor derivado del puntaje
        puntaje = int(predio.get('PREPUNTAJE', 0))
        
        if puntaje < 30:
            return 1
        elif puntaje < 45:
            return 2
        elif puntaje < 60:
            return 3
        elif puntaje < 75:
            return 4
        elif puntaje < 90:
            return 5
        else:
            return 6
    
    def _calcular_valor_catastral(self, predio: pd.Series) -> float:
        """
        Calcula un valor catastral aproximado basado en área y otros factores.
        
        Args:
            predio: Serie de pandas con datos del predio
            
        Returns:
            Valor catastral aproximado
        """
        # En un escenario real, esto vendría del dataset
        # Para esta demostración, calculamos un valor aproximado
        area_terreno = float(predio.get('PREATERRE', 0))
        area_construida = float(predio.get('PREACONST', 0))
        puntaje = int(predio.get('PREPUNTAJE', 0))
        
        # Valor base por metro cuadrado según puntaje
        valor_base_m2 = puntaje * 50000  # Valor ficticio para demostración
        
        # Valor total
        valor_terreno = area_terreno * valor_base_m2 * 0.3
        valor_construccion = area_construida * valor_base_m2 * 0.7
        
        return round(valor_terreno + valor_construccion, 2)
    
    def find_nearby_pois(self, lat: float, lon: float, radius: float = 500) -> Dict[str, Any]:
        """
        Encuentra puntos de interés cercanos a las coordenadas dadas.
        
        Args:
            lat: Latitud
            lon: Longitud
            radius: Radio de búsqueda en metros
            
        Returns:
            Diccionario con puntos de interés cercanos
        """
        # En un escenario real, esto consultaría una base de datos espacial
        # Para esta demostración, devolvemos datos simulados
        
        # Simulación de POIs cercanos
        pois = [
            {
                "tipo": "Colegio",
                "nombre": "Colegio Distrital",
                "distancia": 120.5,
                "direccion": "Calle 65 #10-45"
            },
            {
                "tipo": "Parque",
                "nombre": "Parque Vecinal",
                "distancia": 200.3,
                "direccion": "Carrera 11 #66-20"
            },
            {
                "tipo": "Transporte",
                "nombre": "Estación Transmilenio",
                "distancia": 350.8,
                "direccion": "Avenida Caracas #63-10"
            },
            {
                "tipo": "Comercio",
                "nombre": "Centro Comercial",
                "distancia": 450.2,
                "direccion": "Calle 67 #9-30"
            }
        ]
        
        return {
            "success": True,
            "pois": pois
        }


# Ejemplo de uso
def test_catastro_service():
    """Prueba el servicio de catastro con ejemplos."""
    data_path = "/home/ubuntu/catastro-mcp-latam/data/bogota/TPREDIO.csv"
    
    # Usar API key de Google si está disponible en variables de entorno
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    
    catastro = CatastroService(data_path, api_key)
    
    # Ejemplo 1: Buscar por dirección
    print("\n=== Búsqueda por dirección ===")
    direccion = "Calle 65G BIS A SUR 77I 09, Bogotá, Colombia"
    resultado = catastro.find_predio_by_address(direccion)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Ejemplo 2: Buscar por coordenadas
    print("\n=== Búsqueda por coordenadas ===")
    lat, lon = 4.6097, -74.0817  # Coordenadas en Bogotá
    resultado = catastro.find_nearest_predio(lat, lon)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Ejemplo 3: Buscar POIs cercanos
    print("\n=== POIs cercanos ===")
    resultado = catastro.find_nearby_pois(lat, lon)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_catastro_service()
