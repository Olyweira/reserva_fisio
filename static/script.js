document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM cargado. Empezando script.js...");

    // --- Gestión del Login (AJAX) ---
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        console.log("Formulario de login encontrado.");
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            console.log("Enviando petición de login. Usuario:", username, "Contraseña:", password);

            fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json', // Corregido: application/json
                },
                body: JSON.stringify({ // Corregido: JSON.stringify
                    username: username,
                    password: password
                })
            })
            .then(response => {
                console.log("Respuesta del servidor recibida (login):", response);
                return response.json();
            })
            .then(data => {
                console.log("Datos JSON recibidos (login):", data);
                if (data.success) {
                    console.log("Login exitoso. Guardando en sessionStorage...");
                    sessionStorage.setItem('logged_in', 'true');
                    sessionStorage.setItem('username', data.username);
                    sessionStorage.setItem('user_id', data.user_id);
                    console.log("Datos guardados en sessionStorage:", sessionStorage);
                    console.log("Redirigiendo a /");
                    window.location.href = '/'; // Redirigir.
                } else {
                    //Mostrar el mensaje de error en un div, si existe, y si no, en un alert.
                    const errorDiv = document.getElementById('error-message');
                    if (errorDiv) {
                        errorDiv.textContent = 'Error al iniciar sesión: ' + data.message;
                        errorDiv.style.display = 'block'; // Mostrar el div
                    } else {
                        alert('Error al iniciar sesión: ' + data.message);
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al conectar con el servidor.');
            });
        });
    } else {
        console.log("Formulario de login NO encontrado.");
    }


    // --- Formulario de Reserva (AJAX) ---
    const formReserva = document.getElementById('reserva-form');
    if (formReserva) {
        console.log("Formulario de reserva encontrado.");
        formReserva.addEventListener('submit', function(event) {
            event.preventDefault();

            const nombre = document.getElementById('nombre').value;
            const telefono = document.getElementById('telefono').value;
            const fecha = document.getElementById('fecha').value;
            const hora = document.getElementById('hora').value;
            const tratamiento = document.getElementById('tratamiento').value;
            const empleado_id = sessionStorage.getItem('user_id'); // Obtiene de sessionStorage
            const duracion = document.getElementById('duracion').value; // Obtiene la duración

            console.log("Enviando reserva. Datos:", nombre, telefono, fecha, hora, tratamiento, empleado_id, duracion);

            const reservaData = {
                nombre: nombre,
                telefono: telefono,
                fecha: fecha,
                hora: hora,
                tratamiento: tratamiento,
                empleado_id: empleado_id,
                duracion: duracion // Envía la duración al servidor
            };

            fetch('/reservar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(reservaData)
            })
            .then(response => response.json())
            .then(data => {
                console.log("Respuesta del servidor (reserva):", data);
                if (data.success) {
                    alert('Reserva realizada con éxito!');
                    formReserva.reset();
                    cargarCalendario(); // Recarga el calendario
                } else {
                    alert('Error al realizar la reserva: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al realizar la reserva.');
            });
        });
    } else {
        console.log("Formulario de reserva NO encontrado.");
    }

    // --- LOGOUT ---
    const logoutLink = document.querySelector('a[href="/logout"]');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(event) {
            event.preventDefault();
            fetch('/logout')
                .then(response => {
                    console.log(response);
                    if (response.ok) {
                        sessionStorage.clear();
                        window.location.href = '/';
                    } else {
                        console.error('Error al cerrar sesión');
                        alert('Error al cerrar sesión.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error al conectar con el servidor.');
                });
        });
    }

    // --- FullCalendar ---

    function cargarCalendario() {
        console.log("cargarCalendario() ejecutada");
        const empleadoSelect = document.getElementById('empleado-select');
        console.log("empleadoSelect:", empleadoSelect);
        let calendar; // Declara el calendario FUERA de inicializarCalendario

        function inicializarCalendario() {
            console.log("inicializarCalendario() ejecutada");
            // Destruye el calendario si ya existe
            if (calendar) {
                console.log("Destruyendo instancia anterior de FullCalendar...");
                calendar.destroy();
            }

            var calendarEl = document.getElementById('calendar');
            console.log("calendarEl:", calendarEl);
            if (!calendarEl) {
                console.error("Error: No se encontró el elemento 'calendar' en el DOM.");
                return; // Sale de la función
            }

            calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'timeGridDay',
                locale: 'es',
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridDay' // Solo dos vistas: Mes y Agenda
                },
                events: function(info, successCallback, failureCallback) {
                    var empleadoSeleccionado = empleadoSelect.value;
                    console.log("Obteniendo reservas para empleado:", empleadoSeleccionado);
                    let url = '/obtener_reservas';
                    if (empleadoSeleccionado !== 'mis_reservas') {
                        url += '?empleado=' + encodeURIComponent(empleadoSeleccionado);
                    }
                    console.log("URL de la petición:", url);

                    fetch(url)
                        .then(response => response.json())
                        .then(data => {
                            console.log("Reservas recibidas:", data);  // Añadir este log
                            successCallback(data.map(event => {
                                // Asignar colores según el tratamiento
                                if (event.extendedProps.tratamiento === 'fisioterapia') {
                                    event.backgroundColor = '#007bff'; // Azul
                                    event.borderColor = '#007bff';
                                } else if (event.extendedProps.tratamiento === 'indiba') {
                                    event.backgroundColor = '#ff0000'; // Rojo
                                    event.borderColor = '#ff0000';
                                }
                                return event;
                            }));
                        })
                        .catch(error => {
                            console.error("Error al obtener reservas:", error);
                            failureCallback(error);
                        });
                },
                eventSourceSuccess: function(content, xhr) {
                    console.log("eventSourceSuccess ejecutada. content:", content);
                    return content;
                },
                slotDuration: '00:30:00',
                slotMinTime: '09:00:00',
                slotMaxTime: '20:00:00',
                allDaySlot: false,
                eventContent: function(arg) {
                    // Personalizar el contenido del evento
                    const deleteButton = document.createElement('button');
                    deleteButton.textContent = 'X';
                    deleteButton.className = 'delete-event-btn';
                    deleteButton.onclick = function(event) {
                        event.stopPropagation(); // Evitar que se active el clic del evento
                        if (confirm('¿Estás seguro de que deseas eliminar esta reserva?')) {
                            fetch(`/eliminar_reserva/${arg.event.id}`, { // Usar el ID del evento
                                method: 'DELETE'
                            })
                            .then(response => {
                                if (response.ok) {
                                    arg.event.remove(); // Eliminar el evento del calendario
                                    alert('Reserva eliminada con éxito.');
                                } else {
                                    alert('Error al eliminar la reserva.');
                                }
                            })
                            .catch(error => {
                                console.error('Error:', error);
                                alert('Error al conectar con el servidor.');
                            });
                        }
                    };

                    const eventTitle = document.createElement('div');
                    eventTitle.textContent = arg.event.title;

                    const container = document.createElement('div');
                    container.appendChild(eventTitle);
                    container.appendChild(deleteButton);

                    return { domNodes: [container] };
                },
                height: 'auto', // Ajustar la altura del calendario automáticamente
                expandRows: true // Expandir filas para adaptarse al contenido
            });

            if(empleadoSelect){
                empleadoSelect.addEventListener('change', function() {
                    console.log("Selector de empleado cambiado. Nuevo valor:", empleadoSelect.value);
                    calendar.refetchEvents();
                });
            }

            console.log("Renderizando calendario...");
            calendar.render();
            console.log("Calendario renderizado (¿o no?).");
        }

        // --- Obtener Empleados y Llenar Selector ---
        if (empleadoSelect) {
            console.log("Selector de empleado encontrado.");
            fetch('/obtener_empleados')
                .then(response => response.json())
                .then(empleados => {
                    console.log("Empleados recibidos:", empleados);

                    // Limpiar opciones existentes (MUY IMPORTANTE)
                    empleadoSelect.innerHTML = '';

                    // Crear opciones "Todos" y "Mis Reservas"
                    const optionTodos = document.createElement('option');
                    optionTodos.value = 'todos';
                    optionTodos.text = 'Todos los empleados';
                    empleadoSelect.add(optionTodos);

                    const optionMisReservas = document.createElement('option');
                    optionMisReservas.value = 'mis_reservas';
                    optionMisReservas.text = 'Mis reservas';
                    empleadoSelect.add(optionMisReservas);

                    empleados.forEach(empleado => {
                        if (empleado.nombre !== 'admin') {  // Excluir la opción "admin"
                            const option = document.createElement('option');
                            option.value = empleado.id;
                            option.text = empleado.nombre;
                            empleadoSelect.add(option);
                        }
                    });

                    // Establecer opción por defecto (DESPUÉS de llenar el selector)
                    const loggedIn = sessionStorage.getItem('logged_in');
                    const username = sessionStorage.getItem('username');
                    const userId = sessionStorage.getItem('user_id');

                    console.log("logged_in:", loggedIn, "username:", username, "user_id:", userId);

                    if (loggedIn && username === 'admin') {
                        empleadoSelect.value = 'todos';
                        console.log("Selector establecido a 'todos' (admin).");
                    // Comprobación de empleado logueado
                    } else if (loggedIn && userId) {
                        // Intenta establecer el valor del selector al ID del usuario.
                        empleadoSelect.value = userId;
                        console.log("Intentando establecer selector a user_id:", userId);

                        // Si, después de intentar establecer el valor, el valor seleccionado *no* es el ID del
                        // usuario, significa que la opción no existe. En ese caso, establece 'mis_reservas'.
                        if (empleadoSelect.value !== String(userId)) {  // ¡Importante comparar como strings!
                            empleadoSelect.value = 'mis_reservas';
                            console.log("No se pudo establecer user_id, usando 'mis_reservas'.");
                        } else {
                            console.log("Selector establecido a user_id:", userId);
                        }
                    } else {
                        empleadoSelect.value = 'mis_reservas';
                        console.log("Selector establecido a 'mis_reservas'.");
                    }

                    inicializarCalendario(); // Inicializa FullCalendar DESPUÉS de todo lo anterior
                })
                .catch(error => console.error('Error al obtener la lista de empleados:', error));
        } else {
            console.log("Selector de empleado NO encontrado.");
        }
    }

    //Se comprueba que este el div, sino no se carga el calendario.
    if (document.getElementById('calendar')) {
        cargarCalendario();
    }
});