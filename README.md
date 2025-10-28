# 🌱 Semeia Web: Gestão Inteligente para Distribuição de Sementes

<p align="center">
  <img src="https://raw.githubusercontent.com/thauan-rgb/projeto-distribuicao-de-sementes/main/Projeto_PI_Sementes/img/logo2.png" alt="Logo Semeia Web" width="100"/>
</p>

## 🚀 Introdução e Propósito do Projeto

Este projeto, intitulado **Semeia Web**, foi desenvolvido como parte de um Projeto Integrador (PI) com o objetivo de **projetar e validar um sistema web completo para a gestão do Programa de Aquisição e Distribuição de Sementes**.

O propósito central é modernizar a logística e garantir a transparência de um programa governamental crucial, focando na integração de:
* **Controle de Estoque e Logística:** Otimizando a entrada, movimentação e expedição de lotes.
* **Rastreabilidade:** Fornecendo um histórico completo e imutável de cada lote.
* **Transparência Pública:** Apresentando os resultados agregados de forma clara ao cidadão.

## 💻 Stack Tecnológica (Requisitos do Edital)

O projeto segue os requisitos de arquitetura estabelecidos no edital:

| Componente | Tecnologia Principal | Requisito Específico |
| :--- | :--- | :--- |
| **Front-end** | HTML, CSS, TypeScript e **React/Next.js** | Deve ser Web Responsivo (Desktop e Celular). |
| **Back-end** | **Java (Spring Boot)** | Implementação de uma **API REST** para todas as operações (lotes, expedições, entregas). |
| **Banco de Dados** | **MySQL** | Uso de **triggers** (ex: impedir saldo negativo), **transações** (expedições/entregas) e **integridade referencial**. |
| **Segurança** | Autenticação própria com senhas hasheadas e perfis de acesso. | Segurança mínima esperada: autenticação própria com senhas hasheadas e perfis de acesso (sem integrações externas). |

## ✨ Módulos e Funcionalidades do MVP (Protótipo Implementado)

O protótipo **Semeia Web** cobre as principais áreas definidas no escopo do MVP:

### 1. Gestão de Estoque e Cadastros (`estoque.html`)
O sistema gerencia o estoque detalhado por armazém e lote.

* **Cadastro de Remessa:** Interface para o Operador de Armazém registrar novas entradas, incluindo Fornecedor, Tipo de Semente, **Número do Lote**, Data de Recebimento, Quantidade (kg) e **Armazém Vinculado**.
* **Controle de Saldo:** A arquitetura prevê o uso de `triggers` no banco de dados para impedir o registro de saldo negativo e auditar movimentações, garantindo a integridade dos dados.

### 2. Logística e Distribuição (`distribuicao.html`, `distribuicao2.html`)
Focado na criação e acompanhamento das ordens de expedição.

* **Planejamento de Entregas:** Interface para criação de ordens de expedição, definindo o Município de destino, a Quantidade (kg) e o **Motorista Responsável**.
* **Status e Rastreamento:** A tela de status (simulada com mapa) permite visualizar a rota e o andamento da entrega, com a opção de gerar o Documento de Transporte.

### 3. Rastreabilidade e Transparência
Embora a implementação completa do QR Code seja dependente do back-end, o conceito é central: ao ler o QR Code, o sistema deve exibir o histórico completo do lote, desde a entrada até a entrega final ao agricultor.

* **Painel Público:** O projeto exige um painel sem login (`index.html` menciona "Transparência Pública Imediata") que mostre números agregados como total distribuído por espécie, por município e por período.

### 4. Relatórios Gerenciais (`relatorios.html`)
O módulo de Relatórios permite a geração de análises cruciais para a gestão do programa.

O protótipo inclui telas dedicadas para os seguintes relatórios:
* **Entregas por Município**: Visualiza o volume (kg) distribuído por localidade, utilizando gráficos e tabelas.
* **Entregas por Espécie**: Distribuição percentual do volume por tipo de semente (ex: Milho, Feijão).
* **Produtividade (Entregas por Dia)**: Acompanhamento da eficiência logística por meio de gráficos de tendência (linhas).
* **Divergências de Estoque**: Lista de problemas como saldo divergente (Sistema vs. Físico), crucial para a auditoria.

## 👥 Perfis de Acesso

O sistema é construído com base em perfis de acesso rigorosos, garantindo que cada usuário tenha apenas as permissões necessárias para sua função. O módulo de Usuários permite a gestão dessas permissões.

| Perfil | Função Principal | Módulos Principais |
| :--- | :--- | :--- |
| **Gestor (Admin)** | Configura cadastros e acompanha indicadores. | Dashboard (Alertas, Panorama), Relatórios, Configurações, Usuários. |
| **Operador de Armazém** | Registra entradas e expedições de lotes. | Estoque (Cadastro de Remessa). |
| **Agente de Distribuição** | Registra as entregas efetivas aos agricultores. | Logística (Registro de Entrega). |
| **Cidadão** | Acesso somente leitura ao painel de transparência. | Painel Público (`/index.html` - Transparência). |

## ⚙️ Configurações e Comunicação
O módulo de Configurações, exclusivo para perfis administrativos, não só permite ajustes sistêmicos (Notificações, Integrações, Idiomas) mas também possui uma ferramenta vital para a gestão:
* **Comunicação Interna:** Permite que o Gestor publique comunicados com prioridade (Alta, Média, Baixa) e defina o público-alvo (Gerentes, Administradores, Armazém), garantindo a comunicação eficiente sobre novas regras ou alertas.

---

## 🛠️ Como Rodar o Protótipo (Apenas Frontend)

As telas do protótipo são construídas em HTML, CSS (com Bootstrap) e JavaScript puro para simular a experiência do usuário.

1.  **Clone o repositório:**
    ```bash
    git clone [https://docs.github.com/pt/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github](https://docs.github.com/pt/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)
    cd Projeto-Distribuição-de-Sementes
    ```
2.  **Abra as Telas:** Navegue até a pasta `Projeto_PI_Sementes` e abra qualquer arquivo `.html` (por exemplo, `login.html`, `dashboard_gerente.html`) diretamente no seu navegador.
3.  **Simulação de Login:** A página `login.html` utiliza um script simples para simular o acesso com base no e-mail:
    * Para acessar o Dashboard do Gestor: use o e-mail `gerente@ipa.gov.br`.

## 📜 Licença

Este projeto está sob a licença **MIT** [cite: uploaded:thauan-rgb/projeto-distribuicao-de-sementes/Projeto-Distribuicao-de-Sementes-11aa7c4dad41ddbd86b13c6bf041ce
