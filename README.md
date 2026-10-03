<div align="center">

# 💬 Social Media

### Uma rede social completa, rápida e responsiva construída com Django

Curta e reaja a posts, siga usuários, troque mensagens com anexos, comente em publicações, ative o modo escuro e interaja em tempo real — tudo com alto desempenho e segurança.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containers-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)
![License](https://img.shields.io/badge/Licença-MIT-yellow?style=for-the-badge)

</div>

---

## 📖 Sobre o projeto

O **Social Media** é uma aplicação web completa de rede social desenvolvida em **Django**. O projeto foi expandido para ir além do básico, integrando conceitos avançados de arquitetura web: autenticação segura, envio de e-mails transacionais via API, reações dinâmicas, feed personalizado por seguidores, chat com suporte a mídia, testes automatizados, conteinerização com Docker e deploy em produção na nuvem.

A aplicação conta com uma interface moderna com suporte a **Modo Escuro (Dark Mode)**, carregamento otimizado com **Loading Skeletons**, scroll infinito e atualizações instantâneas via **AJAX**, garantindo alta usabilidade sem recarregamentos desnecessários de página.

---

## ✨ Funcionalidades

### 🔐 Autenticação & Segurança
- **Cadastro e Login seguro** (via e-mail) com *rate limiting* para prevenção de ataques de força bruta.
- **Confirmação de e-mail no cadastro** e **Recuperação de senha** ("Esqueci minha senha") via e-mail transacional.
- Validação rigorosa de arquivos no upload de fotos de perfil e mídias (tipo e tamanho máximo).
- Controle de acesso granular — permissões restritas ao autor para edição e exclusão de posts e mensagens.
- Variáveis de ambiente sensíveis centralizadas via `.env`.

### 📝 Posts & Interação Social
- **Criação e exclusão de posts** com suporte a texto e **upload de imagens/anexos**.
- **Reações variadas** além do clássico like (❤️, 😂, 😮, 😢, etc.).
- **Comentários em posts** para discussões diretas.
- **Sistema de Seguidores (Follow/Unfollow)** e aba de **Feed Personalizado** exibindo apenas publicações de quem você segue.
- **Painel "Mais Curtidos"** otimizado com cache (exibindo apenas posts com mais de 0 curtidas).
- **Busca de posts** avançada por título, conteúdo ou autor com índices de banco de dados.

### 💬 Mensagens & Conversas
- Troca de **mensagens diretas** entre usuários.
- Suporte a **envio de imagens e anexos em conversas**.
- Opção para **apagar mensagens** enviadas.

### 🎨 UX/UI & Acessibilidade
- **Modo Escuro (Dark Mode)** alternável nativo.
- **Loading Skeleton** durante o carregamento do feed.
- **Infinite Scroll** e paginação numerada flexível.
- Notificações discretas estilo **Toast/Snackbar** substituindo os `alerts` padrão do navegador.
- Seção de notícias paginada na página inicial.
- Totalmente **responsivo** e otimizado para navegação por teclado e leitores de tela (`aria-labels`).

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologias & Ferramentas | Descrição |
|---|---|---|
| **Back-end** | **Python 3.12** / **Django 5.0** | Framework web principal e ORM |
| **Banco de Dados** | **PostgreSQL** (via **Supabase**) | Banco de dados relacional em produção (SQLite para dev local) |
| **E-mails Transacionais** | **Resend API** / **Django Mail** | Envio de e-mails de confirmação e redefinição de senha |
| **Front-end & Interatividade** | **HTML5**, **CSS3**, **jQuery**, **AJAX** | Interface reativa, atualizações assíncronas e Dark Mode |
| **Design & Assets** | **Font Awesome**, **Google Fonts** | Tipografia e iconografia |
| **Qualidade & Testes** | **Pytest-Django** / **Unittest** | Suíte de testes automatizados para views, auth e ações |
| **DevOps & CI/CD** | **Docker** & **Docker Compose** | Conteinerização do ambiente de desenvolvimento/produção |
| | **GitHub Actions** | Integração Contínua (CI) executando testes automatizados a cada push |
| **Hospedagem & Deploy** | **Render** | Web Service para hospedagem da aplicação Django |

---

## ⚡ Otimizações de Desempenho

- **Resolução de N+1 Queries:** Consultas otimizadas com `select_related()`, `prefetch_related()` e anotação direta (`annotate(num_likes=Count('likes'))`).
- **Aceleração com Cache:** Painel de posts em alta mantido em memória via cache para reduzir leituras no banco.
- **Índices de Banco (`db_index=True`):** Aplicados nos campos mais buscados como `title` e `data_posted`.
- **Compressão e Lazy Loading:** Imagens e estáticos carregados de forma sob demanda.

---

## 🚀 Como testar e rodar o projeto

> ⚡ **Acesso Rápido:** Para testar a aplicação em funcionamento, basta acessar o link do servidor em produção:
> 
> 👉 **[https://socialmedia-app-b5lv.onrender.com/](https://socialmedia-app-b5lv.onrender.com/)**

---

## 📁 Estrutura do projeto

```
SocialMedia/
├── .github/workflows/  # Pipelines do GitHub Actions (CI)
├── posts/              # App de posts, reações, comentários e feed
├── users/              # App de usuários, autenticação, perfis e seguidores
├── chat/               # App de mensagens diretas e anexos
├── static/
│   ├── css/style.css   # Design system (variáveis CSS, Dark Mode, Toast)
│   └── js/script.js    # Requisições AJAX, Skeleton e interação UI
├── templates/          # Templates HTML com Django Template Language
├── manage.py
├── requirements.txt
├── pytest.ini
├── build.sh            # Build para deploy
└── TODO.m              # Lista de melhorias 
```

---

## 🤝 Contribuindo

Contribuições são muito bem-vindas! Se você tem uma ideia, encontrou um bug ou quer sugerir uma melhoria:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/minha-feature`)
3. Faça commit das suas mudanças (`git commit -m 'Adiciona minha feature'`)
4. Envie para o seu fork (`git push origin feature/minha-feature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Sinta-se livre para usar, estudar e modificar.

---

<div align="center">

**Curtiu o projeto? Deixe uma ⭐ no repositório!**

</div>