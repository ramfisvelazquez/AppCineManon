"""
utils/movie_loader.py
Carga peliculas combinando TMDB + MySQL + JSON local.
- Si hay API key TMDB: trae cartelera, populares, top_rated, upcoming
- Si no hay API key: usa el JSON local de respaldo (con posters y precios)
- Las peliculas de BD con imagen/precio vacio se enriquecen con TMDB
"""

import json, os
from typing import Optional, List, Dict, Any

_THIS_DIR = os.path.dirname(__file__)
DATA_PATH  = os.path.join(_THIS_DIR, "..", "data", "movies.json")
PLACEHOLDER = "https://placehold.co/500x750?text=Sin+imagen"


def _load_json_fallback() -> List[Dict[str, Any]]:
    try:
        with open(os.path.abspath(DATA_PATH), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _serialize(obj):
    from datetime import datetime, date, timedelta
    from decimal import Decimal
    if isinstance(obj, (datetime, date)): return obj.isoformat()
    if isinstance(obj, timedelta):        return str(obj)
    if isinstance(obj, Decimal):          return float(obj)
    return str(obj)


def _row_to_movie(row: dict, funciones: List[dict]) -> Dict[str, Any]:
    pid = row.get("id")
    horarios = [
        f["fecha_hora"].strftime("%H:%M")
        if hasattr(f.get("fecha_hora", ""), "strftime")
        else str(f.get("fecha_hora", ""))[:5]
        for f in funciones if f.get("pelicula_id") == pid
    ]
    precio = float(_serialize(row["precio"])) if row.get("precio") is not None else 0.0
    imagen   = str(row.get("poster_url")   or row.get("imagen")   or "").strip()
    backdrop = str(row.get("backdrop_url") or row.get("backdrop") or "").strip()
    return {
        "id":            str(pid),
        "nombre":        row.get("titulo", ""),
        "descripcion":   row.get("sinopsis", row.get("descripcion", "")),
        "categoria":     row.get("genero",  row.get("categoria", "")),
        "duracion":      str(row.get("duracion_min", row.get("duracion", "")) or ""),
        "precio":        precio,
        "imagen":        imagen  or PLACEHOLDER,
        "backdrop":      backdrop or PLACEHOLDER,
        "horarios":      horarios or ["16:00", "18:30", "21:00"],
        "vip":           bool(row.get("vip", False)),
        "clasificacion": row.get("clasificacion", ""),
        "fecha_estreno": str(row.get("fecha_estreno", "")),
        "director":      row.get("director", ""),
        "tmdb_id":       row.get("tmdb_id"),
        "calificacion_tmdb": float(row.get("calificacion_tmdb") or 0),
        "popularidad":   0.0,
        # Marcar que necesita enriquecimiento si le faltan datos
        "_needs_enrichment": not imagen or precio == 0,
    }


def _enriquecer_con_tmdb(movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Busca en TMDB las peliculas de BD que tienen imagen vacia o precio 0."""
    needs = [m for m in movies if m.get("_needs_enrichment")]
    if not needs:
        return movies

    try:
        from cinemax.utils.tmdb import buscar_pelicula_tmdb, IMG_BASE, IMG_BACKDROP
        import os
        key = os.getenv("TMDB_API_KEY", "").strip()
        if not key or key == "TU_API_KEY_AQUI":
            return movies
    except Exception:
        return movies

    enriched_ids = set()
    result = []

    for m in movies:
        if not m.get("_needs_enrichment"):
            m.pop("_needs_enrichment", None)
            result.append(m)
            continue

        nombre = m.get("nombre", "")
        try:
            hits = buscar_pelicula_tmdb(nombre, paginas=1)
            if hits:
                hit = hits[0]
                if not m["imagen"] or m["imagen"] == PLACEHOLDER:
                    m["imagen"]   = hit.get("imagen",   PLACEHOLDER)
                    m["backdrop"] = hit.get("backdrop", PLACEHOLDER)
                if m["precio"] == 0:
                    m["precio"] = 350.0
                if not m["calificacion_tmdb"]:
                    m["calificacion_tmdb"] = hit.get("calificacion_tmdb", 0)
                if not m["tmdb_id"]:
                    m["tmdb_id"] = hit.get("tmdb_id")
                m["popularidad"] = hit.get("popularidad", 0)
                print(f"  Enriquecida '{nombre}' con TMDB")
        except Exception as e:
            print(f"  Error enriqueciendo '{nombre}': {e}")

        m.pop("_needs_enrichment", None)
        result.append(m)

    return result


def _dedup(movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen_tmdb: set = set()
    seen_name: set = set()
    result:    list = []
    for m in movies:
        tid  = m.get("tmdb_id")
        name = m.get("nombre", "").strip().lower()
        if tid and tid in seen_tmdb: continue
        if name and name in seen_name: continue
        if tid:  seen_tmdb.add(tid)
        if name: seen_name.add(name)
        result.append(m)
    return result


# ── TMDB wrappers con manejo de errores independiente ─────────────────────────
def _tmdb_fetch(fn_name: str, **kwargs):
    try:
        from cinemax.utils import tmdb
        fn = getattr(tmdb, fn_name)
        return fn(**kwargs)
    except ValueError as e:
        # API key no configurada — no spammear logs
        return []
    except Exception as e:
        print(f"TMDB {fn_name} error: {e}")
        return []


# ── Carga principal ───────────────────────────────────────────────────────────
def load_movies() -> List[Dict[str, Any]]:
    todas: List[Dict[str, Any]] = []
    tmdb_disponible = False

    # 1. TMDB (solo si hay API key)
    for fn, kwargs, label in [
        ("peliculas_cartelera",     {"paginas": 2}, "cartelera"),
        ("peliculas_populares",     {"paginas": 2}, "populares"),
        ("peliculas_mejor_calificadas", {"paginas": 1}, "top_rated"),
        ("proximos_estrenos",       {"paginas": 1}, "upcoming"),
    ]:
        result = _tmdb_fetch(fn, **kwargs)
        if result:
            todas += result
            tmdb_disponible = True

    # 2. MySQL
    bd_movies = []
    try:
        from cinemax.utils.db import query
        peliculas_bd = query("SELECT * FROM peliculas ORDER BY fecha_estreno DESC")
        if peliculas_bd:
            try:
                funciones = query("SELECT pelicula_id, fecha_hora FROM funciones ORDER BY fecha_hora")
            except Exception:
                funciones = []
            bd_movies = [_row_to_movie(p, funciones) for p in peliculas_bd]
            print(f"MySQL: {len(bd_movies)} peliculas")
    except Exception as e:
        print(f"MySQL error: {e}")

    # 3. Enriquecer peliculas de BD que tienen datos incompletos
    if bd_movies:
        bd_movies = _enriquecer_con_tmdb(bd_movies)
        todas += bd_movies

    # 4. JSON local: siempre incluir (complementa el catálogo)
    json_movies = _load_json_fallback()
    if json_movies:
        todas += json_movies
        print(f"JSON local: {len(json_movies)} peliculas")

    # 5. Si absolutamente nada cargó
    if not todas:
        print("ADVERTENCIA: ninguna fuente devolvio datos")
        return []

    return _dedup(todas)


# ── Consultas ─────────────────────────────────────────────────────────────────
def get_featured_movies() -> List[Dict[str, Any]]:
    movies   = load_movies()
    featured = [m for m in movies if m.get("vip")]
    return featured if featured else movies[:5]

def get_vip_movies() -> List[Dict[str, Any]]:
    return [m for m in load_movies() if m.get("vip")]

def get_trending_movies() -> List[Dict[str, Any]]:
    return sorted(load_movies(), key=lambda m: float(m.get("popularidad", 0) or 0), reverse=True)[:20]

def get_top_rated_movies() -> List[Dict[str, Any]]:
    all_m = [m for m in load_movies() if m.get("calificacion_tmdb")]
    return sorted(all_m, key=lambda m: float(m.get("calificacion_tmdb", 0) or 0), reverse=True)[:20]

def get_upcoming_movies() -> List[Dict[str, Any]]:
    return [m for m in load_movies() if m.get("categoria") == "Proximo estreno"]

def search_movies(query_str: str) -> List[Dict[str, Any]]:
    if not query_str:
        return load_movies()
    q = query_str.lower()
    local = [m for m in load_movies()
             if q in m.get("nombre", "").lower()
             or q in m.get("descripcion", "").lower()
             or q in m.get("categoria", "").lower()]
    if local:
        return local
    return _tmdb_fetch("buscar_pelicula_tmdb", titulo=query_str, paginas=1)

def filter_by_category(category: str) -> List[Dict[str, Any]]:
    if not category or category == "Todos":
        return load_movies()
    return [m for m in load_movies() if m.get("categoria", "") == category]

def sort_movies(movies: List[Dict[str, Any]], by: str = "nombre", asc: bool = True) -> List[Dict[str, Any]]:
    reverse = not asc
    try:
        if by in ("precio", "calificacion_tmdb", "popularidad"):
            return sorted(movies, key=lambda m: float(m.get(by, 0) or 0), reverse=reverse)
        return sorted(movies, key=lambda m: str(m.get(by, "")), reverse=reverse)
    except (TypeError, ValueError):
        return movies

def get_movie_by_id(movie_id: str) -> Optional[Dict[str, Any]]:
    # MySQL
    try:
        from cinemax.utils.db import query as db_query
        rows = db_query("SELECT * FROM peliculas WHERE id = %s", (movie_id,))
        if rows:
            funciones = db_query(
                "SELECT pelicula_id, fecha_hora FROM funciones WHERE pelicula_id = %s ORDER BY fecha_hora",
                (movie_id,),
            )
            m = _row_to_movie(rows[0], funciones)
            m = _enriquecer_con_tmdb([m])[0]
            return m
    except Exception:
        pass

    # TMDB directo
    if str(movie_id).startswith("tmdb_"):
        tmdb_id_str = movie_id.replace("tmdb_", "")
        if tmdb_id_str.isdigit():
            try:
                from cinemax.utils.tmdb import detalle_pelicula
                r = detalle_pelicula(int(tmdb_id_str))
                if r: return r
            except Exception:
                pass

    return next((m for m in load_movies() if str(m.get("id")) == str(movie_id)), None)

def get_categories() -> List[str]:
    try:
        from cinemax.utils.tmdb import GENEROS_MAP
        tmdb_cats = list(GENEROS_MAP.values())
    except Exception:
        tmdb_cats = []
    try:
        from cinemax.utils.db import query as db_query
        rows = db_query("SELECT nombre FROM generos ORDER BY nombre")
        bd_cats = [r["nombre"] for r in rows if r.get("nombre")]
        all_cats = list(dict.fromkeys(tmdb_cats + bd_cats))
        return ["Todos"] + sorted(all_cats)
    except Exception:
        pass
    movies   = load_movies()
    dynamic  = sorted(set(m.get("categoria", "") for m in movies if m.get("categoria")))
    all_cats = list(dict.fromkeys(tmdb_cats + dynamic))
    return ["Todos"] + sorted(all_cats)
