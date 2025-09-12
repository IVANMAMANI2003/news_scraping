from datetime import datetime

from itemadapter import ItemAdapter


class CleanPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Normalizar fecha
        if adapter.get("fecha") is None:
            adapter["fecha"] = datetime.utcnow().isoformat()

        # Fecha de extracción
        adapter["fecha_extraccion"] = datetime.utcnow().isoformat()

        # Limpiar contenido
        contenido = adapter.get("contenido", "")
        if contenido:
            adapter["caracteres_contenido"] = len(contenido)
            adapter["palabras_contenido"] = len(contenido.split())

        return item
