"""
components/navbar.py
Navbar premium estilo Netflix.
"""

import reflex as rx
from cinemax.pages.styles.theme import *
from cinemax.states.app_state import AppState


def nav_link(label: str, href: str) -> rx.Component:
    return rx.link(
        label,
        href=href,
        color=WHITE_SOFT,
        font_size="14px",
        font_weight="500",
        text_decoration="none",
        padding="6px 0",
        transition="color 0.2s ease",
        _hover={"color": WHITE},
    )


def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            # Logo
            rx.link(
                rx.hstack(
                    rx.text("C", color=RED_CINE, font_size="1.6rem", font_family=FONT_HEADING, display="inline"),
                    rx.text("INEMAX", color=WHITE, font_size="1.6rem", font_family=FONT_HEADING, display="inline"),
                    spacing="0",
                ),
                href="/",
                text_decoration="none",
            ),

            # Desktop Nav
            rx.hstack(
                nav_link("Inicio", "/"),
                nav_link("Cartelera", "/catalogo"),
                nav_link("VIP", "/#vip"),
                nav_link("Promociones", "/#promo"),
                spacing="6",
                display=["none", "none", "flex"],
            ),

            # Auth
            rx.hstack(
                rx.cond(
                    AppState.is_logged_in,
                    rx.hstack(
                        rx.text(
                            "👤 ", AppState.user_name,
                            color=WHITE_SOFT, font_size="14px",
                        ),
                        rx.button(
                            "Salir",
                            on_click=AppState.handle_logout,
                            background="transparent",
                            color=WHITE_MUTED,
                            border="1px solid rgba(255,255,255,0.2)",
                            border_radius="6px",
                            padding="6px 14px",
                            font_size="13px",
                            cursor="pointer",
                            _hover={"color": WHITE, "border_color": "rgba(255,255,255,0.5)"},
                        ),
                        spacing="4",
                        display=["none", "none", "flex"],
                    ),
                    rx.hstack(
                        rx.link(
                            "Iniciar sesión",
                            href="/login",
                            color=WHITE_SOFT,
                            font_size="14px",
                            text_decoration="none",
                            _hover={"color": WHITE},
                            display=["none", "none", "block"],
                        ),
                        rx.link(
                            rx.button(
                                "Registrarse",
                                background=RED_CINE,
                                color=WHITE,
                                border="none",
                                border_radius="8px",
                                padding="8px 20px",
                                font_size="14px",
                                font_weight="600",
                                cursor="pointer",
                                transition="all 0.2s ease",
                                _hover={"background": RED_HOVER, "transform": "translateY(-1px)"},
                            ),
                            href="/registro",
                            text_decoration="none",
                            display=["none", "none", "block"],
                        ),
                        spacing="4",
                        align_items="center",
                    ),
                ),

                # Hamburger
                rx.button(
                    rx.icon("menu", size=22),
                    on_click=AppState.toggle_mobile_menu,
                    background="transparent",
                    border="none",
                    color=WHITE,
                    cursor="pointer",
                    display=["flex", "flex", "none"],
                    padding="4px",
                ),
                align_items="center",
                spacing="4",
            ),

            align="center",
            justify="between",
            width="100%",
        ),

        # Mobile Menu
        rx.cond(
            AppState.mobile_menu_open,
            rx.box(
                rx.vstack(
                    rx.link("Inicio", href="/", color=WHITE_SOFT, text_decoration="none", font_size="16px", padding="8px 0", width="100%"),
                    rx.link("Cartelera", href="/catalogo", color=WHITE_SOFT, text_decoration="none", font_size="16px", padding="8px 0", width="100%"),
                    rx.link("VIP", href="/#vip", color=WHITE_SOFT, text_decoration="none", font_size="16px", padding="8px 0", width="100%"),
                    rx.divider(border_color="rgba(255,255,255,0.1)"),
                    rx.link("Iniciar sesión", href="/login", color=WHITE_SOFT, text_decoration="none", font_size="16px", padding="8px 0", width="100%"),
                    rx.link(
                        rx.box("Registrarse", background=RED_CINE, color=WHITE, border_radius="8px", padding="10px 0", text_align="center", width="100%"),
                        href="/registro",
                        text_decoration="none",
                        width="100%",
                    ),
                    spacing="0",
                    align_items="start",
                    width="100%",
                    padding="1rem 2rem",
                ),
                background="rgba(10,10,10,0.98)",
                backdrop_filter="blur(10px)",
                position="absolute",
                top="64px",
                left="0",
                right="0",
                z_index="999",
                border_top="1px solid rgba(255,255,255,0.08)",
            ),
        ),

        position="fixed",
        top="0",
        left="0",
        right="0",
        z_index="1000",
        height="64px",
        padding="0 2.5rem",
        display="flex",
        align_items="center",
        background="rgba(10,10,10,0.92)",
        backdrop_filter="blur(16px)",
        border_bottom="1px solid rgba(255,255,255,0.06)",
        transition="all 0.3s ease",
    )
