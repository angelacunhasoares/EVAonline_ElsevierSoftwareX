from datetime import date, datetime, timedelta
from typing import Optional, Union, Tuple, List
import os
import pickle
import pandas as pd
import requests
from requests.exceptions import RequestException
from celery import shared_task
from redis import Redis
from loguru import logger

# Definir a URL do Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


class NasaPowerAPI:
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point?"
    
    VALID_PARAMETERS = [
        "T2M_MAX",
        "T2M_MIN",
        "T2M",
        "RH2M",
        "WS2M",
        "ALLSKY_SFC_SW_DWN",
        "PRECTOTCORR",
    ]

    NASA_CACHE_EXPIRY_HOURS = 720  # 30 days

    def __init__(
        self,
        start: Union[date, datetime, pd.Timestamp],
        end: Union[date, datetime, pd.Timestamp],
        long: float,
        lat: float,
        parameter: Optional[list] = None,
        matopiba_only: bool = False,
    ):
        """
        Initialize the class to download daily weather data from NASA POWER.

        Args:
            start: Start date (date, datetime, or pd.Timestamp).
            end: End date (date, datetime, or pd.Timestamp).
            long: Longitude (-180 to 180).
            lat: Latitude (-90 to 90).
            parameter: List of climate parameters to download; if None, uses 
                defaults for FAO-56 ETo.
            matopiba_only: Whether to restrict coordinates to MATOPIBA region.

        Raises:
            ValueError: If parameters, dates, or coordinates are invalid.
        """
        if parameter is not None:
            invalid_params = [
                p for p in parameter 
                if p not in self.VALID_PARAMETERS
            ]
            if invalid_params:
                supported = ", ".join(self.VALID_PARAMETERS)
                raise ValueError(
                    f"Invalid parameters: {invalid_params}. Valid: {supported}"
                )
        self.parameter = (
            parameter if parameter is not None 
            else self.VALID_PARAMETERS
        )

        self.start = (
            start
            if isinstance(start, datetime)
            else datetime.combine(start, datetime.min.time())
        )
        self.end = (
            end
            if isinstance(end, datetime)
            else datetime.combine(end, datetime.min.time())
        )

        # Validações de data
        current_date = datetime.now()
        tomorrow = current_date + timedelta(days=1)
        one_year_ago = current_date - timedelta(days=365)

        # Validar limite de 1 ano para trás
        if self.start < one_year_ago:
            raise ValueError("Data inicial não pode ser anterior a 1 ano atrás.")

        # Validar limite de 1 dia no futuro
        if self.end > tomorrow:
            logger.warning(
                "Data final {} está no futuro. Ajustando para {}.".format(
                    self.end, tomorrow
                )
            )
            self.end = tomorrow

        # Validar ordem das datas
        if self.end < self.start:
            raise ValueError("A data final deve ser posterior à data inicial.")

        # Validar período mínimo e máximo
        period_days = (self.end - self.start).days + 1
        if period_days < 7 or period_days > 15:
            raise ValueError("O período deve ser entre 7 e 15 dias.")

        # Validar coordenadas
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude deve estar entre -90 e 90.")
        if not (-180 <= long <= 180):
            raise ValueError("Longitude deve estar entre -180 e 180.")

        # Validar região MATOPIBA
        lat_valid = -14.5 <= lat <= -2.5
        long_valid = -50.0 <= long <= -41.5
        if matopiba_only and not (lat_valid and long_valid):
            msg = (
                "Coordenadas (lat={}, long={}) fora da região MATOPIBA "
                "(-14.5 a -2.5 lat, -50.0 a -41.5 long)"
            ).format(lat, long)
            logger.warning(msg)

        self.long = long
        self.lat = lat
        self.matopiba_only = matopiba_only
        self.request = self._build_request()

        # Inicializa cliente Redis
        try:
            self.redis_client = Redis.from_url(
                REDIS_URL, decode_responses=False
            )
            self.redis_client.ping()  # Testa conexão
        except Exception as e:
            logger.error("Falha ao conectar com Redis: %s", e)
            self.redis_client = None

    def _build_request(self) -> str:
        """
        Constrói a URL para requisição à API NASA POWER.
        
        Returns:
            str: URL completa com parâmetros.
        """
        params = ",".join(self.parameter)
        start_date = self.start.strftime("%Y%m%d")
        end_date = self.end.strftime("%Y%m%d")
        
        # Constrói a URL
        base = (
            f"{self.BASE_URL}parameters={params}&"
            f"community=AG&format=JSON"
        )
        coords = (
            f"&longitude={self.long}&"
            f"latitude={self.lat}"
        )
        dates = (
            f"&start={start_date}&"
            f"end={end_date}"
        )
        return base + coords + dates

    def _fetch_data(self) -> Tuple[dict, list]:
        """Faz requisição à API NASA POWER."""
        warnings = []
        try:
            response = requests.get(self.request, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Valida resposta
            if not data:
                msg = "Resposta vazia da API NASA POWER"
                warnings.append(msg)
                logger.error(msg)
                return {}, warnings

            has_props = "properties" in data
            has_params = (
                has_props and
                "parameter" in data["properties"]
            )

            if not (has_props and has_params):
                msg = "Resposta inválida da API NASA POWER"
                warnings.append(msg)
                logger.error(msg)
                return {}, warnings
            
            return data, warnings
            
        except RequestException as e:
            msg = f"Erro HTTP NASA POWER: {str(e)}"
            warnings.append(msg)
            logger.error(msg)
            return {}, warnings
            
        except Exception as e:
            msg = f"Erro inesperado NASA POWER: {str(e)}"
            warnings.append(msg)
            logger.error(msg)
            return {}, warnings

    def _save_to_cache(self, df: pd.DataFrame, cache_key: str) -> None:
        """Save data to Redis cache."""
        if not self.redis_client:
            logger.warning("No Redis connection. Skipping cache save.")
            return
        try:
            self.redis_client.setex(
                cache_key,
                timedelta(hours=self.NASA_CACHE_EXPIRY_HOURS),
                pickle.dumps(df)
            )
            logger.info(f"Saved to Redis cache: {cache_key}")
        except Exception as e:
            logger.error("Erro ao salvar no cache Redis: %s", e)

    def _load_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """
        Carrega dados do cache Redis se disponíveis e válidos.
        
        Args:
            cache_key: Chave para buscar no cache.
            
        Returns:
            Optional[pd.DataFrame]: DataFrame com dados ou None.
        """
        if not self.redis_client:
            logger.warning("Sem conexão Redis. Ignorando cache.")
            return None
            
        try:
            # Tenta carregar do cache
            cached_data = self.redis_client.get(cache_key)
            if not cached_data:
                logger.info("Cache Redis não encontrado: %s", cache_key)
                return None
                
            # Desserializa dados
            df = pickle.loads(cached_data)
            
            # Valida período
            if df.index.min() <= self.start and df.index.max() >= self.end:
                logger.info("Carregado do cache Redis: %s", cache_key)
                return df
                
            logger.info(
                "Dados em cache não cobrem o período: %s",
                cache_key
            )
            
        except Exception as e:
            logger.error("Erro ao carregar do cache Redis: %s", e)
            
        return None

    @shared_task
    def get_weather_sync(self) -> Tuple[pd.DataFrame, List[str]]:
        """
        Baixa dados meteorológicos do NASA POWER.

        Returns:
            Tuple[pd.DataFrame, List[str]]: DataFrame com parâmetros climáticos
            diários indexados por data e lista de avisos.

        Example:
            >>> nasa = NasaPowerAPI(
            ...     start="2023-01-01",
            ...     end="2023-01-07",
            ...     long=-45.0,
            ...     lat=-10.0
            ... )
            >>> df, warnings = nasa.get_weather_sync()
        """
        logger.info(
            "Baixando dados NASA POWER para %s a %s (lat=%s, long=%s)",
            self.start.strftime("%Y-%m-%d"),
            self.end.strftime("%Y-%m-%d"),
            self.lat,
            self.long
        )
        
        # Gera chave de cache
        cache_key = (
            f"nasa_power:{self.start:%Y%m%d}:{self.end:%Y%m%d}:"
            f"{self.lat}:{self.long}"
        )
        warnings = []
        
        # Tenta carregar do cache
        df = self._load_from_cache(cache_key)
        if df is not None:
            return df, warnings

        # Busca dados da API
        data, fetch_warnings = self._fetch_data()
        warnings.extend(fetch_warnings)
        
        # Processa resposta
        if data and "properties" in data and "parameter" in data["properties"]:
            try:
                params = data["properties"]["parameter"]
                weather_df = pd.DataFrame(params)
                
                # Converte índice para datetime
                weather_df.index = pd.to_datetime(
                    weather_df.index,
                    format="%Y%m%d",
                    errors="coerce"
                )
                weather_df = weather_df[weather_df.index.notna()]
                
                # Filtra período e colunas
                weather_df = weather_df.loc[
                    self.start:self.end
                ].dropna(how="all")
                weather_df = weather_df[self.parameter]
                
                # Salva no cache
                self._save_to_cache(weather_df, cache_key)
                return weather_df, warnings
                
            except Exception as e:
                msg = f"Erro ao processar dados NASA POWER: {str(e)}"
                logger.error(msg)
                warnings.append(msg)
                return pd.DataFrame(), warnings
        else:
            msg = "Resposta inválida da API NASA POWER"
            logger.error("%s: %s", msg, self.request)
            warnings.append(msg)
            return pd.DataFrame(), warnings

    # Alias para compatibilidade com versão anterior
    get_weather = get_weather_sync
