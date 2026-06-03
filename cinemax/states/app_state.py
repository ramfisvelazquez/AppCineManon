"""
states/app_state.py
Estado global de la aplicación Cinemax — con validación en tiempo real.
"""

import reflex as rx
from typing import Dict, Any, List
import random
import string
import re

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cinemax.utils.movie_loader import (
    load_movies, search_movies, filter_by_category,
    sort_movies, get_movie_by_id, get_categories
)


def _generate_booking_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "CX-" + "".join(random.choices(chars, k=12))


# Asientos pre-ocupados por sala (movie_id -> lista)
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


# ─── HELPERS DE FORMATO ───────────────────────────────────────────────────────

def _format_card_number(raw: str) -> str:
    """1234567890123456 → 1234 5678 9012 3456 (máx 19 chars con espacios)."""
    digits = re.sub(r"\D", "", raw)[:16]
    return " ".join(digits[i:i+4] for i in range(0, len(digits), 4))


def _format_expiry(raw: str) -> str:
    """1005 → 10/05 (máx 5 chars)."""
    digits = re.sub(r"\D", "", raw)[:4]
    if len(digits) > 2:
        return digits[:2] + "/" + digits[2:]
    return digits


def _format_phone(raw: str) -> str:
    """8095551234 → (809) 555-1234 (máx 10 dígitos)."""
    digits = re.sub(r"\D", "", raw)[:10]
    if len(digits) > 6:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    if len(digits) > 3:
        return f"({digits[:3]}) {digits[3:]}"
    if len(digits) > 0:
        return f"({digits}"
    return ""


# ─── HELPERS DE VALIDACIÓN ────────────────────────────────────────────────────

def _validate_card_number(v: str) -> str:
    digits = re.sub(r"\D", "", v)
    if not digits:
        return "Número de tarjeta requerido"
    if len(digits) < 16:
        return f"Número incompleto ({len(digits)}/16 dígitos)"
    return ""


def _validate_card_holder(v: str) -> str:
    if not v.strip():
        return "Nombre del titular requerido"
    if len(v.strip()) < 3:
        return "Nombre demasiado corto"
    return ""


def _validate_expiry(v: str) -> str:
    digits = re.sub(r"\D", "", v)
    if not digits:
        return "Fecha de vencimiento requerida"
    if len(digits) < 4:
        return "Formato requerido: MM/AA"
    month = int(digits[:2])
    if month < 1 or month > 12:
        return "Mes inválido (01–12)"
    return ""


def _validate_cvv(v: str) -> str:
    digits = re.sub(r"\D", "", v)
    if not digits:
        return "CVV requerido"
    if len(digits) < 3:
        return "El CVV debe tener entre 3 y 4 dígitos"
    return ""


def _validate_phone(v: str) -> str:
    digits = re.sub(r"\D", "", v)
    if not digits:
        return "Número de teléfono requerido"
    if len(digits) < 10:
        return "Número de teléfono incompleto"
    return ""


def _validate_bank(v: str) -> str:
    if not v.strip():
        return "Banco de origen requerido"
    return ""


def _validate_account(v: str) -> str:
    if not v.strip():
        return "Número de cuenta requerido"
    if len(v.strip()) < 5:
        return "Número de cuenta inválido"
    return ""


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
    _reserved_by_movie: Dict[str, List[str]] = {}

    # ─── AUTH REQUIRED MODAL ──────────────────────────────────────────
    show_auth_required_modal: bool = False

    @rx.var
    def reserved_seats(self) -> List[str]:
        movie_id = str(self.current_movie.get("id", ""))
        if not movie_id:
            return []
        pre = _DEFAULT_OCCUPIED.get(movie_id, [])
        session = self._reserved_by_movie.get(movie_id, [])
        return list(set(pre + session))

    # ─── PAGO ─────────────────────────────────────────────────────────
    show_payment_modal: bool = False
    selected_payment_method: str = ""
    payment_step: str = "select"
    payment_error: str = ""

    # Tarjeta — valor formateado mostrado al usuario
    card_number: str = ""
    card_holder: str = ""
    card_expiry: str = ""
    card_cvv: str = ""

    # Errores por campo (tiempo real)
    err_card_number: str = ""
    err_card_holder: str = ""
    err_card_expiry: str = ""
    err_card_cvv: str = ""

    # MobilePay
    wallet_phone: str = ""
    err_wallet_phone: str = ""

    # CineTransfer
    transfer_bank: str = ""
    transfer_account: str = ""
    err_transfer_bank: str = ""
    err_transfer_account: str = ""

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

    # ─── LIFECYCLE ────────────────────────────────────────────────────

    def on_load(self):
        self.movies = load_movies()
        self.filtered_movies = self.movies
        self.categories = get_categories()

    def load_movie(self):
        movie_id = self.router.page.params.get("movie_id", "")
        self.current_movie = get_movie_by_id(movie_id) or {}
        if self.current_movie:
            raw = self.current_movie.get("horarios", [])
            self.horarios = [str(h) for h in raw]
            if self.horarios:
                self.selected_showtime = self.horarios[0]
        else:
            self.horarios = []
            self.selected_showtime = ""
        self.selected_seats = []

    # ─── BÚSQUEDA ─────────────────────────────────────────────────────

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

    # ─── FLUJO DE PAGO ────────────────────────────────────────────────

    def confirm_reservation(self):
        if not self.is_logged_in:
            self.show_auth_required_modal = True
            return
        if not self.selected_seats:
            self.show_toast("Selecciona al menos un asiento", "error")
            return
        self.show_payment_modal = True
        self.payment_step = "select"
        self.selected_payment_method = ""
        self.payment_error = ""
        self._reset_payment_fields()

    def close_auth_required_modal(self):
        self.show_auth_required_modal = False

    def _reset_payment_fields(self):
        self.card_number = ""
        self.card_holder = ""
        self.card_expiry = ""
        self.card_cvv = ""
        self.wallet_phone = ""
        self.transfer_bank = ""
        self.transfer_account = ""
        self.err_card_number = ""
        self.err_card_holder = ""
        self.err_card_expiry = ""
        self.err_card_cvv = ""
        self.err_wallet_phone = ""
        self.err_transfer_bank = ""
        self.err_transfer_account = ""
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

    # ─── SETTERS CON FORMATO + VALIDACIÓN EN TIEMPO REAL ─────────────

    def set_card_number(self, val: str):
        self.card_number = _format_card_number(val)
        self.err_card_number = _validate_card_number(self.card_number)

    def set_card_holder(self, val: str):
        # Solo letras, espacios, apóstrofos y guiones (nombres)
        cleaned = re.sub(r"[^A-Za-záéíóúüñÁÉÍÓÚÜÑ\s'\-]", "", val)
        self.card_holder = cleaned
        self.err_card_holder = _validate_card_holder(self.card_holder)

    def set_card_expiry(self, val: str):
        self.card_expiry = _format_expiry(val)
        self.err_card_expiry = _validate_expiry(self.card_expiry)

    def set_card_cvv(self, val: str):
        digits = re.sub(r"\D", "", val)[:4]
        self.card_cvv = digits
        self.err_card_cvv = _validate_cvv(self.card_cvv)

    def set_wallet_phone(self, val: str):
        self.wallet_phone = _format_phone(val)
        self.err_wallet_phone = _validate_phone(self.wallet_phone)

    def set_transfer_bank(self, val: str):
        self.transfer_bank = val
        self.err_transfer_bank = _validate_bank(self.transfer_bank)

    def set_transfer_account(self, val: str):
        # Solo dígitos, guiones y espacios para números de cuenta
        cleaned = re.sub(r"[^\d\-\s]", "", val)
        self.transfer_account = cleaned
        self.err_transfer_account = _validate_account(self.transfer_account)

    # ─── PROCESAR PAGO (con validación final) ─────────────────────────

    def process_payment(self):
        """Valida todos los campos del método activo y avanza si todo está OK."""
        self.payment_error = ""
        method = self.selected_payment_method

        if method == "card":
            self.err_card_number = _validate_card_number(self.card_number)
            self.err_card_holder = _validate_card_holder(self.card_holder)
            self.err_card_expiry = _validate_expiry(self.card_expiry)
            self.err_card_cvv = _validate_cvv(self.card_cvv)
            if any([self.err_card_number, self.err_card_holder,
                    self.err_card_expiry, self.err_card_cvv]):
                self.payment_error = "Por favor corrige los campos marcados"
                return

        elif method == "wallet":
            self.err_wallet_phone = _validate_phone(self.wallet_phone)
            if self.err_wallet_phone:
                self.payment_error = self.err_wallet_phone
                return

        elif method == "transfer":
            self.err_transfer_bank = _validate_bank(self.transfer_bank)
            self.err_transfer_account = _validate_account(self.transfer_account)
            if any([self.err_transfer_bank, self.err_transfer_account]):
                self.payment_error = "Por favor corrige los campos marcados"
                return

        # Todo OK → procesando
        self.payment_step = "processing"

    def finalize_payment(self):
        """Finaliza la reserva y genera el ticket."""
        import datetime

        movie_id = str(self.current_movie.get("id", ""))
        if movie_id:
            current = self._reserved_by_movie.get(movie_id, [])
            updated = list(set(current + self.selected_seats))
            new_map = dict(self._reserved_by_movie)
            new_map[movie_id] = updated
            self._reserved_by_movie = new_map

        self.ticket_code = _generate_booking_code()
        self.ticket_seats = list(self.selected_seats)
        self.ticket_showtime = self.selected_showtime
        self.ticket_movie = self.current_movie.get("nombre", "")
        self.ticket_hall = f"Sala {movie_id}" if movie_id else "Sala 1"
        self.ticket_total = self.total_price
        self.ticket_date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        self.selected_seats = []
        self.show_payment_modal = False
        self.payment_step = "select"
        self.selected_payment_method = ""
        self._reset_payment_fields()
        self.show_ticket = True

    def close_ticket(self):
        self.show_ticket = False

    # ─── HORARIOS ─────────────────────────────────────────────────────

    def set_showtime(self, time: str):
        self.selected_showtime = time
        self.selected_seats = []

    # ─── AUTH ─────────────────────────────────────────────────────────

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

    # ─── VARS COMPUTADAS ──────────────────────────────────────────────

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

    @rx.var
    def card_form_valid(self) -> bool:
        """True si todos los campos de tarjeta están llenos y sin errores."""
        return bool(
            self.card_number and not self.err_card_number and
            self.card_holder and not self.err_card_holder and
            self.card_expiry and not self.err_card_expiry and
            self.card_cvv and not self.err_card_cvv
        )

    @rx.var
    def wallet_form_valid(self) -> bool:
        return bool(self.wallet_phone and not self.err_wallet_phone)

    @rx.var
    def transfer_form_valid(self) -> bool:
        return bool(
            self.transfer_bank and not self.err_transfer_bank and
            self.transfer_account and not self.err_transfer_account
        )

    @rx.var
    def current_form_valid(self) -> bool:
        m = self.selected_payment_method
        if m == "card":
            return self.card_form_valid
        if m == "wallet":
            return self.wallet_form_valid
        if m == "transfer":
            return self.transfer_form_valid
        if m == "credits":
            return True
        return False