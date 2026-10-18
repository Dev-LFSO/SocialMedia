# TODO — Diagnóstico e plano de evolução do SocialMedia

Este documento registra o estado observado no repositório e organiza as melhorias recomendadas por prioridade. Marque cada item como concluído somente depois de implementar a mudança e validar seu comportamento com testes.

## Prioridades

- **P0 — Crítico:** corrigir antes de expor ou manter a aplicação em produção.
- **P1 — Alto:** reduzir riscos relevantes de segurança, indisponibilidade ou perda de dados.
- **P2 — Médio:** melhorar desempenho, confiabilidade e manutenção.
- **P3 — Baixo:** corrigir documentação, consistência e melhorias evolutivas.

---

## P0 — Segurança e confiabilidade de produção

- [ ] **Validar redirecionamentos pós-login e logout.** Não redirecionar diretamente para `next` nem para `HTTP_REFERER` sem validar que o destino é local/permitido. Cobrir URLs externas e destinos malformados com testes.
- [ ] **Usar métodos HTTP adequados para ações com efeito colateral.** Converter logout e início de conversa em operações POST protegidas por CSRF, ou documentar e testar uma alternativa segura; GET deve permanecer sem mutações.
- [ ] **Definir uma política de HTTPS e cookies por ambiente.** Configurar, conforme a infraestrutura real, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` e as opções de proxy. Confirmar que o proxy remove/substitui headers encaminhados pelo cliente antes de confiar em `SECURE_PROXY_SSL_HEADER`.
- [ ] **Zerar os alertas de segurança de produção do Django.** `manage.py check --deploy` sinalizou ausência de HSTS, redirecionamento HTTPS e cookies seguros. Reexecutar o check com uma `SECRET_KEY` longa e aleatória fornecida pelo ambiente; a chave temporária usada na auditoria também gera o alerta de tamanho e não representa a chave real de produção.
- [ ] **Validar a configuração de produção na inicialização/deploy.** Exigir `SECRET_KEY`, `ALLOWED_HOSTS` e credenciais necessárias; falhar com mensagem clara quando estiverem ausentes. Manter `DEBUG=False` em produção e documentar valores esperados sem registrar segredos.
- [ ] **Tornar erros de views explícitos.** Remover `except Exception` que apenas registra e retorna `None`; tratar erros esperados e deixar exceções inesperadas chegarem ao handler 500, com resposta HTTP coerente e log com stack trace.
- [ ] **Evitar falha de registro por indisponibilidade do serviço de e-mail.** Substituir threads iniciadas por requisição por envio assíncrono confiável ou estratégia documentada de retry; informar falha de forma observável e permitir reenvio sem criar contas duplicadas.
- [ ] **Garantir que mensagens só sejam consideradas enviadas quando o provedor confirmar.** As implementações de redefinição de senha e confirmação de e-mail atualmente absorvem falhas e podem dar aparência de sucesso. Unificar provider, variáveis de ambiente, timeout e tratamento de erros.

## P1 — Segurança de uploads, privacidade e abuso

- [ ] **Corrigir XSS armazenado na busca de usuários do chat.** `chat/templates/chat.html` insere `name`, `username` e `avatar` recebidos de `search_user` diretamente em strings HTML e depois usa `.append()`. Criar os elementos DOM e preencher conteúdo/atributos por APIs seguras, validando URLs; adicionar teste com nome contendo markup.
- [ ] **Validar conteúdo real dos uploads.** Não confiar apenas em extensão e `content_type` enviado pelo cliente. Decodificar imagens, conferir o formato detectado, tratar arquivos corrompidos e limitar dimensões/pixels para reduzir risco de arquivo disfarçado e decompression bomb.
- [ ] **Revisar limites e entrega de anexos de chat.** Aplicar limite de tamanho também no servidor/proxy, alinhar os MIME types aceitos com os formatos realmente processados e verificar se os arquivos no Cloudinary são servidos com política segura de conteúdo e acesso adequada.
- [ ] **Adicionar limites de abuso para operações mutáveis.** Aplicar rate limiting coerente para comentários, reações, seguir usuários, envio de mensagens e buscas; usar cache compartilhado em produção para que os limites persistam entre workers.
- [ ] **Restringir e auditar dados pessoais.** Confirmar quais campos de perfil devem ser públicos, privados e editáveis; corrigir a condição de exibição de e-mail no perfil e documentar a política para CPF, localização e dados de contato.
- [ ] **Proteger a integridade das conversas individuais.** Garantir que uma conversa individual só exista uma vez por par de participantes, inclusive com requisições concorrentes, e impedir que conversas com mais participantes sejam reutilizadas por `start_chat`.
- [ ] **Rever a exclusão de conversas.** A exclusão atual apaga a conversa e seu histórico para todos os participantes. Definir e testar se a ação deve apagar globalmente ou apenas ocultar a conversa para quem solicitou.
- [ ] **Evitar armazenar e exibir identificadores sensíveis em logs.** Reduzir logs de e-mail, resposta completa de provedores e dados pessoais; usar `logger.exception` para falhas inesperadas sem incluir tokens, chaves ou conteúdo privado.

## P2 — Desempenho e banco de dados

- [ ] **Reduzir consultas e memória na tela de chat.** A listagem pré-carrega mensagens de todas as conversas para descobrir a última mensagem, e a conversa ativa carrega todo o histórico. Buscar a última mensagem por consulta eficiente e paginar/carregar mensagens sob demanda.
- [ ] **Paginar o perfil público.** `get_user` passa todos os posts do usuário ao template; aplicar paginação consistente com o feed e manter consultas de reações e comentários limitadas à página exibida.
- [ ] **Otimizar contagens de reações.** O endpoint de reação executa uma contagem por tipo após cada alteração. Consolidar as contagens em uma consulta agregada e cobrir o resultado com testes.
- [ ] **Rever índices conforme consultas e volume.** Avaliar índices compostos para feed/comentários e mensagens não lidas; não presumir que `db_index=True` em título acelere buscas `icontains`. Medir com plano de execução e volume representativo antes de criar índices.
- [ ] **Tornar a busca de posts escalável.** Avaliar full-text search apropriado ao banco de produção; a busca atual com `icontains` em título, texto e autor tende a varrer registros.
- [ ] **Usar cache compartilhado em produção.** Substituir `LocMemCache` para cache de notícias e rate limit por backend compartilhado (por exemplo, Redis) ao executar múltiplos workers/instâncias; documentar invalidação e comportamento em indisponibilidade.
- [ ] **Tornar a integração de notícias resiliente.** Tratar chave ausente, respostas HTTP não exitosas, JSON inválido e payload inesperado; registrar a falha e manter uma resposta controlada sem mascarar erros de configuração.
- [ ] **Melhorar a migração de likes para reações.** Avaliar execução em lotes e custo da migração `0007` em bases grandes; verificar a reversibilidade, pois a reversão atual apaga reações do tipo `like`.
- [ ] **Remover lógica de ordenação O(n²) do painel de mais curtidos.** Evitar ordenar resultados usando `ids.index()` repetidamente; preservar explicitamente a ordenação do banco ou usar um mapeamento de posições.

## P2 — Organização, erros e cobertura

- [ ] **Centralizar funções compartilhadas de anotação de posts.** `com_reacoes` está duplicada em `users/views.py` e `posts/views.py`; extrair uma implementação única e testar contagens e reação do usuário.
- [ ] **Remover a definição duplicada de `setupCommentsInfiniteScroll`.** A função aparece duas vezes em `static/js/script.js`; consolidar em uma implementação e validar o carregamento incremental de comentários.
- [ ] **Padronizar formulários de post e tratamento de upload.** Usar `PostCreateForm` no fluxo de criação, em vez de repetir validação manual e `full_clean` na view, preservando erros por campo.
- [ ] **Definir logging estruturado por ambiente.** Configurar `LOGGING` com níveis e handlers explícitos para desenvolvimento e produção; substituir `print` por logs e evitar suprimir exceções.
- [ ] **Adicionar testes para os fluxos críticos ausentes.** Cobrir chat (acesso a conversas, envio, upload, leitura e exclusão), perfil e upload, confirmação/reenvio de e-mail, redirecionamentos, rate limit e falhas dos serviços externos.
- [ ] **Adicionar validações de qualidade automatizadas.** Introduzir checks de lint/format e análise estática compatíveis com o projeto, integrando-os ao workflow de CI sem ocultar falhas.
- [ ] **Revisar comandos de seed.** Documentar claramente o uso apenas em ambientes de teste/desenvolvimento; evitar credenciais padrão conhecidas e limpeza acidental de dados quando o comando for executado fora desses ambientes.

## P3 — Configuração, dependências e implantação

- [ ] **Alinhar versões e documentação do stack.** O README informa Django 5.0 enquanto `requirements.txt` fixa Django 6.1. Definir e testar a versão suportada e sincronizar README, CI e dependências.
- [ ] **Separar dependências de execução e desenvolvimento.** Revisar pins diretos/transitivos e mover pytest e ferramentas de teste para um arquivo ou grupo de desenvolvimento; manter upgrades com testes e changelog.
- [ ] **Documentar todas as variáveis de ambiente.** Criar instruções seguras de configuração para `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, banco, News API, Cloudinary e provedor de e-mail; explicar que `.env` é local e não deve ser versionado.
- [ ] **Rever o fluxo de build/deploy.** `build.sh` instala dependências e executa `collectstatic` e migrações no mesmo fluxo. Definir passos separados e seguros para build, migrações e inicialização; não executar migrações concorrentes em cada worker.
- [ ] **Documentar o comando de inicialização WSGI.** `gunicorn` está listado, mas não há manifesto de processo/Docker rastreado no repositório. Especificar o comando usado pelo provedor e validar workers/timeouts conforme os serviços externos.
- [ ] **Corrigir divergências entre README e arquivos existentes.** O README menciona Docker/Compose, Supabase, Resend e funcionalidades que não estão representadas de forma consistente nos arquivos de deploy/configuração. Documentar somente o que está implementado ou adicionar os artefatos correspondentes.
- [ ] **Rever configuração de estáticos e mídia.** Confirmar `collectstatic`, WhiteNoise e Cloudinary no ambiente de produção e documentar armazenamento, retenção, acesso e recuperação de arquivos.
- [ ] **Remover imports e código comprovadamente sem uso.** Revisar imports duplicados/não usados em `users/views.py`, imports de `sys`/`config` não usados no projeto e identificar se `SocialMedia/asgi.py`, `users/forms.py` (`PostCreateForm`), templates de senha duplicados e outros artefatos têm consumidores antes de removê-los.
- [ ] **Manter testes e migrações alinhados com a configuração real.** Executar testes, `manage.py check`, `manage.py check --deploy` com settings de produção e `makemigrations --check` no CI; investigar qualquer dependência de serviços reais nos testes.

---

## Estado da auditoria

- [x] Revisados os arquivos de configuração rastreados, estrutura dos apps, modelos, formulários, views, URLs, templates relevantes, migrações, testes e workflow de CI.
- [x] Confirmado que não há `Dockerfile`, Compose, `Procfile`, documentação de variáveis `.env` ou arquivo de dependências separado para desenvolvimento entre os arquivos rastreados.
- [x] Confirmado que `manage.py check` e `makemigrations --check --dry-run` não apontaram problemas.
- [x] `manage.py check --deploy` apontou alertas de HSTS, HTTPS, cookie de sessão, cookie CSRF e tamanho/chave temporária de auditoria.
- [x] Suíte atual: `28 passed`; execução com `8` avisos de depreciação das configurações de e-mail, com duração de aproximadamente 4 minutos.
