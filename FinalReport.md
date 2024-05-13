# Implementação - Projeto de Integridade, Autenticação e Autorização

## Grupo

- Ana Vidal (118408)
- Simão Andrade (118345)

## Divisão de Tarefas

- Desenvolvimento do Resource Server:
  - [ ] Criação da estrutura da base de dados;
  - [ ] Criação de funções que gerem aleatoriamente os dados da base de dados;
  - [ ] Chamadas à base dados para o *backend*; 
- Desenvolvimento do Authorization Server:
  - [ ] Implementação do *backend*;
  - [ ] Implementação do cálculo do risco;
  - [ ] Implementação do sistema RBAC;
- Desenvolvimento do IdP:
  - [ ] Desenvolvimento do *frontend* (design e interação com o utilizador); 
  - [ ] Validação e sanitização dos dados inseridos pelo utilizador;
  - [ ] Gestão de *tokens* e *sessões*;
- Testes à aplicação feita:
  - [ ] Testes de validação;
  - [ ] Testes de stress;
  - [ ] Testes com risco alto;
- Relatório Final:
  - [ ] Documentação do projeto;
  - [ ] Descrição do desenvolvimento do projeto;
  - [ ] Análise dos resultados obtidos;

A final report, with no more than 30 pages, describing the system implemented. Such description must include the data structures stored, the structure of the messages exchanged and the message flows, the interfaces used and their parameters, some relevant implementation details (not complete copies of the code!), the MFA and risk tracking approach, and the results achieved.