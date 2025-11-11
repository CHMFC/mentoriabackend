# Mentoria API — Endpoints

## Sumário
- [Healthcheck](#healthcheck)
- [Autenticação](#autenticação)
- [Professores](#professores)
- [Alunos](#alunos)

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

## Observações Gerais
- Tokens são retornados no login e devem ser enviados em `Authorization: Bearer <token>` para chamadas autenticadas.
- Todas as senhas são armazenadas com hash bcrypt.
- Tags de professores possuem 4 dígitos e precisam ser informadas para auto cadastro de alunos ou vínculo posterior.

