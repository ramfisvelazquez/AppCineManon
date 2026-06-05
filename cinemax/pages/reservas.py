"""
pages/reservas.py
Sistema visual de selección de asientos.
"""

import reflex as rx
from cinemax.pages.styles.theme import *
from cinemax.components.navbar import navbar
from cinemax.components.footer import footer
from cinemax.components.toast import toast
from cinemax.states.app_state import AppState


ROWS = ["A", "B", "C", "D", "E", "F", "G", "H"]
SEATS_PER_ROW = 10


def seat_button(row: str, num: int) -> rx.Component:
    seat_id = f"{row}{num}"
    is_reserved = AppState.reserved_seats.contains(seat_id)
    is_selected = AppState.selected_seats.contains(seat_id)

    return rx.button(
        seat_id,
        on_click=AppState.toggle_seat(seat_id),
        background=rx.cond(
            is_reserved,
            "rgba(255,255,255,0.08)",
            rx.cond(is_selected, RED_CINE, "rgba(255,255,255,0.06)"),
        ),
        color=rx.cond(
            is_reserved,
            "rgba(255,255,255,0.2)",
            rx.cond(is_selected, WHITE, WHITE_MUTED),
        ),
        border=rx.cond(
            is_reserved,
            "1px solid rgba(255,255,255,0.06)",
            rx.cond(is_selected, f"1px solid {RED_CINE}", "1px solid rgba(255,255,255,0.12)"),
        ),
        border_radius="6px",
        padding="6px",
        font_size="10px",
        font_weight="600",
        cursor=rx.cond(is_reserved, "not-allowed", "pointer"),
        transition="all 0.15s ease",
        width="40px",
        height="36px",
        opacity=rx.cond(is_reserved, "0.4", "1"),
    )


def seat_row(row: str) -> rx.Component:
    return rx.hstack(
        rx.text(row, color=GRAY_MUTED, font_size="12px", font_weight="700", width="16px", text_align="center"),
        rx.hstack(
            *[seat_button(row, i) for i in range(1, SEATS_PER_ROW + 1)],
            spacing="1",
        ),
        rx.text(row, color=GRAY_MUTED, font_size="12px", font_weight="700", width="16px", text_align="center"),
        spacing="2",
        align="center",
    )


def reservas_page() -> rx.Component:
    return rx.box(
        navbar(),

        rx.box(
            rx.box(
                rx.vstack(
                    rx.vstack(
                        rx.text("SELECCIÓN DE ASIENTOS", font_family=FONT_HEADING, font_size=["2.5rem", "3.5rem"], color=WHITE, letter_spacing="1"),
                        rx.box(width="64px", height="4px", background=RED_CINE, border_radius="2px"),
                        align_items="start",
                        spacing="2",
                        margin_bottom="0.5rem",
                    ),

                    rx.flex(
                        # Seat Map
                        rx.vstack(
                            rx.box(
                                rx.text("PANTALLA", color=WHITE_MUTED, font_size="11px", font_weight="700", letter_spacing="1", text_align="center"),
                                background="linear-gradient(180deg, rgba(229,9,20,0.2) 0%, transparent 100%)",
                                border_top=f"3px solid {RED_CINE}",
                                border_radius="0 0 50% 50%",
                                padding="10px 0 20px",
                                width="80%",
                                margin_bottom="2rem",
                            ),
                            rx.vstack(
                                *[seat_row(row) for row in ROWS],
                                spacing="2",
                            ),
                            rx.hstack(
                                rx.hstack(
                                    rx.box(width="20px", height="20px", background=RED_CINE, border_radius="4px"),
                                    rx.text("Seleccionado", color=WHITE_MUTED, font_size="12px"),
                                    spacing="2", align="center",
                                ),
                                rx.hstack(
                                    rx.box(width="20px", height="20px", background="rgba(255,255,255,0.06)", border="1px solid rgba(255,255,255,0.12)", border_radius="4px"),
                                    rx.text("Disponible", color=WHITE_MUTED, font_size="12px"),
                                    spacing="2", align="center",
                                ),
                                rx.hstack(
                                    rx.box(width="20px", height="20px", background="rgba(255,255,255,0.08)", border_radius="4px", opacity="0.4"),
                                    rx.text("Ocupado", color=WHITE_MUTED, font_size="12px"),
                                    spacing="2", align="center",
                                ),
                                spacing="6",
                                flex_wrap="wrap",
                                margin_top="2rem",
                            ),
                            align_items="center",
                            flex="1",
                            padding="2rem",
                            background=GRAY_DARK,
                            border_radius="16px",
                            border="1px solid rgba(255,255,255,0.06)",
                        ),

                        # Summary Panel
                        rx.vstack(
                            rx.text("RESUMEN DE COMPRA", color=WHITE_MUTED, font_size="11px", font_weight="700", letter_spacing="1"),

                            rx.vstack(
                                rx.text("Película", color=GRAY_MUTED, font_size="12px"),
                                rx.text(
                                    rx.cond(
                                        AppState.movie_loaded,
                                        AppState.current_movie["nombre"],
                                        "Sin seleccionar",
                                    ),
                                    color=WHITE, font_size="15px", font_weight="600",
                                ),
                                align_items="start", spacing="1",
                                padding="1rem",
                                background="rgba(255,255,255,0.03)",
                                border_radius="10px",
                                width="100%",
                                border="1px solid rgba(255,255,255,0.06)",
                            ),

                            rx.vstack(
                                rx.text("Función", color=GRAY_MUTED, font_size="12px"),
                                rx.text(
                                    rx.cond(
                                        AppState.selected_showtime != "",
                                        AppState.selected_showtime,
                                        "No seleccionada",
                                    ),
                                    color=WHITE, font_size="15px", font_weight="600",
                                ),
                                align_items="start", spacing="1",
                                padding="1rem",
                                background="rgba(255,255,255,0.03)",
                                border_radius="10px",
                                width="100%",
                                border="1px solid rgba(255,255,255,0.06)",
                            ),

                            rx.vstack(
                                rx.text("Asientos seleccionados", color=GRAY_MUTED, font_size="12px"),
                                rx.text(
                                    rx.cond(
                                        AppState.seat_count > 0,
                                        AppState.selected_seats.join(", "),
                                        "Ninguno",
                                    ),
                                    color=WHITE, font_size="14px", font_weight="600",
                                ),
                                align_items="start", spacing="1",
                                padding="1rem",
                                background="rgba(255,255,255,0.03)",
                                border_radius="10px",
                                width="100%",
                                border="1px solid rgba(255,255,255,0.06)",
                            ),

                            rx.divider(border_color="rgba(255,255,255,0.08)"),

                            rx.hstack(
                                rx.text("TOTAL", color=WHITE_MUTED, font_size="14px", font_weight="700"),
                                rx.text(
                                    "RD$ ", AppState.total_price,
                                    color=GOLD_VIP, font_size="1.4rem", font_weight="800",
                                ),
                                justify="between",
                                width="100%",
                                align="center",
                            ),

                            rx.button(
                                rx.hstack(
                                    rx.icon("check", size=18),
                                    rx.text("Confirmar Reserva"),
                                    spacing="2", align="center",
                                ),
                                on_click=AppState.confirm_reservation,
                                background=rx.cond(AppState.seat_count > 0, RED_CINE, "rgba(255,255,255,0.08)"),
                                color=rx.cond(AppState.seat_count > 0, WHITE, WHITE_MUTED),
                                border="none",
                                border_radius="10px",
                                padding="14px",
                                font_size="15px",
                                font_weight="700",
                                cursor=rx.cond(AppState.seat_count > 0, "pointer", "not-allowed"),
                                transition="all 0.2s ease",
                                width="100%",
                            ),

                            rx.button(
                                "Limpiar selección",
                                on_click=AppState.clear_seats,
                                background="transparent",
                                color=GRAY_MUTED,
                                border="1px solid rgba(255,255,255,0.1)",
                                border_radius="8px",
                                padding="10px",
                                font_size="13px",
                                cursor="pointer",
                                width="100%",
                                _hover={"color": WHITE, "border_color": "rgba(255,255,255,0.3)"},
                            ),

                            padding="1.5rem",
                            background=GRAY_DARK,
                            border_radius="16px",
                            border="1px solid rgba(255,255,255,0.06)",
                            min_width="280px",
                            max_width="320px",
                            align_items="start",
                            spacing="4",
                            align_self="start",
                            position="sticky",
                            top="80px",
                        ),

                        gap="2rem",
                        flex_wrap=["wrap", "wrap", "nowrap"],
                        align_items="start",
                        width="100%",
                    ),

                    align_items="flex-start",
                    spacing="8",
                    width="100%",
                ),

                max_width="1200px",
                margin="0 auto",
                padding=["6rem 1.5rem 3rem", "7rem 2rem 3rem", "8rem 4rem 3rem"],
            ),

            background=BLACK_CINEMA,
            min_height="100vh",
        ),

        footer(),
        toast(),
        font_family=FONT_BODY,
        background=BLACK_CINEMA,
    )
