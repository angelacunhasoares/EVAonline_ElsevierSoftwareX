/**
 * Auto-renderização de heatmap MATOPIBA
 * Lê dados de atributos data-* e renderiza automaticamente
 */

(function () {
    console.log('🔥 heatmap-auto-render.js carregado');

    // Função para tentar renderizar heatmaps
    function tryRenderHeatmaps() {
        console.log('🔍 Procurando triggers com dados...');

        // Procurar todos os triggers com atributo data-heatmap-config
        const triggers = document.querySelectorAll('[id*="heatmap-trigger"][data-heatmap-config]');

        console.log(`📍 Encontrados ${triggers.length} triggers com dados`);

        triggers.forEach(function (trigger) {
            const triggerId = trigger.id;
            const mapId = triggerId.replace('heatmap-trigger-', 'map-');

            console.log(`🎯 Trigger: ${triggerId} → Mapa: ${mapId}`);

            // Ler dados do atributo
            const configJson = trigger.getAttribute('data-heatmap-config');

            if (!configJson) {
                console.warn(`⚠️ Sem dados em ${triggerId}`);
                return;
            }

            let heatmapData;
            try {
                heatmapData = JSON.parse(configJson);
                console.log(`✅ Dados parseados: ${heatmapData.data.length} pontos`);
            } catch (e) {
                console.error(`❌ Erro ao parsear JSON de ${triggerId}:`, e);
                return;
            }

            // Aguardar mapa estar pronto
            waitAndRenderHeatmap(mapId, heatmapData, 0);
        });
    }

    function waitAndRenderHeatmap(mapId, heatmapData, attempt) {
        const maxAttempts = 30;

        if (attempt >= maxAttempts) {
            console.error(`❌ Timeout: mapa ${mapId} não ficou pronto`);
            return;
        }

        const mapElement = document.getElementById(mapId);

        if (!mapElement) {
            setTimeout(() => waitAndRenderHeatmap(mapId, heatmapData, attempt + 1), 500);
            return;
        }

        const map = mapElement._leaflet_map;

        if (!map) {
            setTimeout(() => waitAndRenderHeatmap(mapId, heatmapData, attempt + 1), 500);
            return;
        }

        // Testar se mapa está pronto
        try {
            map.getCenter();
        } catch (e) {
            setTimeout(() => waitAndRenderHeatmap(mapId, heatmapData, attempt + 1), 500);
            return;
        }

        console.log(`✅ Mapa ${mapId} está pronto! Renderizando...`);
        renderHeatmapOnMap(map, mapId, heatmapData);
    }

    function renderHeatmapOnMap(map, mapId, heatmapData) {
        // Remover layer antigo se existir
        if (map._heatmapLayer) {
            map.removeLayer(map._heatmapLayer);
            console.log(`🗑️ Layer antigo removido de ${mapId}`);
        }

        // Verificar biblioteca
        if (!window.HeatmapOverlay) {
            console.error('❌ HeatmapOverlay não disponível!');
            return;
        }

        const config = {
            radius: heatmapData.config?.radius || 25,
            maxOpacity: heatmapData.config?.maxOpacity || 0.8,
            minOpacity: heatmapData.config?.minOpacity || 0.3,
            blur: heatmapData.config?.blur || 0.75,
            gradient: heatmapData.config?.gradient || {
                '0.0': '#FFEDA0',
                '0.5': '#FD8D3C',
                '1.0': '#BD0026'
            }
        };

        try {
            const heatmapLayer = new HeatmapOverlay(config);
            map.addLayer(heatmapLayer);

            heatmapLayer.setData({
                max: heatmapData.max || 1.0,
                data: heatmapData.data
            });

            map._heatmapLayer = heatmapLayer;

            console.log(`✅✅✅ HEATMAP CRIADO EM ${mapId}!`);
            console.log(`📍 ${heatmapData.data.length} pontos renderizados`);

        } catch (error) {
            console.error(`❌ Erro ao criar heatmap em ${mapId}:`, error);
        }
    }

    // Tentar renderizar após 3 segundos (aguardar Dash carregar)
    setTimeout(tryRenderHeatmaps, 3000);

    // Tentar novamente após 6 segundos (caso primeira tentativa falhe)
    setTimeout(tryRenderHeatmaps, 6000);

    // Expor função globalmente para testes manuais
    window.tryRenderHeatmaps = tryRenderHeatmaps;

    console.log('💡 Para forçar renderização, digite: tryRenderHeatmaps()');

})();
