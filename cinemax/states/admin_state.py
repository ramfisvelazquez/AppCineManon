"""""
states/admin_state.py
Estado del panel de administración — añadir y editar películas.
"""

import reflex as rx
import json
import os
from typing import Dict, Any, List

from cinemax.utils.movie_loader import load_movies, DATA_PATH


CATEGORIAS = [
    "Acción", "Animación", "Ciencia Ficción", "Comedia",
    "Drama", "Horror", "Infantil", "Romance", "Suspenso", "Thriller",
]

CLASIFICACIONES = ["G", "PG", "PG-13", "R", "NC-17"]


def _empty_form() -> Dict[str, Any]:
    return {
        "id": "",
        "nombre": "",
        "descripcion": "",
        "categoria": "",
        "duracion": "",
        "clasificacion": "",
        "precio": "",
        "vip": False,
        "imagen": "",
        "banner": "",
        "trailer": "",
        "horarios_str": "",  # comma-separated, e.g. "14:00, 17:30, 21:00"
    }


class AdminState(rx.State):
    # ── Lista de películas ────────────────────────────────────────────
    admin_movies: List[Dict[str, Any]] = []

    # ── Formulario ───────────────────────────────────────────────────
    form_mode: str = "idle"           # idle | add | edit
    editing_id: str = ""

    form_nombre: str = ""
    form_descripcion: str = ""
    form_categoria: str = ""
    form_duracion: str = ""
    form_clasificacion: str = ""
    form_precio: str = ""
    form_vip: bool = False
    form_imagen: str = ""
    form_banner: str = ""
    form_trailer: str = ""
    form_horarios: str = ""

    # ── Errores ──────────────────────────────────────────────────────
    form_error: str = ""
    form_success: str = ""

    # ── UI ────────────────────────────────────────────────────────────
    show_delete_dialog: bool = False
    delete_target_id: str = ""
    delete_target_name: str = ""
    search_admin: str = ""

    # ── Lifecycle ────────────────────────────────────────────────────

    def load_admin_movies(self):
        """Carga películas al entrar al panel."""
        from cinemax.states.app_state import AppState
        self.admin_movies = load_movies()
        self.form_mode = "idle"
        self.form_error = ""
        self.form_success = ""

    # ── Búsqueda ─────────────────────────────────────────────────────

    def set_search_admin(self, val: str):
        self.search_admin = val

    @rx.var
    def filtered_admin_movies(self) -> List[Dict[str, Any]]:
        q = self.search_admin.lower().strip()
        if not q:
            return self.admin_movies
        return [
            m for m in self.admin_movies
            if q in m.get("nombre", "").lower()
            or q in m.get("categoria", "").lower()
        ]

    @rx.var
    def total_movies_count(self) -> int:
        return len(self.admin_movies)

    @rx.var
    def vip_movies_count(self) -> int:
        return sum(1 for m in self.admin_movies if m.get("vip", False))

    @rx.var
    def filtered_count(self) -> int:
        return len(self.filtered_admin_movies)

    # ── Formulario — abrir ────────────────────────────────────────────

    def open_add_form(self):
        self._clear_form()
        self.form_mode = "add"
        self.editing_id = ""
        self.form_error = ""
        self.form_success = ""

    def open_edit_form(self, movie_id: str):
        movie = next(
            (m for m in self.admin_movies if str(m.get("id")) == str(movie_id)),
            None,
        )
        if not movie:
            return
        self.editing_id = str(movie_id)
        self.form_nombre = movie.get("nombre", "")
        self.form_descripcion = movie.get("descripcion", "")
        self.form_categoria = movie.get("categoria", "")
        self.form_duracion = movie.get("duracion", "")
        self.form_clasificacion = movie.get("clasificacion", "")
        self.form_precio = str(movie.get("precio", ""))
        self.form_vip = bool(movie.get("vip", False))
        self.form_imagen = movie.get("imagen", "")
        self.form_banner = movie.get("banner", "")
        self.form_trailer = movie.get("trailer", "")
        horarios = movie.get("horarios", [])
        self.form_horarios = ", ".join(str(h) for h in horarios)
        self.form_mode = "edit"
        self.form_error = ""
        self.form_success = ""

    def cancel_form(self):
        self._clear_form()
        self.form_mode = "idle"
        self.form_error = ""
        self.form_success = ""

    # ── Setters de campos ─────────────────────────────────────────────

    def set_form_nombre(self, v: str): self.form_nombre = v
    def set_form_descripcion(self, v: str): self.form_descripcion = v
    def set_form_categoria(self, v: str): self.form_categoria = v
    def set_form_duracion(self, v: str): self.form_duracion = v
    def set_form_clasificacion(self, v: str): self.form_clasificacion = v
    def set_form_precio(self, v: str): self.form_precio = v
    def set_form_vip(self, v: bool): self.form_vip = v
    def set_form_imagen(self, v: str): self.form_imagen = v
    def set_form_banner(self, v: str): self.form_banner = v
    def set_form_trailer(self, v: str): self.form_trailer = v
    def set_form_horarios(self, v: str): self.form_horarios = v

    # ── Guardar ───────────────────────────────────────────────────────

    def save_movie(self):
        """Valida y guarda (añade o edita) la película en el JSON."""
        self.form_error = ""
        self.form_success = ""

        # Validaciones básicas
        if not self.form_nombre.strip():
            self.form_error = "El nombre de la película es requerido"
            return
        if not self.form_descripcion.strip():
            self.form_error = "La descripción es requerida"
            return
        if not self.form_categoria:
            self.form_error = "Selecciona una categoría"
            return
        if not self.form_precio.strip():
            self.form_error = "El precio es requerido"
            return
        try:
            precio_val = float(self.form_precio)
            if precio_val < 0:
                raise ValueError
        except ValueError:
            self.form_error = "El precio debe ser un número positivo"
            return

        # Parsear horarios
        horarios_raw = [
            h.strip() for h in self.form_horarios.split(",") if h.strip()
        ]

        movies = load_movies()

        if self.form_mode == "add":
            # Generar nuevo ID
            existing_ids = [int(m.get("id", 0)) for m in movies if str(m.get("id", "")).isdigit()]
            new_id = str(max(existing_ids) + 1) if existing_ids else "1"
            new_movie: Dict[str, Any] = {
                "id": new_id,
                "nombre": self.form_nombre.strip(),
                "descripcion": self.form_descripcion.strip(),
                "categoria": self.form_categoria,
                "duracion": self.form_duracion.strip(),
                "clasificacion": self.form_clasificacion,
                "precio": precio_val,
                "vip": self.form_vip,
                "imagen": self.form_imagen.strip(),
                "banner": self.form_banner.strip(),
                "trailer": self.form_trailer.strip(),
                "horarios": horarios_raw,
            }
            movies.append(new_movie)
            self.form_success = f"✅ Película «{new_movie['nombre']}» añadida correctamente"

        elif self.form_mode == "edit":
            found = False
            for i, m in enumerate(movies):
                if str(m.get("id")) == self.editing_id:
                    movies[i] = {
                        **m,
                        "nombre": self.form_nombre.strip(),
                        "descripcion": self.form_descripcion.strip(),
                        "categoria": self.form_categoria,
                        "duracion": self.form_duracion.strip(),
                        "clasificacion": self.form_clasificacion,
                        "precio": precio_val,
                        "vip": self.form_vip,
                        "imagen": self.form_imagen.strip(),
                        "banner": self.form_banner.strip(),
                        "trailer": self.form_trailer.strip(),
                        "horarios": horarios_raw,
                    }
                    found = True
                    break
            if not found:
                self.form_error = "Película no encontrada"
                return
            self.form_success = f"✅ Película actualizada correctamente"

        # Persistir en JSON
        try:
            path = os.path.abspath(DATA_PATH)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(movies, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.form_error = f"Error al guardar: {str(e)}"
            return

        self.admin_movies = movies
        self.form_mode = "idle"
        self._clear_form()

    # ── Eliminar ──────────────────────────────────────────────────────

    def confirm_delete(self, movie_id: str):
        movie = next(
            (m for m in self.admin_movies if str(m.get("id")) == str(movie_id)),
            None,
        )
        if not movie:
            return
        self.delete_target_id = str(movie_id)
        self.delete_target_name = movie.get("nombre", "")
        self.show_delete_dialog = True

    def cancel_delete(self):
        self.show_delete_dialog = False
        self.delete_target_id = ""
        self.delete_target_name = ""

    def execute_delete(self):
        movies = load_movies()
        movies = [m for m in movies if str(m.get("id")) != self.delete_target_id]
        try:
            path = os.path.abspath(DATA_PATH)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(movies, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.form_error = f"Error al eliminar: {str(e)}"
            self.show_delete_dialog = False
            return
        self.admin_movies = movies
        self.form_success = f"🗑️ Película «{self.delete_target_name}» eliminada"
        self.show_delete_dialog = False
        self.delete_target_id = ""
        self.delete_target_name = ""

    # ── Helpers privados ─────────────────────────────────────────────

    def _clear_form(self):
        self.form_nombre = ""
        self.form_descripcion = ""
        self.form_categoria = ""
        self.form_duracion = ""
        self.form_clasificacion = ""
        self.form_precio = ""
        self.form_vip = False
        self.form_imagen = ""
        self.form_banner = ""
        self.form_trailer = ""
        self.form_horarios = ""
        self.editing_id = ""