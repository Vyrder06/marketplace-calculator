const marketplaceSelect = document.getElementById("marketplace");
const campoModoEnjoei = document.getElementById("campo-modo-enjoei");
const modoEnjoeiSelect = document.getElementById("modo-enjoei");

marketplaceSelect.addEventListener("change", function () {
    if (marketplaceSelect.value === "enjoei") {
        campoModoEnjoei.style.display = "block";
        modoEnjoeiSelect.required = true;
    } else {
        campoModoEnjoei.style.display = "none";
        modoEnjoeiSelect.required = false;
    }
});