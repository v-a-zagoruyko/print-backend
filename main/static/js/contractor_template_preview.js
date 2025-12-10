document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form[id$="_form"]');
    const container = document.querySelector('#label-preview-container');

    const img = document.createElement('img');
    img.style.border = '1px solid';
    img.style.maxWidth = '500px';
    img.style.maxHeight = 'auto';
    container.appendChild(img);

    updateImagePreview('/api/label/preview/contractor/', form, img);

    form.addEventListener('input', () => updateImagePreview('/api/label/preview/contractor/', form, img));
});
