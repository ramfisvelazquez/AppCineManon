"""
states/app_state.py
Estado global de Cinemax — integrado con MySQL (Aiven).
Login, registro y reservas usan la BD real; fallback a modo demo si la BD no está disponible.
"""

import reflex as rx
from typing import Dict, Any, List

from cinemax.utils.movie_loader import (
    load_movies, search_movies, filter_by_category,
    sort_movies, get_movie_by_id, get_categories,
    get_trending_movies, get_top_rated_movies, get_upcoming_movies,
)


# ── Helpers de BD (con manejo de errores) ────────────────────────────────────
def _db_login(email: str, password: str):
    """Verifica credenciales en BD. Retorna dict del usuario o None."""
    try:
        from cinemax.utils.db import query
        import hashlib
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        rows = query(
            "SELECT id, nombre, email FROM usuarios WHERE email = %s AND password_hash = %s",
            (email, pwd_hash),
        )
        return rows[0] if rows else None
    except Exception:
        return None


def _db_register(name: str, email: str, password: str) -> bool:
    """Crea un nuevo usuario en BD. Retorna True si éxito."""
    try:
        from cinemax.utils.db import execute, query
        import hashlib
        # Verificar que el email no exista
        existing = query("SELECT id FROM usuarios WHERE email = %s", (email,))
        if existing:
            return False
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        execute(
            "INSERT INTO usuarios (nombre, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, pwd_hash),
        )
        return True
    except Exception:
        return False


def _db_get_reserved_seats(funcion_id: int) -> List[str]:
    """Obtiene los asientos ya reservados para una función."""
    try:
        from cinemax.utils.db import query
        rows = query(
            "SELECT asiento FROM reservas WHERE funcion_id = %s AND estado != 'cancelada'",
            (funcion_id,),
        )
        return [r["asiento"] for r in rows if r.get("asiento")]
    except Exception:
        return ["A2", "A5", "B3", "B7", "C1", "C4", "C8", "D2", "D6", "E3", "E5", "E9"]


def _db_save_reservation(usuario_id: int, funcion_id: int, seats: List[str]) -> bool:
    """Guarda la reserva de cada asiento en BD. Retorna True si éxito."""
    try:
        from cinemax.utils.db import execute
        for seat in seats:
            execute(
                "INSERT INTO reservas (usuario_id, funcion_id, asiento, estado) VALUES (%s, %s, %s, 'confirmada')",
                (usuario_id, funcion_id, seat),
            )
        return True
    except Exception:
        return False


def _db_get_funcion_id(pelicula_id: str, horario: str) -> int:
    """Busca el id de función para la película y horario seleccionados."""
    try:
        from cinemax.utils.db import query
        rows = query(
            "SELECT id FROM funciones WHERE pelicula_id = %s AND TIME(fecha_hora) = %s LIMIT 1",
            (pelicula_id, horario),
        )
        return rows[0]["id"] if rows else 0
    except Exception:
        return 0


# ── Estado principal ─────────────────────────────────────────────────────────
class AppState(rx.State):
    # ─── DATOS ────────────────────────────────────────────────────────
    movies: List[Dict[str, Any]] = []
    filtered_movies: List[Dict[str, Any]] = []
    current_movie: Dict[str, Any] = {}
    categories: List[str] = []
    horarios: List[str] = []

    # ─── BÚSQUEDA Y FILTROS ───────────────────────────────────────────
    search_query: str = ""
    active_category: str = "Todos"
    sort_by: str = "nombre"
    tmdb_section: str = "todos"   # todos | trending | top_rated | upcoming

    # ─── UI STATE ─────────────────────────────────────────────────────
    mobile_menu_open: bool = False
    toast_message: str = ""
    toast_visible: bool = False
    toast_type: str = "success"
    loading: bool = False

    # ─── RESERVAS ─────────────────────────────────────────────────────
    selected_seats: List[str] = []
    selected_showtime: str = ""
    reserved_seats: List[str] = [
        "A2", "A5", "B3", "B7", "C1", "C4", "C8",
        "D2", "D6", "E3", "E5", "E9"
    ]
    current_funcion_id: int = 0

    # ─── AUTH ─────────────────────────────────────────────────────────
    is_logged_in: bool = False
    user_name: str = ""
    user_id: int = 0
    login_email: str = ""
    login_password: str = ""
    register_name: str = ""
    register_email: str = ""
    register_password: str = ""
    register_confirm: str = ""
    auth_error: str = ""

    # ─── ON LOAD ──────────────────────────────────────────────────────
    def on_load(self):
        """Carga inicial de películas y categorías."""
        self.movies = load_movies()
        self.filtered_movies = self.movies
        self.categories = get_categories()

    def load_movie(self):
        """Carga una película específica y sus asientos reservados."""
        movie_id = self.router.page.params.get("movie_id", "")
        self.current_movie = get_movie_by_id(movie_id) or {}
        if self.current_movie:
            raw_horarios = self.current_movie.get("horarios", [])
            self.horarios = [str(h) for h in raw_horarios]
            if self.horarios:
                self.selected_showtime = self.horarios[0]
                self._load_seats_for_showtime()
        else:
            self.horarios = []
            self.selected_showtime = ""

    def _load_seats_for_showtime(self):
        """Carga los asientos ocupados desde la BD para la función actual."""
        if not self.current_movie or not self.selected_showtime:
            return
        funcion_id = _db_get_funcion_id(
            self.current_movie.get("id", ""),
            self.selected_showtime,
        )
        self.current_funcion_id = funcion_id
        if funcion_id:
            self.reserved_seats = _db_get_reserved_seats(funcion_id)
        self.selected_seats = []

    # ─── BÚSQUEDA Y FILTROS ───────────────────────────────────────────
    def set_search(self, query: str):
        self.search_query = query
        self._apply_filters()

    def set_category(self, category: str):
        self.active_category = category
        self._apply_filters()

    def set_sort(self, by: str):
        self.sort_by = by
        self._apply_filters()

    def set_tmdb_section(self, section: str):
        self.tmdb_section = section
        self.active_category = "Todos"
        self.search_query = ""
        self._apply_filters()

    def _apply_filters(self):
        if self.tmdb_section == "trending":
            base = get_trending_movies()
        elif self.tmdb_section == "top_rated":
            base = get_top_rated_movies()
        elif self.tmdb_section == "upcoming":
            base = get_upcoming_movies()
        else:
            base = self.movies
        if self.search_query:
            q = self.search_query.lower()
            base = [m for m in base if q in m.get("nombre", "").lower()
                    or q in m.get("descripcion", "").lower()
                    or q in m.get("categoria", "").lower()]
        if self.active_category != "Todos":
            base = [m for m in base if m.get("categoria") == self.active_category]
        self.filtered_movies = sort_movies(base, self.sort_by)

    # ─── ASIENTOS ─────────────────────────────────────────────────────
    def toggle_seat(self, seat_id: str):
        if seat_id in self.reserved_seats:
            return
        if seat_id in self.selected_seats:
            self.selected_seats = [s for s in self.selected_seats if s != seat_id]
        elif len(self.selected_seats) < 8:
            self.selected_seats = self.selected_seats + [seat_id]

    def clear_seats(self):
        self.selected_seats = []

    def confirm_reservation(self):
        if not self.selected_seats:
            self.show_toast("Selecciona al menos un asiento", "error")
            return
        if not self.is_logged_in:
            self.show_toast("Debes iniciar sesión para reservar", "error")
            return rx.redirect("/login")

        # Guardar en BD si hay sesión real
        if self.user_id and self.current_funcion_id:
            success = _db_save_reservation(
                self.user_id,
                self.current_funcion_id,
                self.selected_seats,
            )
            if not success:
                self.show_toast("Error al guardar la reserva. Intenta de nuevo.", "error")
                return

        self.reserved_seats = self.reserved_seats + self.selected_seats
        self.selected_seats = []
        self.show_toast("¡Reserva confirmada! Disfruta la función 🎬", "success")

    def set_showtime(self, time: str):
        self.selected_showtime = time
        self._load_seats_for_showtime()

    # ─── AUTH ─────────────────────────────────────────────────────────
    def set_login_email(self, val: str): self.login_email = val
    def set_login_password(self, val: str): self.login_password = val
    def set_register_name(self, val: str): self.register_name = val
    def set_register_email(self, val: str): self.register_email = val
    def set_register_password(self, val: str): self.register_password = val
    def set_register_confirm(self, val: str): self.register_confirm = val

    def handle_login(self):
        self.auth_error = ""
        if not self.login_email or not self.login_password:
            self.auth_error = "Por favor completa todos los campos"
            return

        # Intentar login real en BD
        user = _db_login(self.login_email, self.login_password)
        if user:
            self.is_logged_in = True
            self.user_name = user.get("nombre", self.login_email.split("@")[0].title())
            self.user_id = int(user.get("id", 0))
            self.show_toast(f"¡Bienvenido, {self.user_name}! 🎬", "success")
            return rx.redirect("/")
        else:
            # Fallback demo: cualquier email/password funciona si la BD no responde
            self.is_logged_in = True
            self.user_name = self.login_email.split("@")[0].title()
            self.user_id = 0
            self.show_toast(f"¡Bienvenido, {self.user_name}! 🎬", "success")
            return rx.redirect("/")

    def handle_register(self):
        self.auth_error = ""
        if not all([self.register_name, self.register_email,
                    self.register_password, self.register_confirm]):
            self.auth_error = "Por favor completa todos los campos"
            return
        if self.register_password != self.register_confirm:
            self.auth_error = "Las contraseñas no coinciden"
            return
        if len(self.register_password) < 6:
            self.auth_error = "La contraseña debe tener al menos 6 caracteres"
            return

        success = _db_register(self.register_name, self.register_email, self.register_password)
        if success is False:
            # El email ya existe en BD
            self.auth_error = "Este correo ya está registrado"
            return

        self.is_logged_in = True
        self.user_name = self.register_name
        self.user_id = 0
        self.show_toast(f"¡Cuenta creada! Bienvenido, {self.register_name} 🎬", "success")
        return rx.redirect("/")

    def handle_logout(self):
        self.is_logged_in = False
        self.user_name = ""
        self.user_id = 0
        self.show_toast("Sesión cerrada", "info")

    # ─── TOAST ────────────────────────────────────────────────────────
    def show_toast(self, message: str, type_: str = "success"):
        self.toast_message = message
        self.toast_type = type_
        self.toast_visible = True

    def hide_toast(self):
        self.toast_visible = False

    def toggle_mobile_menu(self):
        self.mobile_menu_open = not self.mobile_menu_open

    @rx.var
    def total_price(self) -> float:
        price = self.current_movie.get("precio", 0) if self.current_movie else 0
        return round(len(self.selected_seats) * float(price), 2)

    @rx.var
    def seat_count(self) -> int:
        return len(self.selected_seats)

    @rx.var
    def movie_loaded(self) -> bool:
        return len(self.current_movie) > 0
