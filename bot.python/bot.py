import asyncio
import aiohttp
from playwright.async_api import async_playwright
import json
import os

# CONFIGURAÇÕES DE PACIÊNCIA
TEMPO_ESPERA_SCROLL = 7      # Segundos de espera após cada scroll
TENTATIVAS_LIMITE = 8        # Quantas vezes ele tenta achar novos canais antes de desistir
TIMEOUT_LINK = 25            # Segundos para esperar a resposta de um link de streaming

async def verificar_canais_carregados(page):
    """
    Função 'caçadora': rola a página devagar e monitora a contagem de botões.
    Se a contagem parar de subir, ele assume que acabou.
    """
    total_anterior = 0
    tentativas_vazias = 0
    
    while tentativas_vazias < TENTATIVAS_LIMITE:
        # Rola um pouco
        await page.mouse.wheel(0, 500)
        await asyncio.sleep(TEMPO_ESPERA_SCROLL)
        
        # Conta quantos canais existem agora
        canais_atuais = await page.query_selector_all('button.video-link')
        total_atual = len(canais_atuais)
        
        if total_atual > total_anterior:
            print(f"    [Monitor] Encontrados {total_atual} canais... continuando busca.")
            total_anterior = total_atual
            tentativas_vazias = 0 # Resetamos a contagem pois achamos mais
        else:
            tentativas_vazias += 1
            print(f"    [Monitor] Sem novos canais (tentativa {tentativas_vazias}/{TENTATIVAS_LIMITE}).")
            
    return await page.query_selector_all('button.video-link')

async def testar_link_robusto(session, url):
    """Testa o link com um timeout bem longo."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        async with session.get(url, timeout=TIMEOUT_LINK, headers=headers) as response:
            # Mantém links que respondem minimamente
            return response.status in [200, 206, 301, 302, 403]
    except:
        return False

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Contexto com User-Agent real para evitar bloqueios
        context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        page = await context.new_page()
        page.set_default_navigation_timeout(120000)
        
        print(">>> Iniciando varredura profunda e paciente...")
        await page.goto('https://famelack.com/tv/', wait_until='networkidle')
        await asyncio.sleep(10)
        
        # Captura todos os países primeiro
        itens = await page.query_selector_all('.country-item')
        codigos = [await item.get_attribute('data-country-code') for item in itens if await item.get_attribute('data-country-code')]
        
        dados_finais = {}
        async with aiohttp.ClientSession() as session:
            for code in codigos:
                url_pais = f"https://famelack.com/tv/{code}/"
                print(f"\n--- PAÍS: {code.upper()} ---")
                
                await page.goto(url_pais, wait_until='networkidle')
                await asyncio.sleep(8)
                
                # Inicia a caçada aos canais
                canais_finais = await verificar_canais_carregados(page)
                print(f"    Total coletado para {code.upper()}: {len(canais_finais)} canais.")
                
                lista_valida = {}
                for canal in canais_finais:
                    nome = await canal.get_attribute('data-channel-name')
                    link = await canal.get_attribute('data-video-url')
                    if nome and link:
                        if await testar_link_robusto(session, link):
                            lista_valida[nome] = link
                
                if lista_valida:
                    dados_finais[code.upper()] = lista_valida
                
                # Volta para a home com calma
                await page.goto('https://famelack.com/tv/', wait_until='networkidle')
                await asyncio.sleep(8)

        # Gravação final
        if not os.path.exists('canaisgringos.html'): os.makedirs('canaisgringos.html')
        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        print("\n>>> SUCESSO: Todos os canais foram processados com paciência máxima.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
