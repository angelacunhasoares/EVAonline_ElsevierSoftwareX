import base64
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import streamlit as st
from PIL import Image


def render_footer():
    """
    Renderiza o footer do aplicativo EVAonline com informações de desenvolvedores,
    logos de parceiros e direitos autorais.
    """
    # Diretório base
    diretorio = Path(__file__).parent if "__file__" in locals() else Path.cwd()
    assets_dir = diretorio / "assets"
    css_file = diretorio / "static" / "styles.css"

    # Verificar se a pasta assets existe
    if not assets_dir.exists():
        st.error(
            f"Pasta {assets_dir} não encontrada! Certifique-se de que ela existe e contém as imagens."
        )
        return

    # Carregar CSS externo
    try:
        with open(css_file) as c:
            css_content = c.read()
            css_content = css_content.strip()  # Limpar espaços e quebras
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(
            f"Arquivo CSS {css_file} não encontrado! Verifique se ele está na pasta src."
        )
        return
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo CSS {css_file}: {e}")
        return

    # Função para converter imagem para base64
    def image_to_base64(image_path):
        try:
            with Image.open(image_path) as img:
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            st.error(f"Erro ao carregar imagem {image_path}: {e}")
            return None

    # Carregar imagens como base64
    logo_images = {
        "esalq": image_to_base64(assets_dir / "logo_esalq_red.png"),
        "usp": image_to_base64(assets_dir / "logo_usp.png"),
        "c4ai": image_to_base64(assets_dir / "logo_c4ai.png"),
        "fapesp": image_to_base64(assets_dir / "logo_fapesp.png"),
        "ibm": image_to_base64(assets_dir / "logo_ibm.png"),
    }

    # Dicionário de links dos parceiros
    partner_links = {
        "esalq": "https://www.esalq.usp.br/",
        "usp": "https://www5.usp.br/",
        "c4ai": "https://c4ai.inova.usp.br/",
        "fapesp": "https://fapesp.br/",
        "ibm": "https://www.ibm.com/br-pt",
    }

    # Dicionário de provedores conhecidos e links de redirecionamento
    EMAIL_PROVIDERS = {
        "gmail.com": "https://mail.google.com/mail/?view=cm&fs=1&to={email}",
        "usp.br": "https://mail.google.com/mail/?view=cm&fs=1&to={email}",
        "unesp.br": "https://mail.google.com/mail/?view=cm&fs=1&to={email}",
        "outlook.com": "https://outlook.live.com/mail/0/deeplink/compose?to={email}",
        "hotmail.com": "https://outlook.live.com/mail/0/deeplink/compose?to={email}",
    }

    # Link padrão para provedores não reconhecidos
    DEFAULT_EMAIL_LINK = "mailto:{email}"

    # Lista de desenvolvedores
    developers = [
        {"name": "Patricia A. A. Marques", "email": "paamarques@usp.br"},
        {"name": "Carlos D. Maciel", "email": "carlos.maciel@unesp.br"},
        {"name": "Ângela S. M. Cunha", "email": "angelassilviane@gmail.com"},
    ]

    # Construir o HTML de forma limpa
    footer_parts = [
        "<footer class='footer'>",
        "<div class='footer-grid'>",
        "<!-- Linha 1, Coluna 1: Desenvolvedores -->",
        "<div class='footer-cell'>",
        "<h4>Developers</h4>",
        "<ul>",
    ]
    for dev in developers:
        email = dev["email"]
        domain = email.split("@")[1].lower()
        email_link_template = EMAIL_PROVIDERS.get(domain, DEFAULT_EMAIL_LINK)
        email_link = email_link_template.format(email=quote(email))
        footer_parts.append(
            f"<li>{dev['name']} - <a href='{email_link}' target='_blank'>{email}</a></li>"
        )

    footer_parts.extend(
        [
            "</ul>",
            "</div>",
            "<!-- Linha 1, Coluna 2: Logos dos Parceiros -->",
            "<div class='footer-cell'>",
            "<h4>Partners</h4>",
            "<div class='logo-container'>",
        ]
    )

    # Adicionar logos com links
    for logo_name, base64_data in logo_images.items():
        if base64_data:
            footer_parts.append(
                f"<a href='{partner_links[logo_name]}' target='_blank'>"
                f"<img src='data:image/png;base64,{base64_data}' width='150' alt='{logo_name.upper()}' class='footer-logo'></a>"
            )

    footer_parts.extend(
        [
            "</div>",
            "</div>",
            "<!-- Linha 2, Colunas 1 e 2: Direitos -->",
            "<div class='footer-cell full-width'>",
            "<p class='copyright-text'>© 2025 EVAonline - All rights reserved.</p>",
            "</div>",
            "</div>",  # Fecha .footer-grid
            "</footer>",  # Fecha .footer
        ]
    )
    footer_html = "".join(footer_parts)

    # Renderizar o HTML
    st.markdown(footer_html, unsafe_allow_html=True)


# if __name__ == "__main__":
#     st.set_page_config(page_title="Footer Test", page_icon=":guardsman:", layout="wide")
#     st.title("Footer Test")
#     render_footer()
