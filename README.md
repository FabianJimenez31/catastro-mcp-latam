
# Catastro MCP LATAM

Un Modelo de Context Protocol (MCP) conversacional para consulta de información catastral a partir de direcciones en lenguaje natural.

## Descripción

Este proyecto implementa un protocolo conversacional (MCP) que permite:

1. **Geocodificar** direcciones utilizando Google Maps Geocoding API con fallback a Nominatim/OpenStreetMap.
2. **Cruzar** las coordenadas con datasets de catastro abiertos.
3. **Devolver** información detallada:
   - Latitud y longitud exactas
   - Dirección formateada
   - Información catastral (área, número predial, uso del suelo, estrato, etc.)
   - Entorno relevante: colegios, hospitales, parques, comercio cercano
4. **Conversar** con el usuario paso a paso, aclarando ciudad, país, o corrigiendo datos imprecisos.

## Estructura del Proyecto

```
catastro-mcp-latam/
├── api/                      # Microservicio REST
│   ├── controllers/          # Controladores de la API
│   ├── models/               # Modelos de datos
│   ├── utils/                # Utilidades (geocodificación, etc.)
│   └── app.py                # Aplicación principal Flask
├── data/                     # Datasets catastrales
│   └── bogota/               # Datos de Bogotá
├── docs/                     # Documentación
├── examples/                 # Ejemplos de uso
│   ├── mock_data.json        # Datos de ejemplo
│   └── demo.ipynb            # Notebook de demostración
├── mcp.yaml                  # Definición del protocolo MCP
├── LICENSE                   # Licencia MIT
└── README.md                 # Este archivo
```

## Requisitos

- Python 3.8+
- Dependencias:
  - Flask
  - Pandas
  - Requests
  - GeoPandas (opcional, para análisis espacial avanzado)
  - Shapely (opcional, para análisis espacial avanzado)
  - Jupyter (para ejecutar ejemplos)

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/catastro-mcp-latam.git
   cd catastro-mcp-latam
   ```

2. Crear un entorno virtual e instalar dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno (opcional):
   ```bash
   export GOOGLE_MAPS_API_KEY="tu_api_key"  # Opcional, se usa Nominatim como fallback
   ```

## Uso

### Ejecutar el microservicio REST

```bash
cd catastro-mcp-latam
python -m api.app
```

El servidor estará disponible en `http://localhost:5000`.

### Endpoints de la API

- `POST /api/catastro/geocode`: Geocodifica una dirección
- `POST /api/catastro/predio/direccion`: Busca información catastral por dirección
- `POST /api/catastro/predio/coordenadas`: Busca información catastral por coordenadas
- `POST /api/catastro/pois/cercanos`: Busca POIs cercanos a unas coordenadas
- `POST /api/catastro/consulta/completa`: Realiza una consulta completa (geocodificación + catastro + POIs)

### Ejemplos de uso

Ver el notebook `examples/demo.ipynb` para ejemplos detallados de uso.

#### Ejemplo de consulta completa

```python
import requests
import json

url = "http://localhost:5000/api/catastro/consulta/completa"
payload = {
    "direccion": "Calle 147 #11-10",
    "ciudad": "Bogotá",
    "pais": "Colombia"
}

response = requests.post(url, json=payload)
result = response.json()

print(json.dumps(result, indent=2, ensure_ascii=False))
```

## Estructura del MCP

El MCP (Modelo de Context Protocol) define un flujo conversacional para la consulta catastral:

1. **Inicio**: Bienvenida y explicación del servicio
2. **Solicitud de dirección**: El usuario proporciona una dirección
3. **Solicitud de ciudad y país**: Si no están incluidos en la dirección
4. **Confirmación**: Verificación de la dirección completa
5. **Geocodificación**: Conversión de dirección a coordenadas
6. **Consulta catastral**: Búsqueda de información del predio
7. **Búsqueda de POIs**: Identificación de puntos de interés cercanos
8. **Presentación de resultados**: Mostrar toda la información recopilada

El archivo `mcp.yaml` contiene la definición completa del protocolo.

## Extensibilidad

El sistema está diseñado para ser fácilmente extensible:

### Añadir nuevos datasets catastrales

1. Agregar el nuevo dataset en la carpeta `data/`
2. Crear una nueva clase que extienda `CatastroService` en `api/models/`
3. Implementar los métodos específicos para el nuevo dataset

### Añadir nuevas funcionalidades

1. Extender los modelos en `api/models/`
2. Añadir nuevos endpoints en `api/controllers/`
3. Actualizar el MCP en `mcp.yaml` si es necesario

## Limitaciones actuales

- El dataset de Bogotá no incluye coordenadas geográficas explícitas, por lo que la búsqueda espacial es simulada
- La información de POIs cercanos es simulada y debería conectarse a una API real (como Google Places o OpenStreetMap)
- El sistema está optimizado para direcciones en Colombia, pero puede extenderse a otros países de LATAM

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir cambios importantes antes de enviar un pull request.

## Contacto

**Autor**: Fabián Jiménez  
**Email**: fabian.jimenez.ing@gmail.com  
**Teléfono**: +573014165044

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Agradecimientos

- Unidad Administrativa Especial de Catastro Distrital (UAECD) por los datos abiertos de Bogotá
- Comunidad de OpenStreetMap por el servicio Nominatim
- Todos los contribuyentes de datos abiertos que hacen posible este tipo de proyectos cívicos
