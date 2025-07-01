#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRIPT PARA GERAÇÃO DE TOPOLOGIAS DE REDE COM ABRANGÊNCIA NACIONAL PARA LABORATÓRIOS
"""

import argparse
import os
import random
import math
import csv
import unicodedata
import json
from collections import defaultdict
import datetime
import sys

# Versão do script
VERSION = "A1.05"  # Atualizada para refletir mudanças

def carregar_configuracao(caminho_config):
    """Carrega as configurações de um arquivo JSON"""
    try:
        with open(caminho_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
            # Converter coordenadas de PTTs para tuplas
            config['PTTS'] = [tuple(item) for item in config['PTTS']]
            
            # Converter cidades por UF para listas de tuplas
            for uf in config['CIDADES_UF']:
                config['CIDADES_UF'][uf] = [tuple(cidade) for cidade in config['CIDADES_UF'][uf]]
                
            return config
    except Exception as e:
        print(f"ERRO: Falha ao carregar arquivo de configuração: {str(e)}")
        sys.exit(1)

# Função para remover acentos e caracteres especiais
def remover_acentos(texto):
    """Remove acentos, caracteres especiais e normaliza strings"""
    if not texto:
        return ""
    
    # Converter para string se não for
    texto = str(texto)
    
    # Normalizar e remover caracteres não ASCII
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    
    # Remover caracteres especiais restantes
    texto = ''.join(c for c in texto if c.isalnum() or c in [' ', '.', '-'])
    return texto

def normalize_str(s):
    """Normaliza string removendo acentos e espaços"""
    s = ''.join(c for c in unicodedata.normalize('NFD', s) 
               if unicodedata.category(c) != 'Mn')
    s = s.replace(' ', '').replace("'", "").replace("-", "")
    return s[:3].upper()

def decimal_to_dms(decimal, coord_type):
    """Converte coordenadas decimais para formato DMS"""
    if decimal >= 0:
        direction = 'N' if coord_type == 'lat' else 'E'
    else:
        direction = 'S' if coord_type == 'lat' else 'W'
    
    decimal = abs(decimal)
    degrees = int(decimal)
    minutes_decimal = (decimal - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = round((minutes_decimal - minutes) * 60)
    
    # Ajuste para overflow
    if seconds == 60:
        minutes += 1
        seconds = 0
        if minutes == 60:
            degrees += 1
            minutes = 0
    
    return f"{degrees}.{minutes}.{seconds}{direction}"

def gerar_siteid(uf, cidade, tipo_elemento, contador, abreviacoes):
    """Gera um siteid único para o elemento"""
    cidade_norm = normalize_str(cidade)
    abrev = abreviacoes[tipo_elemento]
    return f"{uf}{cidade_norm}0{abrev}{contador:03d}"

def obter_regiao(uf, regioes_config):
    """Obtém a região geográfica a partir da UF"""
    for regiao, ufs_regiao in regioes_config.items():
        if uf in ufs_regiao:
            return regiao
    return "Desconhecida"

def distancia_geografica(lat1, lon1, lat2, lon2):
    """Calcula distância aproximada entre duas coordenadas (km)"""
    # Fator de conversão graus para km
    km_por_grau = 111.32
    delta_lat = (lat2 - lat1) * km_por_grau
    delta_lon = (lon2 - lon1) * km_por_grau * abs(math.cos(math.radians((lat1+lat2)/2)))
    return math.sqrt(delta_lat**2 + delta_lon**2)

def gerar_siteid_ptt(cidade):
    """Gera um siteid para elementos PTT (formato: PTT_CIDADENORM)"""
    cidade_norm = normalize_str(cidade).replace(" ", "").upper()
    return f"PTT_{cidade_norm}"

def main():
    
    help_text = f"""
GERADOR PARA LABORATÓRIOS DE ELEMENTOS E CONEXÕES DE REDE PARA BACKBONE NACIONAL {VERSION}
====================================================

⭐ VISÃO GERAL
--------------
Gera arquivos CSV para modelagem de redes backbone hierárquicas:
  elementos.csv    -> Equipamentos e atributos
  conexoes.csv     -> Interconexões entre dispositivos
  localidades.csv  -> Dados geográficos (coordenadas DMS)

🚀 COMO USAR
------------
Formato básico:
  python GeradorBackbone.py [OPÇÕES]

Exemplos:
  1. Topologia padrão (300 elementos):
     python GeradorBackbone.py
  
  2. Topologia personalizada (500 elementos):
     python GeradorBackbone.py -e 500 -c meu_config.json

⚙️ ARGUMENTOS:
--------------
  -e  Quantidade total de elementos (30-1000, padrão: 300)
  -c  Caminho para arquivo de configuração (padrão: config.json)

🔧 PERSONALIZAÇÃO AVANÇADA (config.json)
----------------------------------------
Customize proporções e hierarquia editando:
1. PROPORCAO_CAMADAS:
   • Ajuste % de cada camada (ex: {{"RTIC": 0.03}} = 3% de RTICs)
   • Camadas: RTIC, RTRR, RTPR, RTED, SWAC

2. PROPORCOES_REGIAO:
   • Redistribua elementos por região (ex: {{"Sudeste": 0.5}} = 50% no Sudeste)
   • Regiões: Norte, Nordeste, Centro-Oeste, Sudeste, Sul

3. REGIOES_HIERARQUIA:
   • Defina hubs estratégicos e sub-regiões
   • Exemplo: 
        "Sudeste": {{
            "hubs": ["São Paulo", "Rio de Janeiro"],
            "sub-regioes": {{ ... }}
        }}

4. CIDADES_UF:
   • Adicione novas cidades por UF:
        "SP": [ 
            ["Novo Município", -23.55, -46.63],
            ...
        ]

📂 SAÍDA GERADA
---------------
Pasta: TOPOLOGIA_[QTD]_[TIMESTAMP]/
├── elementos.csv    # Equipamentos (siteid, camada, nível)
├── conexoes.csv     # Conexões (ponta-a, ponta-b, tipo)
├── localidades.csv  # Coordenadas (DMS) e região
└── resumo.txt       # Estatísticas da topologia

🏗️ HIERARQUIA DA REDE (5 Camadas)
---------------------------------
1. INNER-CORE (RTIC: 2%):
   - Núcleo de alta capacidade
   - Forma anéis regionais + backbone nacional
   - Localização: Hubs estratégicos (ex: São Paulo)

2. REFLECTOR (RTRR: 3%):
   - Agregação regional
   - Conectado a 2 RTICs
   - Localização: Capitais de sub-regiões

3. PEERING (RTPR: 3%):
   - Interconexão com IXPs
   - Conectado a 2 RTICs
   - Localização: Proximidade a PTTs

4. EDGE (RTED: 12%):
   - Borda de rede
   - Operam em pares georredudantes
   - Conectados a RTICs e SWACs

5. METRO (SWAC: 80%):
   - Acesso metropolitano
   - Organizados em anéis locais
   - Conectados a pares de RTEDs

⚠️ LIMITAÇÕES IMPORTANTES
-------------------------
• Quantidade mínima: 30 elementos
• Máximo recomendado: 1000 elementos
   - Limite de renderização em ferramentas visuais
   - Desempenho degradado acima disso
• PTTs são OBRIGATÓRIOS:
   - Sem PTTs em uma região = menor redundância
   - Adicione todos PTTs relevantes no config.json

🔍 EXEMPLO DE CUSTOMIZAÇÃO
--------------------------
Para criar topologia com:
- 20% de RTICs
- 60% no Nordeste
Edite config.json:
{{
  "PROPORCAO_CAMADAS": {{
    "RTIC": 0.20,   # << Aumentado para 20%
    ... 
  }},
  "PROPORCOES_REGIAO": {{
    "Nordeste": 0.6, # << 60% dos elementos
    ...
  }}
}}

💡 DICAS RÁPIDAS
----------------
• Combine com GeradorTopologias para visualização .drawio, em:
	https://github.com/flashbsb/Network-Topology-Generator-for-Drawio
• Use coordenadas reais em CIDADES_UF para precisão geográfica
• Monitore resumo.txt para validar distribuição
• Atualizações em: 
	https://github.com/flashbsb/Backbone-Network-Topology-Generator
"""
    # Cria o parser com a descrição completa
    parser = argparse.ArgumentParser(
        description=help_text,  # Usa o texto completo de ajuda aqui
        formatter_class=argparse.RawTextHelpFormatter
    )   
    
    parser.add_argument(
        '-e', 
        type=int, 
        default=300,
        help='Quantidade total de elementos (padrão: 300)'
    )
    
    parser.add_argument(
        '-c',
        type=str,
        default='config.json',
        help='Caminho para o arquivo de configuração (padrão: config.json)'
    )
    
    args = parser.parse_args()


    if args.e < 30:
        print("ERRO: Quantidade mínima de elementos é 30")
        sys.exit(1)
    
    # 1. Carregar configuração
    config = carregar_configuracao(args.c)
    
    # Extrair configurações
    PROPORCAO_CAMADAS = config["PROPORCAO_CAMADAS"]
    PROPORCOES_REGIAO = config["PROPORCOES_REGIAO"]
    REGIOES_HIERARQUIA = config["REGIOES_HIERARQUIA"]
    ABREVIACOES = config["ABREVIACOES"]
    REGIOES = config["REGIOES"]
    PTTS = config["PTTS"]
    CIDADES_UF = config["CIDADES_UF"]
    
    # ========================================================================
    # ALTERAÇÃO PRINCIPAL: Calcular quantidades por camada usando proporções
    # ========================================================================
    
    # Calcular mínimos obrigatórios baseados na hierarquia
    min_rtics = 0
    min_rtrrs = 0
    for regiao, dados in REGIOES_HIERARQUIA.items():
        min_rtics += len(dados["hubs"])
        min_rtrrs += len(dados["sub-regioes"])
    
    # Calcular quantidades com base nas proporções
    dist_real = {
        "RTIC": max(min_rtics, round(PROPORCAO_CAMADAS["RTIC"] * args.e)),
        "RTRR": max(min_rtrrs, round(PROPORCAO_CAMADAS["RTRR"] * args.e)),
        "RTPR": round(PROPORCAO_CAMADAS["RTPR"] * args.e),
        "RTED": round(PROPORCAO_CAMADAS["RTED"] * args.e),
        "SWAC": round(PROPORCAO_CAMADAS["SWAC"] * args.e)
    }
    
    # Ajustar diferença de arredondamento
    total_calculado = sum(dist_real.values())
    diff = args.e - total_calculado
    if diff != 0:
        # Ajustar na camada com maior proporção
        camada_ajuste = max(PROPORCAO_CAMADAS, key=PROPORCAO_CAMADAS.get)
        dist_real[camada_ajuste] += diff
    
    # Garantir que RTED seja par
    if dist_real["RTED"] % 2 != 0:
        dist_real["RTED"] += 1
    
    # 2. Gerar elementos PTT
    elementos_ptt = []
    for ptt in PTTS:
        cidade_ptt = ptt[0]
        uf_ptt = ptt[1]
        lat_ptt = ptt[2]
        lon_ptt = ptt[3]
        
        elementos_ptt.append({
            "elemento": f"PTT-{cidade_ptt[:10]}",
            "camada": "PTT",
            "nivel": 10,
            "cor": "",
            "siteid": gerar_siteid_ptt(cidade_ptt),
            "apelido": "",
            "cidade": cidade_ptt,
            "uf": uf_ptt,
            "lat": lat_ptt,
            "lon": lon_ptt,
            "tipo": "PTT"
        })
    
    # 3. Preparar lista completa de cidades
    todas_cidades = []
    for uf, cidades_uf in CIDADES_UF.items():
        for cidade in cidades_uf:
            todas_cidades.append((cidade[0], uf, cidade[1], cidade[2]))
    
    # Adicionar PTTs à lista de cidades
    for ptt in PTTS:
        if ptt not in todas_cidades:
            todas_cidades.append((ptt[0], ptt[1], ptt[2], ptt[3]))
    
    # Agrupar cidades por região
    cidades_por_regiao = defaultdict(list)
    for cidade in todas_cidades:
        uf = cidade[1]
        regiao = obter_regiao(uf, REGIOES)
        cidades_por_regiao[regiao].append(cidade)
    
    # Calcular distribuição regional proporcional
    dist_regional = {}
    total_elementos = args.e
    for regiao, proporcao in PROPORCOES_REGIAO.items():
        dist_regional[regiao] = round(proporcao * total_elementos)
    
    # Ajustar diferença de arredondamento
    diff = total_elementos - sum(dist_regional.values())
    if diff != 0:
        regiao_maior = max(PROPORCOES_REGIAO, key=PROPORCOES_REGIAO.get)
        dist_regional[regiao_maior] += diff
 
    # 4. Inicializar lista de elementos COM OS PTTs
    elementos = elementos_ptt.copy()  # Mantemos os PTTs aqui
 
    # Dicionários para armazenar elementos
    site_contadores = defaultdict(lambda: defaultdict(int))
    rtics = []
    rtrrs = []
    rtprs = []
    rted_pares = []
    swacs = []
    
    # ========================================================================
    # ALTERAÇÃO: Distribuição proporcional de RTICs por região
    # ========================================================================
    
    # Calcular quantidades de RTICs por região
    rtics_por_regiao = {}
    total_rtics = dist_real["RTIC"]
    
    # Distribuição inicial baseada na proporção regional
    for regiao, proporcao in PROPORCOES_REGIAO.items():
        rtics_por_regiao[regiao] = max(
            1,  # Mínimo 1 por região
            round(proporcao * total_rtics)
        )
    
    # Ajustar diferença
    total_rtics_calculado = sum(rtics_por_regiao.values())
    if total_rtics_calculado < total_rtics:
        # Adicionar RTICs extras nas regiões maiores
        for regiao in sorted(rtics_por_regiao, key=rtics_por_regiao.get, reverse=True):
            if total_rtics_calculado < total_rtics:
                rtics_por_regiao[regiao] += 1
                total_rtics_calculado += 1
            else:
                break
    
    # Gerar RTICs por região
    for regiao, qtd_rtics_regiao in rtics_por_regiao.items():
        # Obter hubs obrigatórios primeiro
        hubs_obrigatorios = REGIOES_HIERARQUIA[regiao]["hubs"]
        cidades_disponiveis = cidades_por_regiao[regiao].copy()
        
        # Gerar hubs obrigatórios
        hubs_gerados = []
        for hub in hubs_obrigatorios:
            cidade_hub = next((c for c in cidades_disponiveis if c[0] == hub), None)
            if cidade_hub:
                siteid = gerar_siteid(
                    cidade_hub[1], cidade_hub[0], "RTIC", 
                    site_contadores[cidade_hub[1]+cidade_hub[0]]["RTIC"] + 1,
                    ABREVIACOES
                )
                site_contadores[cidade_hub[1]+cidade_hub[0]]["RTIC"] += 1
                
                elementos.append({
                    "elemento": f"RTIC-{hub[:3].upper()}{len(rtics)+1:02d}-01",
                    "camada": "INNER-CORE",
                    "nivel": 1,
                    "cor": "",
                    "siteid": siteid,
                    "apelido": "",
                    "cidade": cidade_hub[0],
                    "uf": cidade_hub[1],
                    "lat": cidade_hub[2],
                    "lon": cidade_hub[3],
                    "tipo": "RTIC"
                })
                rtics.append(elementos[-1])
                hubs_gerados.append(hub)
                cidades_disponiveis.remove(cidade_hub)
        
        # Gerar RTICs extras se necessário
        rtics_extras = qtd_rtics_regiao - len(hubs_gerados)
        if rtics_extras > 0:
            # Priorizar cidades com PTTs
            cidades_ptt = [c for c in cidades_disponiveis if c[0] in [p[0] for p in PTTS]]
            if not cidades_ptt:
                cidades_ptt = cidades_disponiveis
            
            for _ in range(rtics_extras):
                if not cidades_ptt:
                    break
                    
                cidade = random.choice(cidades_ptt)
                siteid = gerar_siteid(
                    cidade[1], cidade[0], "RTIC", 
                    site_contadores[cidade[1]+cidade[0]]["RTIC"] + 1,
                    ABREVIACOES
                )
                site_contadores[cidade[1]+cidade[0]]["RTIC"] += 1
                
                elementos.append({
                    "elemento": f"RTIC-{cidade[0][:3].upper()}{len(rtics)+1:02d}-01",
                    "camada": "INNER-CORE",
                    "nivel": 1,
                    "cor": "",
                    "siteid": siteid,
                    "apelido": "",
                    "cidade": cidade[0],
                    "uf": cidade[1],
                    "lat": cidade[2],
                    "lon": cidade[3],
                    "tipo": "RTIC"
                })
                rtics.append(elementos[-1])
                cidades_ptt.remove(cidade)
                if cidade in cidades_disponiveis:
                    cidades_disponiveis.remove(cidade)
    
    # ========================================================================
    # ALTERAÇÃO: Distribuição proporcional de RTRRs por região
    # ========================================================================
    
    # Calcular quantidades de RTRRs por região
    rtrrs_por_regiao = {}
    total_rtrrs = dist_real["RTRR"]
    
    # Distribuição baseada na proporção regional
    for regiao, proporcao in PROPORCOES_REGIAO.items():
        rtrrs_por_regiao[regiao] = max(
            1,  # Mínimo 1 por região
            round(proporcao * total_rtrrs)
        )
    
    # Ajustar diferença
    total_rtrrs_calculado = sum(rtrrs_por_regiao.values())
    if total_rtrrs_calculado < total_rtrrs:
        for regiao in sorted(rtrrs_por_regiao, key=rtrrs_por_regiao.get, reverse=True):
            if total_rtrrs_calculado < total_rtrrs:
                rtrrs_por_regiao[regiao] += 1
                total_rtrrs_calculado += 1
            else:
                break
    
    # Gerar RTRRs por região
    for regiao, qtd_rtrrs_regiao in rtrrs_por_regiao.items():
        # Obter sub-regiões obrigatórias primeiro
        sub_regioes_obrigatorias = list(REGIOES_HIERARQUIA[regiao]["sub-regioes"].keys())
        cidades_disponiveis = cidades_por_regiao[regiao].copy()
        
        # Gerar um RTRR por sub-região obrigatória
        sub_regioes_geradas = []
        for sub_regiao in sub_regioes_obrigatorias:
            # Selecionar cidade representativa (primeira UF da sub-região)
            uf_rep = REGIOES_HIERARQUIA[regiao]["sub-regioes"][sub_regiao][0]
            cidades_sub = [c for c in cidades_disponiveis if c[1] == uf_rep]
            
            if cidades_sub:
                cidade_rep = cidades_sub[0]
                siteid = gerar_siteid(
                    cidade_rep[1], cidade_rep[0], "RTRR", 
                    site_contadores[cidade_rep[1]+cidade_rep[0]]["RTRR"] + 1,
                    ABREVIACOES
                )
                site_contadores[cidade_rep[1]+cidade_rep[0]]["RTRR"] += 1
                
                elementos.append({
                    "elemento": f"RTRR-{sub_regiao[:5]}{len(rtrrs)+1:02d}-01",
                    "camada": "REFLECTOR",
                    "nivel": 3,
                    "cor": "",
                    "siteid": siteid,
                    "apelido": "",
                    "cidade": cidade_rep[0],
                    "uf": cidade_rep[1],
                    "lat": cidade_rep[2],
                    "lon": cidade_rep[3],
                    "tipo": "RTRR"
                })
                rtrrs.append(elementos[-1])
                sub_regioes_geradas.append(sub_regiao)
                if cidade_rep in cidades_disponiveis:
                    cidades_disponiveis.remove(cidade_rep)
        
        # Gerar RTRRs extras se necessário
        rtrrs_extras = qtd_rtrrs_regiao - len(sub_regioes_geradas)
        if rtrrs_extras > 0:
            # Priorizar cidades com PTTs
            cidades_ptt = [c for c in cidades_disponiveis if c[0] in [p[0] for p in PTTS]]
            if not cidades_ptt:
                cidades_ptt = cidades_disponiveis
            
            for _ in range(rtrrs_extras):
                if not cidades_ptt:
                    break
                    
                cidade = random.choice(cidades_ptt)
                siteid = gerar_siteid(
                    cidade[1], cidade[0], "RTRR", 
                    site_contadores[cidade[1]+cidade[0]]["RTRR"] + 1,
                    ABREVIACOES
                )
                site_contadores[cidade[1]+cidade[0]]["RTRR"] += 1
                
                elementos.append({
                    "elemento": f"RTRR-{cidade[0][:5]}{len(rtrrs)+1:02d}-01",
                    "camada": "REFLECTOR",
                    "nivel": 3,
                    "cor": "",
                    "siteid": siteid,
                    "apelido": "",
                    "cidade": cidade[0],
                    "uf": cidade[1],
                    "lat": cidade[2],
                    "lon": cidade[3],
                    "tipo": "RTRR"
                })
                rtrrs.append(elementos[-1])
                cidades_ptt.remove(cidade)
                if cidade in cidades_disponiveis:
                    cidades_disponiveis.remove(cidade)
    
    # ========================================================================
    # GERAR AS DEMAIS CAMADAS (mantido o código original com ajustes)
    # ========================================================================
    
    # 3. Gerar RTPRs (distribuição regional proporcional)
    for regiao, qtd_regiao in dist_regional.items():
        qtd_rtpr_regiao = max(1, round(dist_real["RTPR"] * (qtd_regiao / total_elementos)))
        cidades_regiao = cidades_por_regiao[regiao]
        
        if not cidades_regiao:
            continue
            
        for i in range(qtd_rtpr_regiao):
            # Priorizar cidades com PTTs na região
            cidades_ptt = [c for c in cidades_regiao if c[0] in [p[0] for p in PTTS]]
            if not cidades_ptt:
                cidade = random.choice(cidades_regiao)
            else:
                cidade = random.choice(cidades_ptt)
            
            siteid = gerar_siteid(
                cidade[1], cidade[0], "RTPR", 
                site_contadores[cidade[1]+cidade[0]]["RTPR"] + 1,
                ABREVIACOES
            )
            site_contadores[cidade[1]+cidade[0]]["RTPR"] += 1
            
            elementos.append({
                "elemento": f"RTPR-{cidade[1]}{i+1:02d}-01",
                "camada": "PEERING",
                "nivel": 4,
                "cor": "",
                "siteid": siteid,
                "apelido": "",
                "cidade": cidade[0],
                "uf": cidade[1],
                "lat": cidade[2],
                "lon": cidade[3],
                "tipo": "RTPR"
            })
            rtprs.append(elementos[-1])
    
    # 4. Gerar RTEDs em pares (distribuição regional proporcional)
    for regiao, qtd_regiao in dist_regional.items():
        qtd_rted_regiao = max(2, round(dist_real["RTED"] * (qtd_regiao / total_elementos)))
        # Garantir número par
        if qtd_rted_regiao % 2 != 0:
            qtd_rted_regiao += 1
            
        cidades_regiao = cidades_por_regiao[regiao]
        
        if not cidades_regiao or qtd_rted_regiao < 2:
            continue
            
        pares_regiao = qtd_rted_regiao // 2
        for i in range(pares_regiao):
            # Selecionar cidade base
            cidade_base = random.choice(cidades_regiao)
            
            # Encontrar cidade próxima para o par
            cidade_par = min(
                [c for c in cidades_regiao if c != cidade_base],
                key=lambda c: distancia_geografica(
                    cidade_base[2], cidade_base[3], c[2], c[3]
                )
            )
            
            # Criar primeiro elemento do par
            siteid1 = gerar_siteid(
                cidade_base[1], cidade_base[0], "RTED", 
                site_contadores[cidade_base[1]+cidade_base[0]]["RTED"] + 1,
                ABREVIACOES
            )
            site_contadores[cidade_base[1]+cidade_base[0]]["RTED"] += 1
            
            elementos.append({
                "elemento": f"RTED-{cidade_base[1]}{i+1:02d}-01",
                "camada": "EDGE",
                "nivel": 5,
                "cor": "",
                "siteid": siteid1,
                "apelido": "",
                "cidade": cidade_base[0],
                "uf": cidade_base[1],
                "lat": cidade_base[2],
                "lon": cidade_base[3],
                "tipo": "RTED"
            })
            rted1 = elementos[-1]
            
            # Criar segundo elemento do par
            siteid2 = gerar_siteid(
                cidade_par[1], cidade_par[0], "RTED", 
                site_contadores[cidade_par[1]+cidade_par[0]]["RTED"] + 1,
                ABREVIACOES
            )
            site_contadores[cidade_par[1]+cidade_par[0]]["RTED"] += 1
            
            elementos.append({
                "elemento": f"RTED-{cidade_par[1]}{i+1:02d}-02",
                "camada": "EDGE",
                "nivel": 5,
                "cor": "",
                "siteid": siteid2,
                "apelido": "",
                "cidade": cidade_par[0],
                "uf": cidade_par[1],
                "lat": cidade_par[2],
                "lon": cidade_par[3],
                "tipo": "RTED"
            })
            rted2 = elementos[-1]
            
            rted_pares.append((rted1, rted2))
    
    # 5. Gerar SWACs (distribuição regional proporcional)
    for regiao, qtd_regiao in dist_regional.items():
        qtd_swac_regiao = round(dist_real["SWAC"] * (qtd_regiao / total_elementos))
        cidades_regiao = cidades_por_regiao[regiao]
        
        if not cidades_regiao:
            continue
            
        for i in range(qtd_swac_regiao):
            cidade = random.choice(cidades_regiao)
            siteid = gerar_siteid(
                cidade[1], cidade[0], "SWAC", 
                site_contadores[cidade[1]+cidade[0]]["SWAC"] + 1,
                ABREVIACOES
            )
            site_contadores[cidade[1]+cidade[0]]["SWAC"] += 1
            
            elementos.append({
                "elemento": f"SWAC-{cidade[1]}{i+1:02d}-01",
                "camada": "METRO",
                "nivel": 8,
                "cor": "",
                "siteid": siteid,
                "apelido": "",
                "cidade": cidade[0],
                "uf": cidade[1],
                "lat": cidade[2],
                "lon": cidade[3],
                "tipo": "SWAC"
            })
            swacs.append(elementos[-1])
    
    # ========================================================================
    # RESTANTE DO CÓDIGO (CONEXÕES E SAÍDA) PERMANECE IGUAL
    # ========================================================================
    
    # Gerar conexões
    conexoes = []
    
    # Agrupar RTICs por região
    rtics_por_regiao = defaultdict(list)
    for rtic in rtics:
        regiao = obter_regiao(rtic["uf"], REGIOES)
        rtics_por_regiao[regiao].append(rtic)

    # 1. Criar anéis regionais
    for regiao, rtics_regiao in rtics_por_regiao.items():
        n = len(rtics_regiao)
        if n < 2:
            continue
            
        for i in range(n):
            j = (i+1) % n
            conexoes.append({
                "ponta-a": rtics_regiao[i]["elemento"],
                "ponta-b": rtics_regiao[j]["elemento"],
                "textoconexao": f"Core Ring {regiao}",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })

    # 2. Ordem estratégica das regiões (geográfica)
    ordem_regioes = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    hubs_principais = []
    for regiao in ordem_regioes:
        if rtics_por_regiao.get(regiao):
            hubs_principais.append(rtics_por_regiao[regiao][0])

    # 3. Anel nacional principal
    n_nacional = len(hubs_principais)
    if n_nacional >= 2:
        for i in range(n_nacional):
            j = (i+1) % n_nacional
            conexoes.append({
                "ponta-a": hubs_principais[i]["elemento"],
                "ponta-b": hubs_principais[j]["elemento"],
                "textoconexao": "National Ring",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })

    # 4. Conexões de redundância entre regiões
    for i in range(len(ordem_regioes)):
        regiao_atual = ordem_regioes[i]
        regiao_vizinha = ordem_regioes[(i+1) % len(ordem_regioes)]
        
        if (len(rtics_por_regiao.get(regiao_atual, [])) >= 2 and 
           rtics_por_regiao.get(regiao_vizinha)):
            
            segundo_hub = rtics_por_regiao[regiao_atual][1]
            hub_vizinho = rtics_por_regiao[regiao_vizinha][0]
            
            conexoes.append({
                "ponta-a": segundo_hub["elemento"],
                "ponta-b": hub_vizinho["elemento"],
                "textoconexao": "Cross-Region Redundancy",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })
    
    # Conexões RTRR para RTICs (2 conexões por RTRR)
    for rtrr in rtrrs:
        # Encontrar RTICs na mesma região
        regiao_rtrr = obter_regiao(rtrr["uf"], REGIOES)
        rtics_regiao = [r for r in rtics if obter_regiao(r["uf"], REGIOES) == regiao_rtrr]
        if len(rtics_regiao) < 2:
            # Se não houver 2 RTICs na região, pegar os mais próximos
            rtics_ordenados = sorted(
                rtics,
                key=lambda r: distancia_geografica(
                    rtrr["lat"], rtrr["lon"], r["lat"], r["lon"]
                )
            )[:2]
        else:
            rtics_ordenados = rtics_regiao[:2]
        
        for rtic in rtics_ordenados:
            conexoes.append({
                "ponta-a": rtrr["elemento"],
                "ponta-b": rtic["elemento"],
                "textoconexao": "Reflector Link",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })
    
    # Conexões RTPR para RTICs (2 conexões por RTPR)
    for rtpr in rtprs:
        # Encontrar os 2 RTICs mais próximos
        rtics_ordenados = sorted(
            rtics,
            key=lambda r: distancia_geografica(
                rtpr["lat"], rtpr["lon"], r["lat"], r["lon"]
            )
        )[:2]
        
        for rtic in rtics_ordenados:
            conexoes.append({
                "ponta-a": rtpr["elemento"],
                "ponta-b": rtic["elemento"],
                "textoconexao": "Peering Link",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })
    
    # Conexões RTED (pares e para RTICs)
    for par in rted_pares:
        # Conexão entre o par
        conexoes.append({
            "ponta-a": par[0]["elemento"],
            "ponta-b": par[1]["elemento"],
            "textoconexao": "Edge Pair",
            "strokeWidth": "",
            "strokeColor": "",
            "dashed": "",
            "fontStyle": "",
            "fontSize": ""
        })
        
        # Encontrar dois RTICs diferentes para o par
        rtics_ordenados1 = sorted(
            rtics,
            key=lambda r: distancia_geografica(
                par[0]["lat"], par[0]["lon"], r["lat"], r["lon"]
            )
        )
        
        # Primeiro RTIC para o primeiro elemento do par
        rtic1 = rtics_ordenados1[0]
        conexoes.append({
            "ponta-a": par[0]["elemento"],
            "ponta-b": rtic1["elemento"],
            "textoconexao": "Edge to Core",
            "strokeWidth": "",
            "strokeColor": "",
            "dashed": "",
            "fontStyle": "",
            "fontSize": ""
        })
        
        # Encontrar RTIC diferente para o segundo elemento do par
        rtics_ordenados2 = sorted(
            [r for r in rtics if r != rtic1],
            key=lambda r: distancia_geografica(
                par[1]["lat"], par[1]["lon"], r["lat"], r["lon"]
            )
        )
        
        if rtics_ordenados2:
            rtic2 = rtics_ordenados2[0]
        else:
            # Caso só tenha um RTIC (impossível, mas seguro)
            rtic2 = rtics_ordenados1[0]
        
        conexoes.append({
            "ponta-a": par[1]["elemento"],
            "ponta-b": rtic2["elemento"],
            "textoconexao": "Edge to Core",
            "strokeWidth": "",
            "strokeColor": "",
            "dashed": "",
            "fontStyle": "",
            "fontSize": ""
        })
    
    # Conexões SWAC (anéis conectados a pares de RTED)
    swacs_por_cidade = defaultdict(list)
    for swac in swacs:
        chave = f"{swac['uf']}-{swac['cidade']}"
        swacs_por_cidade[chave].append(swac)
    
    for cidade_swacs in swacs_por_cidade.values():
        # Ordenar aleatoriamente para formar anel
        random.shuffle(cidade_swacs)
        
        # Conectar em anel
        for i in range(len(cidade_swacs)):
            prox = (i + 1) % len(cidade_swacs)
            conexoes.append({
                "ponta-a": cidade_swacs[i]["elemento"],
                "ponta-b": cidade_swacs[prox]["elemento"],
                "textoconexao": "Metro Ring",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })
        
        # Conectar extremidades a um par de RTEDs
        if len(cidade_swacs) > 0 and rted_pares:
            # Encontrar par de RTED mais próximo
            cidade_ref = (cidade_swacs[0]["lat"], cidade_swacs[0]["lon"])
            par_rted = min(
                rted_pares,
                key=lambda p: min(
                    distancia_geografica(cidade_ref[0], cidade_ref[1], p[0]["lat"], p[0]["lon"]),
                    distancia_geografica(cidade_ref[0], cidade_ref[1], p[1]["lat"], p[1]["lon"])
                )
            )
            
            # Conectar primeira e última SWAC ao par de RTED
            conexoes.append({
                "ponta-a": cidade_swacs[0]["elemento"],
                "ponta-b": par_rted[0]["elemento"],
                "textoconexao": "Metro to Edge",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })
            
            conexoes.append({
                "ponta-a": cidade_swacs[-1]["elemento"],
                "ponta-b": par_rted[1]["elemento"],
                "textoconexao": "Metro to Edge",
                "strokeWidth": "",
                "strokeColor": "",
                "dashed": "",
                "fontStyle": "",
                "fontSize": ""
            })
    
    # Criar pasta de saída
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    pasta_saida = f"TOPOLOGIA_{args.e}_{timestamp}"
    os.makedirs(pasta_saida, exist_ok=True)
    
    # Escrever elementos.csv
    with open(f"{pasta_saida}/elementos.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=["elemento", "camada", "nivel", "cor", "siteid", "apelido"],
            delimiter=";"
        )
        writer.writeheader()
        for elem in elementos:
            # Aplicar remoção de acentos em todos os campos textuais
            writer.writerow({
                "elemento": remover_acentos(elem["elemento"]),
                "camada": remover_acentos(elem["camada"]),
                "nivel": elem["nivel"],
                "cor": remover_acentos(elem["cor"]),
                "siteid": remover_acentos(elem["siteid"]),
                "apelido": remover_acentos(elem["apelido"])
            })
    
    # Escrever conexoes.csv
    with open(f"{pasta_saida}/conexoes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=["ponta-a", "ponta-b", "textoconexao", 
                       "strokeWidth", "strokeColor", "dashed", 
                       "fontStyle", "fontSize"],
            delimiter=";"
        )
        writer.writeheader()
        for conn in conexoes:
            # Aplicar remoção de acentos em todos os campos textuais
            writer.writerow({
                "ponta-a": remover_acentos(conn["ponta-a"]),
                "ponta-b": remover_acentos(conn["ponta-b"]),
                "textoconexao": remover_acentos(conn["textoconexao"]),
                "strokeWidth": remover_acentos(conn["strokeWidth"]),
                "strokeColor": remover_acentos(conn["strokeColor"]),
                "dashed": remover_acentos(conn["dashed"]),
                "fontStyle": remover_acentos(conn["fontStyle"]),
                "fontSize": remover_acentos(conn["fontSize"])
            })
    
    # Escrever localidades.csv
    with open(f"{pasta_saida}/localidades.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=["siteid", "Localidade", "RegiaoGeografica", "Latitude", "Longitude"],
            delimiter=";"
        )
        writer.writeheader()
        for elem in elementos:
            regiao = obter_regiao(elem["uf"], REGIOES)
            # Aplicar remoção de acentos em todos os campos textuais
            writer.writerow({
                "siteid": remover_acentos(elem["siteid"]),
                "Localidade": remover_acentos(elem["cidade"]),
                "RegiaoGeografica": remover_acentos(regiao),
                "Latitude": decimal_to_dms(elem["lat"], "lat"),
                "Longitude": decimal_to_dms(elem["lon"], "lon")
            })
    
    # Gerar resumo - manter acentos pois é arquivo texto
    resumo = f"""
RESUMO DA TOPOLOGIA GERADA
==========================

Data de geracao: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total de elementos: {args.e}
Arquivo de configuração: {args.c}

DISTRIBUICAO POR CAMADA:
------------------------
INNER-CORE (RTIC): {dist_real["RTIC"]} elementos
REFLECTOR (RTRR): {dist_real["RTRR"]} elementos
PEERING (RTPR): {dist_real["RTPR"]} elementos
EDGE (RTED): {dist_real["RTED"]} elementos
METRO (SWAC): {dist_real["SWAC"]} elementos

DISTRIBUICAO GEOGRAFICA:
------------------------
Regioes:
"""
    
    dist_regiao = defaultdict(int)
    for elem in elementos:
        regiao = obter_regiao(elem["uf"], REGIOES)
        dist_regiao[regiao] += 1
    
    for regiao, qtd in dist_regiao.items():
        resumo += f"  {regiao}: {qtd} elementos\n"
    
    resumo += "\nEstados com mais elementos:\n"
    dist_uf = defaultdict(int)
    for elem in elementos:
        dist_uf[elem["uf"]] += 1
    
    for uf, qtd in sorted(dist_uf.items(), key=lambda x: x[1], reverse=True)[:5]:
        resumo += f"  {uf}: {qtd} elementos\n"
    
    resumo += f"""
CONEXÕES GERADAS:
-----------------
Total de conexões: {len(conexoes)}
Tipos:
  RTIC-RTIC: {len(rtics)*(len(rtics)-1)//2}
  RTRR-RTIC: {len(rtrrs)*2}
  RTPR-RTIC: {len(rtprs)*2}
  RTED-RTED: {len(rted_pares)}
  RTED-RTIC: {len(rted_pares)*2}
  SWAC-SWAC: {sum(len(grupo) for grupo in swacs_por_cidade.values())}
  SWAC-RTED: {len(swacs_por_cidade)*2}

ARQUIVOS GERADOS:
-----------------
1. elementos.csv: {len(elementos)} registros
2. conexoes.csv: {len(conexoes)} registros
3. localidades.csv: {len(elementos)} registros

Pasta de saída: {pasta_saida}
"""
    
    with open(f"{pasta_saida}/resumo.txt", "w", encoding="utf-8") as f:
        f.write(resumo)
    
    print(f"Topologia gerada com sucesso na pasta: {pasta_saida}")
    print(resumo)

if __name__ == "__main__":
    main()
