<<<<<<< HEAD
document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM cargado. Empezando script.js...");

    const calendarEl = document.getElementById('calendar');

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: window.innerWidth < 768 ? 'listWeek' : 'dayGridMonth', // Vista adaptativa
        locale: 'es',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,agendaButton' // Botón personalizado "Agenda"
        },
        customButtons: {
            agendaButton: {
                text: 'Agenda', // Texto del botón
                click: function () {
                    // Cambiar la vista del calendario a estilo agenda
                    calendar.changeView('listWeek');
                }
            }
        },
        events: '/obtener_reservas', // Ruta para obtener eventos
        dateClick: function (info) {
            // Mostrar un cuadro de diálogo para agendar una nueva reserva
            const nombreCliente = prompt('Ingrese el nombre del cliente:');
            if (!nombreCliente) return;

            const telefonoCliente = prompt('Ingrese el número de teléfono del cliente:');
            if (!telefonoCliente) return;

            const tratamiento = prompt('Ingrese el tratamiento (Indiba o Fisioterapia):');
            if (!tratamiento) return;

            // Crear la nueva reserva
            const nuevaReserva = {
                nombre: nombreCliente,
                telefono: telefonoCliente,
                fecha: info.dateStr,
                hora: '10:00', // Puedes ajustar esto para permitir seleccionar la hora
                tratamiento: tratamiento,
                duracion: 30 // Duración predeterminada de 30 minutos
            };

            fetch('/reservar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(nuevaReserva)
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        alert('Reserva creada exitosamente.');
                        calendar.refetchEvents(); // Recargar los eventos del calendario
                    } else {
                        alert(`Error al crear la reserva: ${result.message}`);
                    }
                })
                .catch(error => {
                    console.error('Error al crear la reserva:', error);
                    alert('Ocurrió un error al intentar crear la reserva.');
                });
        },
        eventContent: function (arg) {
            // Personaliza el contenido del evento para incluir un botón de eliminación
            const title = arg.event.title || '';
            const deleteButton = `<button class="delete-event-btn" onclick="deleteEvent('${arg.event.id}')">❌</button>`;
            return {
                html: `<div style="white-space: pre-wrap; font-size: 0.9rem;">
                            ${title}
                            <div style="text-align: right; margin-top: 5px;">${deleteButton}</div>
                       </div>`
            };
        },
        eventClassNames: function (arg) {
            // Asigna una clase CSS según el tratamiento
            const tratamiento = arg.event.extendedProps.tratamiento.toLowerCase();
            if (tratamiento === 'indiba') {
                return ['evento-indiba'];
            } else if (tratamiento === 'fisioterapia') {
                return ['evento-fisioterapia'];
            }
            return ['evento-default']; // Clase por defecto
        }
    });

    calendar.render();

    setInterval(function () {
        calendar.refetchEvents(); // Recarga los eventos desde el servidor
    }, 60000); // Cada 60 segundos
});

// Función para eliminar un evento
function deleteEvent(eventId) {
    const confirmDelete = confirm('¿Deseas eliminar esta reserva?');
    if (confirmDelete) {
        fetch('/eliminar_reserva', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: eventId })
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert('Reserva eliminada exitosamente.');
                    location.reload(); // Recargar la página para actualizar el calendario
                } else {
                    alert(`Error al eliminar la reserva: ${result.message}`);
                }
            })
            .catch(error => {
                console.error('Error al eliminar la reserva:', error);
                alert('Ocurrió un error al intentar eliminar la reserva.');
            });
    }
}

document.getElementById('reserva-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Evitar el envío del formulario por defecto

    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());

    fetch('/reservar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert(result.message); // Reserva creada exitosamente
            location.reload(); // Recargar la página para actualizar el calendario
        } else {
            alert(`Error: ${result.message}`); // Mostrar mensaje de error
        }
    })
    .catch(error => {
        console.error('Error al enviar la reserva:', error);
        alert('Ocurrió un error al intentar crear la reserva.');
    });
=======
document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM cargado. Empezando script.js...");

    const calendarEl = document.getElementById('calendar');

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: window.innerWidth < 768 ? 'listWeek' : 'dayGridMonth', // Vista adaptativa
        locale: 'es',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,agendaButton' // Botón personalizado "Agenda"
        },
        customButtons: {
            agendaButton: {
                text: 'Agenda', // Texto del botón
                click: function () {
                    // Cambiar la vista del calendario a estilo agenda
                    calendar.changeView('listWeek');
                }
            }
        },
        events: '/obtener_reservas', // Ruta para obtener eventos
        dateClick: function (info) {
            // Mostrar un cuadro de diálogo para agendar una nueva reserva
            const nombreCliente = prompt('Ingrese el nombre del cliente:');
            if (!nombreCliente) return;

            const telefonoCliente = prompt('Ingrese el número de teléfono del cliente:');
            if (!telefonoCliente) return;

            const tratamiento = prompt('Ingrese el tratamiento (Indiba o Fisioterapia):');
            if (!tratamiento) return;

            // Crear la nueva reserva
            const nuevaReserva = {
                nombre: nombreCliente,
                telefono: telefonoCliente,
                fecha: info.dateStr,
                hora: '10:00', // Puedes ajustar esto para permitir seleccionar la hora
                tratamiento: tratamiento,
                duracion: 30 // Duración predeterminada de 30 minutos
            };

            fetch('/reservar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(nuevaReserva)
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        alert('Reserva creada exitosamente.');
                        calendar.refetchEvents(); // Recargar los eventos del calendario
                    } else {
                        alert(`Error al crear la reserva: ${result.message}`);
                    }
                })
                .catch(error => {
                    console.error('Error al crear la reserva:', error);
                    alert('Ocurrió un error al intentar crear la reserva.');
                });
        },
        eventContent: function (arg) {
            // Personaliza el contenido del evento para incluir un botón de eliminación
            const title = arg.event.title || '';
            const deleteButton = `<button class="delete-event-btn" onclick="deleteEvent('${arg.event.id}')">❌</button>`;
            return {
                html: `<div style="white-space: pre-wrap; font-size: 0.9rem;">
                            ${title}
                            <div style="text-align: right; margin-top: 5px;">${deleteButton}</div>
                       </div>`
            };
        },
        eventClassNames: function (arg) {
            // Asigna una clase CSS según el tratamiento
            const tratamiento = arg.event.extendedProps.tratamiento.toLowerCase();
            if (tratamiento === 'indiba') {
                return ['evento-indiba'];
            } else if (tratamiento === 'fisioterapia') {
                return ['evento-fisioterapia'];
            }
            return ['evento-default']; // Clase por defecto
        }
    });

    calendar.render();

    setInterval(function () {
        calendar.refetchEvents(); // Recarga los eventos desde el servidor
    }, 60000); // Cada 60 segundos
});

// Función para eliminar un evento
function deleteEvent(eventId) {
    const confirmDelete = confirm('¿Deseas eliminar esta reserva?');
    if (confirmDelete) {
        fetch('/eliminar_reserva', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: eventId })
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert('Reserva eliminada exitosamente.');
                    location.reload(); // Recargar la página para actualizar el calendario
                } else {
                    alert(`Error al eliminar la reserva: ${result.message}`);
                }
            })
            .catch(error => {
                console.error('Error al eliminar la reserva:', error);
                alert('Ocurrió un error al intentar eliminar la reserva.');
            });
    }
}

document.getElementById('reserva-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Evitar el envío del formulario por defecto

    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());

    fetch('/reservar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert(result.message); // Reserva creada exitosamente
            location.reload(); // Recargar la página para actualizar el calendario
        } else {
            alert(`Error: ${result.message}`); // Mostrar mensaje de error
        }
    })
    .catch(error => {
        console.error('Error al enviar la reserva:', error);
        alert('Ocurrió un error al intentar crear la reserva.');
    });
>>>>>>> 47bf082f8800ac5a939d84ba2b19b9916c3f30ea
});