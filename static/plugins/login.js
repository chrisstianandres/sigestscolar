$(function () {
    validador();
    $("#formlogin").validate({
        rules: {
            username_login: {
                required: true,
                minlength: 2,
                maxlength: 150,
            },
            password_login: {
                required: true,
                minlength: 2,
                maxlength: 128,
            }
        },
        messages: {
            username_login: {
                required: 'Ingresa un nombre de usuario valido',
                minlength: "Ingrese al menos 2 caracteres",
                maxlength: "Ingrese maximo 150 caracteres"

            },
            password_login: {
                required: 'Ingresa una contraseña valida',
                minlength: "Ingrese al menos 2 caracteres",
                maxlength: "Ingrese maximo 128 caracteres"

            }
        }
    });

    $('#formlogin').on('submit', function (e) {
        e.preventDefault();
        if ($('#username_login').val() === "") {
            menssaje_error('Error!', "Debe ingresar un Username", 'far fa-times-circle');
            return false
        } else if ($('#password_login').val() === "") {
            menssaje_error('Error!', "Debe ingresar una contraseña", 'far fa-times-circle');
            return false
        }
        var parametros;
        parametros = {
            'username': $('#username_login').val(),
            'password': $('#password_login').val()
        };
        var isvalid = $(this).valid();
        if (isvalid) {
            var dialog  = bootbox.dialog({
                title: 'Estamos iniciando sesion!!!',
                message: '<p><i class="fa fa-spin fa-spinner"></i> Cargando tu sesion...</p>',
                size: 'small',
                centerVertical: true,
                closeButton: false,
            }).on('shown.bs.modal', function(){
                login( window.location.pathname, parametros, function (data) {
                    window.location.href = '/dashborad'});
                return false;
                 });

        }
    });

    $('#form_person').on('submit', function (e) {
    e.preventDefault();
    var parametros = new FormData(this);
    parametros.append('action', 'add');
    var isvalid = $(this).valid();
    if (isvalid) {
        save_with_ajax2('Alerta',
            '/register', 'Esta seguro que desea guardar este cliente?', parametros,
            function (response) {
                menssaje_ok('Exito!', 'Exito al registrarse, Su usuario y su contraseña son su numero de cedula!', 'far fa-smile-wink', function () {
                    window.location.href = '/login'
                });
            });
    }
});

});

jQuery(function ($) {
    $(document).on('click', '.toolbar a[data-target]', function (e) {
        e.preventDefault();
        var target = $(this).data('target');
        $('.widget-box.visible').removeClass('visible');//hide others
        $(target).addClass('visible');//show target
    });
});

//enviar formulario de nuevo cliente
