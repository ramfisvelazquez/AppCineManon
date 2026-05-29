"""
states/app_state.py
Estado global de la aplicación Cinemax.
"""

import reflex as rx
from typing import Dict, Any, List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cinemax.utils.movie_loader import (
    load_movies, search_movies, filter_by_category,
    sort_movies, get_movie_by_id, get_categories
)


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

    # ─── AUTH ─────────────────────────────────────────────────────────
    is_logged_in: bool = False
    user_name: str = ""
    login_email: str = ""
    login_password: str = ""
    register_name: str = ""
    register_email: str = ""
    register_password: str = ""
    register_confirm: str = ""
    auth_error: str = ""

    def on_load(self):
        """Carga inicial de películas y categorías."""
        self.movies = load_movies()
        self.filtered_movies = self.movies
        self.categories = get_categories()

    def load_movie(self):
        """Carga una película específica desde los parámetros de ruta."""
        movie_id = self.router.page.params.get("movie_id", "")
        self.current_movie = get_movie_by_id(movie_id) or {}
        if self.current_movie:
            raw_horarios = self.current_movie.get("horarios", [])
            self.horarios = [str(h) for h in raw_horarios]
            if self.horarios:
                self.selected_showtime = self.horarios[0]
        else:
            self.horarios = []
            self.selected_showtime = ""

    def set_search(self, query: str):
        self.search_query = query
        self._apply_filters()

    def set_category(self, category: str):
        self.active_category = category
        self._apply_filters()

    def set_sort(self, by: str):
        self.sort_by = by
        self._apply_filters()

    def _apply_filters(self):
        results = search_movies(self.search_query)
        if self.active_category != "Todos":
            results = [m for m in results if m.get("categoria") == self.active_category]
        self.filtered_movies = sort_movies(results, self.sort_by)

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
        self.reserved_seats = self.reserved_seats + self.selected_seats
        self.selected_seats = []
        self.show_toast("¡Reserva confirmada! Disfruta la función 🎬", "success")

    def set_showtime(self, time: str):
        self.selected_showtime = time
        self.selected_seats = []

    # ─── AUTH HANDLERS ────────────────────────────────────────────────
    def set_login_email(self, val: str): self.login_email = val
    def set_login_password(self, val: str): self.login_password = val
    def set_register_name(self, val: str): self.register_name = val
    def set_register_email(self, val: str): self.register_email = val
    def set_register_password(self, val: str): self.register_password = val
    def set_register_confirm(self, val: str): self.register_confirm = val

    def handle_login(self):
        if not self.login_email or not self.login_password:
            self.auth_error = "Por favor completa todos los campos"
            return
        self.is_logged_in = True
        self.user_name = self.login_email.split("@")[0].title()
        self.auth_error = ""
        self.show_toast(f"¡Bienvenido, {self.user_name}! 🎬", "success")
        return rx.redirect("/")

    def handle_register(self):
        if not all([self.register_name, self.register_email,
                    self.register_password, self.register_confirm]):
            self.auth_error = "Por favor completa todos los campos"
            return
        if self.register_password != self.register_confirm:
            self.auth_error = "Las contraseñas no coinciden"
            return
        self.is_logged_in = True
        self.user_name = self.register_name
        self.auth_error = ""
        self.show_toast(f"¡Cuenta creada! Bienvenido, {self.register_name} 🎬", "success")
        return rx.redirect("/")

    def handle_logout(self):
        self.is_logged_in = False
        self.user_name = ""
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
