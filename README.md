# Mentoria API

Backend FastAPI que sustenta a plataforma Mentoria. A versão atual da imagem publicada é **0.11** (`henriquefontaine/mentoria-api:0.11`) e a API pública está exposta em **`https://apicontroller.soumentoria.com`**.

## Sumário
- [Requisitos e variáveis](#requisitos-e-variáveis)
- [Execução local](#execução-local)
- [Execução via Docker](#execução-via-docker)
- [Rotas](#rotas)
  - [Healthcheck](#healthcheck)
  - [Autenticação](#autenticação)
  - [Professores](#professores)
  - [Alunos](#alunos)
  - [Questões](#questões)
- [Observações gerais](#observações-gerais)

---

## Requisitos e variáveis

| Variável                         | Descrição                                                                                          | Exemplo                                                                                               |
| -------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `MENTORIA_DATABASE_URL`          | URL completa do Postgres com driver psycopg2. **Obrigatória**.                                     | `postgresql+psycopg2://mentoria_admin:adminmentoria%402025@170.78.97.36:5464/mentoria`               |
| `MENTORIA_ACCESS_TOKEN_TTL_MINUTES` | Opcional. Tempo de expiração do token de sessão em minutos (padrão: 1440 = 24h).                    | `1440`                                                                                                |

**Banco utilizado:** PostgreSQL (schema criado automaticamente pelo SQLAlchemy no startup).

## Execução local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export MENTORIA_DATABASE_URL="postgresql+psycopg2://..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A documentação interativa (Swagger) fica disponível em `http://localhost:8000/docs`.

## Execução via Docker

```bash
docker run -d \
  --name mentoria-api \
  -e MENTORIA_DATABASE_URL="postgresql+psycopg2://..." \
  -p 8000:8000 \
  henriquefontaine/mentoria-api:0.11
```

Para o TrueNAS SCALE, utilize o Custom App apontando para a mesma imagem, exponha a porta 8000/TCP e injete `MENTORIA_DATABASE_URL` como variável de ambiente.

---

## Healthcheck

| Método | Caminho    | Autenticação | Descrição |
| ------ | ---------- | ------------ | --------- |
| GET    | `/health`  | Não          | Verifica se a API está ativa. |

**Resposta 200**
```json
{ "status": "ok" }
```

---

## Autenticação

### Login
- **Método/Caminho:** `POST /auth/login`
- **Autenticação:** Não
- **Descrição:** Valida credenciais de professor ou aluno e cria uma sessão com token.
- **Body JSON:**
  ```json
  {
    "email": "usuario@example.com",
    "password": "senha",
    "user_type": "teacher" | "student"
  }
  ```
- **Respostas:**
  - `200 OK` — retorna token, id do usuário, tipo e expiração.
  - `401 Unauthorized` — credenciais inválidas.

### Consultar sessão
- **Método/Caminho:** `GET /auth/session`
- **Autenticação:** Sim (Bearer token)
- **Descrição:** Retorna informações da sessão associada ao token.
- **Respostas:**
  - `200 OK` — dados da sessão (token, usuário, expiração).
  - `401 Unauthorized` — token ausente, inválido ou expirado.

---

## Professores

### Criar professor
- **Método/Caminho:** `POST /teachers`
- **Autenticação:** Não
- **Descrição:** Cadastra um novo professor e gera uma tag numérica única de 4 dígitos.
- **Body JSON:**
  ```json
  {
    "name": "Nome",
    "institution": "Instituição",
    "email": "prof@example.com",
    "password": "senha"
  }
  ```
- **Respostas:**
  - `201 Created` — dados do professor com `id` e `tag`.
  - `409 Conflict` — e-mail já cadastrado.

### Perfil do professor logado
- **Método/Caminho:** `GET /teachers/me`
- **Autenticação:** Sim (Bearer token de professor)
- **Descrição:** Retorna os dados do professor autenticado.
- **Respostas:**
  - `200 OK` — dados do professor.
  - `403 Forbidden` — token de aluno.
  - `404 Not Found` — professor desativado.

### Consultar tag própria
- **Método/Caminho:** `GET /teachers/me/tag`
- **Autenticação:** Sim (Bearer token de professor)
- **Descrição:** Obtém a tag numérica do professor autenticado.

### Listar alunos vinculados
- **Método/Caminho:** `GET /teachers/me/students`
- **Autenticação:** Sim (Bearer token de professor)
- **Descrição:** Retorna todos os alunos associados, incluindo contagem de respostas, acertos e erros.

### Respostas de um aluno específico
- **Método/Caminho:** `GET /teachers/students/{student_id}/answers`
- **Autenticação:** Sim (Bearer token de professor)
- **Descrição:** Exibe o histórico de respostas do aluno (questão, data, alternativa marcada e resultado).

### Desativar professor
- **Método/Caminho:** `DELETE /teachers/me`
- **Autenticação:** Sim (Bearer token de professor)
- **Descrição:** Marca o professor como inativo.
- **Respostas:**
  - `200 OK` — mensagem de sucesso.
  - `403 Forbidden` — token de aluno.
  - `404 Not Found` — professor já ausente/inativo.

---

## Alunos

### Auto cadastro com tag
- **Método/Caminho:** `POST /students/self-register`
- **Autenticação:** Não
- **Descrição:** Permite ao aluno criar conta vinculada a um professor existente via tag.
- **Body JSON:**
  ```json
  {
    "name": "Nome",
    "email": "aluno@example.com",
    "password": "senha",
    "teacher_tag": "1234"
  }
  ```
- **Respostas:**
  - `201 Created` — dados do aluno.
  - `404 Not Found` — tag inexistente ou professor inativo.
  - `409 Conflict` — e-mail de aluno já cadastrado.

### Cadastro de aluno pelo professor
- **Método/Caminho:** `POST /students`
- **Autenticação:** Sim (Bearer token de professor)
- **Descrição:** Professor cadastra aluno já vinculado a si.
- **Body JSON:** Igual ao auto cadastro, porém sem campo `teacher_tag`.
- **Respostas:**
  - `201 Created` — dados do aluno.
  - `409 Conflict` — e-mail já cadastrado.
  - `403 Forbidden` — token de aluno.

### Adicionar nova tag de professor
- **Método/Caminho:** `POST /students/me/tags`
- **Autenticação:** Sim (Bearer token de aluno)
- **Descrição:** Aluno vincula-se a um novo professor via tag.
- **Body JSON:**
  ```json
  { "teacher_tag": "1234" }
  ```
- **Respostas:**
  - `200 OK` — mensagem de sucesso.
  - `404 Not Found` — tag inexistente ou professor inativo.
  - `409 Conflict` — tag já vinculada ao aluno.

### Perfil do aluno logado
- **Método/Caminho:** `GET /students/me`
- **Autenticação:** Sim (Bearer token de aluno)
- **Descrição:** Retorna dados do aluno autenticado.
- **Respostas:**
  - `200 OK`
  - `403 Forbidden` — token de professor.
  - `404 Not Found` — aluno desativado.

---

## Questões

| Método | Caminho | Autenticação | Descrição |
| ------ | ------- | ------------ | --------- |
| GET | `/questions/random` | Aluno | Retorna uma questão aleatória com alternativas, texto renderizável em Markdown e links de anexos. |
| POST | `/questions/{question_id}/answer` | Aluno | Registra a resposta do aluno para a questão informada. Corpo: `{ "alternativa": "A" }`. Retorna se acertou e qual era a alternativa correta. |

A resposta é persistida na tabela `respondidas` junto ao `student_id`, `question_id`, alternativa selecionada e flag de acerto.

---

## Observações Gerais
- Tokens são retornados no login e devem ser enviados em `Authorization: Bearer <token>` para chamadas autenticadas.
- Todas as senhas são armazenadas com hash **bcrypt** (via `passlib` + `bcrypt==4.1.2`).
- Tags de professores possuem 4 dígitos e precisam ser informadas no auto cadastro dos alunos ou quando for adicionar um novo professor a um aluno existente.
- A API foi construída com FastAPI 0.111, SQLAlchemy 2.x e utiliza `psycopg2` para conectar ao Postgres.

