// Funcionalidad para la cámara y subida de fotos
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('foto');
    const photoPreview = document.getElementById('photoPreview');
    const previewImg = document.getElementById('previewImg');
    const changePhoto = document.getElementById('changePhoto');
    
    console.log('Camera.js cargado'); // Debug
    
    // Cuando se selecciona un archivo
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            console.log('Archivo seleccionado'); // Debug
            const file = e.target.files[0];
            
            if (file && file.type.includes('image')) {
                console.log('Es una imagen'); // Debug
                // Previsualizar la imagen
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    photoPreview.style.display = 'block';
                    console.log('Imagen previsualizada'); // Debug
                };
                reader.onerror = function(e) {
                    console.error('Error leyendo archivo:', e); // Debug
                };
                reader.readAsDataURL(file);
            } else {
                console.log('No es una imagen válida'); // Debug
            }
        });
    }

    // Cambiar foto
    if (changePhoto) {
        changePhoto.addEventListener('click', function() {
            photoPreview.style.display = 'none';
            if (fileInput) {
                fileInput.value = '';
            }
        });
    }
});