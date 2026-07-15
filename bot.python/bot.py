import asyncio
import aiohttp
import json
import os

async def run():
    # Em vez de Playwright (navegador), usamos Aiohttp para baixar os JSONs direto
    # Isso é instantâneo e não trava no scroll
    async with aiohttp.ClientSession() as session:
        # 1. Primeiro pegamos a lista de códigos dos países (isso a gente faz rápido pelo site)
        # Vamos assumir que você já tem a lista de códigos: ['br', 'us', 'al', 'fr', ...]
        codigos = ['br', 'us', 'al', 'fr', 'pt', 'es'] # Adicione os outros que você encontrar
        
        dados_totais = {}
        
        print(">>> Iniciando extração direta dos arquivos JSON...")
        
        for code in codigos:
            # A URL do arquivo que você descobriu
            url_json = f"https://famelack.com/tv/data/{code}.json" 
            # NOTA: Verifique se o caminho é /tv/data/ ou apenas /tv/
            
            print(f"-> Baixando dados de: {code.upper()}")
            try:
                async with session.get(url_json) as response:
                    if response.status == 200:
                        dados_pais = await response.json()
                        dados_totais[code.upper()] = dados_pais
                        print(f"   Sucesso: {len(dados_pais)} canais encontrados.")
                    else:
                        print(f"   Erro: Não encontrei o arquivo {code}.json")
            except Exception as e:
                print(f"   Falha ao baixar {code}: {e}")

        # 3. Salva tudo em um único arquivo
        if not os.path.exists('canaisgringos.html'): 
            os.makedirs('canaisgringos.html')
            
        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_totais, f, indent=4, ensure_ascii=False)
            
        print(">>> Varredura finalizada. Todos os dados foram baixados diretamente.")

if __name__ == "__main__":
    asyncio.run(run())
