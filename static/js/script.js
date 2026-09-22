function adjustTextareaHeight(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight - 20) + 'px';
}

document.addEventListener('DOMContentLoaded', function () {
    var textareas = document.querySelectorAll('textarea.post-content');
    textareas.forEach(function (textarea) {
        adjustTextareaHeight(textarea);
    });
});

window.addEventListener('pageshow', function (event) {
    if (event.persisted) {
        window.location.reload();
    }
});

/* ==========================================================================
   TOAST / SNACKBAR — substitui o alert() nativo do navegador
   ========================================================================== */
function showToast(message, type) {
    type = type || 'error'; // 'success' | 'error' | 'info'

    var container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    var icons = {
        success: 'fa-solid fa-circle-check',
        error: 'fa-solid fa-circle-exclamation',
        info: 'fa-solid fa-circle-info',
    };

    var toast = document.createElement('div');
    toast.className = 'toast toast--' + type;
    toast.innerHTML =
        '<i class="' + (icons[type] || icons.error) + '"></i>' +
        '<span class="toast__message"></span>' +
        '<button type="button" class="toast__close" aria-label="Fechar">&times;</button>';

    toast.querySelector('.toast__message').textContent = message;

    container.appendChild(toast);

    // Força reflow pra animação de entrada funcionar
    void toast.offsetWidth;
    toast.classList.add('toast--visible');

    function remove() {
        toast.classList.remove('toast--visible');
        toast.addEventListener('transitionend', function () {
            toast.remove();
        }, { once: true });
    }

    var timer = setTimeout(remove, 4000);

    toast.querySelector('.toast__close').addEventListener('click', function () {
        clearTimeout(timer);
        remove();
    });
}

/* ==========================================================================
   MODAL DE CONFIRMAÇÃO — substitui o confirm() nativo do navegador
   ========================================================================== */
function showConfirm(message, onConfirm, options) {
    options = options || {};
    var confirmText = options.confirmText || 'Excluir';
    var cancelText = options.cancelText || 'Cancelar';
    var title = options.title || 'Confirmar ação';

    // Remove qualquer modal de confirmação que já esteja aberto
    var existing = document.getElementById('confirm-modal-overlay');
    if (existing) existing.remove();

    var overlay = document.createElement('div');
    overlay.id = 'confirm-modal-overlay';
    overlay.className = 'modal-overlay';

    overlay.innerHTML =
        '<div class="modal-card">' +
            '<div class="modal-header">' +
                '<h3></h3>' +
                '<button type="button" class="modal-close-btn" aria-label="Fechar">&times;</button>' +
            '</div>' +
            '<div class="modal-body">' +
                '<p class="confirm-modal-message"></p>' +
                '<div class="confirm-modal-actions">' +
                    '<button type="button" class="button-ghost confirm-modal-cancel"></button>' +
                    '<button type="button" class="button-submit confirm-modal-confirm"></button>' +
                '</div>' +
            '</div>' +
        '</div>';

    overlay.querySelector('.modal-header h3').textContent = title;
    overlay.querySelector('.confirm-modal-message').textContent = message;
    overlay.querySelector('.confirm-modal-cancel').textContent = cancelText;
    var confirmBtn = overlay.querySelector('.confirm-modal-confirm');
    confirmBtn.textContent = confirmText;
    confirmBtn.style.backgroundColor = 'var(--danger)';

    document.body.appendChild(overlay);

    // Força reflow pra animação funcionar
    void overlay.offsetWidth;
    overlay.classList.add('active');

    function close() {
        overlay.classList.remove('active');
        overlay.addEventListener('transitionend', function () {
            overlay.remove();
        }, { once: true });
    }

    overlay.querySelector('.modal-close-btn').addEventListener('click', close);
    overlay.querySelector('.confirm-modal-cancel').addEventListener('click', close);
    overlay.addEventListener('click', function (e) {
        if (e.target === overlay) close();
    });

    confirmBtn.addEventListener('click', function () {
        close();
        onConfirm();
    });
}

/* ==========================================================================
   COMENTÁRIOS
   ========================================================================== */
$(document).on('click', '.comment-toggle-btn', function () {
    var $btn = $(this);
    var postId = $btn.data('post-id');
    var $section = $('#comments-section-' + postId);
    var url = $btn.data('url');

    if ($section.is(':visible')) {
        $section.slideUp(150);
        return;
    }

    if ($section.data('loaded')) {
        $section.slideDown(150);
        return;
    }

    $section.html('<p class="comments-loading"><i class="fa-solid fa-spinner fa-spin"></i> Carregando comentários...</p>');
    $section.slideDown(150);

    $.ajax({
        url: url,
        type: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        dataType: 'json',
        success: function (data) {
            $section.html(data.html);
            $section.data('loaded', true);

            var $scrollBox = $section.find('.comments-scroll');
            $scrollBox.data('has-next', data.has_next);
            $scrollBox.data('next-page', data.next_page_number);

            setupCommentsInfiniteScroll($scrollBox[0], url);
        },
        error: function () {
            $section.html('<p class="comments-loading">Erro ao carregar comentários.</p>');
        }
    });
});

function setupCommentsInfiniteScroll(scrollBoxEl, baseUrl) {
    if (!scrollBoxEl) return;
    var $scrollBox = $(scrollBoxEl);
    var sentinel = scrollBoxEl.querySelector('.comments-sentinel');
    if (!sentinel) return;

    var carregando = false;

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                carregarMaisComentarios();
            }
        });
    }, { root: scrollBoxEl, rootMargin: '80px' }); // root = a própria caixa, não a página

    observer.observe(sentinel);

    function carregarMaisComentarios() {
        var hasNext = $scrollBox.data('has-next');
        var nextPage = $scrollBox.data('next-page');
        if (!hasNext || !nextPage || carregando) return;

        carregando = true;
        var $loadingIndicator = $('<p class="comments-loading-more"><i class="fa-solid fa-spinner fa-spin"></i></p>');
        $(sentinel).before($loadingIndicator);

        $.ajax({
            url: baseUrl,
            type: 'GET',
            data: { page: nextPage },
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            dataType: 'json',
            success: function (data) {
                $loadingIndicator.remove();
                $scrollBox.find('.comments-list').append(data.html);
                $scrollBox.data('has-next', data.has_next);
                $scrollBox.data('next-page', data.next_page_number);
            },
            error: function () {
                $loadingIndicator.remove();
            },
            complete: function () {
                carregando = false;
            }
        });
    }
}

function setupCommentsInfiniteScroll(scrollBoxEl, baseUrl) {
    if (!scrollBoxEl) return;
    var $scrollBox = $(scrollBoxEl);
    var sentinel = scrollBoxEl.querySelector('.comments-sentinel');
    if (!sentinel) return;

    var carregando = false;

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                carregarMaisComentarios();
            }
        });
    }, { root: scrollBoxEl, rootMargin: '80px' }); // root = a própria caixa, não a página

    observer.observe(sentinel);

    function carregarMaisComentarios() {
        var hasNext = $scrollBox.data('has-next');
        var nextPage = $scrollBox.data('next-page');
        if (!hasNext || !nextPage || carregando) return;

        carregando = true;
        var $loadingIndicator = $('<p class="comments-loading-more"><i class="fa-solid fa-spinner fa-spin"></i></p>');
        $(sentinel).before($loadingIndicator);

        $.ajax({
            url: baseUrl,
            type: 'GET',
            data: { page: nextPage },
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            dataType: 'json',
            success: function (data) {
                $loadingIndicator.remove();
                $scrollBox.find('.comments-list').append(data.html);
                $scrollBox.data('has-next', data.has_next);
                $scrollBox.data('next-page', data.next_page_number);
            },
            error: function () {
                $loadingIndicator.remove();
            },
            complete: function () {
                carregando = false;
            }
        });
    }
}

$(document).on('submit', '.comment-form', function (e) {
    e.preventDefault();
    var $form = $(this);
    var $input = $form.find('input[name="content"]');
    var content = $input.val().trim();
    if (!content) return;

    var url = $form.data('url');
    var csrfToken = $form.find('[name=csrfmiddlewaretoken]').val() || getCookie('csrftoken');

    $.ajax({
        url: url,
        type: 'POST',
        data: { content: content },
        headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
        dataType: 'json',
        success: function (data) {
            var $section = $form.closest('.comments-section');
            var $list = $section.find('.comments-list');
            $list.find('.comments-empty').remove();
            $list.append(data.html);
            $input.val('');

            var postId = $section.attr('id').replace('comments-section-', '');
            var $countSpan = $('.comment-toggle-btn[data-post-id="' + postId + '"] .comment-count');
            var atual = parseInt($countSpan.text()) || 0;
            $countSpan.text(atual + 1);
        },
        error: function (xhr) {
            var msg = (xhr.responseJSON && xhr.responseJSON.error) || 'Erro ao enviar comentário. Tente novamente.';
            showToast(msg, 'error');
        }
    });
});

$(document).on('click', '.comment-delete-btn', function (e) {
    e.preventDefault();
    var $btn = $(this);
    var $item = $btn.closest('.comment-item');
    var url = $btn.data('url');

    showConfirm('Tem certeza que deseja excluir este comentário?', function () {
        var csrfToken = $('[name=csrfmiddlewaretoken]').val() || getCookie('csrftoken');
        $.ajax({
            url: url,
            type: 'POST',
            headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
            dataType: 'json',
            success: function () {
                var $section = $item.closest('.comments-section');
                $item.fadeOut(200, function () {
                    $(this).remove();
                    if ($section.find('.comment-item').length === 0) {
                        $section.find('.comments-list').append('<p class="comments-empty">Nenhum comentário ainda. Seja o primeiro a comentar!</p>');
                    }
                });

                var postId = $section.attr('id').replace('comments-section-', '');
                var $countSpan = $('.comment-toggle-btn[data-post-id="' + postId + '"] .comment-count');
                var atual = parseInt($countSpan.text()) || 0;
                $countSpan.text(Math.max(0, atual - 1));
            },
            error: function () {
                showToast('Erro ao excluir comentário. Tente novamente.', 'error');
            }
        });
    });
});
function openModal(imgElement) {
  const modal = document.getElementById('image-modal');
  const modalImg = document.getElementById('modal-img');
  
  modalImg.src = imgElement.src;
  modal.classList.add('active');
  document.body.style.overflow = 'hidden'; // Impede a rolagem da página atrás
}

function closeModal(event) {
  // Fecha se clicar fora da imagem ou no botão 'X'
  if (event.target.id === 'image-modal' || event.target.classList.contains('close-btn')) {
    const modal = document.getElementById('image-modal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto'; // Reativa a rolagem da página
  }
}

// Permite fechar a imagem apertando ESC
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    const modal = document.getElementById('image-modal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
  }
});

function incrementarTextoCurtidas(texto, value) {
    var quantidadeAtual = parseInt(texto, 10);
    if (isNaN(quantidadeAtual)) return texto;
    var novaQuantidade = quantidadeAtual + value;
    return novaQuantidade + ' curtidas';
}

function atualizarTrendingItem(postId, estaCurtido) {
    $('.trending-item').each(function (index, elemento) {
        var $link = $(elemento).find('a');
        var href = $link.attr('href');

        if (href && href.includes(postId)) {
            var $primeiraLi = $(elemento).find('ul li').first();
            var textoAtual = $primeiraLi.text();
            var delta = estaCurtido ? 1 : -1;
            var novoTexto = incrementarTextoCurtidas(textoAtual, delta);
            $primeiraLi.text(novoTexto);
        }
    });
}

$(document).on('click', '.like-btn', function() {
    const $btn = $(this);
    const $count = $btn.find('.like-count');

    const likeUrl = $btn.data('url');
    const postId = $btn.data('post-id');

    const isLiked = $btn.attr('aria-pressed') === 'true';
    const newLikedState = !isLiked;
    let currentLikes = parseInt($count.text()) || 0;

    $btn.attr('aria-pressed', newLikedState);
    $count.text(newLikedState ? currentLikes + 1 : currentLikes - 1);

    atualizarTrendingItem(postId, newLikedState);

    const csrfToken = $('[name=csrfmiddlewaretoken]').val() || getCookie('csrftoken');
    $.ajax({
        url: likeUrl,
        type: "POST",
        headers: {
            "X-CSRFToken": csrfToken
        },
        dataType: "json",
        error: function(xhr, status, error) {
            $btn.attr('aria-pressed', isLiked);
            $count.text(currentLikes);
            atualizarTrendingItem(postId, isLiked);
            showToast('Erro ao registrar curtida. Tente novamente.', 'error');
        }
    });
});

/* ==========================================================================
   DARK MODE
   ========================================================================== */
function aplicarIconeTema() {
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    var icon = document.querySelector('#dark-mode-toggle i');
    if (icon) {
        icon.className = isDark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    aplicarIconeTema();

    var toggleBtn = document.getElementById('dark-mode-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function () {
            var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            if (isDark) {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            }
            aplicarIconeTema();
        });
    }
});