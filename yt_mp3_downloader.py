#!/usr/bin/env python3
import os
import time
import concurrent.futures
from pytubefix import YouTube
from pydub import AudioSegment
from tqdm import tqdm
import re

# Lista de links (removendo duplicatas)
links = list(set([
    "https://youtu.be/soEbblbngYI?si=k3yuBni71NVUi2wT",
    "https://youtu.be/wAWEDQzR4Wo?si=U3otxDpfSdxJAwY6",
    "https://youtu.be/yvBKhihUusA?si=ZvPkgKhELu9MXjOl",
    "https://youtu.be/UwNGHeyg46M?si=--5WJR5R58rZ_oaK",
    "https://youtu.be/UwNGHeyg46M?si=ZS8u6sajU0LtWLDs",
    "https://youtu.be/r08a2VDjQoo?si=SCkHkjDDBzEisnjn",
    "https://youtu.be/ACTJbamtObw?si=1pFKNjQQkuwo8X3Q",
    "https://youtu.be/Nx2W3bdfhpo?si=uXCpB4QoURKogYp9",
    "https://youtu.be/OMr7hDwYpAw?si=1ZaDcZ_GonYBPeKv",
    "https://youtu.be/OMr7hDwYpAw?si=HV204VgfOoQiV6Lb",
    "https://youtu.be/ghab6Ubid40?si=i_jPymQ1aPGOXg9T",
    "https://youtu.be/as778QafyqY?si=wA9lHZtuHleu0mWI",
    "https://youtu.be/8gsVNHB0wkM?si=FEYPqNcywpNysWfQ",
    "https://youtu.be/Pg_5fiBqX5w?si=DEcwq9hgvavZC3_y",
    "https://youtu.be/88jGxrRzTNk?si=oc-62zroE_o0BMlh",
    "https://youtu.be/SL_HJkkM_1s?si=yq4C-CUcCx--XWlF",
    "https://youtu.be/lzh2WTYQJeM?si=geaR7KZq3BewVdC4",
    "https://youtu.be/QFNaq8Z-AdY?si=oqAGZ9ksFUYKiiJj",
    "https://youtu.be/QFNaq8Z-AdY?si=NwVhj0rZorag5_MB",
    "https://youtu.be/xkRU_H6T_LU?si=cquy991WWkJg2QZO",
    "https://youtu.be/DM8mIk_IvN4?si=_tBSHmscO7Kw9Lsq",
    "https://youtu.be/6BW-VOYTSeQ?si=lqX0rDSIoys_ohea",
    "https://youtu.be/l470tlpGOPA?si=YgUwLlAQ0Z3UXxAY",
    "https://youtu.be/oi9APaNfnKQ?si=U-xmPqEPKxHkGi3e",
    "https://youtu.be/88jGxrRzTNk?si=OWKFtfEAgKTGMnCX",
    "https://youtu.be/nq0iYIHuWxg?si=wMgIOLxLSNWGtWUg",
    "https://youtu.be/H37pQpCAbfY?si=5brRzo4kpwP5wlP4",
    "https://youtu.be/to5GpZOYmu4?si=_4YlHHN5YcYEE6l1",
    "https://youtu.be/yvBKhihUusA?si=Kb6HjZuqWC1S1BMb",
    "https://youtu.be/ghab6Ubid40?si=TWz389ybPpmXW3Xg",
    "https://youtu.be/ISFmsNyBH7Y?si=MwtOIsoLjLoMy9A_",
    "https://youtu.be/QFNaq8Z-AdY?si=Ay51piVT4iQg3MZf",
    "https://youtu.be/fBpbgQz3J4s?si=fsyeb4BBHMEcnwFn"
]))

# Pasta de saída
output_folder = "mp3_downloads"
os.makedirs(output_folder, exist_ok=True)

# Função para sanitizar nomes de arquivo
def sanitize_filename(filename):
    # Remove caracteres inválidos para nomes de arquivo
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

# Função para baixar e converter um único vídeo
def download_and_convert(url):
    try:
        # Cria objeto YouTube
        yt = YouTube(url)
        
        # Obtém o título do vídeo
        title = yt.title
        safe_title = sanitize_filename(title)
        mp3_path = os.path.join(output_folder, f"{safe_title}.mp3")
        
        # Verifica se o arquivo já existe
        if os.path.exists(mp3_path):
            return {"success": True, "title": title, "status": "já existe"}
        
        # Baixa apenas o stream de áudio com a melhor qualidade
        audio_stream = yt.streams.filter(only_audio=True).first()
        temp_file = audio_stream.download(output_path=output_folder, filename=f"{safe_title}.tmp")
        
        # Converte para MP3 usando pydub
        audio = AudioSegment.from_file(temp_file)
        
        # Qualidade média (128kbps)
        audio.export(mp3_path, format="mp3", bitrate="128k", 
                    tags={
                        "title": title,
                        "artist": yt.author
                    })
        
        # Remove o arquivo temporário
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        return {"success": True, "title": title, "status": "baixado"}
        
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}

# Contador de estatísticas
total = len(links)
start_time = time.time()

# Inicializa contadores
results = {"success": 0, "failed": 0, "skipped": 0}

# Usa multithreading para processamento paralelo
with tqdm(total=total, desc="Progresso") as pbar:
    # Define o número de workers (ajuste baseado no seu sistema)
    max_workers = min(10, len(links))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submete todas as tarefas
        future_to_url = {executor.submit(download_and_convert, url): url for url in links}
        
        # Processa os resultados à medida que são concluídos
        for future in concurrent.futures.as_completed(future_to_url):
            result = future.result()
            
            if result["success"]:
                if result.get("status") == "já existe":
                    print(f"Arquivo já existe: {result['title']}")
                    results["skipped"] += 1
                else:
                    print(f"✓ Baixado: {result['title']}")
                    results["success"] += 1
            else:
                print(f"❌ Erro: {result['error']} - {result['url']}")
                results["failed"] += 1
                
            pbar.update(1)

# Estatísticas finais
elapsed_time = time.time() - start_time
print(f"\nResumo:")
print(f"✓ Baixados: {results['success']} / {total}")
print(f"⏭ Pulados: {results['skipped']} / {total}")
print(f"❌ Falhas: {results['failed']} / {total}")
print(f"⏱️ Tempo total: {elapsed_time:.1f} segundos") 