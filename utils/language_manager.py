from dash import Input, Output, State, callback, no_update
from loguru import logger

# 1. REMOÇÃO: Não precisamos mais de 'dcc', 'html', 'os', ou 'get_translations' aqui.
#    Este módulo será focado apenas na lógica do callback.


def register_language_callbacks(app):
    """
    Registra os callbacks necessários para o gerenciamento de idioma.
    Esta função é chamada uma vez no main.py para configurar a lógica.

    Args:
        app (dash.Dash): A instância da aplicação Dash.
    """

    # 2. CORREÇÃO: O callback agora lê o valor do dropdown e o estado atual do Store.
    #    Ele atualiza o Store, que por sua vez aciona a atualização da UI em outras partes do app.
    @callback(
        Output('language-store', 'data'),
        Input('language-dropdown', 'value'), # O Input agora é o valor do dropdown
        State('language-store', 'data'),
        prevent_initial_call=True
    )
    def update_language(selected_lang, current_lang):
        """
        Atualiza o idioma no dcc.Store quando uma nova opção é selecionada no dropdown.
        """
        # 3. CORREÇÃO: A lógica é muito mais simples e robusta.
        #    Se um novo idioma foi selecionado no dropdown, atualize o store.
        #    Caso contrário, não faça nada.
        if selected_lang and selected_lang != current_lang:
            logger.info(f"Idioma alterado para: {selected_lang}")
            return selected_lang
        
        # Se nenhum novo idioma foi selecionado, não atualiza o estado.
        return no_update

# 4. REMOÇÃO: A função não precisa retornar nada.
#    Sua única função é registrar o callback na instância do app.
