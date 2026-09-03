# Sinal da Cruz — app iOS (Capacitor)

Casca nativa do app web [`geocruz/`](../). Adiciona o que o navegador **não**
consegue fazer:

- **GPS em segundo plano**, com a tela **bloqueada** (`@capacitor-community/background-geolocation`)
- **Notificação nativa** quando chega perto de uma igreja (`@capacitor/local-notifications`)
- **Vibração** nativa (`@capacitor/haptics`)

A mesma `www/index.html` roda como página web comum — o código detecta se está
dentro do app (`window.Capacitor`) e troca o motor de GPS / notificação.

---

## O que você precisa (não tem como fugir disso)

| Item | Por quê |
|---|---|
| **Um Mac** com **Xcode** (App Store, grátis) | build de iOS só compila no macOS |
| **Node.js 18+** no Mac | rodar o Capacitor CLI |
| **CocoaPods** (`sudo gem install cocoapods`) | dependências nativas dos plugins |
| **Um Apple ID** | assinar o app pra instalar no seu iPhone |

Sobre a assinatura:

- **Apple ID normal (grátis):** instala no *seu* iPhone, mas **expira em 7 dias** —
  é só reabrir o Xcode e dar Run de novo. Não gera `.ipa` pra passar pra outra
  pessoa.
- **Apple Developer Program (US$ 99/ano):** app dura 1 ano, e você pode gerar
  `.ipa` / mandar por TestFlight.

> Não existe "arquivo que roda no iPhone" clicando duas vezes. iPhone sem
> jailbreak só instala app assinado, via Xcode, TestFlight ou ferramentas de
> sideload (AltStore/Sideloadly) — todas precisam de um computador e do Apple ID.

---

## Passo a passo (no Mac)

```bash
cd geocruz/app

# 1. dependências
npm install

# 2. cria o projeto iOS nativo (pasta ios/, fora do git)
npx cap add ios

# 3. copia o www/ e instala os pods dos plugins
npx cap sync ios
```

### 4. Info.plist — adicionar as chaves de permissão

Abra `ios/App/App/Info.plist` (ou no Xcode: alvo **App → Info**) e acrescente:

```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>Para avisar quando você se aproxima de uma igreja do trajeto.</string>

<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>Para tocar o alerta mesmo com o app fechado ou a tela bloqueada.</string>

<key>UIBackgroundModes</key>
<array>
  <string>location</string>
</array>
```

### 5. Xcode — assinatura e capability

```bash
npx cap open ios
```

No Xcode:

1. Selecione o projeto **App** → aba **Signing & Capabilities**.
2. **Team:** escolha seu Apple ID (adicione em *Xcode → Settings → Accounts*).
3. **Bundle Identifier:** deixe `com.pedropinho.sinaldacruz` ou troque por um seu.
4. Clique **+ Capability** → **Background Modes** → marque **Location updates**.
   (confirma o que você pôs no Info.plist)

### 6. Rodar no iPhone

1. Conecte o iPhone por cabo, confie no computador.
2. No topo do Xcode, escolha seu iPhone como destino.
3. **▶ Run**.
4. Na 1ª vez: *Ajustes → Geral → VPN e Gerenciamento de Dispositivos* → confie no
   seu perfil de desenvolvedor.
5. Abra o app → aba **Vigiar** → **Começar a vigiar** → aceite localização
   escolhendo **"Sempre"** e as notificações.

### 7. (Opcional) Gerar um `.ipa`

Só com conta paga: **Product → Archive → Distribute App → Ad Hoc** (ou
**TestFlight**). O `.ipa` sai na janela do Organizer.

---

## Testar sem entrar no ônibus

No **Simulador** do Xcode: menu **Features → Location → Custom Location…** (põe uma
coordenada perto de um ponto do `trajeto.json`) ou **Freeway Drive** pra simular
movimento. Com o iPhone plugado: **Debug → Simulate Location** no Xcode, ou um
arquivo `.gpx` do trajeto.

---

## Como funciona por dentro

- `www/index.html` é o app inteiro (mesma cara da versão web).
- `const NATIVO = window.Capacitor?.isNativePlatform()` decide o caminho:
  - **nativo:** `BackgroundGeolocation.addWatcher({ requestPermissions:true,
    stale:false, distanceFilter:12 }, cb)` → a cada posição, calcula a igreja
    mais próxima e, se dentro do gatilho, dispara `LocalNotifications.schedule()`
    + `Haptics.vibrate()`. O watcher continua vivo com o app em 2º plano / tela
    apagada (o iOS mostra a barra azul de localização).
  - **web:** `navigator.geolocation.watchPosition` + Web Notifications, como antes.
- `www/trajeto.json` = os 24 pontos (S. Luís do Curu → Fortaleza / Itapipoca).
  No app nativo eles entram sozinhos no primeiro uso; na aba **Pontos** dá pra
  recarregar, e a aba **Marcar** continua servindo pra completar o que faltar.

## Atualizar o app depois de mexer no `www/`

```bash
npx cap copy ios     # só copia os arquivos web
# ou
npx cap sync ios     # copia + reinstala pods (quando trocar plugin)
```

## Limitações honestas

- Conta grátis = **reinstalar a cada 7 dias**.
- Precisa de **"Sempre"** na permissão de localização; em "Ao usar" o alerta não
  toca com o app fechado.
- Barra/indicador azul de localização fica visível enquanto vigia — é o iOS
  avisando, não dá pra esconder.
- GPS contínuo gasta bateria. Ligue **Vigiar** só no trecho da viagem.
- `distanceFilter: 12` e o gatilho por velocidade tentam compensar o ônibus a
  60–80 km/h, mas ponto muito colado à via pode disparar em cima da hora.
