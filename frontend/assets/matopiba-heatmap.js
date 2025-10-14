/**
 * MATOPIBA Heatmap Integration
 * Integra heatmap.js com Dash-Leaflet para visualização de dados meteorológicos
 * 
 * Documentação: https://github.com/pa7/heatmap.js
 */

// Aguardar carregamento completo do DOM e bibliotecas
if (!window.dash_clientside) {
    window.dash_clientside = {};
}

window.dash_clientside.heatmap = {
    /**
     * Cria/atualiza layer heatmap no mapa Leaflet
     * @param {Object} heatmapData - Dados do heatmap {data: [{lat, lng, value}], config: {...}}
     * @param {string} mapId - ID do componente dl.Map
     */
    updateHeatmap: function (heatmapData, mapId) {
        console.log("🔥 Heatmap callback acionado!", heatmapData);

        if (!heatmapData || !heatmapData.data || heatmapData.data.length === 0) {
            console.warn("⚠️ Sem dados para heatmap");
            return window.dash_clientside.no_update;
        }

        // Aguardar mapa estar pronto
        setTimeout(function () {
            // Buscar instância do mapa Leaflet
            const mapElement = document.getElementById(mapId);
            if (!mapElement || !mapElement._leaflet_id) {
                console.error("❌ Mapa Leaflet não encontrado:", mapId);
                return;
            }

            // Pegar instância L.map
            const map = mapElement._leaflet_map ||
                (window.L && window.L.Map &&
                    Object.values(window).find(v => v instanceof L.Map && v.getContainer() === mapElement));

            if (!map) {
                console.error("❌ Instância L.map não encontrada");
                return;
            }

            console.log("✅ Mapa encontrado, configurando heatmap...");

            // Remover layer antigo se existir
            if (map._heatmapLayer) {
                map.removeLayer(map._heatmapLayer);
                console.log("🗑️ Layer antigo removido");
            }

            // Configuração do heatmap
            const config = {
                radius: heatmapData.config?.radius || 25,
                maxOpacity: heatmapData.config?.maxOpacity || 0.8,
                minOpacity: heatmapData.config?.minOpacity || 0.3,
                blur: heatmapData.config?.blur || 0.75,
                gradient: heatmapData.config?.gradient || {
                    0.0: '#FFEDA0',  // Amarelo claro
                    0.4: '#FED976',  // Amarelo
                    0.6: '#FD8D3C',  // Laranja
                    0.8: '#E31A1C',  // Vermelho
                    1.0: '#BD0026'   // Vermelho escuro
                },
                // Usar canvas para melhor performance
                useLocalExtrema: false,
                scaleRadius: true
            };

            console.log("⚙️ Config heatmap:", config);

            // Criar layer heatmap (usando HeatmapOverlay do plugin)
            // Se HeatmapOverlay não estiver disponível, usar abordagem alternativa
            if (window.HeatmapOverlay) {
                const heatmapLayer = new HeatmapOverlay(config);

                // Adicionar ao mapa
                map.addLayer(heatmapLayer);

                // Configurar dados
                heatmapLayer.setData({
                    max: heatmapData.max || Math.max(...heatmapData.data.map(d => d.value)),
                    data: heatmapData.data
                });

                // Salvar referência
                map._heatmapLayer = heatmapLayer;

                console.log(`✅ Heatmap criado com ${heatmapData.data.length} pontos`);
            } else {
                console.error("❌ HeatmapOverlay não disponível. Verifique se leaflet-heatmap.js está carregado.");

                // Fallback: criar marcadores circulares simples
                console.log("⚠️ Usando fallback com CircleMarkers");
                const markers = L.layerGroup();

                heatmapData.data.forEach(point => {
                    const intensity = point.value / (heatmapData.max || 1);
                    const color = intensity > 0.8 ? '#BD0026' :
                        intensity > 0.6 ? '#E31A1C' :
                            intensity > 0.4 ? '#FD8D3C' :
                                intensity > 0.2 ? '#FED976' : '#FFEDA0';

                    L.circleMarker([point.lat, point.lng], {
                        radius: 8,
                        fillColor: color,
                        fillOpacity: 0.6,
                        stroke: false
                    }).addTo(markers);
                });

                markers.addTo(map);
                map._heatmapLayer = markers;

                console.log(`✅ Fallback criado com ${heatmapData.data.length} marcadores`);
            }

        }, 500); // Delay para garantir que mapa está renderizado

        return window.dash_clientside.no_update;
    }
};

console.log("✅ matopiba-heatmap.js carregado");
