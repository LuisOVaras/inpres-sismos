"""
test_exporters.py

Suite de tests automáticos para verificar la integridad, determinismo y cumplimiento
de estándares de todos los exportadores del pipeline.

Ejecutar con:
    python -m unittest test/test_exporters.py
"""
import unittest
import os
import json
import sys
import pandas as pd

# Añadir raíz del proyecto al sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from exporters import csv_exporter
from exporters.location_normalizer import normalize_location
from exporters.config import (
    GEOJSON_OUT,
    METADATA_OUT,
    RECENT_OUT,
    SAMPLE_OUT,
    STATS_OUT,
)


class TestExporters(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Carga el DataFrame una vez para la suite de tests."""
        cls.df = csv_exporter.load_sismos()

    def test_deterministic_ids_are_unique_and_stable(self):
        """Verifica que los IDs generados son 100% únicos y estables."""
        ids = self.df["id"]
        self.assertEqual(len(ids), len(self.df), "La columna ID debe existir para todas las filas.")
        self.assertEqual(ids.nunique(), len(self.df), "Todos los IDs deben ser únicos (0 colisiones).")
        
        # Verificar longitud del hash SHA-256 truncado
        first_id = ids.iloc[0]
        self.assertEqual(len(first_id), 16, "El ID debe ser un hash hexadecimal de 16 caracteres.")
        
        # Verificar determinismo
        row_sample = self.df.iloc[0]
        recalculated_id = csv_exporter.make_deterministic_id(row_sample)
        self.assertEqual(first_id, recalculated_id, "El mismo evento debe generar exactamente el mismo ID.")

    def test_geojson_validity(self):
        """Verifica que sismos.geojson cumpla con el estándar RFC 7946."""
        self.assertTrue(os.path.exists(GEOJSON_OUT), "El archivo sismos.geojson debe existir.")
        
        with open(GEOJSON_OUT, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertEqual(data.get("type"), "FeatureCollection", "Debe ser de tipo FeatureCollection.")
        features = data.get("features", [])
        self.assertGreater(len(features), 0, "Debe contener features.")
        
        # Validar primera Feature
        f0 = features[0]
        self.assertEqual(f0.get("type"), "Feature", "Cada elemento debe ser de tipo Feature.")
        self.assertIn("id", f0, "La Feature debe incluir 'id' de primer nivel.")
        self.assertEqual(len(f0["id"]), 16, "El Feature.id debe ser de 16 caracteres.")
        
        geom = f0.get("geometry", {})
        self.assertEqual(geom.get("type"), "Point", "La geometría debe ser de tipo Point.")
        coords = geom.get("coordinates", [])
        self.assertEqual(len(coords), 2, "Coordinates debe tener 2 elementos [longitud, latitud].")
        
        props = f0.get("properties", {})
        self.assertIn("ubicacion_normalizada", props, "Debe incluir campos normalizados.")
        self.assertIn("es_argentina", props, "Debe incluir campos booleanos de clasificación.")

    def test_sample_geojson_range(self):
        """Verifica que sample.geojson contenga entre 100 y 300 registros."""
        self.assertTrue(os.path.exists(SAMPLE_OUT), "El archivo sample.geojson debe existir.")
        
        with open(SAMPLE_OUT, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        features = data.get("features", [])
        self.assertGreaterEqual(len(features), 100, "sample.geojson debe contener al menos 100 features.")
        self.assertLessEqual(len(features), 300, "sample.geojson no debe superar los 300 features.")

    def test_metadata_counts_match(self):
        """Verifica que total_registros en metadata.json coincida con el GeoJSON."""
        self.assertTrue(os.path.exists(METADATA_OUT), "El archivo metadata.json debe existir.")
        
        with open(METADATA_OUT, "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        with open(GEOJSON_OUT, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
            
        self.assertEqual(meta.get("schema_version"), "2.0", "La versión de schema debe ser 2.0.")
        self.assertEqual(
            meta.get("total_registros"),
            len(geojson_data.get("features", [])),
            "El total de registros en metadata debe ser igual al total de features en sismos.geojson."
        )

    def test_location_normalizer_known_cases(self):
        """Verifica las reglas clave del normalizador de ubicaciones."""
        # Caso 1: Provincia directa con typo / mayúsculas
        res1 = normalize_location("SAN JUAn")
        self.assertEqual(res1["provincia"], "San Juan")
        self.assertEqual(res1["pais"], "Argentina")
        self.assertTrue(res1["es_argentina"])
        self.assertFalse(res1["es_limite"])

        # Caso 2: TFAIAS (verificado por evidencia geográfica)
        res2 = normalize_location("TFAIAS")
        self.assertEqual(res2["provincia"], "Tierra del Fuego, Antártida e Islas del Atlántico Sur")
        self.assertTrue(res2["es_argentina"])

        # Caso 3: Límite interprovincial
        res3 = normalize_location("LIMITE SAN JUAN - MENDOZA")
        self.assertEqual(res3["provincia"], "San Juan")
        self.assertIn("Mendoza", res3["provincias"])
        self.assertTrue(res3["es_limite"])

        # Caso 4: País extranjero
        res4 = normalize_location("REPÚBLICA DE CHILE")
        self.assertEqual(res4["pais"], "Chile")
        self.assertFalse(res4["es_argentina"])

        # Caso 5: Preservación de original en caso sin clasificar
        res5 = normalize_location("REGION NOT FOUND.")
        self.assertEqual(res5["ubicacion_original"], "REGION NOT FOUND.")
        self.assertEqual(res5["tipo_ubicacion"], "desconocido")


if __name__ == "__main__":
    unittest.main()
