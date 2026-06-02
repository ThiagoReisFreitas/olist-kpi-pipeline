import sys
import os
from unittest.mock import MagicMock

# Adiciona a raiz do projeto ao path para que os imports funcionem
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock do streamlit antes de qualquer import do dashboard — o módulo tem
# efeitos colaterais em nível de módulo (set_page_config, sidebar, radio)
# que falhariam fora de um ambiente Streamlit real.
mock_st = MagicMock()

# Retorna valor que não bate com nenhuma página: impede execução dos blocos if/elif
mock_st.radio.return_value = "__no_page__"

# columns(n) precisa retornar uma lista desempacotável de tamanho n
mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]

sys.modules["streamlit"] = mock_st
