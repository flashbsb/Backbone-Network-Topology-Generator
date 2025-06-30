GERADOR PARA LABORATÓRIOS DE ELEMENTOS E CONEXÕES DE REDE PARA BACKBONE NACIONAL {VERSION}
====================================================

VISÃO GERAL:
-----------
Ferramenta para geração automatizada para laboratórios de elementos e conexões de rede para Backbone Nacional hierárquicas. Gera os arquivos necessários para alimentar o GeradorTopologias:

  - elementos.csv: Definição dos equipamentos e suas propriedades
  - conexoes.csv: Interconexões entre os equipamentos
  - localidades.csv: Dados geográficos dos sites (coordenadas e regiões)

🚫 O QUE ESTE SCRIPT NÃO É:
--------------------------
  • Gerador de diagramas visuais (.drawio) » Use GeradorTopologias para isso
  • Simulador de tráfego ou desempenho
  • Ferramenta de planejamento de capacidade (bandwidth/links)
  • Validador de configurações de equipamentos
  • Gerador de políticas de segurança ou QoS

⭐ LÓGICA DE CONSTRUÇÃO DA TOPOLOGIA:
-----------------------------------
A topologia segue um modelo hierárquico de 5 camadas, com regras específicas de distribuição geográfica e conectividade:

1. DISTRIBUIÇÃO GEOGRÁFICA:
   • Baseada em cidades reais do Brasil (priorizando capitais e PTTs)
   • Proporção regional conforme dados do IBGE (população 2023):
        Norte: 8.3%    | Nordeste: 28.9%
        Centro-Oeste: 7.6% | Sudeste: 43.2% | Sul: 12.0%
   • Hierarquia regional com hubs estratégicos por macro-região

2. PROPORÇÃO DE EQUIPAMENTOS POR CAMADA:
   • RTIC (INNER-CORE): 2%    » Roteadores de núcleo
   • RTRR (REFLECTOR): 3%     » Roteadores refletores
   • RTPR (PEERING): 3%       » Roteadores de peering
   • RTED (EDGE): 12%         » Roteadores de borda
   • SWAC (METRO): 80%        » Switches de acesso

3. REGRAS DE CONECTIVIDADE:
   • RTICs: Formam anéis regionais + anel nacional principal
   • RTRRs: Conectados a 2 RTICs da mesma região
   • RTPRs: Conectados a 2 RTICs mais próximos
   • RTEDs: Operam em pares (mesma região) + conexões redundantes
   • SWACs: Organizados em anéis locais conectados a pares de RTEDs

🚀 COMO USAR:
------------
Formato básico:
  python GeradorBackbone.A1.01.py -e [QUANTIDADE_ELEMENTOS]

Exemplos:
  1. Topologia padrão (300 elementos):
     python GeradorBackbone.{VERSION}.py
  
  2. Topologia personalizada (500 elementos):
     python GeradorBackbone.{VERSION}.py -e 500

⚙️ ARGUMENTOS:
--------------
  -e  Quantidade total de elementos (mínimo: 100, máximo recomendado: 1000)
  -c  Caminho para o arquivo de configuração (padrão: config.json)

📂 SAÍDA GERADA:
---------------
Pasta no formato: TOPOLOGIA_[QTD]_[TIMESTAMP]
Contendo:
  1. elementos.csv    » Equipamentos e atributos
  2. conexoes.csv     » Conexões entre equipamentos
  3. localidades.csv  » Dados geográficos (coordenadas em DMS)
  4. resumo.txt       » Estatísticas da topologia

🔧 DETALHES TÉCNICOS:
-------------------
1. ESTRUTURA HIERÁRQUICA:
   a) INNER-CORE (RTIC):
      - Posicionados em hubs estratégicos (ex: São Paulo, Brasília)
      - Full-mesh regional + anel nacional inter-regiões
      - Mínimo: 2 elementos (1 por hub)

   b) REFLECTOR (RTRR):
      - Alocados nas capitais das sub-regiões
      - Conexões redundantes para 2 RTICs
      - Proporção: 1 por sub-região (ex: Norte1, Nordeste2)

   c) PEERING (RTPR):
      - Posicionados próximo a PTTs (Pontos de Troca de Tráfego)
      - Priorização de cidades com infraestrutura de IXPs
      - Conexão redundante para 2 RTICs

   d) EDGE (RTED):
      - Distribuídos em pares geograficamente próximos
      - Cada par conectado a 2 RTICs diferentes
      - Quantidade sempre PAR (failover ativo-ativo)

   e) METRO (SWAC):
      - Organizados em anéis metropolitanos
      - Cada anel conectado a um par de RTEDs
      - Representam 80% do total de elementos

2. ALGORITMOS-CHAVE:
   • Seleção de cidades:
        - Priorização de PTTs e capitais
        - Balanceamento regional proporcional à população
   • Conexões RTICs:
        - Anéis regionais + backbone nacional em estrela
        - Redundância inter-regiões (ex: Sudeste-Sul)
   • Distribuição de RTEDs/SWACs:
        - Pares geograficamente próximos (distância mínima)
        - Anéis metropolitanos com no mínimo 3 switches
   • Geração de IDs:
        - Formato: [UF][CIDADE][TIPO][SEQ] (ex: SPSAO0IC001)

3. TRATAMENTO DE DADOS:
   • Normalização de caracteres (remoção de acentos)
   • Conversão automática de coordenadas (decimal → DMS)
   • Balanceamento de quantidades após arredondamentos

⚠️ LIMITAÇÕES:
-------------
  • Quantidade mínima: 100 elementos
  • Máximo recomendado: 1,000 elementos (limite do Draw.io)
  • Cidades sem PTTs podem ter menor redundância
  • Não considera topografia física (rios/montanhas)
  • Não modela diferenças de capacidade entre enlaces

📌 EXEMPLO DE EXECUÇÃO:
----------------------
  python GeradorBackbone.{VERSION}.py -e 400 -c meu_config.json

  Saída:
    Pasta: TOPOLOGIA_400_20231025153045/
      elementos.csv    (400 registros)
      conexoes.csv     (~800-1200 registros)
      localidades.csv  (400 registros)
      resumo.txt       (estatísticas detalhadas)

🔍 DICAS:
--------
  • Combine com GeradorTopologias para gerar diagramas .drawio
  • Para grandes topologias (>800 nós), ajuste os parâmetros de layout no config.json do script GeradorTopologias
  • Use localidades.csv como referência para mapas personalizados

https://github.com/flashbsb/Backbone-Network-Topology-Generator
