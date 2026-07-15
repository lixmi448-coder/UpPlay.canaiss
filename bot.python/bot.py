import asyncio
import json
import os
from playwright.async_api import async_playwright

# O bot agora lê o arquivo existente antes de começar
ARQUIVO_JSON = 'canaisgringos.html/canais.json'

def carregar_dados_existentes():
    if os.path.exists(ARQUIVO_JSON):
        with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

async def run():
    dados_finais = carregar_dados_existentes() # Carrega o que já foi feito
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        page = await context.new_page()

        canal_link = {"url": None}
        page.on("request", lambda r: canal_link.update({"url": r.url}) if any(x in r.url for x in ["m3u8", "manifest"]) else None)

        await page.goto('https://famelack.com/tv/', wait_until='networkidle')
        
        # Faz o scroll para carregar todos
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.wait_for_timeout(3000)

        paises = await page.query_selector_all('.country-item')
        codigos = [await p.get_attribute('data-country-code') for p in paises if await p.get_attribute('data-country-code')]

        for code in codigos:
            code_upper = code.upper()
            
            # CHECKPOINT: Se o país já estiver no JSON, pula!
            if code_upper in dados_finais:
                print(f"-> Pulando {code_upper} (já processado).")
                continue
                
            print(f"-> Processando novo país: {code_upper}")
            await page.goto(f'https://famelack.com/tv/{code}/', wait_until='networkidle')
            
            # ... (Lógica de processamento de canais igual à anterior)
            canais = await page.query_selector_all('li.sidebar-entry')
            dados_pais = {}
            for canal in canais:
                nome = await canal.get_attribute('data-channel-name')
                if not nome: continue
                
                canal_link["url"] = None
                btn = await canal.query_selector('button')
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(3500)
                    if canal_link["url"]:
                        dados_pais[nome] = canal_link["url"]
            
            if dados_pais:
                dados_finais[code_upper] = dados_pais
                # Salva a cada país para não perder o progresso se travar de novo
                with open(ARQUIVO_JSON, 'w', encoding='utf-8') as f:
                    json.dump(dados_finais, f, indent=4, ensure_ascii=False)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
