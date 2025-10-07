"""
Componente de rodapé para o aplicativo EVAOnline.
"""
import dash_bootstrap_components as dbc
from dash import html


def render_footer() -> html.Footer:
    """
    Cria um rodapé responsivo com informações de parceiros, desenvolvedores e copyright.
    
    Returns:
        html.Footer: Componente do rodapé
    """
    # Dicionário de links dos parceiros
    partner_links = {
        "c4ai": "https://c4ai.inova.usp.br/",
        "fapesp": "https://fapesp.br/",
        "ibm": "https://www.ibm.com/br-pt",
        "usp": "https://www5.usp.br/",
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
        {"name": "Ângela S. M. C. Soares", "email": "angelassilviane@gmail.com"},
        {"name": "Patricia A. A. Marques", "email": "paamarques@usp.br"},
        {"name": "Carlos D. Maciel", "email": "carlos.maciel@unesp.br"},
    ]
    
    # Função para gerar link de email apropriado
    def get_email_link(email):
        domain = email.split("@")[1].lower()
        email_link_template = EMAIL_PROVIDERS.get(domain, DEFAULT_EMAIL_LINK)
        return email_link_template.format(email=email)
    
    # Seção de Parceiros
    partners_section = html.Div([
        html.H5("Parceiros", className="mb-3", 
                style={"fontSize": "16px", "fontWeight": "600", "color": "#2d5016"}),
        html.Div([
            html.A(
                html.Img(
                    src=f"/assets/images/logo_{partner}.png",
                    style={"height": "50px", "margin": "10px 15px",
                           "filter": "grayscale(30%)", "opacity": "0.85",
                           "transition": "all 0.3s"},
                    className="partner-logo"
                ),
                href=link,
                target="_blank",
                title=partner.upper()
            )
            for partner, link in partner_links.items()
        ], style={"display": "flex", "flexWrap": "wrap", 
                  "justifyContent": "center", "alignItems": "center"})
    ], className="mb-4")
    
    # Seção de Desenvolvedores
    developers_section = html.Div([
        html.H5("Desenvolvedores", className="mb-3",
                style={"fontSize": "16px", "fontWeight": "600", "color": "#2d5016"}),
        html.Ul([
            html.Li([
                html.Strong(dev["name"], style={"color": "#333"}),
                " - ",
                html.A(
                    dev["email"],
                    href=get_email_link(dev["email"]),
                    target="_blank",
                    style={"color": "#2d5016", "textDecoration": "none"},
                    className="email-link"
                )
            ], style={"marginBottom": "8px", "fontSize": "14px"})
            for dev in developers
        ], style={"listStyle": "none", "padding": "0"})
    ], className="mb-4")
    
    # Copyright
    copyright_section = html.Div([
        html.Hr(style={"borderColor": "#dee2e6", "margin": "20px 0"}),
        html.P(
            "© 2025 EVAonline: An online tool for reference EVApotranspiration estimation. Todos os direitos reservados.",
            className="text-center text-muted mb-0",
            style={"fontSize": "13px"}
        )
    ])
    
    return html.Footer(
        dbc.Container([
            dbc.Row([
                # Coluna de Parceiros
                dbc.Col(partners_section, md=6, sm=12, className="text-center"),
                # Coluna de Desenvolvedores
                dbc.Col(developers_section, md=6, sm=12, className="text-center")
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(copyright_section, width=12)
            ])
        ], fluid=True, className="mt-5 p-4 border-top", 
           style={"backgroundColor": "#f8f9fa"})
    )
