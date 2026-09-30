# Sinal da Cruz (geocruz)

App web (PWA) que avisa quando o ônibus se aproxima de uma igreja, capela,
cruzeiro ou cemitério do trajeto, pra dar tempo de fazer o sinal da cruz.
Roda em `pedro-pinho085.github.io/geocruz/`. Versão nativa iOS em
[`app/`](app/README.md).

- [index.html](index.html) — o app (HTML/CSS/JS puro, sem build)
- [manifest.json](manifest.json), [sw.js](sw.js) — PWA instalável, funciona offline
- [trajeto.json](trajeto.json) — pontos pré-carregados (São Luís do Curu → Fortaleza / Itapipoca)
- [firebase-config.js](firebase-config.js) — chave do banco de dados compartilhado (ver abaixo)

## Conectar ao banco de dados (Firestore)

Sem configurar nada, o app funciona 100% local: cada celular guarda seus
próprios pontos no `localStorage` do navegador. Configurando o Firebase, os
pontos passam a ser **compartilhados** — quem marca uma igreja no ônibus,
todo mundo que abrir o app vê, em qualquer aparelho.

Por que Firebase: tem plano gratuito generoso (Spark), o SDK roda direto do
navegador sem precisar de servidor próprio (encaixa no GitHub Pages), e a
"chave" que vai no código **não é secreta** — quem protege os dados são as
regras do Firestore, não a chave.

### 1. Criar o projeto (grátis, ~2 minutos)

1. Vá em [console.firebase.google.com](https://console.firebase.google.com) e
   entre com uma conta Google.
2. **Adicionar projeto** → dê um nome (ex.: `sinal-da-cruz`) → pode desmarcar o
   Google Analytics (não precisa) → **Criar projeto**.

### 2. Ativar o Firestore

1. No menu à esquerda: **Build → Firestore Database → Criar banco de dados**.
2. Localização: qualquer uma do Brasil (`southamerica-east1`, por exemplo).
3. **Modo de produção** (não "modo de teste" — vamos colocar a regra certa
   no passo 4).

### 3. Ativar login anônimo

O app usa login anônimo só pra saber "é um app válido" sem pedir senha nem
e-mail de ninguém.

1. **Build → Authentication → Get started**.
2. Na aba **Sign-in method**, ative **Anonymous**.

### 4. Regras de segurança

Em **Firestore Database → Regras**, substitua pelo conteúdo abaixo e publique:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /pontos/{id} {
      allow read, write: if request.auth != null;
    }
  }
}
```

Isso libera ler/escrever a coleção `pontos` pra qualquer um que abriu o app
(login anônimo automático) — sem exigir cadastro, mas também sem deixar
totalmente aberto pra internet.

### 5. Pegar a config e colar no projeto

1. No topo da página do projeto (ícone de engrenagem → **Configurações do
   projeto**), em **Seus apps**, clique no ícone **`</>`** (Web) → dê um nome
   → **Registrar app** (não precisa de Firebase Hosting).
2. Copie o objeto `firebaseConfig` que aparece.
3. Cole em **[firebase-config.js](firebase-config.js)** (e na cópia em
   [app/www/firebase-config.js](app/www/firebase-config.js) se for usar o app
   nativo), substituindo os `"COLOQUE_AQUI"`.

Pronto — abra o app, marque um ponto, e ele já aparece em qualquer outro
celular que abrir a mesma URL.

### Como funciona por dentro

- `iniciarNuvem()` importa o SDK do Firebase só quando tem `firebase-config.js`
  preenchido; sem internet ou sem config, falha em silêncio e o app segue 100%
  local (ver [index.html](index.html), função `iniciarNuvem`).
- Login anônimo (`signInAnonymously`) roda sozinho, sem tela de login.
- `escutarNuvem()` mantém a coleção `pontos` sincronizada em tempo real
  (`onSnapshot`): o que está na nuvem mas não localmente é baixado; o que
  está localmente e ainda não chegou na nuvem (ex.: marcado sem sinal no
  ônibus) fica guardado e é reenviado sozinho quando a conexão volta.
- Cada ponto marcado, importado ou carregado do `trajeto.json` é gravado com
  `enviarNuvem(ponto)`; apagar um ponto chama `apagarDaNuvem(id)`.
- Documento no Firestore = mesmo `id` do ponto local, então marcar o mesmo
  ponto duas vezes (ex.: dois celulares carregando o trajeto juntos) só
  sobrescreve, nunca duplica.

### Limites do plano gratuito (Spark)

Bem acima do que este app usa: 50 mil leituras/dia, 20 mil escritas/dia,
1 GiB armazenado. Uma família ou um grupo de amigos no mesmo trajeto não
chega perto disso.
