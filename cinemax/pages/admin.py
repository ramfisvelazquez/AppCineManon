"""
pages/admin.py
Panel de administración — exclusivo para usuarios con rol 'admin'.
Permite añadir y editar películas del catálogo.
"""

import reflex as rx
from typing import Dict, Any
from cinemax.pages.styles.theme import *
from cinemax.states.app_state import AppState
from cinemax.states.admin_state import AdminState, CATEGORIAS, CLASIFICACIONES
from cinemax.components.navbar import navbar
from cinemax.components.footer import footer


# ─── Helpers de estilo ───────────────────────────────────────────────

CARD_BG = "rgba(255,255,255,0.04)"
BORDER = "1px solid rgba(255,255,255,0.08)"
BORDER_FOCUS = f"1px solid {RED_CINE}"

FIELD_LABEL_STYLE = {
    "font_size": "12px",
    "font_weight": "600",
    "color": WHITE_MUTED,
    "text_transform": "uppercase",
    "letter_spacing": "0.8px",
    "margin_bottom": "6px",
}

INPUT_ADMIN_STYLE = {
    "background": "rgba(255,255,255,0.05)",
    "border": BORDER,
    "border_radius": "8px",
    "color": WHITE,
    "padding": "10px 14px",
    "font_size": "14px",
    "width": "100%",
    "transition": "border 0.2s",
    "_focus": {
        "border": BORDER_FOCUS,
        "box_shadow": "0 0 0 3px rgba(229,9,20,0.15)",
        "outline": "none",
    },
    "_placeholder": {"color": GRAY_MUTED},
}

TEXTAREA_STYLE = {
    **INPUT_ADMIN_STYLE,
    "min_height": "90px",
    "resize": "vertical",
}

SELECT_STYLE = {
    **INPUT_ADMIN_STYLE,
}


# ─── Componentes de campo ─────────────────────────────────────────────

def field_label(label: str, required: bool = False) -> rx.Component:
    return rx.hstack(
        rx.text(label, **FIELD_LABEL_STYLE),
        rx.cond(required, rx.text("*", color=RED_CINE, font_size="12px", margin_left="2px"), rx.box()),
        align="center",
        spacing="0",
        margin_bottom="6px",
    )


def form_input(label: str, placeholder: str, value: rx.Var, on_change, required: bool = False) -> rx.Component:
    return rx.vstack(
        field_label(label, required),
        rx.input(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            **INPUT_ADMIN_STYLE,
        ),
        align_items="start",
        width="100%",
        spacing="0",
    )


def form_textarea(label: str, placeholder: str, value: rx.Var, on_change, required: bool = False) -> rx.Component:
    return rx.vstack(
        field_label(label, required),
        rx.text_area(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            **TEXTAREA_STYLE,
        ),
        align_items="start",
        width="100%",
        spacing="0",
    )


def form_select(label: str, options: list, value: rx.Var, on_change, placeholder: str = "Seleccionar...", required: bool = False) -> rx.Component:
    return rx.vstack(
        field_label(label, required),
        rx.select(
            options,
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            **SELECT_STYLE,
        ),
        align_items="start",
        width="100%",
        spacing="0",
    )


# ─── Panel de estadísticas ────────────────────────────────────────────

def stat_card(icon: str, value: rx.Var, label: str, color: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=22, color=color),
                rx.text(value, font_size="1.8rem", font_weight="700", color=WHITE, font_family=FONT_HEADING),
                align="center",
                spacing="3",
            ),
            rx.text(label, font_size="13px", color=WHITE_MUTED),
            spacing="1",
        ),
        background=CARD_BG,
        border=BORDER,
        border_radius="12px",
        padding="1.25rem 1.5rem",
        flex="1",
        min_width="160px",
    )


def stats_bar() -> rx.Component:
    return rx.flex(
        stat_card("film", AdminState.total_movies_count, "Películas totales", RED_CINE),
        stat_card("star", AdminState.vip_movies_count, "Películas VIP", GOLD_VIP),
        stat_card("shield-check", "Admin", "Nivel de acceso", "#4ade80"),
        gap="1rem",
        flex_wrap="wrap",
        width="100%",
    )


# ─── Formulario de película ───────────────────────────────────────────

def movie_form() -> rx.Component:
    title = rx.cond(
        AdminState.form_mode == "add",
        "Añadir Nueva Película",
        "Editar Película",
    )
    return rx.box(
        # Header
        rx.hstack(
            rx.hstack(
                rx.icon("clapperboard", size=20, color=RED_CINE),
                rx.text(title, font_size="1.1rem", font_weight="700", color=WHITE),
                align="center",
                spacing="2",
            ),
            rx.button(
                rx.icon("x", size=16),
                on_click=AdminState.cancel_form,
                background="transparent",
                border="none",
                color=WHITE_MUTED,
                cursor="pointer",
                padding="4px",
                border_radius="6px",
                _hover={"background": "rgba(255,255,255,0.08)", "color": WHITE},
            ),
            justify="between",
            align="center",
            width="100%",
            margin_bottom="1.5rem",
        ),

        # Error / Success
        rx.cond(
            AdminState.form_error != "",
            rx.box(
                rx.hstack(
                    rx.icon("alert-circle", size=16, color=RED_CINE),
                    rx.text(AdminState.form_error, color=RED_CINE, font_size="13px"),
                    align="center",
                    spacing="2",
                ),
                background="rgba(229,9,20,0.1)",
                border="1px solid rgba(229,9,20,0.3)",
                border_radius="8px",
                padding="10px 14px",
                margin_bottom="1rem",
                width="100%",
            ),
            rx.box(),
        ),

        # ── Fila 1: Nombre + Categoría ───────────────────────────────
        rx.grid(
            form_input("Título", "Nombre de la película", AdminState.form_nombre, AdminState.set_form_nombre, required=True),
            form_select("Categoría", CATEGORIAS, AdminState.form_categoria, AdminState.set_form_categoria, required=True),
            columns="2",
            gap="1rem",
            width="100%",
        ),

        rx.box(height="1rem"),

        # ── Fila 2: Duración + Clasificación + Precio ────────────────
        rx.grid(
            form_input("Duración", "ej. 120 min", AdminState.form_duracion, AdminState.set_form_duracion),
            form_select("Clasificación", CLASIFICACIONES, AdminState.form_clasificacion, AdminState.set_form_clasificacion),
            form_input("Precio (RD$)", "ej. 350", AdminState.form_precio, AdminState.set_form_precio, required=True),
            columns="3",
            gap="1rem",
            width="100%",
        ),

        rx.box(height="1rem"),

        # ── Descripción ──────────────────────────────────────────────
        form_textarea("Descripción", "Sinopsis de la película...", AdminState.form_descripcion, AdminState.set_form_descripcion, required=True),

        rx.box(height="1rem"),

        # ── Horarios ─────────────────────────────────────────────────
        form_input(
            "Horarios",
            "Separados por coma: 14:00, 17:30, 21:00",
            AdminState.form_horarios,
            AdminState.set_form_horarios,
        ),

        rx.box(height="1rem"),

        # ── URLs ─────────────────────────────────────────────────────
        rx.grid(
            form_input("URL Imagen (póster)", "https://...", AdminState.form_imagen, AdminState.set_form_imagen),
            form_input("URL Banner (fondo)", "https://...", AdminState.form_banner, AdminState.set_form_banner),
            columns="2",
            gap="1rem",
            width="100%",
        ),

        rx.box(height="1rem"),

        form_input("URL Trailer (YouTube embed)", "https://www.youtube.com/embed/...", AdminState.form_trailer, AdminState.set_form_trailer),

        rx.box(height="1rem"),

        # ── VIP toggle ───────────────────────────────────────────────
        rx.hstack(
            rx.switch(
                checked=AdminState.form_vip,
                on_change=AdminState.set_form_vip,
                color_scheme="yellow",
            ),
            rx.vstack(
                rx.text("Película VIP", font_size="14px", font_weight="600", color=GOLD_VIP),
                rx.text("Los usuarios VIP tienen acceso especial a estas películas", font_size="12px", color=WHITE_MUTED),
                spacing="0",
                align_items="start",
            ),
            align="center",
            spacing="3",
            background="rgba(245,197,24,0.06)",
            border="1px solid rgba(245,197,24,0.2)",
            border_radius="10px",
            padding="12px 16px",
            width="100%",
        ),

        rx.box(height="1.5rem"),

        # ── Botones ──────────────────────────────────────────────────
        rx.hstack(
            rx.button(
                "Cancelar",
                on_click=AdminState.cancel_form,
                background="transparent",
                color=WHITE_MUTED,
                border="1px solid rgba(255,255,255,0.15)",
                border_radius="8px",
                padding="10px 24px",
                font_size="14px",
                cursor="pointer",
                _hover={"background": "rgba(255,255,255,0.05)", "color": WHITE},
            ),
            rx.button(
                rx.hstack(
                    rx.icon(
                        rx.cond(AdminState.form_mode == "add", "plus", "save"),
                        size=16,
                    ),
                    rx.text(rx.cond(AdminState.form_mode == "add", "Añadir Película", "Guardar Cambios")),
                    align="center",
                    spacing="2",
                ),
                on_click=AdminState.save_movie,
                background=RED_CINE,
                color=WHITE,
                border="none",
                border_radius="8px",
                padding="10px 24px",
                font_size="14px",
                font_weight="600",
                cursor="pointer",
                _hover={"background": RED_HOVER, "transform": "translateY(-1px)"},
            ),
            justify="end",
            spacing="3",
        ),

        background=CARD_BG,
        border=BORDER,
        border_radius="14px",
        padding="2rem",
        width="100%",
        margin_bottom="2rem",
    )


# ─── Fila de película en la tabla ────────────────────────────────────

def movie_row(movie: Dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            # Póster thumbnail
            rx.box(
                rx.cond(
                    movie["imagen"] != "",
                    rx.image(
                        src=movie["imagen"],
                        width="44px",
                        height="60px",
                        object_fit="cover",
                        border_radius="6px",
                    ),
                    rx.box(
                        rx.icon("image-off", size=18, color=GRAY_MUTED),
                        width="44px",
                        height="60px",
                        background=GRAY_MID,
                        border_radius="6px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                ),
                flex_shrink="0",
            ),

            # Info
            rx.vstack(
                rx.hstack(
                    rx.text(movie["nombre"], font_size="14px", font_weight="600", color=WHITE, no_of_lines=1),
                    rx.cond(
                        movie["vip"],
                        rx.badge(
                            "VIP",
                            color_scheme="yellow",
                            variant="soft",
                            font_size="10px",
                            padding="1px 6px",
                        ),
                        rx.box(),
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.hstack(
                    rx.badge(movie["categoria"], color_scheme="red", variant="soft", font_size="11px"),
                    rx.text("•", color=GRAY_MUTED, font_size="12px"),
                    rx.text(movie["duracion"], font_size="12px", color=WHITE_MUTED),
                    rx.text("•", color=GRAY_MUTED, font_size="12px"),
                    rx.text(
                        rx.hstack(
                            rx.text("RD$", font_size="11px", color=GRAY_MUTED),
                            rx.text(movie["precio"], font_size="13px", font_weight="600", color=WHITE_SOFT),
                            spacing="1",
                        ),
                    ),
                    align="center",
                    spacing="1",
                    flex_wrap="wrap",
                ),
                spacing="1",
                align_items="start",
                flex="1",
            ),

            # Acciones
            rx.hstack(
                rx.tooltip(
                    rx.button(
                        rx.icon("pencil", size=15),
                        on_click=AdminState.open_edit_form(movie["id"]),
                        background="rgba(255,255,255,0.06)",
                        border="1px solid rgba(255,255,255,0.1)",
                        border_radius="7px",
                        color=WHITE_SOFT,
                        cursor="pointer",
                        padding="7px 10px",
                        _hover={"background": f"rgba(229,9,20,0.15)", "border_color": RED_CINE, "color": WHITE},
                    ),
                    content="Editar",
                ),
                rx.tooltip(
                    rx.button(
                        rx.icon("trash-2", size=15),
                        on_click=AdminState.confirm_delete(movie["id"]),
                        background="rgba(255,255,255,0.06)",
                        border="1px solid rgba(255,255,255,0.1)",
                        border_radius="7px",
                        color=WHITE_MUTED,
                        cursor="pointer",
                        padding="7px 10px",
                        _hover={"background": "rgba(229,9,20,0.15)", "border_color": RED_CINE, "color": RED_CINE},
                    ),
                    content="Eliminar",
                ),
                spacing="2",
                flex_shrink="0",
            ),

            align="center",
            justify="between",
            width="100%",
            spacing="3",
        ),
        background=CARD_BG,
        border=BORDER,
        border_radius="10px",
        padding="12px 16px",
        transition="border-color 0.2s",
        _hover={"border_color": "rgba(255,255,255,0.15)"},
    )


# ─── Diálogo de confirmación de eliminación ───────────────────────────

def delete_dialog() -> rx.Component:
    return rx.cond(
        AdminState.show_delete_dialog,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.box(
                        rx.icon("trash-2", size=32, color=RED_CINE),
                        background="rgba(229,9,20,0.1)",
                        border="1px solid rgba(229,9,20,0.25)",
                        border_radius="50%",
                        padding="16px",
                        width="fit-content",
                        margin="0 auto 1rem",
                    ),
                    rx.text(
                        "Eliminar Película",
                        font_size="1.25rem",
                        font_weight="700",
                        color=WHITE,
                        text_align="center",
                    ),
                    rx.text(
                        rx.hstack(
                            rx.text("¿Eliminar", color=WHITE_MUTED, font_size="14px"),
                            rx.text(f"«{AdminState.delete_target_name}»", color=WHITE, font_size="14px", font_weight="600"),
                            rx.text("del catálogo? Esta acción no se puede deshacer.", color=WHITE_MUTED, font_size="14px"),
                            flex_wrap="wrap",
                            justify="center",
                            spacing="1",
                        ),
                        text_align="center",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancelar",
                            on_click=AdminState.cancel_delete,
                            background="transparent",
                            color=WHITE_MUTED,
                            border="1px solid rgba(255,255,255,0.15)",
                            border_radius="8px",
                            padding="10px 24px",
                            cursor="pointer",
                            _hover={"background": "rgba(255,255,255,0.05)"},
                        ),
                        rx.button(
                            rx.hstack(rx.icon("trash-2", size=15), rx.text("Eliminar"), align="center", spacing="2"),
                            on_click=AdminState.execute_delete,
                            background=RED_CINE,
                            color=WHITE,
                            border="none",
                            border_radius="8px",
                            padding="10px 24px",
                            font_weight="600",
                            cursor="pointer",
                            _hover={"background": RED_HOVER},
                        ),
                        justify="center",
                        spacing="3",
                        width="100%",
                        margin_top="0.5rem",
                    ),
                    spacing="4",
                    align_items="center",
                    width="100%",
                ),
                background=GRAY_DARK,
                border="1px solid rgba(255,255,255,0.1)",
                border_radius="16px",
                padding="2rem",
                max_width="440px",
                width="90%",
                position="relative",
                z_index="1001",
            ),
            position="fixed",
            top="0",
            left="0",
            right="0",
            bottom="0",
            background="rgba(0,0,0,0.75)",
            display="flex",
            align_items="center",
            justify_content="center",
            z_index="1000",
            backdrop_filter="blur(4px)",
        ),
        rx.box(),
    )


# ─── Página principal del admin ───────────────────────────────────────

def admin_page() -> rx.Component:
    return rx.box(
        navbar(),

        # Acceso denegado
        rx.cond(
            ~AppState.is_admin,
            rx.box(
                rx.vstack(
                    rx.icon("shield-x", size=64, color=RED_CINE, margin_bottom="1rem"),
                    rx.text(
                        "Acceso Restringido",
                        font_size="2rem",
                        font_weight="700",
                        font_family=FONT_HEADING,
                        color=WHITE,
                        letter_spacing="1px",
                    ),
                    rx.text(
                        "Esta área es exclusiva para administradores.",
                        font_size="15px",
                        color=WHITE_MUTED,
                        text_align="center",
                    ),
                    rx.link(
                        rx.button(
                            rx.hstack(rx.icon("arrow-left", size=16), rx.text("Volver al inicio"), align="center", spacing="2"),
                            background=RED_CINE,
                            color=WHITE,
                            border="none",
                            border_radius="8px",
                            padding="12px 28px",
                            font_size="15px",
                            font_weight="600",
                            cursor="pointer",
                            margin_top="1rem",
                            _hover={"background": RED_HOVER},
                        ),
                        href="/",
                        text_decoration="none",
                    ),
                    align_items="center",
                    justify="center",
                    min_height="70vh",
                    spacing="3",
                ),
                display="flex",
                align_items="center",
                justify_content="center",
                width="100%",
                padding_top="80px",
            ),

            # Panel real
            rx.box(
                # Header del panel
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.hstack(
                                rx.icon("shield-check", size=24, color=RED_CINE),
                                rx.text(
                                    "Panel de Administración",
                                    font_size="1.8rem",
                                    font_weight="700",
                                    font_family=FONT_HEADING,
                                    color=WHITE,
                                    letter_spacing="1px",
                                ),
                                align="center",
                                spacing="3",
                            ),
                            rx.badge(
                                rx.hstack(
                                    rx.icon("user", size=12),
                                    rx.text(AppState.user_name),
                                    align="center",
                                    spacing="1",
                                ),
                                color_scheme="red",
                                variant="soft",
                                padding="5px 12px",
                                font_size="13px",
                            ),
                            justify="between",
                            align="center",
                            width="100%",
                        ),
                        rx.text(
                            "Gestiona el catálogo de películas de KANKYCINE",
                            font_size="14px",
                            color=WHITE_MUTED,
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    background=f"linear-gradient(135deg, rgba(229,9,20,0.08) 0%, rgba(10,10,10,0) 60%)",
                    border_bottom="1px solid rgba(255,255,255,0.06)",
                    padding="2rem 3rem",
                    width="100%",
                ),

                # Contenido
                rx.box(
                    # Estadísticas
                    stats_bar(),
                    rx.box(height="2rem"),

                    # Mensaje de éxito
                    rx.cond(
                        AdminState.form_success != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("check-circle-2", size=16, color="#4ade80"),
                                rx.text(AdminState.form_success, color="#4ade80", font_size="13px"),
                                align="center",
                                spacing="2",
                            ),
                            background="rgba(74,222,128,0.08)",
                            border="1px solid rgba(74,222,128,0.25)",
                            border_radius="8px",
                            padding="10px 14px",
                            margin_bottom="1.5rem",
                            width="100%",
                        ),
                        rx.box(),
                    ),

                    # Formulario (cuando está abierto)
                    rx.cond(
                        AdminState.form_mode != "idle",
                        movie_form(),
                        rx.box(),
                    ),

                    # Tabla de películas
                    rx.box(
                        # Cabecera de la tabla
                        rx.hstack(
                            rx.vstack(
                                rx.text("Catálogo de Películas", font_size="1.1rem", font_weight="700", color=WHITE),
                                rx.text(
                                    f"{AdminState.filtered_count} película(s) en el catálogo",
                                    font_size="12px",
                                    color=WHITE_MUTED,
                                ),
                                spacing="0",
                                align_items="start",
                            ),
                            rx.hstack(
                                # Buscador
                                rx.box(
                                    rx.hstack(
                                        rx.icon("search", size=16, color=GRAY_MUTED),
                                        rx.input(
                                            placeholder="Buscar película...",
                                            value=AdminState.search_admin,
                                            on_change=AdminState.set_search_admin,
                                            background="transparent",
                                            border="none",
                                            outline="none",
                                            color=WHITE,
                                            font_size="14px",
                                            width="180px",
                                            _placeholder={"color": GRAY_MUTED},
                                            _focus={"outline": "none"},
                                        ),
                                        align="center",
                                        spacing="2",
                                    ),
                                    background="rgba(255,255,255,0.05)",
                                    border=BORDER,
                                    border_radius="8px",
                                    padding="8px 12px",
                                ),
                                # Botón añadir
                                rx.button(
                                    rx.hstack(
                                        rx.icon("plus", size=16),
                                        rx.text("Añadir Película"),
                                        align="center",
                                        spacing="2",
                                    ),
                                    on_click=AdminState.open_add_form,
                                    background=RED_CINE,
                                    color=WHITE,
                                    border="none",
                                    border_radius="8px",
                                    padding="9px 18px",
                                    font_size="14px",
                                    font_weight="600",
                                    cursor="pointer",
                                    _hover={"background": RED_HOVER, "transform": "translateY(-1px)"},
                                ),
                                spacing="3",
                                align="center",
                            ),
                            justify="between",
                            align="center",
                            margin_bottom="1.25rem",
                            flex_wrap="wrap",
                            gap="0.75rem",
                        ),

                        # Lista de películas
                        rx.vstack(
                            rx.foreach(
                                AdminState.filtered_admin_movies,
                                movie_row,
                            ),
                            spacing="2",
                            width="100%",
                        ),

                        # Estado vacío
                        rx.cond(
                            AdminState.filtered_count == 0,
                            rx.box(
                                rx.vstack(
                                    rx.icon("film", size=40, color=GRAY_MUTED),
                                    rx.text(
                                        rx.cond(
                                            AdminState.search_admin != "",
                                            "No se encontraron películas con esa búsqueda",
                                            "No hay películas en el catálogo",
                                        ),
                                        color=WHITE_MUTED,
                                        font_size="15px",
                                    ),
                                    align_items="center",
                                    spacing="3",
                                    padding="3rem",
                                ),
                                background=CARD_BG,
                                border=BORDER,
                                border_radius="12px",
                                text_align="center",
                            ),
                            rx.box(),
                        ),

                        background=CARD_BG,
                        border=BORDER,
                        border_radius="14px",
                        padding="1.5rem",
                        width="100%",
                    ),

                    padding="2rem 3rem",
                    max_width="1200px",
                    margin="0 auto",
                    width="100%",
                ),
                padding_top="64px",
                min_height="100vh",
                background=BLACK_CINEMA,
            ),
        ),

        # Diálogo de eliminación (encima de todo)
        delete_dialog(),

        background=BLACK_CINEMA,
        min_height="100vh",
    )