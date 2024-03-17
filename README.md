# Projeto IAA

O trabalho consiste em desenvolver um IdP (*Identity Provider*) que suporte serviços com diferentes graus de criticidade e aplique MFA, de forma dinâmica, de acordo com os requisitos do serviço e o risco percebido pelo utilizador.

## Descrição de Serviços

O sistema CRM desenvolvido para a Teka Telecomunicações é uma ferramenta abrangente projetada para gestão todas as facetas dos projetos e atividades de negócios relacionados. 

Uma característica fundamental é a capacidade de gestão um repositório de projetos, fornecendo informações detalhadas sobre cada obra, incluindo dados sobre stakeholder's, contactos com clientes diretos e indiretos (prospect's) que solicitam cotações diretamente à Teka Telecomunicações e os materiais necessários para a execução de cada projeto. Além disso, o sistema mantém informações de gestão de clientes, como endereços das sedes e filiais dos clientes.

Além disso, o sistema possui outros componentes de grande relevância como o planeamento, execução e relatório de atividades destinadas a capturar negócios relacionados com os projetos. Isso permite uma abordagem estruturada para angariar e gestão negócios, garantindo que todas as etapas do processo sejam registadas e acompanhadas de forma eficiente.

## Arquitetura

### Linguagens e Ferramentas

1. Linguagens de programação:
   - [JavaScript](https://developer.mozilla.org/pt-BR/docs/Web/JavaScript)
   - [React](https://reactjs.org/)
2. Base de dados:
   - [PL/SQL](https://www.oracle.com/database/)
3. Frameworks:
   - [OAuth2](https://oauth.net/2/)

### Entidades e relações

Atores:
- Diretor da Obra
- Vendedor
- Técnico de Telecomunicações
- Fornecedor
- Trabalhador de Fábrica

### Diagrama de Sequencial (Feito p/ Ana)

<p align="center">
  <img src="Diagrama_CRM_IAA.png" alt="Diagrama Sequencial CRM" width="500"/>
</p>

### Diagrama de Casos de Uso (2 casos de uso p/ Ana Vidal, 2 casos de uso p/ Simão Andrade)

### Modelo Hierárquico dos Utilizadores (Simão Andrade)

### Controlo de Acesso

#### Níveis de Acesso

Com base nas funções desempenhadas pelos utilizadores do sistema e sensibilidade dos recursos acedidos, foi desenvolvida a seguinte hierarquia de acesso:

<p align="center">
  <img src="Hierarquia_CRM.png" alt="Hierarquia dos Utilizadores" width="700"/>
</p>

Sendo, o **Nível 3** o acesso **mais restrito** e o **Nível 1** o acesso **mais permissivo**.

#### Mapeamento de recursos

Para a implementação do controlo de acesso, foi feito um mapeamento das funções dos utilizadores para os recursos do sistema. 

Com isto, foi definida a seguinte estrutura baseada:

| Acessos                         | Vendedor | Dir. da Obra | Fornecedor | Tec. Telecom | Trab. de Fábrica |
| ------------------------------- | -------- | ------------ | ---------- | ------------ | ---------------- |
| Morada e contactos dos Clientes | Sim      | Sim          | Não        | Não          | Não              |
| Contactos do diretor da obra    | Sim      | -            | Sim        | Não          | Não              |
| Morada da obra                  | Sim      | Sim          | Não        | Não          | Não              |
| Material da obra                | Sim      | Sim          | Sim        | Sim          | Sim              |
| Material em stock               | Não      | Não          | Sim        | Não          | Sim              |
| Tabela de preços                | Sim      | Sim          | Sim        | Não          | Não              |
| Escalão de desconto             | Sim      | Não          | Sim        | Não          | Não              |
| Status da obra                  | Sim      | Sim          | Não        | Não          | Não              |

## *Authentication* e *Authorization flow* (Por analisar p/ Simão Andrade)

A framework OAuth 2.0 diversos modos de obter tokens de acesso e como estes são geridos no processo de autenticação. A escolha do fluxo de autenticação depende do tipo de aplicação, nível de confiança com a aplicação cliente e a fadiga do utilizador.

Para obter uma melhor resposta a qual *flow* de autenticação usar, foram feitas as seguintes questões:

### A aplicação cliente é uma *Single-Page App*?

Dada a abundância de dados envolvidos, o sistema foi desenvolvido como uma *Multi-page App*. Isso garante que a complexidade de desenvolvimento seja mantida baixa, enquanto proporciona um tempo de carregamento inicial rápido. Isso significa que os utilizadores podem acessar informações de maneira mais imediata, sem sacrificar a eficiência ou a usabilidade do sistema.

### A aplicação cliente é o *Resource Owner*?

Como a solução da aplicação cliente é uma aplicação *web*, a abordagem onde o *Resource Owner* é o *Client* não é a mais adequada. Isso porque a aplicação cliente não é confiável com as credenciais do utilizador, podendo trazer riscos de segurança.

### A aplicação cliente é um *Web Server*?

Sim, a aplicação cliente é um *Web Server*.

### A aplicação cliente precisa de comunicar com *Resource Servers* diferentes?

Não, a aplicação cliente apenas precisa de comunicar com o *Resource Server* da Teka Telecomunicações.

Dados os requisitos do sistema e feita a análise das questões acima, o *flow* de autenticação escolhido foi o *Authorization Code*.

### Diagrama de *Authorization Code* (Simão Andrade)

## Modelo de gestão de risco

Durante o processo de autenticação, o IdP avalia o risco percebido pelo utilizador e o serviço que está a ser acedido.

### Identificação de riscos (por analisar (Ana Vidal))

Para a identificação dos riscos associados ao sistema, foi feita uma enumeração das possíveis ameaças e vulnerabilidades que podem afetar a segurança do sistema.

Ameaças:
1. Corrupção/Perda de dados associados a projetos e clientes;
2. Controlo de acesso quebrado;
3. Disponibilidade do sistema ser comprometida;
4. Acesso não autorizado a dados sensíveis;
5. Ataques de *phishing* (roubo de credenciais);
6. Ataques de *spoofing* (falsificação de identidade);

Vulnerabilidades:
1. Registo de atividades não monitorizado (logs);
2. Regras de controlo de acesso mal definidas;
3. *Password Spraying* (ataque de força bruta);
4. *Cross-site scripting* (XSS);
5. Ataques de *SQL injection*;
6. Ataques de *DDoS* (negação de serviço distribuída);
7. Ataques de *Broken Authentication*;



### Análise/Avaliação de riscos (Fiz as tabelas, mas falta a análise (Ana Vidal))

A partir desta enumeração, foi feita uma análise de risco para determinar a probabilidade de ocorrência e o impacto de cada risco identificado. 

A análise de risco foi feita com base numa análise quantitativa, onde:

| Probabilidade/Impacto | Muito Baixo | Baixo | Médio | Alto | Muito Alto |
| --------------------- | ----------- | ----- | ----- | ---- | ---------- |
| Improvável            | 1           | 2     | 3     | 4    | 5          |
| Pouco provável        | 2           | 4     | 6     | 8    | 10         |
| Provável              | 3           | 6     | 9     | 12   | 15         |
| Bastante provável     | 4           | 8     | 12    | 16   | 20         |
| Muito provável        | 5           | 10    | 15    | 20   | 25         |

Onde a probabilidade representa:

| Nível de probabilidade | Descrição         | Número médio de Ocorrências |
| ---------------------- | ----------------- | --------------------------- |
| Nível 1                | Improvável        | 0-1                         |
| Nível 2                | Pouco provável    | 1-2                         |
| Nível 3                | Provável          | 2-3                         |
| Nível 4                | Bastante provável | 3-4                         |
| Nível 5                | Muito provável    | 4+                          |

E o impacto representa:

| Nível de impacto | Impacto     | Descrição do impacto            |
| ---------------- | ----------- | ------------------------------- |
| Nível 1          | Muito Baixo | Um posto de trabalho parado     |
| Nível 2          | Baixo       | Um sistema/processo parado      |
| Nível 3          | Médio       | Um departamento parado          |
| Nível 4          | Alto        | Mais que um departamento parado |
| Nível 5          | Muito Alto  | A empresa parada                |


Obtendo-se a seguinte matriz de risco:

| Risco = f(Ameaça, Vulnerabilidade)                                          | Probabilidade | Impacto | Valor do Risco = (P * I) |
| --------------------------------------------------------------------------- | ------------- | ------- | ------------------------ |
| Comprometimento de dados sensíveis causados por *phishing*                  | -             | -       | -                        |
| Acesso de colaborados a documentos sensíveis, por privilégios mal definidos | -             | -       | -                        |
| Disponibilidade do sistema comprometida por *DDoS*                          | -             | -       | -                        |
| Acesso não autorizado a dados sensíveis, causado por *SQL injection*        | -             | -       | -                        |
| Manipulação de dados sensíveis por *Cross-site scripting*                   | -             | -       | -                        |

### Identificação de controlos a implementar (Simão Andrade)

Com base nos riscos anteriormente enumerados, foram identificados os controlos a implementar para mitigar os mesmos. 

A presente tabela, mostra os controlos identificados junto do novo valor do risco:

| Risco = f(Ameaça, Vulnerabilidade)                                          | Probabilidade(2) | Impacto(2) | Controlo a implementar | Novo Valor do Risco |
| --------------------------------------------------------------------------- | ---------------- | ---------- | ---------------------- | ------------------- |
| Comprometimento de dados sensíveis causados por *phishing*                  | -                | -          | -                      | -                   |
| Acesso de colaborados a documentos sensíveis, por privilégios mal definidos | -                | -          | -                      | -                   |
| Disponibilidade do sistema comprometida por *DDoS*                          | -                | -          | -                      | -                   |
| Acesso não autorizado a dados sensíveis, causado por *SQL injection*        | -                | -          | -                      | -                   |
| Manipulação de dados sensíveis por *Cross-site scripting*                   | -                | -          | -                      | -                   |


### Pontuação de risco (Ana Vidal)
