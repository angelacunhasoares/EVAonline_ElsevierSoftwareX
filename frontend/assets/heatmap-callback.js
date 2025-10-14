/**
 * Callback Dash para renderizar heatmap MATOPIBA
 * Versão robusta com wait-for-ready pattern
 */

if (!window.dash_clientside) {
    window.dash_clientside = {};
}

window.dash_clientside.matopiba = {
    renderHeatmap: function (heatmapData) {
        console.log('🔥🔥🔥 CALLBACK HEATMAP DISPARADO!');

        if (!heatmapData || !heatmapData.data || heatmapData.data.length === 0) {
            console.warn('⚠️ Sem dados para heatmap');
            return 'no-data';
        }

        console.log(`✅ ${heatmapData.data.length} pontos recebidos`);

        // Descobrir qual mapa renderizar
        let mapId = 'map-today-eto_calculated'; // Default

        const ctx = window.dash_clientside.callback_context;
        if (ctx && ctx.triggered && ctx.triggered.length > 0) {
            const triggeredId = ctx.triggered[0].prop_id.split('.')[0];
            mapId = triggeredId.replace('heatmap-data-', 'map-');
            console.log('📍 MapId:', mapId);
        }

        // Aguardar mapa estar pronto (recursivo com timeout)
        waitAndRender(mapId, heatmapData, 0);

        return 'rendering';
    }
};

function waitAndRender(mapId, heatmapData, attempt) {
    const maxAttempts = 30; // 30 tentativas x 500ms = 15 segundos max

    if (attempt >= maxAttempts) {
        console.error('❌ Timeout: mapa não ficou pronto em 15 segundos');
        return;
    }

    console.log(`⏱️ Tentativa ${attempt + 1}/${maxAttempts}...`);

    const mapElement = document.getElementById(mapId);

    if (!mapElement) {
        console.log('⌛ Aguardando elemento do mapa...');
        setTimeout(() => waitAndRender(mapId, heatmapData, attempt + 1), 500);
        return;
    }

    const map = mapElement._leaflet_map;

    if (!map) {
        console.log('⌛ Aguardando instância Leaflet...');
        setTimeout(() => waitAndRender(mapId, heatmapData, attempt + 1), 500);
        return;
    }

    // Testar se mapa está pronto (sem causar erro)
    try {
        map.getCenter(); // Isso falha se mapa não está inicializado
        console.log('✅ Mapa está pronto!');
    } catch (e) {
        console.log('⌛ Mapa ainda não está pronto...');
        setTimeout(() => waitAndRender(mapId, heatmapData, attempt + 1), 500);
        return;
    }

    // Mapa está pronto! Renderizar heatmap
    renderHeatmapNow(map, heatmapData);
}

function renderHeatmapNow(map, heatmapData) {
    console.log('🎨 Renderizando heatmap...');

    // Remover layer antigo
    if (map._heatmapLayer) {
        map.removeLayer(map._heatmapLayer);
        console.log('🗑️ Layer antigo removido');
    }

    // Verificar biblioteca
    if (!window.HeatmapOverlay) {
        console.error('❌ HeatmapOverlay não disponível!');
        console.log('h337:', typeof window.h337);
        console.log('L:', typeof window.L);
        return;
    }

    console.log('✅ HeatmapOverlay disponível');

    // Configuração
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

    console.log('⚙️ Config:', config);

    try {
        // Criar layer
        const heatmapLayer = new HeatmapOverlay(config);
        map.addLayer(heatmapLayer);

        // Setar dados
        heatmapLayer.setData({
            max: heatmapData.max || 1.0,
            data: heatmapData.data
        });

        // Salvar referência
        map._heatmapLayer = heatmapLayer;

        console.log('✅✅✅ HEATMAP CRIADO COM SUCESSO!');
        console.log(`📍 ${heatmapData.data.length} pontos renderizados`);

    } catch (error) {
        console.error('❌ Erro ao criar heatmap:', error);
        console.error('Stack:', error.stack);
    }
}

console.log('✅ heatmap-callback.js carregado (versão robusta)');
