# Trabalho Prático de Integridade, Autenticação e Autorização

O trabalho consiste em desenvolver um *IdP* (*Identity Provider*) que suporte serviços com diferentes graus de criticidade e aplique *MFA* (*Multi-Factor Authentication*), de forma dinâmica, de acordo com os requisitos do serviço e o risco percebido pelo utilizador.

## Membros do Grupo

Este projeto foi desenvolvido por:

- Ana Vidal (118408)
- Simão Andrade (118345)

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