<div align="center">

# 💬 Social Media

### Uma rede social simples, rápida e feita com Django

Curta posts, siga conversas, monte seu perfil e descubra o que está bombando — tudo isso rodando no seu próprio servidor.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?style=for-the-badge&logo=django&logoColor=white)
![jQuery](https://img.shields.io/badge/jQuery-3.7-0769AD?style=for-the-badge&logo=jquery&logoColor=white)
![License](https://img.shields.io/badge/Licença-MIT-yellow?style=for-the-badge)

</div>

---

## 📖 Sobre o projeto

O **Social Media** é uma aplicação web de rede social desenvolvida em **Django**, criada para colocar em prática (e mostrar na prática) conceitos como autenticação de usuários, relacionamento entre modelos, requisições assíncronas com AJAX e uma interface responsiva e agradável.

Aqui você pode criar sua conta, publicar posts, curtir publicações de outras pessoas, buscar conteúdos e usuários, personalizar seu perfil com foto e bio, e acompanhar o que está em alta na aba de **Mais Curtidos**.

> 🎯 O foco do projeto é unir uma experiência de front-end fluida (curtidas instantâneas, paginação, navegação suave) com um back-end Django limpo e organizado em apps.

---

## ✨ Funcionalidades

- 🔐 **Autenticação completa** — cadastro, login (via e-mail) e logout
- 📝 **Criação e exclusão de posts**
- ❤️ **Sistema de curtidas em tempo real**, com atualização otimista via AJAX (sem recarregar a página)
- 🔥 **Painel "Mais Curtidos"**, com scroll independente e navegação direta até o post (mesmo que ele esteja em outra página)
- 🔎 **Busca de posts** por título, conteúdo ou autor
- 👤 **Perfil de usuário** com foto, biografia, cidade, estado e país
- ✏️ **Edição de perfil** em tempo real, com upload e remoção de foto
- 📄 **Paginação** no feed geral, nos resultados de busca e nos posts do seu perfil (30 por página)
- 📱 Interface **responsiva**, com design próprio e tipografia customizada

---

## 🛠️ Tecnologias utilizadas

| Camada | Tecnologia |
|---|---|
| **Back-end** | [Django](https://www.djangoproject.com/) |
| **Banco de dados** | SQLite (padrão de desenvolvimento — configurável para PostgreSQL/MySQL em produção) |
| **Front-end** | HTML5, CSS3 (design system próprio com variáveis CSS) |
| **Interatividade** | [jQuery](https://jquery.com/) + AJAX |
| **Ícones** | [Font Awesome](https://fontawesome.com/) |
| **Tipografia** | Google Fonts |

---

## 🚀 Como baixar e rodar o projeto

### Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- [Python 3.10+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/)
- [Git](https://git-scm.com/)

### Passo a passo

**1. Clone o repositório**
```bash
git clone https://github.com/seu-usuario/SocialMedia.git
cd SocialMedia
```

**2. Crie e ative um ambiente virtual**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

**4. Aplique as migrações do banco de dados**
```bash
python manage.py migrate
```

**5. Crie um super usuário (opcional, para acessar o admin)**
```bash
python manage.py createsuperuser
```

**6. Rode o servidor de desenvolvimento**
```bash
python manage.py runserver
```

**7. Acesse no navegador** 🎉
```
http://127.0.0.1:8000/
```

> 💡 **Dica:** quer testar o feed com bastante conteúdo (paginação, busca, ranking de curtidas)? O projeto conta com um comando de seed que gera posts fictícios automaticamente:
> ```bash
> python manage.py seed_posts --count 60
> ```

---

## 📁 Estrutura do projeto

```
SocialMedia/
├── posts/              # App responsável pelos posts (criar, curtir, buscar, excluir)
├── users/              # App responsável por autenticação e perfis de usuário
├── static/
│   ├── css/style.css   # Estilos globais e design system
│   └── js/script.js
├── templates/          # Templates HTML (Django Template Language)
├── manage.py
└── requirements.txt
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

Feito com 💙 e muitas xícaras de café.

**Curtiu o projeto? Deixe uma ⭐ no repositório!**

</div>