"""
Rotas internas para funcionalidades da página About.
Estas rotas são consumidas pelo frontend Dash e não são expostas diretamente
ao usuário.
"""

from typing import Dict, List, Union
from fastapi import APIRouter

# Router interno para funções da página About
about_router = APIRouter(
    prefix="/api/internal/about",
    tags=["About Internal"]
)


@about_router.get("/info")
async def get_about_info() -> Dict[str, Union[Dict[str, str], List[Dict[str, str]]]]:
    """
    Endpoint interno para obter informações sobre o software.
    Chamado pelo frontend na página About.

    Returns:
        Dict com informações sobre desenvolvedores, parceiros e software
    """
    return {
        "software": {
            "name": "EVAonline",
            "version": "1.0.0",
            "description": "Calculadora online de Evapotranspiração",
            "repository": "https://github.com/angelacunhasoares/EVAonline",
            "license": "MIT"
        },
        "developers": {
            "main": "Angela Cunha Soares <angelacunhasoares@gmail.com>",
            "supervisor": "Prof. Dr. Fábio Ricardo Marin <fabio.marin@usp.br>"
        },
        "partners": [
            {
                "name": "ESALQ/USP",
                "url": "https://www.esalq.usp.br/",
                "logo": "logo_esalq.png"
            },
            {
                "name": "USP",
                "url": "https://www5.usp.br/",
                "logo": "logo_usp.png"
            },
            {
                "name": "FAPESP",
                "url": "https://fapesp.br/",
                "logo": "logo_fapesp.png"
            },
            {
                "name": "C4AI",
                "url": "http://c4ai.inova.usp.br/",
                "logo": "logo_c4ai.png"
            },
            {
                "name": "IBM",
                "url": "https://www.ibm.com/",
                "logo": "logo_ibm.png"
            }
        ]
    }
