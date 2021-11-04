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
            login('/connect/', parametros, function (data) {
                $.isLoading({
                    text: "<strong>" + 'Iniciando Sesion...' + "</strong>",
                    tpl: '<span class="isloading-wrapper %wrapper%"><i class="fa fa-refresh fa-2x fa-spin"></i><br>%text%</span>',
                });
                setTimeout(function () {
                    $.isLoading('hide');
                    if (data.reset){
                        window.location.href = '/persona/reset'
                    }  else {window.location.href = '/menu';}
                }, 1000);
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
