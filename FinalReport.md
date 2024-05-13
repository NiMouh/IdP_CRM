# Implementação - Projeto de Integridade, Autenticação e Autorização

## Grupo

- Ana Vidal (118408)
- Simão Andrade (118345)

## Divisão de Tarefas

- Desenvolvimento do Resource Server (Simão Andrade):
  - [x] Criação da estrutura da base de dados;
  - [ ] Criação de funções que gerem aleatoriamente os dados da base de dados (Não quero fazer esta porra);
  - [ ] Implementação de um sistema de logs;
  - [ ] Validação e sanitização dos dados inseridos pelo utilizador;
  - [ ] Chamadas à base dados para o *backend*;
- Desenvolvimento do IdP (Simão Andrade e Ana Vidal):
  - [ ] Desenvolvimento do *backend*;
  - [ ] Desenvolvimento do *frontend* (design e interação com o utilizador);
  - [ ] Implementação de MFAs;
  - [ ] Implementação de um sistema de logs;
  - [ ] Gestão de *tokens* e *sessões*;
  - [ ] Definição do cálculo do risco;
  - [ ] Implementação do sistema RBAC;
- Desenvolvimento dos três Client Applications (Ana Vidal):
  - [ ] Implementação do *frontend* (design e interação com o utilizador);
  - [ ] Validação e sanitização dos dados inseridos pelo utilizador;
- Testes à aplicação feita (Ana Vidal e Simão Andrade):
  - [ ] Testes de validação;
  - [ ] Testes de stress;
  - [ ] Testes com risco alto;
- Relatório Final (Ana Vidal e Simão Andrade):
  - [ ] Descrição das estruturas de dados armazenadas;
  - [ ] Estrutura das mensagens trocadas e fluxos de mensagens;
  - [ ] Interfaces utilizadas e os seus parâmetros;
  - [ ] Alguns detalhes de implementação relevantes;
  - [ ] Abordagem MFA e gestão de riscos;
  - [ ] Resultados obtidos; 
- Extra:
  - [ ] Documentação do projeto;

## Implementação

<p align="center">
  <img src="img/Implementacao_Diagrama.png" width="600" title="Implementação">
</p>
<p align="center">
  <i>Figura 1 - Diagrama de Implementação</i>
</p>