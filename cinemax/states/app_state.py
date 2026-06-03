"""
states/app_state.py
Estado global de la aplicación Cinemax.
"""

import reflex as rx
from typing import Dict, Any, List
import random
import string

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cinemax.utils.movie_loader import (
    load_movies, search_movies, filter_by_category,
    sort_movies, get_movie_by_id, get_categories
)


def _generate_qr_code() -> str:
    """Genera un código QR falso (texto en base64 de un SVG simple)."""
    chars = string.ascii_uppercase + string.digits
    code = "CX-" + "".join(random.choices(chars, k=12))
    return code


# Asientos pre-ocupados por sala (movie_id -> lista de asientos)
_DEFAULT_OCCUPIED: Dict[str, List[str]] = {
    "1": ["A2", "A5", "B3", "B7", "C1", "C4", "C8", "D2", "D6"],
    "2": ["B1", "B5", "C3", "C7", "D4", "E2", "E6"],
    "3": ["A1", "A3", "B2", "B8", "C5", "D3", "D7", "E1"],
    "4": ["A4", "A7", "B6", "C2", "C9", "D5", "E8"],
    "5": ["A2", "B4", "B9", "C3", "C7", "D1", "D6", "E4"],
    "6": ["A5", "B2", "B7", "C4", "D2", "D8", "E3", "E7"],
    "7": ["A3", "A8", "B5", "C1", "C6", "D3", "E2", "E9"],
    "8": ["A6", "B3", "B8", "C5", "D1", "D7", "E4", "E8"],
}


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
    # reserved_seats ahora es por sala (movie_id): se almacena como JSON string
    # para simplificar: guardamos un dict str->List[str] serializado
    _reserved_by_movie: Dict[str, List[str]] = {}

    @rx.var
    def reserved_seats(self) -> List[str]:
        """Retorna los asientos ocupados para la película actual."""
        movie_id = str(self.current_movie.get("id", ""))
        if not movie_id:
            return []
        # Combinar pre-ocupados con reservas hechas en sesión
        pre = _DEFAULT_OCCUPIED.get(movie_id, [])
        session = self._reserved_by_movie.get(movie_id, [])
        combined = list(set(pre + session))
        return combined

    # ─── PAGO ─────────────────────────────────────────────────────────
    show_payment_modal: bool = False
    selected_payment_method: str = ""
    payment_step: str = "select"   # "select" | "form" | "processing" | "done"
    payment_error: str = ""
    # Campos tarjeta
    card_number: str = ""
    card_holder: str = ""
    card_expiry: str = ""
    card_cvv: str = ""
    # Campos billetera virtual
    wallet_phone: str = ""
    # Campos transferencia
    transfer_bank: str = ""
    transfer_account: str = ""

    # ─── TICKET ───────────────────────────────────────────────────────
    show_ticket: bool = False
    ticket_code: str = ""
    ticket_seats: List[str] = []
    ticket_showtime: str = ""
    ticket_movie: str = ""
    ticket_hall: str = ""
    ticket_total: float = 0.0
    ticket_date: str = ""

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
        # Limpiar asientos seleccionados al cambiar de película
        self.selected_seats = []

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
        """Abre el modal de pago."""
        if not self.selected_seats:
            self.show_toast("Selecciona al menos un asiento", "error")
            return
        self.show_payment_modal = True
        self.payment_step = "select"
        self.selected_payment_method = ""
        self.payment_error = ""
        self._reset_payment_fields()

    def _reset_payment_fields(self):
        self.card_number = ""
        self.card_holder = ""
        self.card_expiry = ""
        self.card_cvv = ""
        self.wallet_phone = ""
        self.transfer_bank = ""
        self.transfer_account = ""
        self.payment_error = ""

    def close_payment_modal(self):
        self.show_payment_modal = False
        self.payment_step = "select"
        self.selected_payment_method = ""
        self._reset_payment_fields()

    def select_payment_method(self, method: str):
        self.selected_payment_method = method
        self.payment_step = "form"
        self.payment_error = ""

    def go_back_to_methods(self):
        self.payment_step = "select"
        self.selected_payment_method = ""
        self._reset_payment_fields()

    def process_payment(self):
        """Valida el formulario antes de procesar."""
        self.payment_error = ""
        method = self.selected_payment_method

        if method == "card":
            if not self.card_number.strip():
                self.payment_error = "Por favor ingresa el número de tarjeta"
                return
            if not self.card_holder.strip():
                self.payment_error = "Por favor ingresa el nombre del titular"
                return
            if not self.card_expiry.strip():
                self.payment_error = "Por favor ingresa la fecha de vencimiento"
                return
            if not self.card_cvv.strip():
                self.payment_error = "Por favor ingresa el CVV"
                return

        elif method == "wallet":
            if not self.wallet_phone.strip():
                self.payment_error = "Por favor ingresa tu número de teléfono"
                return

        elif method == "transfer":
            if not self.transfer_bank.strip():
                self.payment_error = "Por favor ingresa el banco de origen"
                return
            if not self.transfer_account.strip():
                self.payment_error = "Por favor ingresa el número de cuenta"
                return

        # Todo OK → avanzar
        self.payment_step = "processing"

    def finalize_payment(self):
        """Finaliza la reserva y genera el ticket."""
        import datetime

        movie_id = str(self.current_movie.get("id", ""))

        # Añadir asientos reservados a la sala correcta
        if movie_id:
            current = self._reserved_by_movie.get(movie_id, [])
            updated = list(set(current + self.selected_seats))
            new_map = dict(self._reserved_by_movie)
            new_map[movie_id] = updated
            self._reserved_by_movie = new_map

        # Generar ticket
        self.ticket_code = _generate_qr_code()
        self.ticket_seats = list(self.selected_seats)
        self.ticket_showtime = self.selected_showtime
        self.ticket_movie = self.current_movie.get("nombre", "")
        self.ticket_hall = f"Sala {movie_id}" if movie_id else "Sala 1"
        self.ticket_total = self.total_price
        self.ticket_date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        # Limpiar selección
        self.selected_seats = []
        self.show_payment_modal = False
        self.payment_step = "select"
        self.selected_payment_method = ""
        self._reset_payment_fields()

        # Mostrar ticket
        self.show_ticket = True

    def close_ticket(self):
        self.show_ticket = False

    # ─── SETTERS PAGO ────────────────────────────────────────────────
    def set_card_number(self, val: str): self.card_number = val
    def set_card_holder(self, val: str): self.card_holder = val
    def set_card_expiry(self, val: str): self.card_expiry = val
    def set_card_cvv(self, val: str): self.card_cvv = val
    def set_wallet_phone(self, val: str): self.wallet_phone = val
    def set_transfer_bank(self, val: str): self.transfer_bank = val
    def set_transfer_account(self, val: str): self.transfer_account = val

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