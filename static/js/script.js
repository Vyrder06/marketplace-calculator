const marketplace = document.getElementById('marketplace');
const campoModoEnjoei = document.getElementById('campo-modo-enjoei');

function atualizarModoEnjoei() {
    const ehEnjoei = marketplace.value === 'enjoei';

    campoModoEnjoei.style.display = ehEnjoei ? 'block' : 'none';
}

marketplace.addEventListener('change', atualizarModoEnjoei);

atualizarModoEnjoei();