# Descrição do projeto

O trabalho consiste em desenvolver um IdP que suporte serviços com diferentes graus de criticidade e que aplique métodos de autenticação multi-fator, de forma dinâmica, conforme os requisitos do serviço e o risco percebido pelo utilizador. Pretende-se também abordar a questão da fadiga da autenticação multi-factor, adaptando o processo de autenticação de modo a manter o nível de segurança, sem sobrecarregar demasiado o utilizador.

O IdP apoiará a definição de serviços, que consistem em aplicações Web que utilizam o IdP para autenticar os seus utilizadores. Ao definir um serviço, deve ser definido um conjunto de políticas baseadas em aspetos como o risco, o tempo de sessão, a localização ou qualquer outra condicionante. Este conjunto de políticas irá influenciar como o IdP autentica efetivamente o utilizador em cada sessão.

Por exemplo, aplicações críticas podem implicar a necessidade de validação adicional por meio de MFA ou verificações de comportamento mais rigorosas. O IdP pode exigir mais autenticações se a pontuação de risco do utilizador for elevada ou estiver-se ativa uma pulverização de palavras-passe. Pode relaxar os requisitos de autenticação se a pontuação de risco do utilizador ou do serviço for baixa. Os métodos de autenticação utilizados também são flexíveis e definidos pelo IdP conforme o risco atual percebido. Os métodos implícitos, como o endereço IP, o agente do utilizador ou a hora do dia (para citar alguns), podem ser utilizados na avaliação do risco.

Os alunos devem definir um conjunto de métodos de autenticação, políticas e comportamentos plausíveis. Em seguida, deve ser apresentado um processo claro de autenticação baseado no risco, definindo os diferentes estados e como as ações observadas podem influenciar este processo.

É necessário integrar pelo menos três serviços. Podem reutilizar o mesmo código aplicacional, mas devem existir como três clientes diferentes. Terão políticas e perfis de risco diferentes, permitindo a validação de todo o processo.

Estes serviços terão alguns recursos que são protegidos, portanto, vinculados à autenticação e autorização. A abordagem de controlo de acesso deve considerar as funções na concessão de acesso aos recursos, com princípios de Bell-LaPadula e Biba. Um simples painel de mensagens mapeado para uma estrutura baseada em funções pode servir este objetivo.

A comunicação entre os serviços e o IdP deve ser efetuada via um fluxo OAuth2 adequado. Consoante o objetivo deste trabalho, o IdP deve utilizar os tokens de atualização para controlar finalmente a duração da sessão.

## Primeira entrega

Um relatório inicial, com um máximo de 10 páginas, deve ser fornecido com a arquitetura, a descrição dos serviços, os fluxos gerais de autenticação e autorização e o modelo geral de rastreio de riscos.

## Segunda entrega

Um relatório final, com um máximo de 30 páginas, que descreva o sistema implementado. Essa descrição deve incluir as estruturas de dados armazenadas, a estrutura das mensagens trocadas e os fluxos de mensagens, as interfaces utilizadas e os seus parâmetros, alguns pormenores de implementação relevantes (não cópias completas do código!), a abordagem de AMF e de rastreio do risco e os resultados obtidos.