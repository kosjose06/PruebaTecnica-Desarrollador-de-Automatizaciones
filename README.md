# PruebaTecnica-Desarrollador-de-Automatizaciones
Prueba ETL extracción de datos 
Descripción de la Solución
Proceso ETL automatizado que extrae información de contactos empresariales desde una página web, filtra empresas según criterios específicos, almacena los datos en MongoDB y registra cada proceso ETL mediante una API REST.
Funcionalidades Principales

Web Scraping: Extracción automatizada de datos desde tabla HTML
Filtrado Inteligente: Criterios de negocio para empresas tecnológicas y cargos ejecutivos
Almacenamiento en MongoDB: Inserción con prevención de duplicados
Tracking de Procesos: Registro mediante API REST
Containerización: Solución dockerizada y portable
Logs Estructurados: Formato JSON para observabilidad
Manejo de Errores: Reintentos automáticos y recuperación de fallos

Criterios de Filtrado

Empresas Tecnológicas: Contienen palabras como "Tech", "Data", "Cloud", "Digital", "Software", "System"
Cargos Directivos: CEO, CTO, Director, VP, Chief, Vice President, President
Múltiples Contactos: Empresas con mínimo 2 contactos registrados

Resultados de Ejecución Real

Contactos extraídos: 60 registros
Contactos filtrados: 10 registros
Contactos insertados: 5 nuevos registros
Duplicados omitidos: 5 registros
Tiempo de procesamiento: 2.12 segundos
Estado: Exitoso

🔧 Instrucciones de Instalación
Prerequisitos

Python 3.11+
Docker 20.0+
Docker Compose 2.0+
Git

Instalación Local (Desarrollo)
bash# Clonar repositorio
git clone <tu-repositorio-url>
cd etl-business-contacts

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
Instalación con Docker
bash# Clonar repositorio
git clone <tu-repositorio-url>
cd etl-business-contacts

# Construir imagen
docker build -t etl-scraper .
▶ Comandos de Ejecución
Ejecución con Python Local
bash# Configurar variables de entorno (Windows PowerShell)
$env:WEB_URL="http://52.0.216.22:7080"
$env:MONGODB_URI="mongodb://etl_user:etl_pass123@52.0.216.22:27017/etl_tracker"
$env:API_BASE_URL="http://52.0.216.22:7300"

# Configurar variables de entorno (Linux/Mac)
export WEB_URL=http://52.0.216.22:7080
export MONGODB_URI=mongodb://etl_user:etl_pass123@52.0.216.22:27017/etl_tracker
export API_BASE_URL=http://52.0.216.22:7300

# Ejecutar ETL
python main.py
Ejecución con Docker
bash# Método 1: Docker Run
docker run --rm \
  -e WEB_URL="http://52.0.216.22:7080" \
  -e MONGODB_URI="mongodb://etl_user:etl_pass123@52.0.216.22:27017/etl_tracker" \
  -e API_BASE_URL="http://52.0.216.22:7300" \
  etl-scraper

# Método 2: Docker Compose
docker-compose up --build

# Método 3: Docker Compose en background
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f etl-scraper

Configuración de Variables
Archivo .env
bashWEB_URL=http://52.0.216.22:7080
MONGODB_URI=mongodb://etl_user:etl_pass123@52.0.216.22:27017/etl_tracker
API_BASE_URL=http://52.0.216.22:7300
LOG_LEVEL=info
RETRY_ATTEMPTS=3
PROCESO_DESCRIPCION="Extracción contactos empresariales Q3 2024"




 Ejemplos de Uso
Ejemplo 1: Ejecución Básica

Ejemplo 1: Ejecución Básica
bash# Con Docker
docker-compose up --build

# {"timestamp": "2025-09-02 23:44:18,259", "level": "INFO", "message": "ETL Business Contacts Scraper Starting..."}
# {"timestamp": "2025-09-02 23:44:18,259", "level": "INFO", "message": "Starting ETL process with ID: ec4851d7-8ea5-47be-a664-bef9caee423f"}
# {"timestamp": "2025-09-02 23:44:18,459", "level": "INFO", "message": "Extracted 60 valid contacts"}
# {"timestamp": "2025-09-02 23:44:18,459", "level": "INFO", "message": "Filtered 10 contacts from 60 total"}
# {"timestamp": "2025-09-02 23:44:19,181", "level": "INFO", "message": "Inserted 5 new contacts into MongoDB"}
# {"timestamp": "2025-09-02 23:44:20,373", "level": "INFO", "message": "ETL process registered successfully"}
# {"timestamp": "2025-09-02 23:44:20,381", "level": "INFO", "message": "ETL process completed successfully!"}


Ejemplo 2: Ejecución con Logs Detallados
bash# Docker con debug
docker run --rm \
  -e LOG_LEVEL="debug" \
  -e WEB_URL="http://52.0.216.22:7080" \
  -e MONGODB_URI="mongodb://etl_user:etl_pass123@52.0.216.22:27017/etl_tracker" \
  -e API_BASE_URL="http://52.0.216.22:7300" \
  etl-scraper

# Salida esperada incluye detalles adicionales de debugging
Ejemplo 3: Ejecución con Descripción Personalizada
bash# Python local con descripción personalizada
export PROCESO_DESCRIPCION="ETL Scraping - Empresas Tech Enero 2024"
python main.py

# Docker con descripción personalizada
docker run --rm \
  -e PROCESO_DESCRIPCION="ETL Scraping - Empresas Tech Enero 2024" \
  -e WEB_URL="http://52.0.216.22:7080" \
  -e MONGODB_URI="mongodb://etl_user:etl_pass123@52.0.216.22:27017/etl_tracker" \
  -e API_BASE_URL="http://52.0.216.22:7300" \
  etl-scraper

 Troubleshooting Común
Error: "No se puede conectar a MongoDB"
bash# Diagnóstico
# Verificar conectividad a MongoDB
docker run --rm mongo:5 mongosh "mongodb://etl_user:etl_pass123@52.0.216.22:27017/etl_tracker" --eval "db.adminCommand('ismaster')"

# Solución
# 1. Verificar que las credenciales sean correctas
# 2. Confirmar que el servidor MongoDB esté disponible
# 3. Revisar reglas de firewall
Error: "Timeout en web scraping"
bash# Diagnóstico
curl -v http://52.0.216.22:7080

# Solución
# Aumentar reintentos
docker run --rm -e RETRY_ATTEMPTS="5" etl-scraper

# Verificar conectividad de red
ping 52.0.216.22
Error: "No se encuentra la tabla HTML"
bash# Diagnóstico
curl -s http://52.0.216.22:7080 | grep -i "<table"

# Solución
# 1. Verificar que la página web esté disponible
# 2. Confirmar estructura HTML de la tabla
# 3. Habilitar logs debug para más detalles
docker run --rm -e LOG_LEVEL="debug" etl-scraper
Error: "API registration failed"
bash# Diagnóstico
curl -X GET http://52.0.216.22:7300/api/etl?limit=1

# Test manual de POST
curl -X POST http://52.0.216.22:7300/api/etl \
  -H "Content-Type: application/json" \
  -d '{"cantidadDatos": 1, "descripcion": "test"}'

# Solución
# 1. Verificar que la API esté disponible
# 2. Confirmar formato correcto del payload
# 3. Revisar logs para detalles del error
Error: "TypeError: Retry.init() got unexpected keyword argument 'method_whitelist'"
bash# Solución 1: Actualizar urllib3
pip install urllib3==1.26.18

# Solución 2: Actualizar código (ya implementado)
# Cambiar 'method_whitelist' por 'allowed_methods' en main.py
Problemas de Permisos Docker
bash# Windows: Ejecutar PowerShell como Administrador
# Linux/Mac: Usar sudo si es necesario

# Reconstruir imagen sin cache
docker build --no-cache -t etl-scraper .

# Verificar permisos del usuario dentro del contenedor
docker run --rm etl-scraper whoami
Problemas con Variables de Entorno
bash# Verificar variables cargadas
# Windows
echo $env:WEB_URL


# En Docker, verificar variables
docker run --rm etl-scraper env | grep -E "(WEB_URL|MONGODB_URI|API_BASE_URL)

