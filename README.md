# Desafio Técnico — Estágio Python (b2bflow)

Script que busca contatos cadastrados no Supabase e envia uma mensagem personalizada para cada um via WhatsApp, usando a Z-API.

## Como pensei a solução

A ideia era manter simples e direto, já que é um script utilitário e não uma aplicação grande: um único `main.py`, sem frameworks desnecessários, com responsabilidades bem separadas em funções pequenas (buscar contatos, enviar mensagem, validar ambiente). Preferi isso a over-engineering com classes e camadas que não agregariam nada num projeto desse tamanho.

Pontos que priorizei:

- **Falha rápido e com mensagem clara** se faltar alguma variável de ambiente — evita debugar erro genérico depois.
- **Um contato com problema não derruba os outros** — se um telefone estiver mal formatado, o script loga o erro e segue pros próximos.
- **Pequeno delay entre os envios** (`time.sleep(2)`) pra não estourar rate limit da Z-API.
- **Logs estruturados** em vez de `print()`, pra dar pra acompanhar o que está acontecendo (e debugar depois, se precisar).

## Stack

- Python 3.11+
- [Supabase](https://supabase.com/) — banco + API REST
- [Z-API](https://www.z-api.io/) — envio via WhatsApp

## Setup

### 1. Banco no Supabase

Cria a tabela:

```sql
create table contatos (
  id bigint generated always as identity primary key,
  nome_contato text not null,
  telefone text not null,
  created_at timestamp with time zone default now()
);
```

Libera leitura pública (necessário pra chave anon conseguir consultar):

```sql
alter table contatos enable row level security;

create policy "Permitir leitura publica"
on contatos
for select
to anon
using (true);
```

Insere os contatos de teste:

```sql
insert into contatos (nome_contato, telefone) values
('Nome 1', '55DDDNUMERO1'),
('Nome 2', '55DDDNUMERO2'),
('Nome 3', '55DDDNUMERO3');
```

Telefone sempre como DDI + DDD + número, só dígitos. Ex: `5511999999999`.

### 2. Variáveis de ambiente

Duplica o `.env.example`, renomeia pra `.env` e preenche:

```
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-publishable-aqui
ZAPI_INSTANCE_ID=seu-instance-id-aqui
ZAPI_TOKEN=seu-token-aqui
ZAPI_CLIENT_TOKEN=seu-client-token-de-seguranca-aqui
```

Onde pegar cada uma:

- `SUPABASE_URL` e `SUPABASE_KEY` → Project Settings → API Keys, no painel do Supabase
- `ZAPI_INSTANCE_ID` e `ZAPI_TOKEN` → tela da instância no painel da Z-API
- `ZAPI_CLIENT_TOKEN` → aba Segurança do painel da Z-API (a API exige esse header em toda chamada, mesmo aparecendo como "opcional" na tela)

O `.env` não vai pro repositório (está no `.gitignore`).

### 3. Rodando localmente

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
python main.py
```

## O que o script faz, na prática

1. Confere se todas as variáveis de ambiente estão setadas — se faltar alguma, para na hora com uma mensagem dizendo qual.
2. Busca até 3 contatos na tabela `contatos`.
3. Monta a mensagem `Olá, <nome> tudo bem com você?` pra cada um.
4. Dispara via Z-API.
5. Loga sucesso ou erro de cada envio, e no final mostra um resumo (quantos deram certo, quantos falharam).

## Erros que tratei

- Variável de ambiente faltando → para a execução antes de tentar conectar em qualquer serviço.
- Contato sem nome ou telefone no banco → pula esse contato, loga aviso, continua pros outros.
- Falha na chamada da Z-API (timeout, 400, etc) → captura a exceção, loga o detalhe retornado pela API, não derruba o script.

## Possíveis melhorias (se fosse pra produção)

- Retry com backoff pra falhas temporárias de rede.
- Mover o limite de 3 contatos pra variável de ambiente, em vez de hardcoded.
- Validar formato do telefone antes de tentar enviar (hoje só falha quando a Z-API rejeita).

---

Kauã da Silva Gonçalves — desafio técnico para Estágio em Desenvolvimento Python, b2bflow.
