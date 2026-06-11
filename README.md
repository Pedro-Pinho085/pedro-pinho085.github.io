# 🏪 Freitas Mercadinho — Sistema de Pedidos Online

## Como rodar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar número do WhatsApp
Abra `static/js/store.js` e altere:
```js
const WHATSAPP_NUMBER = '5585999999999'; // DDI + DDD + número
```

### 3. Rodar
```bash
python app.py
```

- **Loja:** http://localhost:5000
- **Admin:** http://localhost:5000/admin

## Credenciais do admin
- **Usuário:** `admin`
- **Senha:** `freitas2024`

> Altere a senha em `app.py`:
> ```python
> ADMIN_PASS = hashlib.sha256("SUA_SENHA".encode()).hexdigest()
> ```

## Produtos pré-cadastrados
Pães, Hortifruti, Cereais, Bebidas e Carvão — todos alinhados com o
cardápio do Facebook do Freitas Mercadinho.

## Funcionalidades
- ✅ Cardápio com filtro por categoria
- ✅ Busca por nome/descrição
- ✅ Carrinho sidebar animado
- ✅ Campo de nome + WhatsApp do cliente
- ✅ Pedido registrado no banco SQLite
- ✅ Link automático para WhatsApp com resumo do pedido
- ✅ Painel admin com login protegido
- ✅ CRUD de produtos com categorias e unidades
- ✅ Gestão de pedidos com troca de status
- ✅ Link direto para WhatsApp do cliente na lista de pedidos
