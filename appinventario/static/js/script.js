// Mostrar/ocultar campos según el tipo de producto
document.addEventListener('DOMContentLoaded', function() {
    const tipoSelect = document.getElementById('tipo');
    
    // Función para mostrar los campos correspondientes
    function mostrarCamposPorTipo(tipo) {
    console.log('Mostrando campos para:', tipo);

    const campos = ['dispositivoFields', 'productoVentaFields', 'materialGeneralFields'];
    campos.forEach(id => {
        const elemento = document.getElementById(id);
        if (elemento) {
            // Ocultar el campo y remover required de todos los inputs
            elemento.style.display = 'none';
            elemento.querySelectorAll('[required]').forEach(input => {
                input.removeAttribute('required');
            });
        }
    });

    // Mostrar campos del tipo seleccionado y agregar required
    let visible;
    if (tipo === 'dispositivo') visible = document.getElementById('dispositivoFields');
    else if (tipo === 'producto_venta') visible = document.getElementById('productoVentaFields');
    else if (tipo === 'material_general') visible = document.getElementById('materialGeneralFields');

    if (visible) {
        visible.style.display = 'block';
        // Agregar required solo a los campos del tipo visible
        visible.querySelectorAll('input[required], select[required], textarea[required]').forEach(input => {
            input.setAttribute('required', 'required');
        });
    }
}
    // Función para manejar la visibilidad del campo canal_vpn
    function manejarCampoCanalVPN() {
        const vpnSelect = document.getElementById('vpn');
        const canalVpnInput = document.getElementById('canal_vpn');
        
        if (vpnSelect && canalVpnInput) {
            // Función para actualizar el estado del campo canal_vpn
            function actualizarEstadoCanalVPN() {
                if (vpnSelect.value === 'No tiene') {
                    canalVpnInput.disabled = true;
                    canalVpnInput.required = false;
                    canalVpnInput.value = ''; // Limpiar el valor
                    canalVpnInput.placeholder = 'No aplica';
                } else {
                    canalVpnInput.disabled = false;
                    canalVpnInput.required = true;
                    canalVpnInput.placeholder = 'Canal VPN';
                }
            }
            
            // Actualizar estado inicial
            actualizarEstadoCanalVPN();
            
            // Actualizar cuando cambie la selección
            vpnSelect.addEventListener('change', actualizarEstadoCanalVPN);
        }
    }

    if (tipoSelect) {
        console.log('Elemento tipoSelect encontrado');
        
        // Mostrar campos según el valor inicial (si hay alguno seleccionado)
        if (tipoSelect.value) {
            setTimeout(() => {
                mostrarCamposPorTipo(tipoSelect.value);
            }, 100);
        }
        
        tipoSelect.addEventListener('change', function() {
            mostrarCamposPorTipo(this.value);
            // Si se selecciona dispositivo, inicializar manejo de canal VPN
            if (this.value === 'dispositivo') {
                setTimeout(manejarCampoCanalVPN, 100);
            }
        });
    } else {
        console.log('Elemento tipoSelect NO encontrado');
    }

    // Inicializar manejo de canal VPN si ya está en dispositivo
    if (tipoSelect && tipoSelect.value === 'dispositivo') {
        setTimeout(manejarCampoCanalVPN, 100);
    }

    // Funcionalidad para arrastrar y soltar archivos
    const fileUploadBox = document.getElementById('fileUploadBox');
    const fileInput = document.getElementById('foto');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const removeFileBtn = document.getElementById('removeFile');
    const photoPreview = document.getElementById('photoPreview');
    const previewImg = document.getElementById('previewImg');

    if (fileUploadBox && fileInput) {
        console.log('Inicializando funcionalidad de arrastrar y soltar');
        
        // Prevenir comportamientos por defecto para arrastrar
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileUploadBox.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        // Efectos al arrastrar
        ['dragenter', 'dragover'].forEach(eventName => {
            fileUploadBox.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            fileUploadBox.addEventListener(eventName, unhighlight, false);
        });

        function highlight() {
            fileUploadBox.classList.add('highlight');
        }

        function unhighlight() {
            fileUploadBox.classList.remove('highlight');
        }

        // Manejar archivos soltados
        fileUploadBox.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;
            handleFiles(files);
        }

        // Manejar selección de archivo por click
        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });

        // Eliminar archivo seleccionado
        if (removeFileBtn) {
            removeFileBtn.addEventListener('click', function() {
                fileInput.value = '';
                fileInfo.style.display = 'none';
                photoPreview.style.display = 'none';
                fileUploadBox.style.display = 'block';
            });
        }

        function handleFiles(files) {
            if (files.length > 0) {
                const file = files[0];
                console.log('Archivo seleccionado:', file.name);
                
                // Mostrar información del archivo
                fileName.textContent = file.name;
                fileInfo.style.display = 'flex';
                fileUploadBox.style.display = 'none';
                
                // Previsualizar imagen
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        previewImg.src = e.target.result;
                        photoPreview.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                }
            }
        }
    } else {
        console.log('Elementos de subida de archivos NO encontrados');
    }

    // Validación del formulario antes de enviar
// Validación del formulario antes de enviar
function validarFormulario(formData) {
    const tipo = formData.get('tipo');
    console.log('Validando formulario para tipo:', tipo);
    
    // Validar campos requeridos según el tipo
    if (tipo === 'dispositivo') {
        const camposRequeridos = ['responsable', 'marca', 'vpn', 'room', 'pais', 'costo'];
        // Solo validar canal_vpn si no es "No tiene"
        const vpn = formData.get('vpn');
        if (vpn !== 'No tiene') {
            camposRequeridos.push('canal_vpn');
        }
        
        for (const campo of camposRequeridos) {
            if (!formData.get(campo)) {
                return `El campo "${campo}" es requerido para dispositivos`;
            }
        }
    }
    else if (tipo === 'producto_venta') {
        const camposRequeridos = ['marca_venta', 'descripcion_venta', 'costo_venta'];
        for (const campo of camposRequeridos) {
            if (!formData.get(campo)) {
                return `El campo "${campo}" es requerido para productos de venta`;
            }
        }
    }
    else if (tipo === 'material_general') {
        const camposRequeridos = ['nombre_material', 'tipo_material', 'precio_material', 'room_material'];
        for (const campo of camposRequeridos) {
            if (!formData.get(campo)) {
                return `El campo "${campo}" es requerido para material general`;
            }
        }
    }
    
    return null; // No hay errores
}

    // Manejar envío de formulario de agregar producto
    const productForm = document.getElementById('productForm');
    if (productForm) {
        console.log('Formulario de producto encontrado');
        
        productForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Formulario enviado');
            
            const formData = new FormData(this);
            const resultMessage = document.getElementById('resultMessage');
            
            // Validar campos requeridos
            const errorValidacion = validarFormulario(formData);
            if (errorValidacion) {
                resultMessage.innerHTML = 
                    `<div class="message error">
                        <p>${errorValidacion}</p>
                     </div>`;
                return;
            }
            
            // Mostrar mensaje de carga
            resultMessage.innerHTML = 
                `<div class="message info">
                    <p>Procesando, por favor espere...</p>
                 </div>`;
            
            fetch('/agregar_producto', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log('Respuesta del servidor:', data);
                if (data.success) {
                    resultMessage.innerHTML = 
                        `<div class="message success">
                            <p>${data.message}</p>
                            <p><strong>Tipo:</strong> ${data.tipo}</p>
                            <p><strong>Grupo:</strong> ${data.grupo}</p>
                            <p><strong>Código de barras:</strong> ${data.codigo_barras}</p>
                            <div class="barcode-image">
                                <img src="${data.barcode_image}" alt="Código de barras" style="max-width: 300px;">
                            </div>
                            ${data.foto_url ? `<p><strong>Foto:</strong> <a href="${data.foto_url}" target="_blank">Ver imagen</a></p>` : ''}
                            <p>Guarde esta información para referencia futura</p>
                         </div>`;
                    productForm.reset();
                    
                    // Ocultar todos los campos de producto
                    document.getElementById('dispositivoFields').style.display = 'none';
                    document.getElementById('productoVentaFields').style.display = 'none';
                    document.getElementById('materialGeneralFields').style.display = 'none';
                    
                    // Ocultar previsualización de foto y resetear subida de archivos
                    const photoPreview = document.getElementById('photoPreview');
                    const fileInfo = document.getElementById('fileInfo');
                    const fileUploadBox = document.getElementById('fileUploadBox');
                    
                    if (photoPreview) photoPreview.style.display = 'none';
                    if (fileInfo) fileInfo.style.display = 'none';
                    if (fileUploadBox) fileUploadBox.style.display = 'block';
                    
                    // Resetear el selector de tipo
                    if (tipoSelect) tipoSelect.value = '';
                } else {
                    resultMessage.innerHTML = 
                        `<div class="message error">
                            <p>${data.message}</p>
                         </div>`;
                }
            })
            .catch(error => {
                console.error('Error en la solicitud:', error);
                resultMessage.innerHTML = 
                    `<div class="message error">
                        <p>Error: ${error.message}</p>
                     </div>`;
            });
        });
    } else {
        console.log('Formulario de producto NO encontrado');
    }

    // Manejar envío de formulario de edición
    const editForm = document.getElementById('editForm');
    if (editForm) {
        console.log('Formulario de edición encontrado');
        
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Formulario de edición enviado');
            
            const formData = new FormData(this);
            const messageDiv = document.getElementById('message');
            
            // Obtener tipo e ID desde los atributos data
            const tipo = this.dataset.tipo;
            const productoId = this.dataset.productoId;
            
            // Mostrar mensaje de carga
            messageDiv.innerHTML = 
                `<div class="message info">
                    <p>Guardando cambios, por favor espere...</p>
                 </div>`;
            
            fetch(`/editar_producto/${tipo}/${productoId}`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log('Respuesta de edición:', data);
                if (data.success) {
                    messageDiv.innerHTML = 
                        `<div class="message success">
                            <p>${data.message}</p>
                         </div>`;
                    
                    // Actualizar la página después de 2 segundos para ver los cambios
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    messageDiv.innerHTML = 
                        `<div class="message error">
                            <p>${data.message}</p>
                         </div>`;
                }
            })
            .catch(error => {
                console.error('Error en la edición:', error);
                messageDiv.innerHTML = 
                    `<div class="message error">
                        <p>Error: ${error.message}</p>
                     </div>`;
            });
        });
    } else {
        console.log('Formulario de edición NO encontrado');
    }
    
    // Enfocar automáticamente el campo de búsqueda
    const codigoBarrasInput = document.getElementById('codigo_barras');
    if (codigoBarrasInput) {
        console.log('Campo de búsqueda encontrado');
        codigoBarrasInput.focus();
        
        // Enviar formulario al presionar Enter (útil para lectores de código de barras)
        codigoBarrasInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                console.log('Enter presionado en búsqueda');
                this.form.submit();
            }
        });
    } else {
        console.log('Campo de búsqueda NO encontrado');
    }

    // Debug: Verificar que todos los elementos existen
    console.log('Elementos verificados:');
    console.log('- tipoSelect:', document.getElementById('tipo'));
    console.log('- dispositivoFields:', document.getElementById('dispositivoFields'));
    console.log('- productoVentaFields:', document.getElementById('productoVentaFields'));
    console.log('- materialGeneralFields:', document.getElementById('materialGeneralFields'));
    console.log('- productForm:', document.getElementById('productForm'));
});