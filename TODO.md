# ✅ TODO — Social Media

Lista de melhorias e novas funcionalidades pra evoluir o projeto, organizada por prioridade e categoria. Marque os itens conforme for implementando.

---

## 🐛 Débitos técnicos (vale resolver primeiro)

- [ ] **Resolver N+1 queries no feed** — hoje, pra cada post no `{% for %}`, o template chama `post.likes.count` e `request.user in post.likes.all` separadamente. Com 30 posts por página, isso gera dezenas de queries extras. Dá pra resolver anotando os likes na própria queryset da view:
  ```python
  Post.objects.annotate(num_likes=Count('likes')).select_related('user')
  ```
- [ ] **Trocar `alert()` por notificações mais bonitas** — hoje os erros de curtida usam `alert()` do navegador (`"Erro ao registrar curtida..."`). Um toast/snackbar discreto no canto da tela deixa a experiência bem mais profissional.
- [ ] **Mover `SECRET_KEY` e `DEBUG` pra variáveis de ambiente** (`django-environ` ou `.env` + `python-decouple`), se ainda não estiver assim — essencial antes de colocar o projeto em produção.
- [ ] **Adicionar índices de banco** (`db_index=True`) em campos usados em buscas/filtros com frequência, como `title` e `data_posted`.

---

## 🔐 Segurança

- [ ] Recuperação de senha ("Esqueci minha senha") via e-mail
- [ ] Confirmação de e-mail no cadastro
- [ ] Rate limiting no login e no cadastro (evitar força bruta)
- [ ] Validar tipo e tamanho máximo da foto de perfil no upload
- [ ] Revisar permissões — garantir que só o dono do post pode editá-lo/excluí-lo (já existe no delete, replicar em qualquer edição futura)

---

## ⚡ Performance

- [ ] `select_related` / `prefetch_related` nas queries de posts (usuário, likes)
- [ ] Cache do painel "Mais Curtidos" (ex: `cache_page` ou cache manual por alguns minutos)
- [ ] Lazy loading de imagens (fotos de perfil, futuras imagens de post)
- [ ] Compressão de arquivos estáticos (CSS/JS) em produção

---

## ✨ Novas funcionalidades

- [ ] **Comentários em posts**
- [ ] **Seguir / deixar de seguir usuários**, com feed personalizado mostrando só quem você segue
- [ ] **Sistema de mensagens privadas** — o `style.css` já tem várias classes prontas pra isso (`.chat-main-window`, `.chat-sidebar-header`, `.chat-header`...), então parece que já tinha esse plano; falta só o back-end (model de conversa/mensagem + views)
- [ ] **Notificações** (alguém curtiu seu post, novo seguidor, etc.)
- [ ] **Edição de posts** já publicados (hoje só existe criar e excluir)
- [ ] **Upload de imagens/anexos nos posts**, não só texto
- [ ] **Hashtags** e página de posts por tag
- [ ] **Reações além do like** (❤️ 😂 😮 😢, por exemplo)
- [ ] **Posts salvos/favoritos** (marcar pra ler depois)
- [ ] **Modo escuro** (dark mode)

---

## 🎨 UX / Design

- [ ] Loading skeleton enquanto o feed carrega (em vez de tela em branco)
- [ ] Infinite scroll como alternativa à paginação numerada (ou as duas, à escolha do usuário)
- [ ] Estado de "carregando..." no botão de curtir durante a requisição AJAX
- [ ] Melhorar mensagens de erro de formulário (feedback mais claro pro usuário)
- [ ] Revisar acessibilidade: contraste de cores, navegação por teclado, `aria-label`s em todos os botões de ícone

---

## 🧪 Qualidade e infraestrutura

- [ ] Escrever testes automatizados (`pytest-django` ou `unittest`) pras views principais: curtir, criar post, buscar, paginação
- [ ] Configurar CI (GitHub Actions) rodando os testes a cada push
- [ ] Dockerizar o projeto (`Dockerfile` + `docker-compose.yml` com banco de dados)
- [ ] Deploy em produção (Railway, Render, PythonAnywhere ou similar)
- [ ] Trocar SQLite por PostgreSQL em produção
- [ ] Logging estruturado de erros (ex: Sentry)

---

## 💡 Ideias futuras (bônus)

- [ ] Estatísticas no perfil (total de curtidas recebidas, posts por mês, etc.)
- [ ] Compartilhar post em redes externas (usando o link direto que já criamos com `goto_post`)
- [ ] Modo "rascunho" pra salvar um post sem publicar
- [ ] Exportar meus dados (LGPD-friendly)

---

> 📌 Dica: vá riscando os itens aqui conforme for implementando, e sinta-se à vontade pra me chamar pra qualquer um desses pontos — é só falar qual quer atacar primeiro.