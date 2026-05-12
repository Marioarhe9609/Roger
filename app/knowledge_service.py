"""
Knowledge service for querying Firestore collections.
Provides search and retrieval of enterprise architecture data.
"""
import logging
from google.cloud import firestore
from app.config import (
    COLLECTION_DATOS_MAESTROS,
    COLLECTION_DICCIONARIO,
    COLLECTION_FLUJOS,
    COLLECTION_METADATA,
    GCP_PROJECT_ID,
)

logger = logging.getLogger(__name__)

_db = None


def _get_db():
    """Lazy initialization of Firestore client."""
    global _db
    if _db is None:
        _db = firestore.Client(project=GCP_PROJECT_ID)
    return _db


def get_all_tablas():
    """Retrieve all master data tables."""
    db = _get_db()
    docs = db.collection(COLLECTION_DATOS_MAESTROS).stream()
    tablas = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        tablas.append(data)
    return tablas


def get_tabla_by_name(nombre):
    """Search for a table by name (case-insensitive partial match)."""
    db = _get_db()
    docs = db.collection(COLLECTION_DATOS_MAESTROS).stream()
    nombre_lower = nombre.lower().strip()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        table_name = data.get("nombre_tabla", "").lower()
        if nombre_lower in table_name or table_name in nombre_lower:
            results.append(data)
    return results


def get_diccionario_by_tabla(nombre_tabla):
    """Get all dictionary entries for a specific table/file."""
    db = _get_db()
    docs = db.collection(COLLECTION_DICCIONARIO).stream()
    nombre_lower = nombre_tabla.lower().strip()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        archivo = data.get("nombre_archivo", "").lower()
        tabla_ref = data.get("tabla_referencia", "").lower()
        if nombre_lower in archivo or nombre_lower in tabla_ref:
            results.append(data)
    return results


def get_all_diccionario():
    """Retrieve all dictionary entries."""
    db = _get_db()
    docs = db.collection(COLLECTION_DICCIONARIO).stream()
    entries = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        entries.append(data)
    return entries


def get_all_flujos():
    """Retrieve all information flow descriptions."""
    db = _get_db()
    docs = db.collection(COLLECTION_FLUJOS).stream()
    flujos = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        flujos.append(data)
    return flujos


def get_flujo_by_name(nombre):
    """Search for a flow by name (case-insensitive partial match)."""
    db = _get_db()
    docs = db.collection(COLLECTION_FLUJOS).stream()
    nombre_lower = nombre.lower().strip()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        flow_name = data.get("nombre", "").lower()
        desc = data.get("descripcion", "").lower()
        if nombre_lower in flow_name or nombre_lower in desc:
            results.append(data)
    return results


def search_all(query):
    """
    Search across all collections for a given query string.
    Returns categorized results.
    """
    query_lower = query.lower().strip()
    results = {
        "tablas": [],
        "variables": [],
        "flujos": [],
    }

    # Search tables
    tablas = get_all_tablas()
    for tabla in tablas:
        searchable = " ".join([
            tabla.get("nombre_tabla", ""),
            tabla.get("descripcion", ""),
            tabla.get("area", ""),
            " ".join(tabla.get("atributos", [])),
        ]).lower()
        if query_lower in searchable:
            results["tablas"].append(tabla)

    # Search dictionary variables
    variables = get_all_diccionario()
    for var in variables:
        searchable = " ".join([
            var.get("nombre_variable", ""),
            var.get("descripcion_variable", ""),
            var.get("nombre_archivo", ""),
            var.get("tipo_dato", ""),
        ]).lower()
        if query_lower in searchable:
            results["variables"].append(var)

    # Search flows
    flujos = get_all_flujos()
    for flujo in flujos:
        searchable = " ".join([
            flujo.get("nombre", ""),
            flujo.get("descripcion", ""),
            " ".join(flujo.get("sistemas", [])),
            " ".join(flujo.get("etapas", [])),
        ]).lower()
        if query_lower in searchable:
            results["flujos"].append(flujo)

    return results


def build_context_for_query(query):
    """
    Build a context string from Firestore data relevant to the user's query.
    Used for RAG with Gemini.
    """
    results = search_all(query)
    context_parts = []

    if results["tablas"]:
        context_parts.append("### Tablas Encontradas")
        for t in results["tablas"][:5]:
            attrs = ", ".join(t.get("atributos", []))
            context_parts.append(
                f"- **{t.get('nombre_tabla', 'N/A')}** ({t.get('area', '')}): "
                f"{t.get('descripcion', '')} | Atributos: {attrs} | "
                f"Georreferenciado: {t.get('georreferenciado', 'N/A')}"
            )

    if results["variables"]:
        context_parts.append("\n### Variables Encontradas")
        for v in results["variables"][:10]:
            pk = "🔑 PK" if v.get("llave_primaria") else ""
            fk = "🔗 FK" if v.get("llave_foranea") else ""
            context_parts.append(
                f"- **{v.get('nombre_variable', 'N/A')}** "
                f"(Archivo: {v.get('nombre_archivo', 'N/A')}) | "
                f"Tipo: {v.get('tipo_dato', 'N/A')} | "
                f"{v.get('descripcion_variable', '')} {pk} {fk}"
            )

    if results["flujos"]:
        context_parts.append("\n### Flujos Encontrados")
        for f in results["flujos"][:5]:
            sistemas = ", ".join(f.get("sistemas", []))
            etapas = " → ".join(f.get("etapas", []))
            context_parts.append(
                f"- **{f.get('nombre', 'N/A')}**: {f.get('descripcion', '')} | "
                f"Sistemas: {sistemas} | Etapas: {etapas}"
            )

    if not any(results.values()):
        # Return full summary if no specific match
        context_parts.append("### Resumen General")
        all_tablas = get_all_tablas()
        if all_tablas:
            context_parts.append("**Tablas disponibles:**")
            for t in all_tablas:
                attrs = ", ".join(t.get("atributos", []))
                context_parts.append(f"- {t.get('nombre_tabla', 'N/A')}: {attrs}")

        all_flujos = get_all_flujos()
        if all_flujos:
            context_parts.append("\n**Flujos disponibles:**")
            for f in all_flujos:
                context_parts.append(f"- {f.get('nombre', 'N/A')}: {f.get('descripcion', '')[:100]}")

    return "\n".join(context_parts)
