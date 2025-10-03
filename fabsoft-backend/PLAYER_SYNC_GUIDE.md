# Guia de Sincronização de Jogadores - SlamTalk

## 🚨 Problema Resolvido

**Erro Original**: `OperationalError: SSL connection has been closed unexpectedly`

**Causa**: A sincronização de detalhes de jogadores era feita **durante requisições HTTP**, causando:
- Timeouts de 30+ segundos na NBA API
- Conexão PostgreSQL fechada por inatividade
- Falha total da requisição

## ✅ Solução Implementada

### 1. **Remoção de Sincronização Sob Demanda**
- **ANTES**: Ao acessar `/jogadores/{slug}/details`, o sistema tentava buscar detalhes da NBA API automaticamente
- **AGORA**: O endpoint retorna apenas dados já sincronizados no banco

**Arquivo**: `fabsoft-backend/app/routers/jogadores.py`
```python
# REMOVIDO: Sincronização sob demanda causa timeout em produção
# Os detalhes devem ser populados via batch sync ou sincronização agendada
```

### 2. **Batch Sync Melhorado**
Endpoint `/admin/sync-all-players-teams` agora tem:
- ✅ **Limite padrão reduzido**: 10 jogadores (antes: 100)
- ✅ **Commits individuais**: Cada jogador é commitado separadamente (evita transação longa)
- ✅ **Sessões isoladas**: Cada jogador usa nova sessão DB (evita timeout de conexão)
- ✅ **Skip automático de timeouts**: Continua processando mesmo com falhas
- ✅ **Contador de restantes**: Mostra quantos jogadores ainda precisam de sync

### 3. **Retry Logic Otimizado**
`sync_player_details_by_id()` agora falha mais rápido:
- **Antes**: 3 tentativas com espera exponencial (5s, 10s, 15s) = até 30s por jogador
- **Agora**: 2 tentativas com espera fixa (3s) = máximo 6s por jogador
- **Resultado**: Processa mais jogadores no mesmo tempo, sem travar conexões

**Arquivo**: `fabsoft-backend/app/services/nba_importer.py`

## 📋 Como Usar em Produção (Render)

### **Estratégia Recomendada**: Sincronização em Lotes Pequenos

#### 1️⃣ Execute o batch sync múltiplas vezes (10 jogadores por vez)
```bash
# Via cURL ou Postman
POST https://slamtalk-backend.onrender.com/admin/sync-all-players-teams?limit=10

Headers:
  Authorization: Bearer {seu_token_admin}
```

**Resposta Esperada**:
```json
{
  "message": "Sincronização concluída! 561 jogadores restantes.",
  "jogadores_processados": 10,
  "times_atualizados": 8,
  "erros": 2,
  "erros_detalhes": [
    "Precious Achiuwa: timeout",
    "Player X: timeout"
  ],
  "remaining": 561,
  "recomendacao": "Execute novamente com limit=10 para processar os restantes"
}
```

#### 2️⃣ Repita até `remaining = 0`
- Execute o endpoint 50-60 vezes (571 jogadores / 10 = ~57 execuções)
- Cada execução leva ~30-60 segundos (10 jogadores × 3-6s cada)
- **Total estimado**: 30-60 minutos para sincronizar todos os 571 jogadores

#### 3️⃣ Automatização (Opcional)
Crie um script Python para executar automaticamente:

```python
import requests
import time

API_URL = "https://slamtalk-backend.onrender.com"
TOKEN = "seu_token_admin_aqui"

headers = {"Authorization": f"Bearer {TOKEN}"}

while True:
    response = requests.post(
        f"{API_URL}/admin/sync-all-players-teams?limit=10",
        headers=headers
    )
    data = response.json()
    
    print(f"Processados: {data['jogadores_processados']}, Restantes: {data['remaining']}")
    
    if data['remaining'] == 0:
        print("✅ Todos os jogadores sincronizados!")
        break
    
    # Aguarda 10s entre lotes (respeita rate limits)
    time.sleep(10)
```

### **Parâmetros do Endpoint**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `limit` | int | 10 | Jogadores por lote (máx: 20) |
| `skip_on_timeout` | bool | true | Continua mesmo com timeouts |

**Exemplos**:
```bash
# Padrão (recomendado para produção)
POST /admin/sync-all-players-teams?limit=10

# Mais agressivo (pode dar timeout em conexões lentas)
POST /admin/sync-all-players-teams?limit=20

# Falha na primeira exceção (debugging)
POST /admin/sync-all-players-teams?limit=5&skip_on_timeout=false
```

## 🔍 Verificação

### 1. Verificar quantos jogadores faltam sincronizar
```sql
-- PostgreSQL
SELECT COUNT(*) 
FROM jogador 
WHERE time_atual_id IS NULL OR posicao IS NULL;
```

### 2. Ver detalhes de um jogador específico
```bash
GET /jogadores/lebron-james/details
```

**Se retornar `posicao: null`** = Jogador ainda não sincronizado

### 3. Ver elenco de um time
```bash
GET /times/los-angeles-lakers/roster
```

**Se retornar lista vazia** = Jogadores do time ainda não sincronizados

## ⚠️ Problemas Comuns

### 1. **Timeouts Persistentes**
**Sintoma**: Muitos erros `timeout` no batch sync

**Causa**: NBA API bloqueando cloud providers (Render)

**Solução**:
- Reduza `limit` para 5 jogadores por vez
- Aumente intervalo entre execuções (20-30s)
- Execute em horários de menos tráfego (madrugada)

### 2. **Free Agents / Jogadores Aposentados**
**Sintoma**: `times_atualizados < jogadores_processados`

**Explicação**: Normal - jogadores sem time atual retornam `TEAM_ID = 0` na NBA API

**Resultado**: Jogador terá detalhes (altura, peso, etc.) mas `time_atual_id = NULL`

### 3. **Endpoint Retorna 0 Remaining mas Rosters Vazios**
**Causa**: Jogadores foram sincronizados mas são free agents

**Solução**: Verifique se o time específico tem jogadores ativos:
```sql
SELECT j.nome, j.time_atual_id, j.posicao 
FROM jogador j
JOIN time t ON j.time_atual_id = t.id
WHERE t.slug = 'los-angeles-lakers';
```

## 📊 Métricas Esperadas

Com 571 jogadores ativos:
- **Sincronizações necessárias**: ~57 execuções (limit=10)
- **Tempo por lote**: 30-60s (10 jogadores)
- **Tempo total**: 30-60 minutos
- **Taxa de sucesso**: ~85-90% (50-80 timeouts esperados)
- **Jogadores com time**: ~450-500 (resto são free agents)

## 🔄 Sincronização Agendada

O sistema possui sincronização automática semanal (Domingos 3h):
- **Endpoint**: `/admin/scheduler/run-player-sync` (manual)
- **Função**: Apenas adiciona novos jogadores (não atualiza detalhes)
- **Detalhes**: Devem ser sincronizados manualmente via batch sync

**IMPORTANTE**: A sincronização agendada NÃO popula detalhes automaticamente!

## 📝 Changelog

### v2.0 - Fix de Timeout em Produção (03/10/2025)
- ✅ Removida sincronização sob demanda em rotas HTTP
- ✅ Batch sync com commits individuais e sessões isoladas
- ✅ Retry logic reduzido (2 tentativas × 3s = 6s max)
- ✅ Limite padrão reduzido para 10 jogadores
- ✅ Skip automático de timeouts
- ✅ Contador de jogadores restantes

### v1.0 - Implementação Original
- ❌ Sincronização sob demanda causava timeouts
- ❌ Batch sync com transação única (timeout de conexão)
- ❌ 3 retries exponenciais (até 30s por jogador)

---

**Autor**: Lucas Bobato & Jandir Neto
**Projeto**: SlamTalk - Fábrica de Software 2025/2
