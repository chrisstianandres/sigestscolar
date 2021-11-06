var tbl_productos;

// function mostrar() {
//     $('#div_table').removeClass('col-xl-12').addClass('col-xl-8 col-lg-12');
//     $('#div_form').show();
//     datatable.destroy();
//     datatable_fun();
//     $('#nuevo').hide();
// }
//
// function ocultar(form) {
//     reset(form);
//     $('#div_table').removeClass('col-xl-8 col-lg-12').addClass('col-xl-12');
//     $('#div_form').hide();
//     datatable.destroy();
//     datatable_fun();
//     $('#nuevo').show();
// }
//
// $('#cancel').on('click', function () {
//     $('#div_table').removeClass('col-xl-8 col-lg-12').addClass('col-xl-12');
//     ocultar('#form');
// });
//

function borrar_todo_alert(title, content, callback, callback2) {
    Swal.fire({
        title: title,
        html: content,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: '<i class="fa fa-thumbs-o-up"></i> Si',
        cancelButtonText: '<i class="fa fa-thumbs-down"></i> No'
    }).then((result) => {
        if (result.isConfirmed) {
            callback();
        }
    })
}

//
function save_with_ajax(title, url, content, parametros, callback) {
    Swal.fire({
        title: title,
        text: content,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Si',
        cancelButtonText: 'No'
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                dataType: 'JSON',
                type: 'POST',
                url: url,
                data: parametros,
            }).done(function (data) {
                if (!data.hasOwnProperty('error')) {
                    $.isLoading({
                        text: "<strong>" + 'Cargando..' + "</strong>",
                        tpl: '<span class="isloading-wrapper %wrapper%"><i class="fa fa-refresh fa-2x fa-spin"></i><br>%text%</span>',
                    });
                    setTimeout(function () {
                        $.isLoading('hide');
                        callback(data);
                    }, 1000);
                    return false;
                }
                menssaje_error('Error', data.error, 'fas fa-exclamation-circle');

            }).fail(function (jqXHR, textStatus, errorThrown) {
                alert(textStatus + ': ' + errorThrown);
            });
        }
    })
}

function callback(response) {
    printpdf('Alerta!', '¿Desea generar el comprobante en PDF?', function () {
        window.open('/venta/printpdf/' + response['id'], '_blank');
        // location.href = '/venta/printpdf/' + response['id'];
        localStorage.clear();
        location.href = '/venta/lista';
    }, function () {
        localStorage.clear();
        location.href = '/venta/lista';
    })

}

function callback_2(response, entidad) {
    printpdf('Alerta!', '¿Desea generar el comprobante en PDF?', function () {
        window.open('/' + entidad + '/printpdf/' + response['id'], '_blank');
        localStorage.clear();
        location.href = '/' + entidad + '/lista';
    }, function () {
        localStorage.clear();
        location.href = '/' + entidad + '/lista';
    })

}

function save_estado(title, url, content, parametros, callback) {
    Swal.fire({
        title: title,
        text: content,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Si',
        cancelButtonText: 'No'
    }).then((result) => {
        if (result.isConfirmed) {
             var dialog  = bootbox.dialog({
                title: 'Estamos procesando!!!',
                message: '<p><i class="fa fa-spin fa-spinner"></i> Cargando...</p>',
                size: 'small',
                centerVertical: true,
                closeButton: false,
            })
                 .on('shown.bs.modal', function(){
                     $.ajax({
                         dataType: 'JSON',
                         type: 'POST',
                         url: url,
                         data: parametros,
                     }).done(function (data) {
                         dialog.modal('hide');
                         if (!data.hasOwnProperty('error')) {
                             callback(data);
                             return false;
                         }
                         menssaje_error(data.error, data.content, 'fa fa-times-circle');
                     })
                         .fail(function (jqXHR, textStatus, errorThrown) {
                             dialog.modal('hide');
                             alert(textStatus + ': ' + errorThrown);
                         });
                 });

        }
    })
}

function printpdf(title, content, callback, cancel) {
    Swal.fire({
        title: title,
        text: content,
        icon: 'info',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'si',
        cancelButtonText: 'no'
    }).then((result) => {
        if (result.isConfirmed) {
            callback();
        } else {
            cancel();
        }
    });
}

function preguntar(title, content, callback, cancel, nada) {
    Swal.fire({
        title: title,
        text: content,
        icon: 'info',
        showCancelButton: true,
        showDenyButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        denyButtonColor: '#008000',
        confirmButtonText: '<i class="fa fa-pencil-square-o" aria-hidden="true"></i> Editar',
        cancelButtonText: '<i class="fa fa-ban" aria-hidden="true"></i> Cerrar Ventana',
        denyButtonText: '<i class="fa fa-money" aria-hidden="true"></i> Facturar',
    }).then((result) => {
        if (result.isConfirmed) {
            callback();
        } else if (result.isDenied){
            cancel();
        } else{
            nada();
        }
    });
}
function preguntar2(title, content, callback, cancel, nada) {
    Swal.fire({
        title: title,
        text: content,
        icon: 'info',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: '<i class="fa fa-pencil-square-o" aria-hidden="true"></i> Editar',
        cancelButtonText: '<i class="fa fa-ban" aria-hidden="true"></i> Cerrar Ventana',
    }).then((result) => {
        if (result.isConfirmed) {
            callback();
        } else if (result.isDenied){
             nada();
        }
    });
}

function menssaje_error(title, content, icon, callback) {
    var obj = Swal.fire(
        title,
        content,
        'error'
    );
    setTimeout(function () {
        // some point in future.
        obj.close();
    }, 3000);
}

function error_login(title, content, icon, callback) {
    Swal.fire({
            title: title,
            text: content,
            icon: 'error',
        }
    ).then((result) => {
        if (result.isConfirmed) {
            callback();
        }
    });
}

function menssaje_ok(title, content, icon, callback) {
    Swal.fire({
            title: title,
            text: content,
            icon: 'success',
        }
    ).then((result) => {
        if (result.isConfirmed) {
            callback();

        }
    });
}

function login(url, parametros, callback, callback2) {
    $.ajax({
        dataType: 'JSON',
        type: 'POST',
        url: url,
        data: parametros,
    }).done(function (data) {
        if (!data.hasOwnProperty('error')) {
            callback(data);
            return false;
        }
        menssaje_error('Error!', data.error, 'far fa-times-circle');
    }).fail(function (jqXHR, textStatus, errorThrown) {
        alert(textStatus + ': ' + errorThrown);
    })


}

function save_with_ajax2(title, url, content, parametros, callback) {
    Swal.fire({
        title: title,
        text: content,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Si',
        cancelButtonText: 'No'
    }).then((result) => {
        if (result.isConfirmed) {
            var dialog  = bootbox.dialog({
                title: 'Estamos procesando!!!',
                message: '<p><i class="fa fa-spin fa-spinner"></i> Cargando...</p>',
                size: 'small',
                centerVertical: true,
                closeButton: false,
            })
                .on('shown.bs.modal', function(){
                    $.ajax({
                        dataType: 'JSON',
                        type: 'POST',
                        url: url,
                        processData: false,
                        contentType: false,
                        data: parametros,
                    }).done(function (data) {
                         dialog.modal('hide');
                        if (!data.hasOwnProperty('error')) {
                            callback(data);
                            return false;
                        }
                        menssaje_error_form('Error', data.error, 'fa fa-ban');
                    }).fail(function (jqXHR, textStatus, errorThrown) {
                        dialog.modal('hide');
                        alert(textStatus + ': ' + errorThrown);
                    });
                });
        }
    })
}


function reset_form(formulario) {
    let form = $(formulario);
    var validator = form.validate();
    validator.resetForm();
    form[0].reset();
    $('.is-invalid').removeClass('is-invalid');
    $('.is-valid').removeClass('is-valid');
}

function menssaje_error_form(title, content, icon, callback) {
    var html = '<ul>';
    if(typeof content==='string'){
         html +=content;
    }else {
        $.each(content, function (key, value) {
            html += key + ': ' + value+'<br>';
        });
    }
    html += '</ul>';
    Swal.fire({
        title: title,
        icon: 'error',
        html: html,
        confirmButtonText:
            '<i class="fa fa-thumbs-up"></i> OK!',
    });
}


// function borrar_producto_carito(title, content, callback) {
//     var obj = $.dialog({
//         icon: 'fa fa-spinner fa-spin',
//         title: title,
//         content: content,
//         type: 'blue',
//         typeAnimated: true,
//         draggable: true,
//         onClose: function () {
//             callback();
//         },
//     });
//     setTimeout(function () {
//         // some point in future.
//         obj.close();
//     }, 2000);
//
//
// }
//
//
function customize(doc) {
    const monthNames = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
        "Noviembre", "Diciembre"
    ];
    var date = new Date();

    function formatDateToString(date) {
        // 01, 02, 03, ... 29, 30, 31
        var dd = (date.getDate() < 10 ? '0' : '') + date.getDate();
        // 01, 02, 03, ... 10, 11, 12
        // month < 10 ? '0' + month : '' + month; // ('' + month) for string result
        var MM = monthNames[date.getMonth() + 1]; //monthNames[d.getMonth()])
        // 1970, 1971, ... 2015, 2016, ...
        var yyyy = date.getFullYear();
        // create the format you want
        return (dd + " de " + MM + " de " + yyyy);
    }

    var jsDate = formatDateToString(date);
    //[izquierda, arriba, derecha, abajo]
    doc.pageMargins = [25, 50, 25, 50];
    doc.defaultStyle.fontSize = 12;
    doc.styles.tableHeader.fontSize = 12;
    doc.content[1].table.body[0].forEach(function (h) {
        h.fillColor = '#B86E8A'
    });
    doc.styles.title = {color: '#000000', fontSize: '16', alignment: 'center'};
    doc['header'] = (function () {
        return {
            columns: [
                {
                    text: $("#nombre_empresa").val() + '\n\n', fontSize: 30,
                    alignment: 'center',
                },
                // {
                //     text: $('#direccion_empresa').val(), fontSize: 45, alignment: 'center', margin: [-90, 33, 0]
                // },
            ],
            margin: [20, 10, 0, 0],  //[izquierda, arriba, derecha, abajo]


        }
    });
    doc['footer'] = (function (page, pages) {
        return {
            columns: [
                {
                    alignment: 'left',
                    text: ['Reporte creado el: ', {text: jsDate.toString()}]
                },
                {
                    alignment: 'right',
                    text: ['Pagina ', {text: page.toString()}, ' de ', {text: pages.toString()}]
                }
            ],
            margin: 20
        }
    });
    var objLayout = {};
    objLayout['hLineWidth'] = function (i) {
        return .5;
    };
    objLayout['vLineWidth'] = function (i) {
        return .5;
    };
    objLayout['hLineColor'] = function (i) {
        return '#000000';
    };
    objLayout['vLineColor'] = function (i) {
        return '#000000';
    };
    objLayout['paddingLeft'] = function (i) {
        return 4;
    };
    objLayout['paddingRight'] = function (i) {
        return 4;
    };
    doc.content[0].layout = objLayout;
    doc.content[1].table.widths = Array(doc.content[1].table.body[0].length + 2).join('*').split('');
    doc.styles.tableBodyEven.alignment = 'center';
    doc.styles.tableBodyOdd.alignment = 'center';
}

function customize_report(doc) {
    const monthNames = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
        "Noviembre", "Diciembre"
    ];
    var date = new Date();

    function formatDateToString(date) {
        // 01, 02, 03, ... 29, 30, 31
        var dd = (date.getDate() < 10 ? '0' : '') + date.getDate();
        // 01, 02, 03, ... 10, 11, 12
        // month < 10 ? '0' + month : '' + month; // ('' + month) for string result
        var MM = monthNames[date.getMonth() + 1]; //monthNames[d.getMonth()])
        // 1970, 1971, ... 2015, 2016, ...
        var yyyy = date.getFullYear();
        // create the format you want
        return (dd + " de " + MM + " de " + yyyy);
    }

    var jsDate = formatDateToString(date);
    //[izquierda, arriba, derecha, abajo]
    doc.pageMargins = [25, 50, 25, 50];
    doc.defaultStyle.fontSize = 12;
    doc.styles.tableHeader.fontSize = 12;
    doc.content[1].table.body[0].forEach(function (h) {
        h.fillColor = '#97af83'
    });
    doc.content[1].table.body[doc.content[1].table.body.length - 1].forEach(function (h) {
        h.fillColor = '#97AF83'
    });
    doc.styles.title = {color: '#2D1D10', fontSize: '16', alignment: 'center'};
    doc['header'] = (function () {
        return {
            columns: [
                {
                    text: $("#nombre_empresa").val() + '\n\n', fontSize: 30,
                    alignment: 'center',
                },
                // {
                //     text: $('#direccion_empresa').val(), fontSize: 45, alignment: 'center', margin: [-90, 33, 0]
                // },
            ],
            margin: [20, 10, 0, 0],  //[izquierda, arriba, derecha, abajo]


        }
    });
    doc['footer'] = (function (page, pages) {
        return {
            columns: [
                {
                    alignment: 'left',
                    text: ['Reporte creado el: ', {text: jsDate.toString()}]
                },
                {
                    alignment: 'right',
                    text: ['Pagina ', {text: page.toString()}, ' de ', {text: pages.toString()}]
                }
            ],
            margin: 20
        }
    });
    var objLayout = {};
    objLayout['hLineWidth'] = function (i) {
        return .5;
    };
    objLayout['vLineWidth'] = function (i) {
        return .5;
    };
    objLayout['hLineColor'] = function (i) {
        return '#000000';
    };
    objLayout['vLineColor'] = function (i) {
        return '#000000';
    };
    objLayout['paddingLeft'] = function (i) {
        return 4;
    };
    objLayout['paddingRight'] = function (i) {
        return 4;
    };
    doc.content[0].layout = objLayout;
    doc.content[1].table.widths = Array(doc.content[1].table.body[0].length + 1).join('*').split('');
    doc.styles.tableBodyEven.alignment = 'center';
    doc.styles.tableBodyOdd.alignment = 'center';
}
function validateEmail($email) {
  var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
  return emailReg.test( $email );
}
function validador() {
    jQuery.validator.addMethod("lettersonly", function (value, element) {
        return this.optional(element) || /^[a-z," "]+$/i.test(value);
    }, "Solo puede ingresar letras y espacios");

    $.validator.addMethod("tipo", function (value, element) {
        var tipo = $("#id_tipo").val();
        if (tipo === '0') {
            return ((value.length === 10));
        } else if (tipo === '1') {
            return ((value.length === 13));
        }
    }, "");
    $.validator.addMethod("email_valido", function (value, element) {
      return validateEmail(value);
    }, "");
    ///^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/


    $.validator.setDefaults({
        errorClass: 'error invalid-feedback',
        highlight: function (element, errorClass, validClass) {
            $(element).addClass("is-invalid").removeClass("is-valid");
        },
        unhighlight: function (element, errorClass, validClass) {
            $(element).addClass("is-valid").removeClass("is-invalid");
        }
    });

    jQuery.validator.addMethod("validar", function (value, element) {
        return validar(element);
    }, "Número de documento no valido para Ecuador");

    function validar(element) {
        var cad = document.getElementById(element.id).value.trim();
        var total = 0;
        var longitud = cad.length;
        var longcheck = longitud - 1;
        if (longitud === 10) {
            return aux(total, cad);
        } else if (longitud === 13 && cad.slice(10, 13) === '001') {
            return aux(total, cad);
        } else {
            return false;
        }
    }

    function aux(total, cad) {
        if (cad !== "") {
            for (var i = 0; i < 9; i++) {
                if (i % 2 === 0) {
                    var aux = cad.charAt(i) * 2;
                    if (aux > 9) aux -= 9;
                    total += aux;
                } else {
                    total += parseInt(cad.charAt(i)); // parseInt o concatenará en lugar de sumar
                }
            }

            total = total % 10 ? 10 - total % 10 : 0;
            return parseInt(cad.charAt(9)) === total;
        }
    }
}


function year_footer() {
    var ano = (new Date).getFullYear();
    $('#year').text(ano);

}


function salir() {
    var parametros = {'data': ''};
    save_estado('Cerrando Sesion', '/logout', 'Esta Seguro que quieres cerrar sesion?', parametros, function () {
        window.location.href = '/login';
    })
}

function titleCase(texto) {
    const re = /(^|[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ])(?:([a-záéíóúüñ])|([A-ZÁÉÍÓÚÜÑ]))|([A-ZÁÉÍÓÚÜÑ]+)/gu;
    return texto.replace(re,
        (m, caracterPrevio, minuscInicial, mayuscInicial, mayuscIntermedias) => {
            const locale = ['es', 'gl', 'ca', 'pt', 'en'];
            if (mayuscIntermedias)
                return mayuscIntermedias.toLocaleLowerCase(locale);
            return caracterPrevio + (minuscInicial ? minuscInicial.toLocaleUpperCase(locale) : mayuscInicial);
        }
    );
}


function ajax_sin_confirmar(url, parametros, callback) {
    $.ajax({
        dataType: 'JSON',
        type: 'GET',
        url: url,
        data: parametros,
    }).done(function (data) {
        if (!data.hasOwnProperty('error')) {
                callback(data);
            return false;
        }
        menssaje_error(data.error, data.content, 'fa fa-times-circle');
    });

}