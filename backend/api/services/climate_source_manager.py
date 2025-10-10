"""
Gerenciador de fontes de dados climáticos.

Detecta quais fontes estão disponíveis para uma determinada localização
e gerencia a fusão de dados de múltiplas fontes.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from loguru import logger


class ClimateSourceManager:
    """Gerencia disponibilidade e seleção de fontes climáticas.
    
    Estratégia de Resolução Temporal:
    ------------------------------------
    - OpenMeteo: HORÁRIA
        * Uso exclusivo para heatmap MATOPIBA
        * Dados horários de hoje + amanhã
        * 337 cidades fixas
        * Atualização às 05:00 BRT
    
    - Demais fontes: DIÁRIA
        * Uso para mapa mundial (qualquer ponto)
        * Dados diários para período de 7-15 dias
        * Sob demanda (clique do usuário)
        * Fusão de múltiplas fontes
    """

    # Configuração de fontes de dados disponíveis
    SOURCES_CONFIG = {
        "openmeteo": {
            "id": "openmeteo",
            "name": "Open-Meteo",
            "coverage": "global",
            "temporal": "hourly",
            "bbox": None,  # Global coverage
            "license": "non_commercial",  # CC-BY-NC - APENAS NÃO COMERCIAL
            "realtime": True,
            "priority": 1,
            "url": "https://api.open-meteo.com/v1/forecast",
            "variables": [
                "temperature_2m",
                "relative_humidity_2m",
                "wind_speed_10m",
                "shortwave_radiation",
                "precipitation",
                "et0_fao_evapotranspiration"
            ],
            "delay_hours": 0,  # Dados em tempo real
            "update_frequency": "hourly",
            # RESTRIÇÕES CRÍTICAS - CC-BY-NC:
            "restrictions": {
                "visualization_only": True,  # Apenas visualização
                "no_download": True,  # Sem download de dados
                "no_data_fusion": True,  # Não usar em fusão
                "clear_cache": True,  # Limpar cache regularmente
                "limit_requests": 10000  # 10k req/dia
            },
            "use_case": "MATOPIBA heatmap visualization only"
        },
        "nasa_power": {
            "id": "nasa_power",
            "name": "NASA POWER",
            "coverage": "global",
            "temporal": "daily",
            "bbox": None,  # Global coverage
            "license": "public_domain",  # Domínio Público
            "realtime": False,  # Atraso 2-3 dias (T, RH, precip, vento)
                                # Atraso 5-7 dias (radiação solar)
            "priority": 2,
            "url": "https://power.larc.nasa.gov/api/temporal/daily/point",
            "variables": [
                "T2M_MAX",
                "T2M_MIN",
                "T2M",
                "RH2M",
                "WS2M",
                "ALLSKY_SFC_SW_DWN",
                "PRECTOTCORR"
            ],
            "delay_hours": 72,  # 2-3 dias de atraso
            "update_frequency": "daily",
            "historical_start": "1981-01-01",
            "restrictions": {
                "limit_requests": 1000  # 1000 req/dia
            },
            "use_case": "Global daily ETo, data fusion"
        },
        "met_norway": {
            "id": "met_norway",
            "name": "MET Norway",
            "coverage": "europe",
            "temporal": "daily",
            "bbox": (-25.0, 35.0, 45.0, 72.0),  # (W, S, E, N) - Europa
            "license": "CC-BY-4.0",  # Creative Commons Attribution 4.0
            "realtime": True,
            "priority": 4,
            "url": "https://api.met.no/weatherapi/locationforecast/2.0",
            "variables": [
                "air_temperature",
                "relative_humidity",
                "wind_speed",
                "cloud_area_fraction",
                "precipitation_amount"
            ],
            "delay_hours": 1,
            "update_frequency": "daily",
            "restrictions": {
                "attribution_required": True,  # Obrigatório citar a fonte
                "limit_requests": "20 req/s"   # Rate limit
            },
            "use_case": "Europe daily ETo, data fusion"
        },
        "nws_usa": {
            "id": "nws_usa",
            "name": "National Weather Service (NOAA)",
            "coverage": "usa",
            "temporal": "daily",
            "bbox": (-125.0, 24.0, -66.0, 49.0),  # (W,S,E,N) USA Continental
            "license": "public_domain",  # Domínio Público (US Government)
            "realtime": True,
            "priority": 5,
            "url": "https://api.weather.gov/",
            "variables": [
                "temperature",
                "relativeHumidity",
                "windSpeed",
                "windDirection",
                "skyCover",
                "quantitativePrecipitation"
            ],
            "delay_hours": 1,
            "update_frequency": "daily",
            "restrictions": {
                "attribution_required": True,  # Citar NOAA
                "user_agent_required": True    # User-Agent obrigatório
            },
            "use_case": "USA daily ETo, data fusion"
        }
    }

    # Validação de datasets (offline, apenas documentação)
    VALIDATION_DATASETS = {
        "xavier_brazil": {
            "name": "Xavier et al. Daily Weather Gridded Data",
            "period": "1961-01-01 to 2024-03-20",
            "resolution": "0.25° x 0.25°",
            "coverage": "brazil",
            "cities": [
                # MATOPIBA (16 cidades)
                {"name": "Balsas", "uf": "MA",
                 "lat": -7.5312, "long": -46.0390},
                {"name": "Imperatriz", "uf": "MA",
                 "lat": -5.5265, "long": -47.4798},
                {"name": "Barra do Corda", "uf": "MA",
                 "lat": -5.5083, "long": -45.2390},
                {"name": "Carolina", "uf": "MA",
                 "lat": -7.3308, "long": -47.4701},
                {"name": "Bom Jesus", "uf": "PI",
                 "lat": -9.0709, "long": -44.3605},
                {"name": "Corrente", "uf": "PI",
                 "lat": -10.4409, "long": -45.1633},
                {"name": "Gilbués", "uf": "PI",
                 "lat": -9.8346, "long": -45.3469},
                {"name": "Uruçuí", "uf": "PI",
                 "lat": -7.2435, "long": -44.5435},
                {"name": "Barreiras", "uf": "BA",
                 "lat": -12.1449, "long": -45.0042},
                {"name": "Luís Eduardo Magalhães", "uf": "BA",
                 "lat": -12.0784, "long": -45.8005},
                {"name": "Formosa do Rio Preto", "uf": "BA",
                 "lat": -11.0470, "long": -45.1910},
                {"name": "Correntina", "uf": "BA",
                 "lat": -13.3418, "long": -44.6411},
                {"name": "Araguaína", "uf": "TO",
                 "lat": -7.1913, "long": -48.2087},
                {"name": "Gurupi", "uf": "TO",
                 "lat": -11.7298, "long": -49.0715},
                {"name": "Palmas", "uf": "TO",
                 "lat": -10.1840, "long": -48.3336},
                {"name": "Porto Nacional", "uf": "TO",
                 "lat": -10.7084, "long": -48.4176},
                # Piracicaba, SP (controle)
                {"name": "Piracicaba", "uf": "SP",
                 "lat": -22.7249, "long": -47.6486}
            ],
            "reference": "https://doi.org/10.1002/joc.5325",
            "validation_metric": "ETo_FAO56"
        },
        "agera5": {
            "name": "AgERA5 (ECMWF - Copernicus)",
            "period": "1979-01-01 to present (historical)",
            "resolution": "0.1° x 0.1°",
            "coverage": "global",
            "license": "CC-BY-4.0",  # Creative Commons Attribution 4.0
            "delay": "~7 days",
            "use_case": "Validation only (not for real-time ETo)",
            "reference": (
                "https://cds.climate.copernicus.eu/datasets/"
                "sis-agrometeorological-indicators"
            ),
            "validation_metric": "ETo_reference",
            "note": (
                "AgERA5 is designed for historical analysis and model "
                "validation. It provides reanalysis data (hindcast) with "
                "~7 days delay, making it unsuitable for real-time ETo "
                "calculation but excellent for validating results."
            )
        }
    }

    def __init__(self):
        """Inicializa o gerenciador de fontes."""
        self.enabled_sources = {
            key: value for key, value in self.SOURCES_CONFIG.items()
        }
        logger.info(
            "ClimateSourceManager initialized with %d sources",
            len(self.enabled_sources)
        )

    def get_available_sources(
        self,
        lat: float,
        long: float
    ) -> List[Dict]:
        """
        Retorna fontes disponíveis para uma coordenada específica.

        Args:
            lat: Latitude (-90 a 90)
            long: Longitude (-180 a 180)

        Returns:
            List[Dict]: Lista de fontes disponíveis com metadados
        """
        available = []

        for source_id, metadata in self.enabled_sources.items():
            if self._is_point_covered(lat, long, metadata):
                available.append({
                    "id": source_id,
                    "name": metadata["name"],
                    "coverage": metadata["coverage"],
                    "temporal": metadata["temporal"],
                    "realtime": metadata["realtime"],
                    "priority": metadata["priority"],
                    "delay_hours": metadata.get("delay_hours", 0),
                    "variables": metadata.get("variables", [])
                })

        # Ordena por prioridade
        available.sort(key=lambda x: x["priority"])

        logger.info(
            "Found %d sources for lat=%s, long=%s: %s",
            len(available), lat, long,
            [s["id"] for s in available]
        )

        return available

    def get_available_sources_for_location(
        self,
        lat: float,
        lon: float,
        exclude_non_commercial: bool = True
    ) -> Dict[str, Dict]:
        """
        Retorna fontes disponíveis para uma localização específica.
        
        Este método é otimizado para uso no mapa mundial, excluindo
        automaticamente fontes com restrições de licença não-comercial
        (como Open-Meteo) que não podem ser usadas em fusão de dados.

        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
            exclude_non_commercial: Se True, exclui fontes CC-BY-NC
                                   (default: True para mapa mundial)

        Returns:
            Dict[str, Dict]: Dicionário com fontes disponíveis e metadados
                {
                    "nasa_power": {
                        "available": True,
                        "name": "NASA POWER",
                        "coverage": "global",
                        "bbox": None,
                        "license": "public_domain",
                        "priority": 2,
                        "can_fuse": True,
                        "can_download": True
                    },
                    ...
                }

        Example:
            >>> manager = ClimateSourceManager()
            >>> # Paris, França
            >>> sources = manager.get_available_sources_for_location(
            ...     48.8566, 2.3522
            ... )
            >>> # Retorna: nasa_power (global), met_norway (Europa)
            >>> # Exclui: openmeteo (non-commercial), nws_usa (fora bbox)
        """
        result = {}

        for source_id, metadata in self.enabled_sources.items():
            # Filtrar fontes não-comerciais se solicitado
            license_type = metadata.get("license", "")
            is_non_commercial = license_type == "non_commercial"

            if exclude_non_commercial and is_non_commercial:
                logger.debug(
                    "Excluding %s (non-commercial license) from mundial map",
                    source_id
                )
                continue

            # Verificar cobertura geográfica
            bbox = metadata.get("bbox")
            is_covered = self._is_point_covered(lat, lon, metadata)

            # Verificar restrições de fusão e download
            restrictions = metadata.get("restrictions", {})
            can_fuse = not restrictions.get("no_data_fusion", False)
            can_download = not restrictions.get("no_download", False)

            result[source_id] = {
                "available": is_covered,
                "name": metadata["name"],
                "coverage": metadata["coverage"],
                "bbox": bbox,
                "bbox_str": self._format_bbox(bbox),
                "license": license_type,
                "priority": metadata["priority"],
                "can_fuse": can_fuse,
                "can_download": can_download,
                "realtime": metadata.get("realtime", False),
                "temporal": metadata.get("temporal", "daily"),
                "variables": metadata.get("variables", []),
                "attribution_required": restrictions.get(
                    "attribution_required", False
                )
            }

        # Log das fontes disponíveis
        available_ids = [
            sid for sid, meta in result.items() if meta["available"]
        ]
        logger.info(
            "Sources for lat=%.4f, lon=%.4f: %d available (%s)",
            lat, lon, len(available_ids),
            ", ".join(available_ids) if available_ids else "none"
        )

        return result

    def _format_bbox(self, bbox: Optional[tuple]) -> str:
        """
        Formata bbox para exibição legível.

        Args:
            bbox: Tupla (west, south, east, north) ou None

        Returns:
            str: Bbox formatado (ex: "Europe: 35°N-72°N, 25°W-45°E")
        """
        if bbox is None:
            return "Global coverage"

        west, south, east, north = bbox

        # Formatar coordenadas
        def format_coord(value: float, is_latitude: bool) -> str:
            """Formata coordenada com direção cardinal."""
            direction = ""
            if is_latitude:
                direction = "N" if value >= 0 else "S"
            else:
                direction = "E" if value >= 0 else "W"
            return f"{abs(value):.0f}°{direction}"

        lat_range = f"{format_coord(south, True)}-{format_coord(north, True)}"
        lon_range = f"{format_coord(west, False)}-{format_coord(east, False)}"

        return f"{lat_range}, {lon_range}"

    def _is_point_covered(
        self,
        lat: float,
        long: float,
        metadata: Dict
    ) -> bool:
        """
        Verifica se um ponto está coberto pela fonte.

        Args:
            lat: Latitude
            long: Longitude
            metadata: Metadados da fonte

        Returns:
            bool: True se ponto está coberto
        """
        bbox = metadata.get("bbox")

        # Cobertura global
        if bbox is None:
            return True

        # Cobertura regional (bbox format: west, south, east, north)
        west, south, east, north = bbox
        return west <= long <= east and south <= lat <= north

    def validate_period(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida período de datas conforme especificações.

        Regras:
        - Mínimo: 7 dias
        - Máximo: 15 dias
        - Não pode ser mais de 1 ano no passado
        - Não pode ser mais de 1 dia no futuro

        Args:
            start_date: Data inicial
            end_date: Data final

        Returns:
            Tuple[bool, Optional[str]]: (válido, mensagem_erro)
        """
        now = datetime.now()

        # Verifica ordem das datas
        if end_date <= start_date:
            return False, "Data final deve ser posterior à data inicial"

        # Calcula duração
        period_days = (end_date - start_date).days + 1

        # Valida duração
        if period_days < 7:
            return False, f"Período mínimo: 7 dias (atual: {period_days})"

        if period_days > 15:
            return False, f"Período máximo: 15 dias (atual: {period_days})"

        # Valida limite passado (1 ano)
        one_year_ago = now.replace(year=now.year - 1)
        if start_date < one_year_ago:
            return False, (
                f"Data inicial não pode ser anterior a "
                f"{one_year_ago.strftime('%d/%m/%Y')}"
            )

        # Valida limite futuro (amanhã)
        tomorrow = now.replace(hour=23, minute=59, second=59)
        if end_date > tomorrow:
            return False, (
                f"Data final não pode ser posterior a "
                f"{tomorrow.strftime('%d/%m/%Y')}"
            )

        return True, None

    def get_fusion_weights(
        self,
        sources: List[str],
        location: Tuple[float, float]
    ) -> Dict[str, float]:
        """
        Calcula pesos para fusão de dados baseado em prioridades.

        ⚠️ IMPORTANTE: Valida licenças antes de calcular pesos.
        Open-Meteo (CC-BY-NC) não pode ser usado em fusão.

        Args:
            sources: Lista de IDs de fontes selecionadas
            location: Tupla (lat, long)

        Returns:
            Dict[str, float]: Pesos normalizados para cada fonte

        Raises:
            ValueError: Se fonte com licença não-comercial for incluída
        """
        # Validação de licenciamento
        non_commercial_sources = []
        for source_id in sources:
            if source_id in self.SOURCES_CONFIG:
                config = self.SOURCES_CONFIG[source_id]
                license_type = config.get("license", "")

                # Bloqueia fontes não-comerciais em fusão
                if license_type == "non_commercial":
                    non_commercial_sources.append({
                        "id": source_id,
                        "name": config["name"],
                        "license": license_type,
                        "use_case": config.get("use_case", "")
                    })

        if non_commercial_sources:
            source_names = ", ".join(
                [s["name"] for s in non_commercial_sources]
            )
            error_msg = (
                f"License violation: {source_names} cannot be used in "
                f"data fusion due to non-commercial license restrictions. "
                f"These sources are restricted to: "
                f"{non_commercial_sources[0]['use_case']}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Cálculo de pesos (prioridade inversa)
        weights = {}
        total_priority = 0

        for source_id in sources:
            if source_id in self.SOURCES_CONFIG:
                # Peso inverso da prioridade (menor prioridade = maior peso)
                priority = self.SOURCES_CONFIG[source_id]["priority"]
                weight = 1.0 / priority
                weights[source_id] = weight
                total_priority += weight

        # Normaliza pesos (soma = 1.0)
        if total_priority > 0:
            weights = {
                k: v / total_priority for k, v in weights.items()
            }

        logger.debug("Fusion weights for %s: %s", sources, weights)
        return weights

    def get_validation_info(self) -> Dict:
        """
        Retorna informações sobre datasets de validação.

        Returns:
            Dict: Informações dos datasets de validação
        """
        return self.VALIDATION_DATASETS
