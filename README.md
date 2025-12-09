# 📘 Semeia Web — Plataforma de Gestão do Programa de Distribuição de Sementes (PADS)


Semeia Web é uma plataforma web voltada para modernizar o Programa de Aquisição e Distribuição de Sementes (PADS), integrando controle de estoque, logística, rastreabilidade e transparência pública.


Este sistema foi desenvolvido como Projeto Integrador (PI), aplicando conceitos de Análise e Desenvolvimento de Sistemas.

---

## 🚀 Objetivo

Criar uma plataforma digital capaz de:

- Otimizar o controle de estoque de sementes
- Acompanhar logística e entregas em tempo real
- Rastrear lotes através de códigos
- Aumentar a transparência pública
- Facilitar a comunicação entre gestores, armazéns e agentes de distribuição

---

## 📸 Tela Principal
<p align="center"><img width="1883" height="867" alt="Captura de tela 2025-12-08 213609" src="https://github.com/user-attachments/assets/f3699f23-e470-482f-b32c-457773855b09" width="700"> </p>

## 🚀 Equipe

- Arthur Vinícius
- Caio Sabino
- Marcos Vinicius
- Thauan Bezerra

---

## 🧩 Funcionalidades

### 🔹 Cadastros
- Espécies
- Fornecedores
- Armazéns
- Municípios
- Agricultores

### 🔹 Estoque
- Entrada e saída de lotes
- Transferências entre armazéns
- Saldo por lote e por armazém
- Bloqueio automático de saldo negativo

### 🔹 Logística
- Ordens de expedição
- Controle de datas previstas
- Upload de comprovantes

### 🔹 Entregas
- Registro detalhado por lote
- Associação do agricultor
- Comprovantes de entrega

### 🔹 Rastreabilidade
- Geração de QR Code por lote
- Histórico completo de movimentações

### 🔹 Painel Público (Transparência)
- Total distribuído por espécie
- Indicadores por município e período

### 🔹 Relatórios
- Por espécie, lote e período
- Divergências e inconsistências
- Produtividade operacional

---

## 👥 Perfis de Usuários

- **Gestor (Admin):** gerenciamento geral e indicadores
- **Operador de Armazém:** movimentações e expedições
- **Agente de Distribuição:** registro de entregas
- **Cooperativa:** pedido de sementes

---

## 🏗️ Stack Tecnológica

### **Front-end**
- React / Next.js  
- JavaScript  
- HTML / CSS  
- Bootstrap  

### **Back-end**
- Python
- Flask 
- JWT  

### **Banco de Dados**
- MySQL  
- Procedures  
- Views  
- Triggers  
- Transações  

### **Ferramentas**
- MySQL Workbench  
- Git / GitHub  
- Figma (protótipos)

---

## 📊 Modelagem e Regras de Negócio

- Modelo DER completo
- Triggers para evitar saldo negativo
- Procedures para expedições e entregas
- Auditoria de movimentações
- Autenticação com níveis de acesso

---

## 📦 Como Rodar o Projeto

### 🧩 Login
gerente@ipa.gov.br <br>
cooperativa@ipa.gov.br <br>
operador@ipa.gov.br <br>
agente@ipa.gov.br

1️⃣ Clonar o repositório
git clone https://github.com/usuario/projeto-distribuicao-sementes.git

2️⃣ Instalar dependências
pip install -r requirements.txt

3️⃣ Configurar banco de dados no arquivo banco.py
config = {
    "host": "localhost",
    "user": "root",
    "password": "sua_senha",
    "database": "distribuicao_sementes"}

4️⃣ Rodar o servidor
python app.py

5️⃣ Acessar no navegador
http://localhost:5000
