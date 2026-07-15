import asyncio
from playwright.async_api import async_playwright
import json
import os

# Esta função é a principal que vai executar todo o trabalho do bot
async def run():
    # Iniciamos o navegador de forma assíncrona
    async with async_playwright() as p:
        # Iniciamos o browser. Deixamos o headless=True para rodar no servidor do GitHub
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Lista de países com seus respectivos links
        # Adicione novos países aqui conforme necessário
        paises = {
            "Estados Unidos": "https://famelack.com/tv/us/wviGS5VGRxTxKj",
        }
        
        # Dicionário que vai armazenar os dados organizados por país
        dados_organizados = {}

        # Loop para percorrer cada país definido acima
        for nome_pais, url in paises.items():
            print(f"--- Iniciando a coleta para: {nome_pais} ---")
            
            # Acessa a URL do país
            await page.goto(url, timeout=60000)
            
            # Espera forçada para garantir que a página carregue inicialmente
            await asyncio.sleep(5)
            
            # Rotina de scroll forçado para carregar elementos dinâmicos
            # Isso garante que não "economize" nenhum canal escondido na página
            await page.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        let distance = 100;
                        let timer = setInterval(() => {
                            let scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 50);
                    });
                }
            """)
            
            # Pequena pausa após o scroll para estabilizar o carregamento
            await asyncio.sleep(5)
            
            # Busca todos os elementos que contêm os links dos canais
            canais = await page.query_selector_all('button.video-link')
            
            lista_canais = {}
            
            # Extrai o nome e o link de cada canal encontrado
            for canal in canais:
                nome = await canal.get_attribute('data-channel-name')
                link = await canal.get_attribute('data-video-url')
                
                # Só adiciona se ambos existirem
                if nome and link:
                    lista_canais[nome] = link
            
            # Adiciona a lista coletada ao dicionário final
            dados_organizados[nome_pais] = lista_canais
            print(f"Sucesso! Foram coletados {len(lista_canais)} canais para {nome_pais}.")

        # Verifica se a pasta existe, se não, cria ela
        if not os.path.exists('canaisgringos.html'):
            os.makedirs('canaisgringos.html')

        # Grava os dados no arquivo JSON com formatação legível (indent=4)
        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_organizados, f, indent=4, ensure_ascii=False)
            
        print("Processo finalizado com sucesso.")
        await browser.close()

# Executa o bot
if __name__ == "__main__":
    asyncio.run(run())
