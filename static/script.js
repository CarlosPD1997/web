console.log('📝 script.js cargado correctamente');

// Variables globales
let salaActual = null;
let salaActualNombre = '';

// ---------- FUNCIONES DE DÍAS HÁBILES ----------
function esDiaHabil(fechaStr) {
    if (!fechaStr) return false;
    var fecha = new Date(fechaStr + 'T00:00:00');
    var dia = fecha.getDay();
    return dia !== 0 && dia !== 6;
}

function obtenerSiguienteDiaHabil(fechaStr) {
    var fecha = new Date(fechaStr + 'T00:00:00');
    fecha.setDate(fecha.getDate() + 1);
    var intentos = 0;
    while (!esDiaHabil(fecha.toISOString().split('T')[0]) && intentos < 10) {
        fecha.setDate(fecha.getDate() + 1);
        intentos++;
    }
    return fecha.toISOString().split('T')[0];
}

function formatearFecha(fechaStr) {
    if (!fechaStr) return '';
    var fecha = new Date(fechaStr + 'T00:00:00');
    var diasSemana = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
    var meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    var diaSemana = diasSemana[fecha.getDay()];
    var dia = fecha.getDate();
    var mes = meses[fecha.getMonth()];
    var año = fecha.getFullYear();
    return diaSemana + ', ' + dia + ' de ' + mes + ' de ' + año;
}

// ---------- FUNCIONES DE CALENDARIO ----------
function seleccionarSala(salaId, nombre) {
    console.log('📌 Seleccionando sala:', salaId, nombre);
    salaActual = salaId;
    salaActualNombre = nombre;
    
    var tabs = document.querySelectorAll('.tab-sala');
    for (var i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove('active');
        if (parseInt(tabs[i].dataset.sala) === salaId) {
            tabs[i].classList.add('active');
        }
    }
    
    var titulo = document.getElementById('sala-titulo');
    if (titulo) {
        titulo.textContent = '📌 ' + nombre;
    }
    
    cargarCalendario();
}

function cambiarFecha(direccion) {
    console.log('📅 Cambiando fecha:', direccion);
    var input = document.getElementById('fecha-select');
    if (!input) return;
    
    var fecha = new Date(input.value + 'T00:00:00');
    var intentos = 0;
    do {
        fecha.setDate(fecha.getDate() + direccion);
        intentos++;
        if (intentos > 10) break;
    } while (!esDiaHabil(fecha.toISOString().split('T')[0]));
    
    input.value = fecha.toISOString().split('T')[0];
    cargarCalendario();
}

function irHoy() {
    console.log('📅 Ir a hoy');
    var input = document.getElementById('fecha-select');
    if (!input) return;
    
    var hoy = new Date();
    var año = hoy.getFullYear();
    var mes = String(hoy.getMonth() + 1).padStart(2, '0');
    var dia = String(hoy.getDate()).padStart(2, '0');
    var fechaHoy = año + '-' + mes + '-' + dia;
    
    console.log('📅 Fecha actual real:', fechaHoy);
    
    if (!esDiaHabil(fechaHoy)) {
        var siguienteHabil = obtenerSiguienteDiaHabil(fechaHoy);
        input.value = siguienteHabil;
    } else {
        input.value = fechaHoy;
    }
    
    cargarCalendario();
}

function cargarCalendario() {
    console.log('🔄 Cargando calendario...');
    
    if (!salaActual) {
        console.error('❌ No hay sala seleccionada');
        return;
    }
    
    var fechaInput = document.getElementById('fecha-select');
    if (!fechaInput) {
        console.error('❌ No se encuentra el selector de fecha');
        return;
    }
    
    var fecha = fechaInput.value;
    console.log('📅 Fecha:', fecha);
    
    var fechaForm = document.getElementById('fecha-form');
    if (fechaForm) fechaForm.value = fecha;
    
    var salaIdInput = document.getElementById('sala_id');
    if (salaIdInput) salaIdInput.value = salaActual;
    
    var formReserva = document.getElementById('form-reserva-rapida');
    if (formReserva) formReserva.style.display = 'none';
    
    if (!esDiaHabil(fecha)) {
        var contenedor = document.getElementById('calendario-bloques');
        if (contenedor) {
            contenedor.innerHTML = '<div class="mensaje-info">📅 Los fines de semana no están disponibles para reservar</div>';
        }
        var fechaTitulo = document.getElementById('fecha-titulo');
        if (fechaTitulo) fechaTitulo.textContent = formatearFecha(fecha) + ' (Fin de semana)';
        return;
    }
    
    var fechaTitulo = document.getElementById('fecha-titulo');
    if (fechaTitulo) fechaTitulo.textContent = formatearFecha(fecha);
    
    var url = '/calendario/' + salaActual + '?fecha=' + fecha;
    console.log('🌐 URL:', url);
    
    fetch(url)
        .then(function(response) {
            console.log('📡 Respuesta recibida, status:', response.status);
            return response.json();
        })
        .then(function(data) {
            console.log('📊 Datos recibidos:', data);
            if (data.error) {
                var contenedor = document.getElementById('calendario-bloques');
                if (contenedor) {
                    contenedor.innerHTML = '<div class="mensaje-info">' + data.error + '</div>';
                }
                return;
            }
            console.log('📊 Total eventos:', data.length);
            renderizarCalendario(data);
        })
        .catch(function(error) {
            console.error('❌ Error:', error);
            var contenedor = document.getElementById('calendario-bloques');
            if (contenedor) {
                contenedor.innerHTML = '<p class="error">❌ Error al cargar el calendario</p>';
            }
        });
}

function renderizarCalendario(reservas) {
    console.log('🎨 Renderizando calendario con', reservas.length, 'eventos');
    var contenedor = document.getElementById('calendario-bloques');
    if (!contenedor) {
        console.error('❌ No se encuentra el contenedor del calendario');
        return;
    }
    
    var capacidad = 0;
    for (var i = 0; i < reservas.length; i++) {
        if (reservas[i].tipo === 'info') {
            capacidad = reservas[i].capacidad || 0;
            break;
        }
    }
    
    var capacidadInfo = document.getElementById('capacidad-maxima');
    if (capacidadInfo) {
        capacidadInfo.textContent = capacidad || '--';
    }
    
    var numAlumnosInput = document.getElementById('num_alumnos');
    if (numAlumnosInput && capacidad) {
        numAlumnosInput.max = capacidad;
        numAlumnosInput.placeholder = 'Máx. ' + capacidad;
    }
    
    var eventos = [];
    for (var i = 0; i < reservas.length; i++) {
        if (reservas[i].tipo !== 'info') {
            eventos.push(reservas[i]);
        }
    }
    
    var html = '';
    
    for (var hora = 7; hora < 21; hora++) {
        var horaStr = String(hora).padStart(2, '0') + ':00';
        var horaFinStr = String(hora + 1).padStart(2, '0') + ':00';
        
        var evento = null;
        for (var j = 0; j < eventos.length; j++) {
            var r = eventos[j];
            var inicio = r.hora_inicio;
            var fin = r.hora_fin;
            if (horaStr >= inicio && horaStr < fin) {
                evento = r;
                break;
            }
        }
        
        if (evento) {
            var clase = '';
            var texto = '';
            var titulo = '';
            
            if (evento.es_clase) {
                clase = 'bloque-clase';
                texto = evento.usuario;
                titulo = '📚 Clase: ' + texto;
            } else if (evento.es_mia) {
                clase = 'bloque-ocupado-mio';
                texto = '👤 ' + evento.usuario + ' (Tú)';
                titulo = 'Mi reserva: ' + texto;
            } else {
                clase = 'bloque-ocupado';
                texto = '👤 ' + evento.usuario;
                titulo = 'Reservado por: ' + texto;
            }
            
            html += '<div class="bloque ' + clase + '" title="' + titulo + ' - ' + horaStr + ' a ' + horaFinStr + '">';
            html += '<span class="hora-bloque">' + horaStr + '</span>';
            html += '<span class="usuario-bloque">' + texto + '</span>';
            html += '</div>';
        } else {
            html += '<div class="bloque bloque-disponible" onclick="abrirReservaRapida(\'' + horaStr + '\', \'' + horaFinStr + '\')" title="Disponible - Haz clic para reservar">';
            html += '<span class="hora-bloque">' + horaStr + '</span>';
            html += '<span class="disponible-texto">✅ Disponible</span>';
            html += '</div>';
        }
    }
    
    contenedor.innerHTML = html;
    console.log('✅ Calendario renderizado correctamente');
}

// ---------- RESERVA RÁPIDA ----------
function abrirReservaRapida(horaInicio, horaFin) {
    console.log('📌 Abriendo reserva rápida:', horaInicio, '-', horaFin);
    var fecha = document.getElementById('fecha-select').value;
    
    document.getElementById('hora_inicio').value = horaInicio;
    document.getElementById('hora_fin').value = horaFin;
    document.getElementById('info-fecha').textContent = formatearFecha(fecha);
    document.getElementById('info-horario').textContent = horaInicio + ' - ' + horaFin;
    document.getElementById('form-reserva-rapida').style.display = 'block';
    
    document.getElementById('form-reserva-rapida').scrollIntoView({ behavior: 'smooth' });
}

function cerrarReservaRapida() {
    document.getElementById('form-reserva-rapida').style.display = 'none';
}

// ---------- INICIALIZACIÓN ----------
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando sistema...');
    
    var fechaInput = document.getElementById('fecha-select');
    if (!fechaInput) {
        console.error('❌ No se encuentra el selector de fecha');
        return;
    }
    
    var hoy = new Date();
    var año = hoy.getFullYear();
    var mes = String(hoy.getMonth() + 1).padStart(2, '0');
    var dia = String(hoy.getDate()).padStart(2, '0');
    var fechaHoy = año + '-' + mes + '-' + dia;
    
    console.log('📅 Fecha actual real:', fechaHoy);
    
    if (!esDiaHabil(fechaHoy)) {
        var siguienteHabil = obtenerSiguienteDiaHabil(fechaHoy);
        fechaInput.value = siguienteHabil;
        console.log('📅 Hoy es fin de semana, mostrando:', siguienteHabil);
    } else {
        fechaInput.value = fechaHoy;
        console.log('📅 Mostrando fecha actual:', fechaHoy);
    }
    
    var primeraSala = document.querySelector('.tab-sala');
    if (primeraSala) {
        var id = parseInt(primeraSala.dataset.sala);
        var nombre = primeraSala.textContent.trim().replace('🔒', '').trim();
        console.log('📌 Sala seleccionada:', id, nombre);
        seleccionarSala(id, nombre);
    } else {
        console.error('❌ No hay salas disponibles');
    }
    
    console.log('✅ Sistema inicializado correctamente');
});

console.log('✅ script.js completamente cargado');