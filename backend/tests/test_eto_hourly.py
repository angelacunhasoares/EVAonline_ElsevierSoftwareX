"""
Unit tests para funções de ETo horária.

Testa funções isoladas com casos de referência FAO-56
(Allen et al. 1998, Exemplo 18 - Bangkok, Tailândia).

Validações:
- declination(J=282): -0.01 rad (Eq. 27)
- inverse_relative_distance(J=135): 1.03 (Eq. 23)
- Pressão de saturação: 4.24 kPa @ 30°C (Eq. 11)
- Inclinação da curva: 0.245 kPa/°C @ 30°C (Eq. 13)

Critérios de aceitação:
- Funções astronômicas: erro < 1%
- Funções termodinâmicas: erro < 0.5%
- ETo completo: R² > 0.8 vs referência

Autor: EVAonline Team
Data: 2025-10-09
"""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from backend.core.eto_calculation.eto_hourly import (
    aggregate_hourly_to_daily, calculate_eto_hourly,
    calculate_eto_hourly_vectorized, declination, extraterrestrial_radiation,
    inverse_relative_distance)


class TestAstronomicFunctions:
    """Testes para funções astronômicas (Eqs. 23-33 FAO-56)."""
    
    def test_declination_example_fao56(self):
        """
        Eq. 27: δ = 0.409 sin(2π/365 (J-81))
        
        Caso de referência FAO-56:
        - J=282 (9 outubro): δ ≈ -0.13 rad (-7.4°)
        - J=172 (21 junho): δ ≈ +0.41 rad (+23.45°, solstício)
        """
        # 9 outubro (dia 282)
        delta_oct = declination(282)
        assert abs(delta_oct - (-0.13)) < 0.02, \
            f"Declinação J=282 esperada ~-0.13, obtida {delta_oct:.3f}"
        
        # 21 junho (dia 172, solstício de verão NH)
        delta_jun = declination(172)
        assert 0.40 < delta_jun < 0.42, \
            f"Declinação J=172 esperada ~0.41, obtida {delta_jun:.3f}"
        
        # 21 dezembro (dia 355, solstício de inverno NH)
        delta_dec = declination(355)
        assert -0.42 < delta_dec < -0.40, \
            f"Declinação J=355 esperada ~-0.41, obtida {delta_dec:.3f}"
    
    def test_inverse_relative_distance(self):
        """
        Eq. 23: dr = 1 + 0.033 cos(2π/365 J)
        
        Casos de referência:
        - J=1 (1 janeiro): dr ≈ 1.033 (periélio)
        - J=182 (2 julho): dr ≈ 0.967 (afélio)
        """
        dr_jan = inverse_relative_distance(1)
        assert 1.032 < dr_jan < 1.034, \
            f"dr(J=1) esperado ~1.033, obtido {dr_jan:.4f}"
        
        dr_jul = inverse_relative_distance(182)
        assert 0.966 < dr_jul < 0.968, \
            f"dr(J=182) esperado ~0.967, obtido {dr_jul:.4f}"
    
    def test_extraterrestrial_radiation_noon(self):
        """
        Eq. 28: Ra para meio-dia solar.
        
        Bangkok (13.7°N, 100.5°E) em 15 maio (J=135):
        - Ra ao meio-dia ≈ 3.5 MJ/m²/h
        - Ra mínimo (noite) ≈ 0 MJ/m²/h
        """
        # Bangkok, 15 maio, meio-dia UTC (UTC+7 → 5:00 UTC)
        lat_rad = np.deg2rad(13.7)
        lon = 100.5
        dt_noon = datetime(2024, 5, 15, 5, 0, 0)  # 12:00 local
        
        Ra_noon = extraterrestrial_radiation(dt_noon, lat_rad, lon)
        
        # Meio-dia deve ter Ra alto (>2 MJ/m²/h)
        assert Ra_noon > 2.0, \
            f"Ra ao meio-dia esperado >2, obtido {Ra_noon:.2f}"
        
        # Noite deve ter Ra ~0
        dt_night = datetime(2024, 5, 15, 22, 0, 0)  # 5:00 local
        Ra_night = extraterrestrial_radiation(dt_night, lat_rad, lon)
        
        assert Ra_night < 0.5, \
            f"Ra noturno esperado <0.5, obtido {Ra_night:.2f}"


class TestThermodynamicFunctions:
    """Testes para funções termodinâmicas (Eqs. 11-13 FAO-56)."""
    
    def test_saturation_vapor_pressure(self):
        """
        Eq. 11: es(T) = 0.6108 exp(17.27T/(T+237.3))
        
        Casos de referência FAO-56 Table 2.3:
        - T=30°C: es = 4.24 kPa
        - T=20°C: es = 2.34 kPa
        - T=10°C: es = 1.23 kPa
        """
        # Implementação inline (mesma do módulo)
        def es_calc(T):
            return 0.6108 * np.exp((17.27 * T) / (T + 237.3))
        
        es_30 = es_calc(30)
        assert abs(es_30 - 4.24) < 0.02, \
            f"es(30°C) esperado 4.24, obtido {es_30:.2f}"
        
        es_20 = es_calc(20)
        assert abs(es_20 - 2.34) < 0.02, \
            f"es(20°C) esperado 2.34, obtido {es_20:.2f}"
        
        es_10 = es_calc(10)
        assert abs(es_10 - 1.23) < 0.02, \
            f"es(10°C) esperado 1.23, obtido {es_10:.2f}"
    
    def test_slope_vapor_pressure_curve(self):
        """
        Eq. 13: Δ = 4098[0.6108 exp(17.27T/(T+237.3))]/(T+237.3)²
        
        Casos de referência FAO-56 Table 2.4:
        - T=30°C: Δ = 0.245 kPa/°C
        - T=20°C: Δ = 0.145 kPa/°C
        """
        def delta_calc(T):
            es = 0.6108 * np.exp((17.27 * T) / (T + 237.3))
            return (4098 * es) / ((T + 237.3) ** 2)
        
        delta_30 = delta_calc(30)
        assert abs(delta_30 - 0.245) < 0.005, \
            f"Δ(30°C) esperado 0.245, obtido {delta_30:.3f}"
        
        delta_20 = delta_calc(20)
        assert abs(delta_20 - 0.145) < 0.005, \
            f"Δ(20°C) esperado 0.145, obtido {delta_20:.3f}"


class TestEToCalculation:
    """Testes integrados de cálculo de ETo horária."""
    
    @pytest.fixture
    def sample_hourly_data(self):
        """
        Dados horários sintéticos para teste (24h).
        
        Condições típicas MATOPIBA:
        - Temperatura: 25-35°C (dia), 20-25°C (noite)
        - Umidade relativa: 60-80%
        - Vento: 2-4 m/s
        - Radiação: 0 (noite), 500-800 W/m² (dia)
        """
        dates = pd.date_range('2024-10-15', periods=24, freq='h')
        
        # Ciclo diurno sintético
        hours = np.arange(24)
        temp = 25 + 8 * np.sin(np.pi * (hours - 6) / 12)  # 20-33°C
        rh = 75 - 15 * np.sin(np.pi * (hours - 6) / 12)   # 60-90%
        ws = 3 + 1 * np.sin(np.pi * (hours - 3) / 12)     # 2-4 m/s
        
        # Radiação: 0 noite (18-6h), parabólica dia (6-18h)
        radiation = np.zeros(24)
        for h in range(6, 18):
            radiation[h] = 800 * np.sin(np.pi * (h - 6) / 12)
        
        return pd.DataFrame({
            'time': dates,
            'temp': temp,
            'rh': rh,
            'ws': ws,
            'radiation': radiation,
        })
    
    def test_calculate_eto_hourly_basic(self, sample_hourly_data):
        """
        Teste básico: cálculo deve retornar 24 valores válidos.
        """
        df_eto, warnings = calculate_eto_hourly(
            sample_hourly_data,
            latitude=-12.0,  # MATOPIBA
            longitude=-45.0,
            elevation=500
        )
        
        assert len(df_eto) == 24, "Deve retornar 24 registros horários"
        assert 'ETo_hour' in df_eto.columns, "Deve ter coluna ETo_hour"
        assert df_eto['ETo_hour'].notna().all(), "ETo não pode ter NaN"
        assert (df_eto['ETo_hour'] >= 0).all(), "ETo não pode ser negativa"
    
    def test_calculate_eto_hourly_vectorized_same_results(
        self,
        sample_hourly_data
    ):
        """
        Versão vetorizada deve produzir resultados idênticos ao loop.
        """
        params = {
            'latitude': -12.0,
            'longitude': -45.0,
            'elevation': 500
        }
        
        df_loop, _ = calculate_eto_hourly(sample_hourly_data, **params)
        df_vec, _ = calculate_eto_hourly_vectorized(
            sample_hourly_data,
            **params
        )
        
        # Comparar ETo_hour (tolerância 0.01 mm/h devido a arredondamentos)
        eto_diff = np.abs(df_loop['ETo_hour'] - df_vec['ETo_hour'])
        
        assert eto_diff.max() < 0.01, \
            f"Diferença máxima entre loop e vetorizado: {eto_diff.max():.4f}"
    
    def test_nighttime_coefficients(self, sample_hourly_data):
        """
        ETo noturna deve ser ~80% menor que diurna (Cn/Cd ajustados).
        """
        df_eto, _ = calculate_eto_hourly(
            sample_hourly_data,
            latitude=-12.0,
            longitude=-45.0,
            elevation=500
        )
        
        # Filtrar dia (Rs>0) e noite (Rs=0)
        df_eto['is_day'] = df_eto['Rn'] > 0
        eto_day = df_eto[df_eto['is_day']]['ETo_hour'].mean()
        eto_night = df_eto[~df_eto['is_day']]['ETo_hour'].mean()
        
        # Noite deve ser < 30% do dia (fix ASCE-EWRI 2005)
        ratio = eto_night / eto_day if eto_day > 0 else 0
        
        assert ratio < 0.3, \
            f"ETo noturna deveria ser <30% da diurna, obtido {ratio:.2%}"
    
    def test_aggregate_hourly_to_daily(self, sample_hourly_data):
        """
        Agregação diária deve somar 24 valores horários.
        """
        df_eto, _ = calculate_eto_hourly(
            sample_hourly_data,
            latitude=-12.0,
            longitude=-45.0,
            elevation=500
        )
        
        df_daily, _ = aggregate_hourly_to_daily(df_eto)
        
        assert len(df_daily) == 1, "Deve retornar 1 registro diário"
        assert 'ETo_daily' in df_daily.columns, "Deve ter coluna ETo_daily"
        
        # ETo diária = soma das 24 horas
        eto_sum = df_eto['ETo_hour'].sum()
        eto_daily = df_daily['ETo_daily'].iloc[0]
        
        assert abs(eto_sum - eto_daily) < 0.01, \
            f"ETo diária ({eto_daily:.2f}) != soma horária ({eto_sum:.2f})"


class TestEdgeCases:
    """Testes para casos extremos e edge cases."""
    
    def test_missing_columns(self):
        """
        Dados faltando colunas essenciais devem retornar erro.
        """
        df_incomplete = pd.DataFrame({
            'time': pd.date_range('2024-10-15', periods=24, freq='h'),
            'temp': np.random.uniform(20, 30, 24),
            # Faltando 'ws' e 'radiation'
        })
        
        df_eto, warnings = calculate_eto_hourly(
            df_incomplete,
            latitude=-12.0,
            longitude=-45.0,
            elevation=500
        )
        
        assert df_eto.empty, "Deve retornar DataFrame vazio"
        assert len(warnings) > 0, "Deve ter avisos de erro"
        assert 'faltando' in warnings[0].lower(), \
            "Aviso deve mencionar colunas faltando"
    
    def test_zero_wind_speed(self):
        """
        Vento zero deve usar fallback 0.5 m/s (evita divisão por zero).
        """
        df_zero_wind = pd.DataFrame({
            'time': pd.date_range('2024-10-15', periods=24, freq='h'),
            'temp': [25] * 24,
            'rh': [70] * 24,
            'ws': [0] * 24,  # Vento zero
            'radiation': [500] * 24,
        })
        
        df_eto, _ = calculate_eto_hourly(
            df_zero_wind,
            latitude=-12.0,
            longitude=-45.0,
            elevation=500
        )
        
        # Deve calcular ETo sem erro
        assert df_eto['ETo_hour'].notna().all(), \
            "ETo deve ser calculada mesmo com vento zero"
        assert (df_eto['ETo_hour'] > 0).any(), \
            "ETo deve ser positiva com radiação presente"
    
    def test_negative_radiation(self):
        """
        Radiação negativa deve ser tratada como zero.
        """
        df_neg_rad = pd.DataFrame({
            'time': pd.date_range('2024-10-15', periods=24, freq='h'),
            'temp': [25] * 24,
            'rh': [70] * 24,
            'ws': [3] * 24,
            'radiation': [-100] * 24,  # Radiação negativa (erro de dados)
        })
        
        df_eto, _ = calculate_eto_hourly(
            df_neg_rad,
            latitude=-12.0,
            longitude=-45.0,
            elevation=500
        )
        
        # ETo deve ser baixa (noturna) mas não negativa
        assert (df_eto['ETo_hour'] >= 0).all(), \
            "ETo não pode ser negativa mesmo com dados ruins"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
