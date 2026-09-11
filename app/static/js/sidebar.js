/**
 * Controla o estado retrátil (collapsed/expanded) da sidebar, persistindo
 * a preferência do usuário em localStorage para manter o estado entre
 * navegações de página (recarrega o layout, mas não a experiência do menu).
 */
document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const mainContent = document.getElementById("mainContent");
    const toggleBtn = document.getElementById("sidebarToggle");

    if (!sidebar || !mainContent || !toggleBtn) {
        return;
    }

    const STORAGE_KEY = "finance_sidebar_collapsed";

    function aplicarEstado(collapsed) {
        sidebar.classList.toggle("collapsed", collapsed);
        mainContent.classList.toggle("collapsed", collapsed);
    }

    // Restaura preferência salva
    const estadoSalvo = localStorage.getItem(STORAGE_KEY) === "true";
    aplicarEstado(estadoSalvo);

    toggleBtn.addEventListener("click", function () {
        const novoEstado = !sidebar.classList.contains("collapsed");
        aplicarEstado(novoEstado);
        localStorage.setItem(STORAGE_KEY, novoEstado);
    });

    // Marca o link ativo com base na URL atual, para destaque visual.
    const linksAtuais = sidebar.querySelectorAll(".sidebar-link");
    const caminhoAtual = window.location.pathname;
    linksAtuais.forEach(function (link) {
        const href = link.getAttribute("href");
        if (href && caminhoAtual.startsWith(href) && href !== "/") {
            link.classList.add("active");
        }
    });
});
