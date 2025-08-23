"""
Módulo de componentes reutilizáveis para o aplicativo EVAOnline.
"""
from components.navbar import render_navbar_bootswatch
from components.footer import render_footer_bootswatch
from components.home_layout import create_home_layout
from components.map_components import create_legend, create_map_components
from components.coordinate_callbacks import register_coordinate_callbacks

# Exportar os componentes
__all__ = [
    'render_navbar_bootswatch',
    'render_footer_bootswatch',
    'create_home_layout',
    'create_legend',
    'create_map_components',
    'register_coordinate_callbacks'
]
