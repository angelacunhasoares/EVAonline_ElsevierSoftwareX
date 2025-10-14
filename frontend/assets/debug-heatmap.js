/**
 * Script de DEBUG para Heatmap MATOPIBA
 * Executa automaticamente ao carregar
 */

(function () {
    console.log('\n%c=== 🔍 DEBUG AUTOMÁTICO HEATMAP ===', 'background: #222; color: #bada55; font-size: 16px; font-weight: bold; padding: 10px;');
    console.log('%c⏱️ Aguardando 6 segundos para Dash carregar dados...', 'color: yellow; font-style: italic;');

    // Aguardar 6 segundos para garantir que callbacks do Dash executaram
    setTimeout(function () {
        console.log('\n%c🔍 INICIANDO VERIFICAÇÃO...', 'background: #0a0; color: #fff; font-weight: bold; padding: 5px;');
        console.log('%c--- VERIFICAÇÃO 1: Namespace ---', 'color: cyan; font-weight: bold;');
        console.log('window.dash_clientside:', typeof window.dash_clientside);
        console.log('Conteúdo:', window.dash_clientside);

        console.log('\n%c--- VERIFICAÇÃO 2: Módulo matopiba ---', 'color: cyan; font-weight: bold;');
        if (window.dash_clientside && window.dash_clientside.matopiba) {
            console.log('✅ window.dash_clientside.matopiba:', 'EXISTE');
            console.log('Conteúdo:', window.dash_clientside.matopiba);
        } else {
            console.log('❌ window.dash_clientside.matopiba:', 'NÃO EXISTE');
        }

        console.log('\n%c--- VERIFICAÇÃO 3: Função renderHeatmap ---', 'color: cyan; font-weight: bold;');
        if (window.dash_clientside && window.dash_clientside.matopiba && window.dash_clientside.matopiba.renderHeatmap) {
            console.log('✅ renderHeatmap:', typeof window.dash_clientside.matopiba.renderHeatmap);
        } else {
            console.log('❌ renderHeatmap:', 'NÃO EXISTE');
        }

        console.log('\n%c--- VERIFICAÇÃO 4: Biblioteca HeatmapOverlay ---', 'color: cyan; font-weight: bold;');
        console.log('window.HeatmapOverlay:', typeof window.HeatmapOverlay);
        console.log('window.h337:', typeof window.h337);
        console.log('window.L (Leaflet):', typeof window.L);

        console.log('\n%c--- VERIFICAÇÃO 5: Elementos DOM ---', 'color: cyan; font-weight: bold;');

        const storeIds = [
            'heatmap-data-today-eto',
            'heatmap-data-today-precipitation',
            'heatmap-data-tomorrow-eto',
            'heatmap-data-tomorrow-precipitation'
        ];

        storeIds.forEach(function (id) {
            const el = document.getElementById(id);
            if (el) {
                console.log('✅ Store "' + id + '": EXISTE');

                // Tentar ler dados
                if (el._dashprivate_layout && el._dashprivate_layout.props && el._dashprivate_layout.props.data) {
                    const data = el._dashprivate_layout.props.data;
                    if (data.data && data.data.length) {
                        console.log('   📊 Dados: ' + data.data.length + ' pontos');
                        console.log('   📍 Primeiro ponto:', data.data[0]);
                    } else {
                        console.log('   ⚠️ Store existe mas sem dados');
                    }
                } else {
                    console.log('   ⚠️ Não conseguiu acessar props.data');
                }
            } else {
                console.log('❌ Store "' + id + '": NÃO EXISTE');
            }
        });

        console.log('\n%c--- VERIFICAÇÃO 6: Mapas Leaflet ---', 'color: cyan; font-weight: bold;');

        const mapIds = [
            'map-today-eto',
            'map-today-precipitation',
            'map-tomorrow-eto',
            'map-tomorrow-precipitation'
        ];

        mapIds.forEach(function (id) {
            const el = document.getElementById(id);
            if (el) {
                console.log('✅ Map "' + id + '": EXISTE');
                if (el._leaflet_map) {
                    console.log('   🗺️ Instância Leaflet: EXISTE');
                    try {
                        const center = el._leaflet_map.getCenter();
                        console.log('   ✅ Mapa pronto! Centro:', center);
                    } catch (e) {
                        console.log('   ⚠️ Mapa não está pronto ainda');
                    }
                } else {
                    console.log('   ⚠️ Instância Leaflet: NÃO EXISTE');
                }
            } else {
                console.log('❌ Map "' + id + '": NÃO EXISTE');
            }
        });

        console.log('\n%c--- VERIFICAÇÃO 7: Callbacks Dash ---', 'color: cyan; font-weight: bold;');

        // Tentar acessar informações de callbacks (se disponível)
        if (window.dash_clientside && window.dash_clientside.callback_context) {
            console.log('Callback context:', window.dash_clientside.callback_context);
        } else {
            console.log('⚠️ Callback context não acessível');
        }

        console.log('\n%c--- TESTE MANUAL ---', 'color: yellow; font-weight: bold;');
        console.log('Para testar manualmente, execute:');
        console.log('%ctestarHeatmap()', 'background: #333; color: #0f0; padding: 5px; font-family: monospace;');

        // Criar função de teste global
        window.testarHeatmap = function () {
            console.log('%c🧪 TESTE MANUAL INICIADO', 'background: #0f0; color: #000; font-size: 14px; font-weight: bold; padding: 5px;');

            if (!window.dash_clientside || !window.dash_clientside.matopiba || !window.dash_clientside.matopiba.renderHeatmap) {
                console.error('❌ Função renderHeatmap não disponível!');
                return;
            }

            const testData = {
                data: [
                    { lat: -10.5, lng: -46.0, value: 0.8 },
                    { lat: -10.0, lng: -46.5, value: 0.5 },
                    { lat: -11.0, lng: -45.5, value: 0.3 }
                ],
                config: {
                    radius: 25,
                    maxOpacity: 0.8,
                    minOpacity: 0.3,
                    blur: 0.75,
                    gradient: {
                        '0.0': '#FFEDA0',
                        '0.5': '#FD8D3C',
                        '1.0': '#BD0026'
                    }
                },
                max: 1.0
            };

            console.log('📤 Chamando renderHeatmap com dados de teste...');
            try {
                window.dash_clientside.matopiba.renderHeatmap(testData);
            } catch (e) {
                console.error('❌ Erro ao executar:', e);
            }
        };

        console.log('\n%c=== FIM DO DEBUG ===', 'background: #222; color: #bada55; font-size: 16px; font-weight: bold; padding: 10px;');
        console.log('');

    }, 6000); // Aguarda 6 segundos para callbacks Dash executarem

})();

console.log('🔍 debug-heatmap.js carregado - executará em 6 segundos...');
