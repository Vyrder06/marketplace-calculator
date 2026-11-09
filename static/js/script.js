
async function salvarCampo(input) {
    const resposta = await fetch(`/produtos/${input.dataset.id}/campo`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({campo: input.dataset.campo, valor: input.value})
    });
    if (resposta.status === 401) {
        window.location.href = "/";
        return;
    }
    input.classList.toggle("salvo", resposta.ok);
    input.classList.toggle("erro", !resposta.ok);
}
