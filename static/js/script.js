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