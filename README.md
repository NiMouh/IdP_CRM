# Trabalho Prático de Integridade, Autenticação e Autorização

O trabalho consiste em desenvolver um *IdP* (*Identity Provider*) que suporte serviços com diferentes graus de criticidade e aplique *MFA* (*Multi-Factor Authentication*), de forma dinâmica, de acordo com os requisitos do serviço e o risco percebido pelo utilizador.

## Membros do Grupo

Este projeto foi desenvolvido por:

- Ana Vidal (118408)
- Simão Andrade (118345)

## Estrutura do Projeto

As diretorias do projeto estão organizadas da seguinte forma:

```
project/ --> Diretoria principal
│
├── frontend/ --> Diretoria das aplicações cliente
│   ├── client1/
│   ├── client2/
│   └── client3/
│
├── backend/ --> Diretoria das aplicações servidor
│   ├── database/
│   │    ├── db_script.py --> *Script* para criar as tabelas da base de dados
│   │    └── database.sql
│   ├── authorization_server.py
│   └── resource_server.py
│
└── requirements.txt
```


## Dependências

Para criar o *environment*, correr o seguinte comando:

```bash
$ python -m venv venv
```

Para ativar o *environment*, correr o seguinte comando:

```bash
$ venv\Scripts\activate
```

Para instalar as dependências necessárias para correr o projeto, basta correr o seguinte comando:

```bash
$ pip install -r requirements.txt
```

Para adicionar as tabelas à base de dados, correr o seguinte *script* `db_script.sql`:

```bash
$ python db_script.py
```

> [!IMPORTANT]
> De modo aos caminhos da base de dados estarem corretos, é necessário que o *script* seja corrido na pasta onde se encontra a aplicação (pois o código é interpretado relativamente ao local onde se encontra).

## Segurança

Para a geração de assinaturas de *tokens* JWT, é usado um par de chaves RSA. Para gerar as chaves, correr o *script* `generate_rsa.bash` na diretoria `backend/keys` do seguinte modo:

```bash
$ bash generate_rsa.bash
```

> [!IMPORTANT]
> Quando utilizar a aplicação, é necessário gerar um novo par de chaves RSA, de modo a não comprometer a segurança da aplicação.


## Divisão de Tarefas

- Desenvolvimento do Resource Server (Simão Andrade):
  - [x] Criação da estrutura da base de dados;
  - [x] Criação de funções que gerem aleatoriamente os dados da base de dados;
  - [x] Chamadas à base dados para o *backend*;
  - [x] Validação dos *tokens* de acesso;
  - [x] Controlo de acessos;
  - [x] Implementação de um sistema de logs;
  - [x] Validação e sanitização dos dados inseridos pelo utilizador;
- Desenvolvimento do IdP (Simão Andrade e Ana Vidal):
  - [x] Desenvolvimento do *backend*;
  - [x] Desenvolvimento do *frontend* (design e interação com o utilizador);
  - [x] Implementação de MFAs (excluindo o *smartcard*);
  - [x] Implementação de um sistema de logs;
  - [x] Gestão de *tokens* e *sessões*;
  - [x] Definição do cálculo do risco;
  - [x] Proteção contra erros de CSRF (*Cross-Site Request Forgery*);
  - [x] Validação e sanitização dos dados inseridos pelo utilizador;
  - [ ] Implementação de autenticação por *smartcard*;
- Desenvolvimento dos três Client Applications (Ana Vidal):
  - [x] Implementação do *authentication code flow* do lado do cliente;
  - [x] Implementação do *frontend* (design e interação com o utilizador);
  - [x] Validação e sanitização dos dados inseridos pelo utilizador;
- Testes à aplicação feita (Ana Vidal e Simão Andrade):
  - [x] Testes de validação;
  - [x] Testes de stress;
  - [x] Testes com risco alto;
- Relatório Final (Ana Vidal e Simão Andrade):
  - [x] Descrição das estruturas de dados armazenadas;
  - [x] Estrutura das mensagens trocadas e fluxos de mensagens;
  - [x] Abordagem MFA e gestão de riscos;
  - [ ] Interfaces utilizadas e os seus parâmetros;
  - [x] Alguns detalhes de implementação relevantes;
  - [x] Resultados obtidos; 
- Extra:
  - [ ] Documentação do projeto;
