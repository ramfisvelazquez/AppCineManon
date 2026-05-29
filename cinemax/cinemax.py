"""
cinemax.py
Punto de entrada principal de la aplicación Cinemax.
"""

import reflex as rx
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cinemax.pages.index import index_page
from cinemax.pages.catalogo import catalogo_page
from cinemax.pages.pelicula import movie_detail_page
from cinemax.pages.reservas import reservas_page
from cinemax.pages.login import login_page
from cinemax.pages.registro import registro_page
from cinemax.states.app_state import AppState
from cinemax.pages.styles.theme import BLACK_CINEMA, FONT_BODY


GLOBAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600;700&display=swap');

* { box-sizing: border-box; }

html { scroll-behavior: smooth; }

body {
  background-color: #0f0f0f !important;
  color: #e5e5e5;
  font-family: 'DM Sans', sans-serif;
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f0f0f; }
::-webkit-scrollbar-thumb { background: #3a3a3a; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #e50914; }

::selection { background: rgba(229, 9, 20, 0.3); color: #fff; }

@keyframes shimmer {
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
}

@keyframes slideInRight {
  from { transform: translateX(100px); opacity: 0; }
  to   { transform: translateX(0);     opacity: 1; }
}

@keyframes fadeInUp {
  from { transform: translateY(20px); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
}
"""


def index() -> rx.Component:
    return index_page()


def catalogo() -> rx.Component:
    return catalogo_page()


def pelicula_id() -> rx.Component:
    return movie_detail_page()


def reservas() -> rx.Component:
    return reservas_page()


def login() -> rx.Component:
    return login_page()


def registro() -> rx.Component:
    return registro_page()


# ── App ───────────────────────────────────────────────────────────────
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="red",
    ),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600;700&display=swap",
    ],
    style={
        "background_color": BLACK_CINEMA,
        "font_family": FONT_BODY,
        "color": "#e5e5e5",
    },
    html_lang="es",
)

# ── Routes ────────────────────────────────────────────────────────────
app.add_page(index, route="/", on_load=AppState.on_load)
app.add_page(catalogo, route="/catalogo", on_load=AppState.on_load)
app.add_page(pelicula_id, route="/pelicula/[movie_id]", on_load=AppState.load_movie)
app.add_page(reservas, route="/reservas", on_load=AppState.on_load)
app.add_page(login, route="/login")
app.add_page(registro, route="/registro")
