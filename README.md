# MyGames Admin - Painel de Gestão e Backoffice

## Descrição
Painel administrativo central para a triagem, gestão de lotes e controle de produtos do sistema MyGames.

## Pré-requisitos
- Python 3.x
- Acesso ao banco de dados MySQL
- Arquivo `.env` com as variáveis de ambiente (será fornecido separadamente para a equipe de instalação).

---

## Como Instalar e Rodar no Servidor

### 1. Clonar o Repositório
```bash
git clone [https://github.com/avernax-droid/MyGames_Admin.git](https://github.com/avernax-droid/MyGames_Admin.git)
cd MyGames_Admin

2. Configuração do Banco de Dados (Produção)
Para garantir a integridade relacional do sistema, a importação dos scripts SQL deve seguir estritamente a ordem abaixo no banco de dados de produção (ex: mygames_prod).

   Passo 2.1: Estrutura Base
      Executar o arquivo responsável por criar as tabelas, chaves estrangeiras e o usuário administrador inicial.
         mysql -u mygames_user -p mygames_prod < schema.sql

   Passo 2.2: Carga de Parametrização
      Executar o arquivo que injeta os dados de configurações e regras de negócio (Catálogo de Jogos, Regiões de Atendimento, Fatores de Perícia, etc.).
         mysql -u mygames_user -p mygames_prod < carga_configs.sql

   Passo 2.3: Validação (Opcional)
      Acesse o MySQL e rode a query abaixo. Se retornar um número maior que zero, a carga inicial foi um sucesso: 
         SELECT count(*) FROM mygames_prod.catalogo_mestre;     
