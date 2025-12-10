document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form[id$="_form"]');
    const container = document.querySelector('#label-preview-container');

    const img = document.createElement('img');
    img.style.border = '1px solid';
    img.style.maxWidth = '500px';
    img.style.maxHeight = 'auto';
    container.appendChild(img);

    const getValues = (form) => {
        const values = {};
        form.querySelectorAll('input:not([type=submit]), select, textarea').forEach(f => {
            values[f.name] = f.value;
        });
        return values;
    };

    const updatePreview = async () => {
        const payload = getValues(form);
        const response = await fetch('/api/label/preview/template/', {
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

    updatePreview();

    form.addEventListener('input', updatePreview);
});
