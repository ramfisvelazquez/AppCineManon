"""
components/footer.py
Footer cinematográfico premium y responsive.
"""

import reflex as rx
from cinemax.pages.styles.theme import *


def social_icon(icon_name: str, href: str) -> rx.Component:
    return rx.link(
        rx.icon(icon_name, size=18),
        href=href,
        color=WHITE_MUTED,
        transition="color 0.2s ease",
        _hover={"color": RED_CINE},
    )


def footer_link(label: str, href: str) -> rx.Component:
    return rx.link(
        label,
        href=href,
        color=WHITE_MUTED,
        font_size="13px",
        text_decoration="none",
        transition="color 0.2s ease",
        _hover={"color": WHITE_SOFT},
    )


def footer() -> rx.Component:
    return rx.box(
        rx.box(
            rx.flex(
                # Brand
                rx.vstack(
                    rx.hstack(
                        rx.text("C", color=RED_CINE, font_size="1.8rem", font_family=FONT_HEADING, display="inline"),
                        rx.text("INEMAX", color=WHITE, font_size="1.8rem", font_family=FONT_HEADING, display="inline"),
                        spacing="0",
                    ),
                    rx.text(
                        "La mejor experiencia cinematográfica de República Dominicana.",
                        color=WHITE_MUTED,
                        font_size="13px",
                        max_width="240px",
                        line_height="1.6",
                    ),
                    rx.hstack(
                        social_icon("camera", "#"),     # instagram → camera
                        social_icon("globe", "#"),      # facebook → globe
                        social_icon("message-circle", "#"),  # twitter → message-circle
                        social_icon("play", "#"),       # youtube → play
                        spacing="4",
                    ),
                    align_items="start",
                    spacing="4",
                ),

                # Quick links
                rx.vstack(
                    rx.text("Navegación", color=WHITE, font_size="13px", font_weight="700", text_transform="uppercase", letter_spacing="1", margin_bottom="0.5rem"),
                    footer_link("Inicio", "/"),
                    footer_link("Cartelera", "/catalogo"),
                    footer_link("VIP Premium", "/#vip"),
                    footer_link("Promociones", "/#promo"),
                    footer_link("Reservas", "/reservas"),
                    spacing="2",
                    align_items="start",
                ),

                # Account links
                rx.vstack(
                    rx.text("Mi Cuenta", color=WHITE, font_size="13px", font_weight="700", text_transform="uppercase", letter_spacing="1", margin_bottom="0.5rem"),
                    footer_link("Iniciar Sesión", "/login"),
                    footer_link("Registrarse", "/registro"),
                    footer_link("Mis Reservas", "#"),
                    footer_link("Perfil VIP", "#"),
                    spacing="2",
                    align_items="start",
                ),

                # Contact
                rx.vstack(
                    rx.text("Contacto", color=WHITE, font_size="13px", font_weight="700", text_transform="uppercase", letter_spacing="1", margin_bottom="0.5rem"),
                    rx.hstack(rx.icon("map-pin", size=14, color=GRAY_MUTED), rx.text("Santo Domingo, RD", color=WHITE_MUTED, font_size="13px"), spacing="2"),
                    rx.hstack(rx.icon("phone", size=14, color=GRAY_MUTED), rx.text("+1 (809) 555-0100", color=WHITE_MUTED, font_size="13px"), spacing="2"),
                    rx.hstack(rx.icon("mail", size=14, color=GRAY_MUTED), rx.text("info@cinemax.com.do", color=WHITE_MUTED, font_size="13px"), spacing="2"),
                    spacing="2",
                    align_items="start",
                ),

                gap="3rem",
                flex_wrap="wrap",
            ),

            rx.divider(border_color="rgba(255,255,255,0.08)", margin="2.5rem 0 1.5rem"),

            rx.flex(
                rx.text("© 2025 Cinemax Premium. Todos los derechos reservados.", color=GRAY_MUTED, font_size="12px"),
                rx.hstack(
                    footer_link("Términos de uso", "#"),
                    rx.text("·", color=GRAY_MUTED, font_size="12px"),
                    footer_link("Política de privacidad", "#"),
                    rx.text("·", color=GRAY_MUTED, font_size="12px"),
                    footer_link("Cookies", "#"),
                    spacing="2",
                    align_items="center",
                ),
                justify="between",
                flex_wrap="wrap",
                gap="1rem",
                align_items="center",
            ),

            max_width="1200px",
            margin="0 auto",
            padding="3rem 2rem",
        ),

        background=BLACK_DEEP,
        border_top="1px solid rgba(255,255,255,0.06)",
        width="100%",
    )
