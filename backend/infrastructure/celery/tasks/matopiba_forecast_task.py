"""
Celery Task para atualização periódica de previsões MATOPIBA.
(Atualizado: +PostgreSQL histórico, cleanup automático, run scheduling)

Pipeline:
- Busca de previsões Open-Meteo para 337 cidades (2-5 min)
- Cálculo de ETo EVAonline (Penman-Monteith)
- Validação com ETo Open-Meteo (R², RMSE, Bias) - não bloqueante
- Redis cache "quente" (TTL 6h) → latência <100ms
- PostgreSQL histórico → auditoria/recovery
- Execução: 00h, 06h, 12h, 18h UTC (crontab)

Autor: EVAonline Team
Data: 2025-10-10
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List

from celery import shared_task
from loguru import logger
from redis import Redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.api.services.openmeteo_matopiba_client import \
    OpenMeteoMatopibaClient
from backend.core.eto_calculation.eto_matopiba import \
    calculate_eto_matopiba_batch

# Configuração do logging
logger.add(
    "./logs/matopiba_task.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# Constantes
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")
DB_URL = os.getenv("DB_URL", "postgresql://evaonline:evaonline@localhost:5432/evaonline")

# Redis URL
if REDIS_PASSWORD:
    REDIS_URL = f"redis://default:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Redis Keys (mudança: :latest para sempre apontar pro run atual)
REDIS_KEY_FORECASTS = "matopiba:forecasts:latest"
REDIS_KEY_METADATA = "matopiba:metadata:latest"
CACHE_TTL_HOURS = 6

# PostgreSQL Engine
try:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("✅ PostgreSQL engine inicializado")
except Exception as e:
    logger.warning(f"⚠️ PostgreSQL não disponível: {e}")
    engine = None
    SessionLocal = None


@shared_task(
    name="update_matopiba_forecasts",
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutos
)
def update_matopiba_forecasts(self):
    """
    Task Celery para atualização de previsões MATOPIBA.
    
    Pipeline:
    1. Buscar previsões Open-Meteo (337 cidades × 2 dias) → 2-5 min
    2. Calcular ETo EVAonline
    3. Validar com ETo Open-Meteo (R²/RMSE/Bias) - não bloqueante
    4. Salvar Redis (cache quente, TTL 6h) → latência <100ms
    5. Salvar PostgreSQL (histórico) → auditoria/recovery
    
    Execução: Automática 00h, 06h, 12h, 18h UTC (crontab)
    
    Returns:
        Dict com resumo da execução
    
    Raises:
        Exception: Em caso de erro crítico (tentará retry automático)
    """
    task_id = self.request.id
    start_time = datetime.now()
    current_hour_utc = start_time.hour  # Ex: 0 para 00h UTC
    
    # Determina run label baseado no horário
    if current_hour_utc in [0, 6, 12, 18]:
        run_label = f"Run {current_hour_utc:02d}h UTC"
    else:
        run_label = f"Run off-schedule {current_hour_utc:02d}h UTC"
    
    logger.info("="*60)
    logger.info("INICIANDO %s: Update MATOPIBA (Task ID: %s)", run_label, task_id)
    logger.info("="*60)
    
    # Conectar ao Redis
    try:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=False)
        redis_client.ping()
        logger.info("✅ Redis conectado")
    except Exception as e:
        msg = f"Erro ao conectar Redis: {e}"
        logger.error(msg)
        raise Exception(msg)
    
    # Conectar ao PostgreSQL (opcional)
    db_session = None
    if SessionLocal:
        try:
            db_session = SessionLocal()
            logger.info("✅ PostgreSQL conectado")
        except Exception as e:
            logger.warning("⚠️ PostgreSQL não disponível: %s", e)
    
    try:
        
        # ===================================================================
        # STEP 1: Buscar previsões Open-Meteo
        # ===================================================================
        logger.info("STEP 1/5: Buscando previsões Open-Meteo para %s...", run_label)
        
        client = OpenMeteoMatopibaClient(forecast_days=2)  # Hoje + Amanhã
        forecasts_raw, warnings_fetch = client.get_forecasts_all_cities()
        
        n_cities_fetched = len(forecasts_raw)
        logger.info(
            "✅ Previsões obtidas: %d/337 cidades (%.1f%%)",
            n_cities_fetched, (n_cities_fetched / 337) * 100
        )
        
        if n_cities_fetched < 300:  # Menos de 90%
            logger.warning(
                "⚠️ Poucos dados obtidos (%d cidades). Continuando...",
                n_cities_fetched
            )
        
        if not forecasts_raw:
            msg = "Nenhum dado obtido do Open-Meteo"
            logger.error(msg)
            raise Exception(msg)
        
        # ===================================================================
        # STEP 2: Calcular ETo EVAonline
        # ===================================================================
        logger.info("STEP 2/5: Calculando ETo EVAonline para %d cidades...", n_cities_fetched)
        
        results, warnings_calc, validation_metrics = calculate_eto_matopiba_batch(
            forecasts_raw
        )
        
        n_cities_calculated = len(results)
        logger.info(
            "✅ ETo calculada: %d/%d cidades (%.1f%%)",
            n_cities_calculated, n_cities_fetched,
            (n_cities_calculated / n_cities_fetched) * 100
        )
        
        if not results:
            msg = "Falha no cálculo de ETo para todas as cidades"
            logger.error(msg)
            raise Exception(msg)
        
        # ===================================================================
        # STEP 3: Validar ETo (R², RMSE, Bias) - NÃO BLOQUEIA CACHE
        # ===================================================================
        logger.info("STEP 3/5: Métricas de validação (%s)", run_label)
        logger.info("  R² (correlação):      %.3f", validation_metrics.get('r2', 0))
        logger.info("  RMSE (erro):          %.3f mm/dia", validation_metrics.get('rmse', 0))
        logger.info("  Bias (viés):          %.3f mm/dia", validation_metrics.get('bias', 0))
        logger.info("  MAE (erro absoluto):  %.3f mm/dia", validation_metrics.get('mae', 0))
        logger.info("  Amostras:             %d", validation_metrics.get('n_samples', 0))
        logger.info("  Status:               %s", validation_metrics.get('status', 'N/A'))
        
        # Avaliação da qualidade (não bloqueia, apenas alerta)
        r2 = validation_metrics.get('r2', 0)
        rmse = validation_metrics.get('rmse', 999)
        if r2 >= 0.75 and rmse <= 1.2:
            quality = "EXCELENTE"
            logger.info("✅ QUALIDADE: EXCELENTE (R²≥0.75, RMSE≤1.2)")
        elif r2 >= 0.65 and rmse <= 1.5:
            quality = "ACEITÁVEL"
            logger.warning("⚠️  QUALIDADE: ACEITÁVEL (R²≥0.65, RMSE≤1.5)")
        else:
            quality = "ABAIXO DO ESPERADO"
            logger.warning("⚠️  QUALIDADE: ABAIXO DO ESPERADO (revisar pós-deploy)")
            logger.warning("    Dados serão salvos no cache para disponibilidade")
            logger.warning("    Análise detalhada recomendada nos logs")
        
        # ===================================================================
        # STEP 4: Salvar no Redis (cache "quente", TTL 6h)
        # ===================================================================
        logger.info("STEP 4/5: Salvando Redis (cache quente)...")
        
        # Preparar dados para Redis
        cache_data = {
            'forecasts': results,  # {code_city: {today: {eto, precip, ...}, tomorrow: {...}}}
            'validation': validation_metrics,
            'metadata': {
                'run_label': run_label,  # NOVO: Ex: "Run 00h UTC"
                'updated_at': start_time.isoformat(),
                'next_update': (start_time + timedelta(hours=6)).isoformat(),
                'n_cities': n_cities_calculated,
                'n_cities_expected': 337,
                'success_rate': round((n_cities_calculated / 337) * 100, 1),
                'quality': quality,  # NOVO: EXCELENTE/ACEITÁVEL/ABAIXO
                'task_id': task_id,
                'version': '1.0.0'
            }
        }
        
        # Serializar e salvar
        try:
            # Usar JSON em vez de pickle para compatibilidade com frontend
            serialized = json.dumps(cache_data, ensure_ascii=False, default=str)
            ttl_seconds = CACHE_TTL_HOURS * 3600
            
            # Salvar dados principais (key :latest sempre aponta pro run atual)
            redis_client.setex(
                REDIS_KEY_FORECASTS,
                ttl_seconds,
                serialized
            )
            
            # Salvar metadata separadamente (para acesso rápido)
            redis_client.setex(
                REDIS_KEY_METADATA,
                ttl_seconds,
                json.dumps(cache_data['metadata'])
            )
            
            # 🧹 CLEANUP: Deleta chaves antigas se existirem
            old_keys_pattern = "matopiba:forecasts:previous*"
            old_keys = redis_client.keys(old_keys_pattern)
            if old_keys:
                redis_client.delete(*old_keys)
                logger.info("🧹 Cleanup: %d chaves antigas deletadas", len(old_keys))
            
            logger.info("✅ Redis salvo (TTL: %dh, key: %s)", CACHE_TTL_HOURS, REDIS_KEY_FORECASTS)
            
        except Exception as e:
            msg = f"Erro ao salvar no Redis: {e}"
            logger.error(msg)
            raise Exception(msg)
        
        # ===================================================================
        # STEP 5: Salvar PostgreSQL (histórico para auditoria/recovery)
        # ===================================================================
        if db_session:
            logger.info("STEP 5/5: Salvando histórico PostgreSQL...")
            try:
                # Tabela: matopiba_runs 
                # Schema:
                #   id SERIAL PRIMARY KEY
                #   run_label VARCHAR(50)
                #   updated_at TIMESTAMP
                #   n_cities INTEGER
                #   r2 FLOAT, rmse FLOAT, bias FLOAT
                #   success_rate FLOAT
                #   quality VARCHAR(20)
                #   metadata_json JSONB
                
                insert_query = text("""
                    INSERT INTO matopiba_runs (
                        run_label, updated_at, n_cities, r2, rmse, bias, 
                        success_rate, quality, metadata_json
                    )
                    VALUES (
                        :run_label, :updated_at, :n_cities, :r2, :rmse, :bias,
                        :success_rate, :quality, :metadata_json::jsonb
                    )
                    ON CONFLICT (updated_at) DO NOTHING;
                """)
                
                db_session.execute(insert_query, {
                    'run_label': run_label,
                    'updated_at': start_time,
                    'n_cities': n_cities_calculated,
                    'r2': validation_metrics.get('r2', 0),
                    'rmse': validation_metrics.get('rmse', 0),
                    'bias': validation_metrics.get('bias', 0),
                    'success_rate': cache_data['metadata']['success_rate'],
                    'quality': quality,
                    'metadata_json': json.dumps(cache_data['metadata'])
                })
                db_session.commit()
                logger.info("✅ PostgreSQL salvo (histórico %s)", run_label)
                
            except Exception as e:
                logger.warning("⚠️ Erro PostgreSQL (não bloqueia): %s", e)
                db_session.rollback()
        else:
            logger.info("STEP 5/5: PostgreSQL não disponível (skip histórico)")
        
        # ===================================================================
        # FINALIZAÇÃO
        # ===================================================================
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            'status': 'SUCCESS',
            'run_label': run_label,
            'task_id': task_id,
            'started_at': start_time.isoformat(),
            'finished_at': end_time.isoformat(),
            'duration_seconds': duration,
            'cities_processed': n_cities_calculated,
            'cities_expected': 337,
            'success_rate': (n_cities_calculated / 337) * 100,
            'quality': quality,
            'validation': validation_metrics,
            'warnings_count': len(warnings_fetch) + len(warnings_calc),
            'next_update': (start_time + timedelta(hours=6)).isoformat()
        }
        
        logger.info("="*60)
        logger.info("✅ CONCLUÍDO: %s (Update MATOPIBA)", run_label)
        logger.info("Duração: %.1f segundos (%.1f minutos)", duration, duration / 60)
        logger.info("Taxa de sucesso: %.1f%% (%d/337 cidades)",
                   summary['success_rate'], n_cities_calculated)
        logger.info("Qualidade: %s", quality)
        logger.info("="*60)
        
        return summary
    
    except Exception as e:
        error_msg = f"Erro na task MATOPIBA (%s): %s" % (run_label if 'run_label' in locals() else 'Unknown', str(e))
        logger.exception(error_msg)
        
        # Tentar retry se não excedeu limite
        if self.request.retries < self.max_retries:
            logger.warning(
                "Tentando novamente em 5 minutos... (tentativa %d/%d)",
                self.request.retries + 1, self.max_retries
            )
            raise self.retry(exc=e)
        
        # Falha definitiva
        logger.error("❌ Task falhou após %d tentativas", self.max_retries)
        
        return {
            'status': 'FAILURE',
            'task_id': task_id,
            'run_label': run_label if 'run_label' in locals() else 'Unknown',
            'error': error_msg,
            'retries': self.request.retries
        }
    
    finally:
        # Fechar conexões
        try:
            if 'redis_client' in locals():
                redis_client.close()
                logger.debug("Redis connection closed")
        except Exception:
            pass
        
        try:
            if db_session:
                db_session.close()
                logger.debug("PostgreSQL session closed")
        except Exception:
            pass


@shared_task(name="get_matopiba_cache_status")
def get_matopiba_cache_status():
    """
    Task para verificar status do cache MATOPIBA.
    
    Returns:
        Dict com informações do cache
    """
    try:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        
        # Verificar se existe cache
        exists = redis_client.exists(REDIS_KEY_FORECASTS)
        
        if not exists:
            return {
                'status': 'EMPTY',
                'message': 'Cache vazio - aguardando primeira atualização'
            }
        
        # Obter TTL
        ttl_seconds = redis_client.ttl(REDIS_KEY_FORECASTS)
        
        # Obter metadata
        metadata_raw = redis_client.get(REDIS_KEY_METADATA)
        if metadata_raw:
            metadata = json.loads(metadata_raw)
        else:
            metadata = {}
        
        return {
            'status': 'ACTIVE',
            'ttl_seconds': ttl_seconds,
            'ttl_minutes': ttl_seconds / 60,
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error("Erro ao verificar cache: %s", e)
        return {
            'status': 'ERROR',
            'error': str(e)
        }


# Configuração de schedule (adicionar ao celery_config.py)
"""
Para ativar esta task no celery_config.py, adicione:

from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'update-matopiba-forecasts': {
        'task': 'update_matopiba_forecasts',
        'schedule': crontab(hour='0,6,12,18', minute=0),  # Exato: 00h, 06h, 12h, 18h UTC
        'options': {'queue': 'matopiba_processing'}
    },
}

celery_app.conf.task_routes.update({
    'update_matopiba_forecasts': {'queue': 'matopiba_processing'},
})

# Criar tabela PostgreSQL (executar no psql ou pgAdmin):
CREATE TABLE IF NOT EXISTS matopiba_runs (
    id SERIAL PRIMARY KEY,
    run_label VARCHAR(50) NOT NULL,
    updated_at TIMESTAMP NOT NULL UNIQUE,
    n_cities INTEGER NOT NULL,
    r2 FLOAT,
    rmse FLOAT,
    bias FLOAT,
    success_rate FLOAT,
    quality VARCHAR(20),
    metadata_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_matopiba_runs_updated_at ON matopiba_runs(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_matopiba_runs_run_label ON matopiba_runs(run_label);
"""


if __name__ == "__main__":
    # Teste manual da task
    logger.info("=== TESTE MANUAL: update_matopiba_forecasts ===")
    result = update_matopiba_forecasts()
    logger.info("Resultado: %s", result)
