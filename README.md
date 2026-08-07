# INPRES Sismos — Data Pipeline

> **⚠️ Este repositorio NO es un proyecto oficial del INPRES.**
> Utiliza únicamente datos públicos publicados por el [INPRES](https://www.inpres.gob.ar/) (Instituto Nacional de Prevención Sísmica de Argentina).

Fuente oficial de datos sísmicos de Argentina.
Este repositorio obtiene, procesa y publica automáticamente los datos del INPRES en múltiples formatos listos para consumir.

---

## ¿Qué hace este repositorio?

1. **Scrapea** diariamente el sitio del INPRES usando Selenium.
2. **Normaliza** los datos (fechas, horas, profundidades, indicador de sentido).
3. **Deduplica** registros para garantizar integridad.
4. **Actualiza** la base de datos SQLite.
5. **Sincroniza** con Supabase.
6. **Exporta** los datos en formatos reutilizables (GeoJSON, JSON).
7. **Publica** todo automáticamente vía GitHub Actions.

---

## Archivos de datos disponibles

Todos los archivos se actualizan automáticamente cada día. Podés consumirlos directamente desde GitHub raw.

| Archivo | Formato | Descripción |
|---|---|---|
| [`data/sismos.csv`](data/sismos.csv) | CSV | Dataset completo. Fuente de verdad del pipeline. |
| [`data/sismos.db`](data/sismos.db) | SQLite | Base de datos histórica. Permite consultas SQL directas. |
| [`data/exports/sismos.geojson`](data/exports/sismos.geojson) | GeoJSON | FeatureCollection estándar RFC 7946. Consumible directamente por MapLibre GL JS, Leaflet, QGIS, etc. |
| [`data/exports/metadata.json`](data/exports/metadata.json) | JSON | Metadatos del dataset: total de registros, rango de fechas, rango de magnitudes, provincias, timestamp de última actualización. |
| [`data/exports/sismos_recientes.json`](data/exports/sismos_recientes.json) | JSON | Últimos 500 sismos en JSON plano. Alternativa liviana para aplicaciones de tiempo real. |
| [`data/sismos_historicos.csv`](data/sismos_historicos.csv) | CSV | Datos históricos recopilados con el spider Scrapy. |

### URLs raw para consumo directo

```
https://raw.githubusercontent.com/LuisOVaras/inpres-sismos/main/data/sismos.csv
https://raw.githubusercontent.com/LuisOVaras/inpres-sismos/main/data/exports/sismos.geojson
https://raw.githubusercontent.com/LuisOVaras/inpres-sismos/main/data/exports/metadata.json
https://raw.githubusercontent.com/LuisOVaras/inpres-sismos/main/data/exports/sismos_recientes.json
```

---

## Esquema de datos

| Campo | Tipo | Descripción |
|---|---|---|
| `fecha` | string `DD/MM/YYYY` | Fecha del evento sísmico. |
| `hora` | string `HH:MM:SS` | Hora del evento (UTC). |
| `latitud` | float | Latitud geográfica (negativa = Sur). |
| `longitud` | float | Longitud geográfica (negativa = Oeste). |
| `profundidad` | float | Profundidad en kilómetros. |
| `magnitud` | float | Magnitud del evento (escala Richter / Mw). |
| `provincia` | string | Provincia argentina más cercana al epicentro. |
| `sentido` | string `Si/No` | Indica si el sismo fue reportado como sentido por la población. |

---

## Pipeline de datos

```
INPRES (sitio web)
       │
       ▼
selenium/actualizar_sismos.py   ← scraping + normalización → data/sismos.csv
       │
       ▼
db_scripts/actualizar_database.py   → data/sismos.db  (SQLite)
       │
       ▼
db_scripts/actualizar_supabase.py   → Supabase  (sync de los 100 más recientes)
       │
       ▼
exporters/run_exports.py
   ├── geojson_exporter.py     → data/exports/sismos.geojson
   ├── metadata_exporter.py    → data/exports/metadata.json
   └── recent_exporter.py      → data/exports/sismos_recientes.json
       │
       ▼
git commit + push  (GitHub Actions lo publica automáticamente)
```

---

## Automatización

| Workflow | Frecuencia | Descripción |
|---|---|---|
| `scraping_daily.yml` | Diario a las 10:20 UTC | Pipeline completo: scraping → SQLite → Supabase → exports → push. |
| `updatedb.yml` | Manual | Actualiza únicamente la base de datos SQLite desde el CSV. |

---

## Estructura del repositorio

```
inpres-sismos/
├── .github/
│   └── workflows/
│       ├── scraping_daily.yml     # Pipeline principal diario
│       └── updatedb.yml           # Actualización manual de DB
├── data/
│   ├── sismos.csv                 # Dataset completo (fuente de verdad)
│   ├── sismos.db                  # Base de datos SQLite
│   ├── sismos_historicos.csv      # Datos históricos (spider Scrapy)
│   ├── exports/
│   │   ├── sismos.geojson         # GeoJSON exportado
│   │   ├── metadata.json          # Metadatos del dataset
│   │   └── sismos_recientes.json  # Últimos 500 registros
│   ├── provincia/                 # Shapefiles de provincias (IGN)
│   └── pais/                      # Shapefile del país (IGN)
├── exporters/
│   ├── config.py                  # Rutas comunes
│   ├── run_exports.py             # Orquestador de exportaciones
│   ├── csv_exporter.py            # Lector del CSV principal
│   ├── geojson_exporter.py        # Exportador GeoJSON
│   ├── metadata_exporter.py       # Exportador de metadatos
│   └── recent_exporter.py         # Exportador de recientes
└── inpres_sismos/
    └── inpres_sismos/
        ├── selenium/
        │   └── actualizar_sismos.py    # Scraper principal
        ├── db_scripts/
        │   ├── actualizar_database.py  # CSV → SQLite
        │   ├── actualizar_supabase.py  # Sync Supabase
        │   └── crear_database.py       # Inicialización DB
        └── spiders/
            └── historicos.py           # Spider datos históricos
```

---

## Tecnologías

- **[Selenium WebDriver](https://www.selenium.dev/)** — Extracción automatizada del sitio del INPRES.
- **[Scrapy](https://scrapy.org/)** — Spider para datos históricos (ejecución manual cuando es necesario).
- **[Pandas](https://pandas.pydata.org/)** — Procesamiento y normalización del dataset.
- **[SQLite](https://www.sqlite.org/)** — Base de datos histórica local.
- **[Supabase](https://supabase.com/)** — Sincronización remota de los registros más recientes.
- **[GitHub Actions](https://github.com/features/actions)** — Automatización del pipeline diario.

---

## Dependencias

```bash
pip install -r requirements.txt
```

---

## Uso del pipeline de forma local

```bash
# 1. Clonar el repositorio
git clone https://github.com/LuisOVaras/inpres-sismos.git
cd inpres-sismos

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar el scraper manualmente
python inpres_sismos/inpres_sismos/selenium/actualizar_sismos.py

# 4. Actualizar la base de datos
python inpres_sismos/inpres_sismos/db_scripts/actualizar_database.py

# 5. Generar exportaciones
python exporters/run_exports.py
```

---

## Proyectos que consumen estos datos

- **argentina-earthquakes** — Visualización interactiva de sismos (React + MapLibre + Three.js). *(enlace cuando esté disponible)*

---

## Licencia y atribución

Los datos provienen del [INPRES](https://www.inpres.gob.ar/) y son de acceso público.
Este repositorio es un proyecto personal independiente y no tiene ninguna afiliación oficial con el INPRES.
