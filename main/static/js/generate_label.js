const getValues = (form) => {
    const values = {};
    form.querySelectorAll('input:not([type=submit]), select, textarea').forEach(f => {
        values[f.name] = f.value;
    });
    return values;
};

const updateImagePreview = async (url, form, img) => {
    const payload = getValues(form);
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': payload.csrfmiddlewaretoken
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) return;
    const data = await response.json()
    img.src = `data:image/png;base64,${data.image}`;
};

const updatePdfPreview = async (url, form, iframe) => {
    const payload = getValues(form);
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': payload.csrfmiddlewaretoken
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) return;

    const data = await response.json();
    iframe.src = `data:application/pdf;base64,${data.pdf}`;
};

window.getValues = getValues
window.updateImagePreview = updateImagePreview
window.updatePdfPreview = updatePdfPreview