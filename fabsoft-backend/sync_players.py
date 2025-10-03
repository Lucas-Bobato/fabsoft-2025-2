#!/usr/bin/env python3
"""
Script de sincronização em lote para jogadores do SlamTalk.

Uso:
    python sync_players.py --url https://slamtalk-api.onrender.com --token SEU_TOKEN
    
Opções:
    --url: URL da API (padrão: http://localhost:8000)
    --token: Token de autenticação admin (obrigatório)
    --batch-size: Jogadores por lote (padrão: 10, máx: 20)
    --delay: Segundos entre lotes (padrão: 10)
    --max-batches: Número máximo de lotes (0 = ilimitado, padrão: 0)
"""

import argparse
import requests
import time
from datetime import datetime

def sync_players(api_url: str, token: str, batch_size: int = 10, delay: int = 10, max_batches: int = 0):
    """
    Executa sincronização em lote de jogadores.
    
    Args:
        api_url: URL base da API
        token: Token de autenticação
        batch_size: Jogadores por lote
        delay: Segundos entre lotes
        max_batches: Número máximo de lotes (0 = ilimitado)
    """
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"{api_url}/admin/sync-all-players-teams"
    
    print(f"🏀 Iniciando sincronização de jogadores...")
    print(f"   API: {api_url}")
    print(f"   Lote: {batch_size} jogadores")
    print(f"   Delay: {delay}s entre lotes")
    print(f"   Máximo de lotes: {'ilimitado' if max_batches == 0 else max_batches}")
    print(f"   Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    batch_count = 0
    total_processados = 0
    total_atualizados = 0
    total_erros = 0
    
    try:
        while True:
            batch_count += 1
            
            # Verifica se atingiu o limite de lotes
            if max_batches > 0 and batch_count > max_batches:
                print(f"\n✋ Limite de {max_batches} lotes atingido. Parando...")
                break
            
            print(f"\n📦 Lote #{batch_count} ({datetime.now().strftime('%H:%M:%S')})")
            
            try:
                response = requests.post(
                    endpoint,
                    params={"limit": batch_size, "skip_on_timeout": True},
                    headers=headers,
                    timeout=120  # 2 minutos de timeout para o request
                )
                
                if response.status_code != 200:
                    print(f"   ❌ Erro HTTP {response.status_code}: {response.text}")
                    break
                
                data = response.json()
                
                # Atualiza contadores
                processados = data.get("jogadores_processados", 0)
                atualizados = data.get("times_atualizados", 0)
                erros = data.get("erros", 0)
                remaining = data.get("remaining", 0)
                
                total_processados += processados
                total_atualizados += atualizados
                total_erros += erros
                
                # Mostra resultados do lote
                print(f"   Processados: {processados}")
                print(f"   Times atualizados: {atualizados}")
                print(f"   Erros: {erros}")
                print(f"   Restantes: {remaining}")
                
                # Mostra detalhes de erros se houver
                if erros > 0 and "erros_detalhes" in data:
                    print(f"   Detalhes dos erros:")
                    for erro in data["erros_detalhes"][:3]:  # Mostra apenas 3 primeiros
                        print(f"     - {erro}")
                    if len(data["erros_detalhes"]) > 3:
                        print(f"     ... e mais {len(data['erros_detalhes']) - 3} erros")
                
                # Verifica se terminou
                if remaining == 0:
                    print(f"\n✅ Sincronização completa! Todos os jogadores processados.")
                    break
                
                # Calcula progresso
                total_players = total_processados + remaining
                progress = (total_processados / total_players) * 100 if total_players > 0 else 0
                print(f"   Progresso geral: {progress:.1f}% ({total_processados}/{total_players})")
                
                # Aguarda antes do próximo lote
                if remaining > 0:
                    print(f"   ⏳ Aguardando {delay}s antes do próximo lote...")
                    time.sleep(delay)
                
            except requests.exceptions.Timeout:
                print(f"   ⏰ Timeout na requisição. Aguardando {delay}s e tentando novamente...")
                time.sleep(delay)
                continue
                
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Erro na requisição: {e}")
                break
    
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Sincronização interrompida pelo usuário (Ctrl+C)")
    
    finally:
        # Resumo final
        print("\n" + "=" * 60)
        print("📊 RESUMO DA SINCRONIZAÇÃO")
        print("=" * 60)
        print(f"Lotes executados: {batch_count}")
        print(f"Jogadores processados: {total_processados}")
        print(f"Times atualizados: {total_atualizados}")
        print(f"Erros totais: {total_erros}")
        print(f"Taxa de sucesso: {(total_atualizados / total_processados * 100) if total_processados > 0 else 0:.1f}%")
        print(f"Término: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(
        description="Script de sincronização em lote para jogadores do SlamTalk"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="URL da API (padrão: http://localhost:8000)"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Token de autenticação admin (obrigatório)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Jogadores por lote (padrão: 10, máx: 20)"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=10,
        help="Segundos entre lotes (padrão: 10)"
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=0,
        help="Número máximo de lotes (0 = ilimitado, padrão: 0)"
    )
    
    args = parser.parse_args()
    
    # Valida batch_size
    if args.batch_size > 20:
        print(f"⚠️  Aviso: batch_size {args.batch_size} reduzido para 20 (máximo permitido)")
        args.batch_size = 20
    
    if args.batch_size < 1:
        print(f"❌ Erro: batch_size deve ser >= 1")
        return
    
    # Valida delay
    if args.delay < 0:
        print(f"❌ Erro: delay deve ser >= 0")
        return
    
    # Executa sincronização
    sync_players(
        api_url=args.url.rstrip("/"),
        token=args.token,
        batch_size=args.batch_size,
        delay=args.delay,
        max_batches=args.max_batches
    )

if __name__ == "__main__":
    main()
