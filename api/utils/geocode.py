"""
Módulo de geocodificación para el MCP de Catastro Geográfico Inteligente.

Este módulo proporciona funciones para geocodificar direcciones utilizando:
1. Google Maps Geocoding API (principal)
2. Nominatim/OpenStreetMap (fallback)

Autor: Fabián Jiménez
Licencia: MIT
"""

import os
import requests
import json
import time
from typing import Dict, Any, Optional, Tuple, List

# Constantes
GOOGLE_MAPS_API_URL = "https://maps.googleapis.com/maps/api/geocode/json"
NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"

class GeocodingService:
    """Servicio de geocodificación con soporte para múltiples proveedores."""
    
    def __init__(self, google_api_key: Optional[str] = None):
        """
        Inicializa el servicio de geocodificación.
        
        Args:
            google_api_key: Clave de API de Google Maps (opcional)
        """
        self.google_api_key = google_api_key
        self.use_google = google_api_key is not None
        
    def geocode_address(self, address: str, country: Optional[str] = None) -> Dict[str, Any]:
        """
        Geocodifica una dirección utilizando el servicio principal o fallback.
        
        Args:
            address: Dirección a geocodificar
            country: País para limitar la búsqueda (opcional)
            
        Returns:
            Diccionario con los resultados de la geocodificación
        """
        if self.use_google:
            try:
                result = self._geocode_google(address, country)
                if result.get("status") == "OK":
                    return result
            except Exception as e:
                print(f"Error en geocodificación con Google: {e}")
        
        # Fallback a Nominatim si Google falla o no está disponible
        return self._geocode_nominatim(address, country)
    
    def _geocode_google(self, address: str, country: Optional[str] = None) -> Dict[str, Any]:
        """
        Geocodifica una dirección utilizando Google Maps API.
        
        Args:
            address: Dirección a geocodificar
            country: País para limitar la búsqueda (opcional)
            
        Returns:
            Diccionario con los resultados de la geocodificación
        """
        params = {
            "address": address,
            "key": self.google_api_key
        }
        
        if country:
            params["components"] = f"country:{country}"
            
        response = requests.get(GOOGLE_MAPS_API_URL, params=params)
        return response.json()
    
    def _geocode_nominatim(self, address: str, country: Optional[str] = None) -> Dict[str, Any]:
        """
        Geocodifica una dirección utilizando Nominatim/OpenStreetMap.
        
        Args:
            address: Dirección a geocodificar
            country: País para limitar la búsqueda (opcional)
            
        Returns:
            Diccionario con los resultados de la geocodificación en formato compatible
        """
        params = {
            "q": address,
            "format": "json",
            "addressdetails": 1,
            "limit": 5
        }
        
        if country:
            params["countrycodes"] = country
            
        # Añadir User-Agent para cumplir con los términos de uso de Nominatim
        headers = {
            "User-Agent": "CatastroMCP/1.0"
        }
        
        # Respetar límite de 1 solicitud por segundo
        time.sleep(1)
        
        response = requests.get(NOMINATIM_API_URL, params=params, headers=headers)
        nominatim_results = response.json()
        
        # Convertir formato Nominatim a formato similar a Google para compatibilidad
        return self._convert_nominatim_to_google_format(nominatim_results)
    
    def _convert_nominatim_to_google_format(self, nominatim_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convierte los resultados de Nominatim al formato de Google Maps API.
        
        Args:
            nominatim_results: Lista de resultados de Nominatim
            
        Returns:
            Diccionario con formato similar a Google Maps API
        """
        if not nominatim_results:
            return {
                "status": "ZERO_RESULTS",
                "results": []
            }
        
        google_format_results = []
        
        for result in nominatim_results:
            lat = float(result.get("lat", 0))
            lon = float(result.get("lon", 0))
            
            formatted_address = result.get("display_name", "")
            
            # Extraer componentes de dirección
            address_components = []
            if "address" in result:
                for component_type, value in result["address"].items():
                    address_components.append({
                        "long_name": value,
                        "short_name": value,
                        "types": [component_type]
                    })
            
            google_format_result = {
                "formatted_address": formatted_address,
                "geometry": {
                    "location": {
                        "lat": lat,
                        "lng": lon
                    },
                    "location_type": "APPROXIMATE",
                    "viewport": {
                        "northeast": {
                            "lat": lat + 0.01,
                            "lng": lon + 0.01
                        },
                        "southwest": {
                            "lat": lat - 0.01,
                            "lng": lon - 0.01
                        }
                    }
                },
                "place_id": result.get("place_id", ""),
                "types": result.get("class", "").split(","),
                "address_components": address_components
            }
            
            google_format_results.append(google_format_result)
        
        return {
            "status": "OK",
            "results": google_format_results
        }
    
    def extract_location_data(self, geocode_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae datos relevantes del resultado de geocodificación.
        
        Args:
            geocode_result: Resultado de geocodificación
            
        Returns:
            Diccionario con datos de ubicación extraídos
        """
        if geocode_result.get("status") != "OK" or not geocode_result.get("results"):
            return {
                "success": False,
                "error": "No se encontraron resultados para la dirección proporcionada"
            }
        
        result = geocode_result["results"][0]
        
        # Extraer coordenadas
        location = result["geometry"]["location"]
        lat = location["lat"]
        lng = location["lng"]
        
        # Extraer dirección formateada
        formatted_address = result["formatted_address"]
        
        # Extraer componentes de dirección
        address_components = {}
        for component in result.get("address_components", []):
            for component_type in component["types"]:
                address_components[component_type] = component["long_name"]
        
        return {
            "success": True,
            "coordinates": {
                "lat": lat,
                "lng": lng
            },
            "formatted_address": formatted_address,
            "address_components": address_components
        }


# Ejemplo de uso
def test_geocoding(address: str, country: Optional[str] = None) -> None:
    """
    Prueba la geocodificación con una dirección de ejemplo.
    
    Args:
        address: Dirección a geocodificar
        country: País para limitar la búsqueda (opcional)
    """
    # Usar API key de Google si está disponible en variables de entorno
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    
    geocoder = GeocodingService(api_key)
    
    print(f"Geocodificando dirección: {address}")
    if country:
        print(f"País: {country}")
    
    # Probar con Google Maps API si hay API key
    if api_key:
        print("\n=== Google Maps API ===")
        try:
            google_result = geocoder._geocode_google(address, country)
            print(json.dumps(google_result, indent=2, ensure_ascii=False))
            
            if google_result.get("status") == "OK":
                location_data = geocoder.extract_location_data(google_result)
                print("\nDatos extraídos:")
                print(json.dumps(location_data, indent=2, ensure_ascii=False))
            else:
                print(f"\nError: {google_result.get('status')}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Probar con Nominatim
    print("\n=== Nominatim/OpenStreetMap ===")
    try:
        nominatim_result = geocoder._geocode_nominatim(address, country)
        print(json.dumps(nominatim_result, indent=2, ensure_ascii=False))
        
        if nominatim_result.get("status") == "OK":
            location_data = geocoder.extract_location_data(nominatim_result)
            print("\nDatos extraídos:")
            print(json.dumps(location_data, indent=2, ensure_ascii=False))
        else:
            print(f"\nError: {nominatim_result.get('status')}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Ejemplos de direcciones en LATAM para pruebas
    test_addresses = [
        ("Calle 147 #11-10, Bogotá, Colombia", "co"),
        ("Av. Paulista, 1578, São Paulo, Brasil", "br"),
        ("Av. Insurgentes Sur 1602, Ciudad de México, México", "mx"),
        ("Av. 9 de Julio 1925, Buenos Aires, Argentina", "ar")
    ]
    
    for address, country in test_addresses:
        test_geocoding(address, country)
        print("\n" + "="*50 + "\n")
