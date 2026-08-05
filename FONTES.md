# Guia de Tamanhos de Fonte

Todos os tamanhos são alterados nos arquivos de `views/`.
Procure por `CTkFont(size=XX)` e troque o número.

## Referência rápida

| Tamanho | Onde é usado | Arquivo |
|---------|-------------|---------|
| **20**  | Títulos de tela ("Objetos Registrados", "Histórico...") | todos os views |
| **16**  | Títulos de janelas modais (editar objeto, editar retirada) | lista_objetos_view.py |
| **15**  | Botão Entrar (login), títulos de seção (usuários) | login_view.py, usuarios_view.py |
| **14**  | Botões de ação (✋ ✏️ 🗑️), mensagem vazia da lista | lista_objetos_view.py |
| **13**  | Texto das linhas da tabela, labels de campos, menu sidebar | todos os views |
| **12**  | Textos secundários, dicas, nome do usuário no rodapé | vários |
| **11**  | Textos menores (hints, informações de nível) | usuarios_view.py |

## Como alterar

### Aumentar todas as letras da tabela de uma vez
Em `lista_objetos_view.py` e `historico_retiradas_view.py`:
- Procure `size=13` nas linhas → troque para `size=14` ou `size=15`

### Aumentar o cabeçalho das colunas
- Procure `size=13, weight="bold"` → troque para `size=14, weight="bold"`

### Aumentar os títulos de tela
- Procure `size=20, weight="bold"` → troque para `size=22, weight="bold"`

### Aumentar os botões de ação
- Procure `size=14` nos CTkButton com texto emoji → troque para `size=16`

### Aumentar só os campos do formulário de cadastro
Em `cadastro_objeto_view.py`:
- Procure `size=13` → troque para `size=14`

## Exemplo prático

Antes:
```python
ctk.CTkLabel(linha, text=val, font=ctk.CTkFont(size=13), ...)
```

Depois (maior):
```python
ctk.CTkLabel(linha, text=val, font=ctk.CTkFont(size=15), ...)
```
