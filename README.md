GERADOR PARA LABORATÓRIOS DE ELEMENTOS E CONEXÕES DE REDE PARA BACKBONE NACIONAL 
====================================================

VISÃO GERAL:
-----------
Ferramenta para geração automatizada para laboratórios de elementos e conexões de rede para Backbone Nacional hierárquicas. Gera os arquivos necessários para alimentar o GeradorTopologias:

  - elementos.csv: Definição dos equipamentos e suas propriedades
  - conexoes.csv: Interconexões entre os equipamentos
  - localidades.csv: Dados geográficos dos sites (coordenadas e regiões)


⭐ LÓGICA DE CONSTRUÇÃO DA TOPOLOGIA:
-----------------------------------
A topologia segue um modelo hierárquico de 5 camadas, com regras específicas de distribuição geográfica e conectividade:

1. DISTRIBUIÇÃO GEOGRÁFICA:
   • Baseada em cidades reais do Brasil (priorizando capitais e PTTs)
   • Proporção regional:
        Norte: 8.3%    | Nordeste: 28.9%
        Centro-Oeste: 7.6% | Sudeste: 43.2% | Sul: 12.0%
        • Alterar proporção em config.json
   • Hierarquia regional com hubs estratégicos por macro-região

2. PROPORÇÃO DE EQUIPAMENTOS POR CAMADA:
   • RTIC (INNER-CORE): 2%    » Roteadores de núcleo
   • RTRR (REFLECTOR): 3%     » Roteadores refletores
   • RTPR (PEERING): 3%       » Roteadores de peering
   • RTED (EDGE): 12%         » Roteadores de borda
   • SWAC (METRO): 80%        » Switches de acesso
   • Alterar proporção em config.json

3. REGRAS DE CONECTIVIDADE:
   • RTICs: Formam anéis regionais + anel nacional principal
   • RTRRs: Conectados a 2 RTICs da mesma região
   • RTPRs: Conectados a 2 RTICs mais próximos
   • RTEDs: Operam em pares (mesma região) + conexões redundantes
   • SWACs: Organizados em anéis locais conectados a pares de RTEDs

## Fluxo do Programa

```mermaid
flowchart TD
    A([Início]) --> B[Ler Argumentos: -e, -c]
    B --> C{Arquivo config.json válido?}
    C -->|Sim| D[Carregar configurações]
    C -->|Não| E[ERRO: Finalizar script]
    D --> F[Calcular distribuição por camada]
    F --> G[Gerar elementos PTT]
    G --> H[Preparar lista de cidades]
    H --> I[Distribuir elementos por região]
    
    subgraph Distribuição por Camada
        I --> J[Gerar RTICs]
        I --> K[Gerar RTRRs]
        I --> L[Gerar RTPRs]
        I --> M[Gerar RTEDs em pares]
        I --> N[Gerar SWACs]
    end
    
    J --> O[Conexões RTICs]
    K --> P[Conexões RTRRs]
    L --> Q[Conexões RTPRs]
    M --> R[Conexões RTEDs]
    N --> S[Conexões SWACs]
    
    subgraph Gerar Conexões
        O -->|Anéis regionais| T
        O -->|Backbone nacional| T
        O -->|Redundância| T
        P -->|Para 2 RTICs| T
        Q -->|Para 2 RTICs| T
        R -->|Entre pares e RTICs| T
        S -->|Anéis metropolitanos| T
    end
    
    T[Gerar arquivos de saída] --> U[elementos.csv]
    T --> V[conexoes.csv]
    T --> W[localidades.csv]
    T --> X[resumo.txt]
    U --> Y[Pasta timestamp]
    V --> Y
    W --> Y
    X --> Y
    Y --> Z([Fim])
    
    style A fill:#2ecc71,stroke:#27ae60
    style E fill:#e74c3c,stroke:#c0392b
    style Z fill:#2ecc71,stroke:#27ae60
    style F fill:#3498db,stroke:#2980b9
    style G fill:#3498db,stroke:#2980b9
    style T fill:#9b59b6,stroke:#8e44ad
```
### **Passo a Passo Explicado**

#### **1. Inicialização e Configuração**
- **Argumentos de Linha de Comando**:
  - Recebe `-e` (quantidade de elementos) e `-c` (caminho do arquivo de configuração `config.json`).
  - Valida quantidade mínima de elementos (≥100).
- **Carregamento do Config**:
  - Lê `config.json` e normaliza estruturas de dados (listas → tuplas).
  - Extrai proporções de camadas, regiões geográficas, hierarquias, abreviações, PTTs e cidades.

#### **2. Pré-processamento de Dados**
- **Lista de Cidades**:
  - Compila todas as cidades por UF (incluindo PTTs).
  - Agrupa cidades por região geográfica (Norte, Nordeste, etc.).
- **Distribuição Proporcional**:
  - Calcula quantidades de elementos por camada (RTIC, RTRR, RTPR, RTED, SWAC) baseado nas proporções do `config.json`.
  - Ajusta arredondamentos para garantir total exato de elementos.
  - Garante número par de RTEDs (failover ativo-ativo).

#### **3. Geração de Elementos de Rede**
##### **a) Camada RTIC (Inner-Core)**
- **Priorização**: Hubs regionais definidos em `REGIOES_HIERARQUIA` (ex: São Paulo, Brasília).
- **Distribuição**:
  - 1 RTIC por hub obrigatório.
  - RTICs extras alocados em cidades com PTTs.
  - Balanceamento regional conforme `PROPORCOES_REGIAO`.

##### **b) Camada RTRR (Reflector)**
- **Priorização**: Sub-regiões definidas em `REGIOES_HIERARQUIA` (ex: Norte1, Sudeste2).
- **Distribuição**:
  - 1 RTRR por sub-região obrigatória.
  - RTRRs extras em cidades com PTTs.

##### **c) Camada RTPR (Peering)**
- **Priorização**: Cidades com PTTs (infraestrutura de IXPs).
- **Distribuição**: Proporcional à quantidade de elementos por região.

##### **d) Camada RTED (Edge)**
- **Formação de Pares**:
  - Cada par é composto por 2 RTEDs geograficamente próximos.
  - Distância calculada via `distancia_geografica()`.
- **Distribuição**: Proporcional por região.

##### **e) Camada SWAC (Metro)**
- **Organização**: Em anéis metropolitanos.
- **Distribuição**: Aleatória por região, respeitando proporções.

#### **4. Geração de Conexões**
##### **a) Conexões RTIC**
- **Anéis Regionais**: RTICs de uma mesma região conectados em anel.
- **Backbone Nacional**: Hubs principais de todas as regiões conectados em anel.
- **Redundância Inter-regiões**: Conexões extras entre RTICs de regiões vizinhas.

##### **b) Conexões RTRR → RTIC**
- Cada RTRR conectado a 2 RTICs da mesma região (ou mais próximos).

##### **c) Conexões RTPR → RTIC**
- Cada RTPR conectado aos 2 RTICs mais próximos.

##### **d) Conexões RTED**
- **Par RTED-RTED**: Conexão direta entre elementos do par.
- **RTED → RTIC**: Cada RTED conectado a um RTIC diferente.

##### **e) Conexões SWAC**
- **Anéis Metropolitanos**: SWACs de uma mesma cidade conectados em anel.
- **SWAC → RTED**: Extremidades do anel conectadas a um par de RTEDs próximo.

#### **5. Saída de Arquivos**
- **CSVs Gerados**:
  1. `elementos.csv`: Lista de equipamentos (siteid, camada, tipo, etc.).
  2. `conexoes.csv`: Interconexões entre equipamentos (ponta-a, ponta-b, tipo).
  3. `localidades.csv`: Dados geográficos (coordenadas em DMS).
- **Resumo Estatístico** (`resumo.txt`):
  - Distribuição de elementos por camada/região.
  - Quantidade de conexões por tipo.
  - Estados com maior presença.
- **Pasta de Saída**: Nomeada como `TOPOLOGIA_[QTD]_[TIMESTAMP]`.

#### **6. Tratamentos Especiais**
- **Normalização de Dados**:
  - Remoção de acentos e caracteres especiais nos CSVs.
  - Conversão de coordenadas decimais para DMS.
- **Balanceamento**:
  - Correção automática de diferenças por arredondamento.
  - Garantia de redundância (mínimo 2 RTICs por região).

---

### **Lógica Chave**
- **Hierarquia de 5 Camadas**:
  - RTIC (núcleo) → RTRR (refletores) → RTPR (peering) → RTED (borda) → SWAC (acesso).
- **Distribuição Geográfica**:
  - Baseada em cidades reais do Brasil (priorizando capitais e PTTs).
  - Proporções regionais ajustáveis via `config.json`.
- **Conectividade Redundante**:
  - Anéis (RTICs, SWACs), pares (RTEDs) e links redundantes (RTRR-RTIC, RTPR-RTIC).

### **Limitações**
- Quantidade mínima: **100 elementos**.
- Não considera topografia física (rios, montanhas).
- Não modela capacidade de enlaces.

Este fluxo garante a geração de topologias realistas, balanceadas e prontas para uso em ferramentas como o `GeradorTopologias` para visualização em `.drawio`.


📦 INSTALAÇÃO DE DEPENDÊNCIAS:
----------------------------

    # Windows
    Instalar Python 3 (Microsof Store):
      a. abra Microsoft Store no menu iniciar.
      b. pesquise "Python 3", escolher versão superior
      c. selecionar instalar.

	# Linux Debian:
    Instalar Python 3 (ou superior)
		apt update & apt install python3
    
🚀 COMO USAR:
------------
Formato básico:
  python GeradorBackbone.A1.01.py -e [QUANTIDADE_ELEMENTOS]

Exemplos:
  1. Topologia padrão (300 elementos):
     python GeradorBackbone.py
  
  2. Topologia personalizada (500 elementos):
     python GeradorBackbone.py -e 500

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

🚫 O QUE ESTE SCRIPT NÃO É:
--------------------------
  • Gerador de diagramas visuais (.drawio) » Use GeradorTopologias para isso
  • Simulador de tráfego ou desempenho
  • Ferramenta de planejamento de capacidade (bandwidth/links)
  • Validador de configurações de equipamentos
  • Gerador de políticas de segurança ou QoS

📌 EXEMPLO DE EXECUÇÃO:
----------------------
  python GeradorBackbone.py -e 400 -c meu_config.json

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

## Atualizações em https://github.com/flashbsb/Backbone-Network-Topology-Generator

## MIT License
https://raw.githubusercontent.com/flashbsb/Backbone-Network-Topology-Generator/refs/heads/main/LICENSE
