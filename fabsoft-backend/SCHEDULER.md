# Sistema de Jobs Agendados - SlamTalk

## Visão Geral

O SlamTalk utiliza o APScheduler para executar tarefas de sincronização automáticas em segundo plano, eliminando a necessidade de sincronizações manuais frequentes.

## Jobs Configurados

### 1. Sincronização de Jogadores (Semanal)
- **Frequência**: 1x por semana (Domingos às 3:00 AM)
- **Função**: `sync_players_job()`
- **O que faz**:
  - Sincroniza lista completa de jogadores usando dados estáticos (instantâneo)
  - Atualiza status ativo/inativo dos jogadores
  - Adiciona novos rookies e jogadores recém-contratados
  - Usa `force=True` para garantir execução mesmo se dados forem recentes

### 2. Sincronização de Jogos Futuros (Diária)
- **Frequência**: 1x por dia (Diariamente às 4:00 AM)
- **Função**: `sync_future_games_job()`
- **O que faz**:
  - Busca jogos agendados para os próximos 30 dias
  - Adiciona novos jogos ao calendário
  - Atualiza horários e arenas quando necessário

## Como Funciona

### Inicialização
Quando o backend inicia (`uvicorn app.main:app`):
1. O scheduler é inicializado no `lifespan` do FastAPI
2. Os jobs são registrados com seus horários
3. O scheduler começa a monitorar os horários agendados
4. Logs informativos são exibidos no console

### Execução Automática
- Os jobs são executados automaticamente nos horários configurados
- Cada execução é logada no console com timestamp e resultados
- Erros são capturados e logados sem derrubar a aplicação

### Encerramento
Quando o backend é encerrado:
1. O scheduler é desligado graciosamente
2. Jobs em execução são finalizados
3. Recursos são liberados adequadamente

## Endpoints Admin

### Verificar Status do Scheduler
```http
GET /admin/scheduler/status
Authorization: Bearer {token}
```

**Resposta**:
```json
{
  "running": true,
  "jobs": [
    {
      "id": "sync_players_weekly",
      "name": "Sincronização Semanal de Jogadores",
      "next_run_time": "2025-10-06T03:00:00",
      "trigger": "cron[day_of_week='sun', hour='3', minute='0']"
    },
    {
      "id": "sync_future_games_daily",
      "name": "Sincronização Diária de Jogos Futuros",
      "next_run_time": "2025-10-04T04:00:00",
      "trigger": "cron[hour='4', minute='0']"
    }
  ]
}
```

### Executar Sincronização de Jogadores Manualmente
```http
POST /admin/scheduler/run-sync-players
Authorization: Bearer {token}
```

### Executar Sincronização de Jogos Futuros Manualmente
```http
POST /admin/scheduler/run-sync-future-games
Authorization: Bearer {token}
```

## Configuração

### Horários Padrão
Os horários podem ser alterados em `app/scheduler.py`:

```python
# Sincronização de jogadores - Domingos às 3h
scheduler.add_job(
    sync_players_job,
    trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
    # ...
)

# Sincronização de jogos - Diariamente às 4h
scheduler.add_job(
    sync_future_games_job,
    trigger=CronTrigger(hour=4, minute=0),
    # ...
)
```

### Triggers Disponíveis

**CronTrigger** (horário específico):
```python
from apscheduler.triggers.cron import CronTrigger

# Todo dia às 14h30
CronTrigger(hour=14, minute=30)

# Toda segunda-feira às 9h
CronTrigger(day_of_week='mon', hour=9, minute=0)

# Todo dia 1º do mês às 0h
CronTrigger(day=1, hour=0, minute=0)
```

**IntervalTrigger** (intervalo fixo):
```python
from apscheduler.triggers.interval import IntervalTrigger

# A cada 6 horas
IntervalTrigger(hours=6)

# A cada 30 minutos
IntervalTrigger(minutes=30)

# A cada 7 dias
IntervalTrigger(days=7)
```

## Logs

### Durante Inicialização
```
🚀 Aplicação iniciada.

🕐 Configurando jobs agendados...
   ✓ Job configurado: Sincronização de jogadores (Domingos 3:00 AM)
   ✓ Job configurado: Sincronização de jogos futuros (Diariamente 4:00 AM)
   ✓ Scheduler iniciado com sucesso!
   ℹ️ Próximos jobs agendados:
      - Sincronização Semanal de Jogadores: 2025-10-06 03:00:00
      - Sincronização Diária de Jogos Futuros: 2025-10-04 04:00:00
```

### Durante Execução de Job
```
============================================================
🔄 [SCHEDULED JOB] Iniciando sincronização diária de jogos futuros - 2025-10-04 04:00:00
============================================================
    -> Buscando jogos via ScheduleLeagueV2 para temporada 2025-26...
    -> 82 jogos encontrados via ScheduleLeagueV2
✅ [SCHEDULED JOB] Sincronização de jogos futuros concluída!
   - Total processado: 82
   - Novos jogos adicionados: 15
============================================================
```

## Testes

### Testar Jobs Localmente
1. Inicie o backend:
```bash
cd fabsoft-backend
uvicorn app.main:app --reload
```

2. Use os endpoints de execução manual para testar:
```bash
# Testar sincronização de jogadores
curl -X POST http://localhost:8000/admin/scheduler/run-sync-players \
  -H "Authorization: Bearer {seu_token}"

# Testar sincronização de jogos
curl -X POST http://localhost:8000/admin/scheduler/run-sync-future-games \
  -H "Authorization: Bearer {seu_token}"
```

3. Verifique os logs no console do backend

### Testar com Intervalos Curtos (Desenvolvimento)
Para testes, você pode adicionar jobs com intervalos mais curtos em `scheduler.py`:

```python
# Adicionar após os jobs principais, dentro de start_scheduler()
# APENAS PARA DESENVOLVIMENTO - REMOVER EM PRODUÇÃO

from apscheduler.triggers.interval import IntervalTrigger

scheduler.add_job(
    sync_future_games_job,
    trigger=IntervalTrigger(minutes=5),  # A cada 5 minutos
    id='test_sync_games',
    name='[TESTE] Sincronização de Jogos (5 min)',
    replace_existing=True
)
```

## Troubleshooting

### Scheduler não está rodando
Verifique:
1. Se APScheduler está instalado: `pip install APScheduler==3.10.4`
2. Se há erros no console durante inicialização
3. Endpoint de status: `GET /admin/scheduler/status`

### Jobs não são executados
Verifique:
1. Timezone do sistema (scheduler usa timezone local)
2. Se o backend ficou rodando no horário agendado
3. Logs do console para erros específicos

### Erros durante execução de jobs
- Jobs são isolados e erros não derrubam o scheduler
- Verifique logs no console para detalhes
- Teste manualmente via endpoints `/admin/scheduler/run-*`

## Produção

### Considerações
1. **Timezone**: Configure timezone correto no servidor
2. **Logging**: Considere usar arquivo de log em vez de console
3. **Monitoramento**: Implemente alertas para falhas de jobs
4. **Persistência**: APScheduler usa memória por padrão, considere usar JobStore persistente se necessário

### Recomendações
- Mantenha horários fora do horário de pico de usuários
- Configure alertas para falhas consecutivas
- Monitore tempo de execução dos jobs
- Use ambiente separado para testes de jobs pesados

## Dependências

```txt
APScheduler==3.10.4
```

Instalação:
```bash
pip install -r requirements.txt
```
