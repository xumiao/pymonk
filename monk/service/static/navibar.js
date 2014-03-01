$(document).ready( function () {
    // Button :: Save Panda
    $("button#savePanda" ).button({
        create: function( event, ui ) {
            $(this).button("disable");
        }
    }).click(function() {
        var pandaId = pandaTableObj.settings.current_id;
        if (pandaId) {
            $.get(svcs_host + "/panda.rpy/save",
              {
                  "pandaId" : pandaId
              }).done(function () {
                    $.pnotify({
                        title: 'Save Classifier',
                        text: 'Classifier ' + pandaId + " Done! ",
                        styling: 'bootstrap',
                        delay: 1000
                    });
              }).error(function () {
                    $.pnotify({
                        title: 'Save Classifer',
                        text: 'Failed to save classifier : ' + pandaId,
                        type: 'error',
                        delay: 1000
                    });
              });
        }
    });

    // Button :: train
    $("button#trainPanda").button({
        create: function (event, ui) {
        }
    }).click(function () {
        var pandaId = pandaTableObj.settings.current_id;
        if (pandaId) {
            $.get(svcs_host + "/panda.rpy/train",
            {
                "pandaId": pandaId
            }).done(function () {
                $.pnotify({
                    title: 'Train Classifier',
                    text: 'Training ' + pandaId + ' Started!',
                    styling: 'bootstrap',
                    delay: 1000
                });
            }).error(function () {
                $.pnotify({
                    title: 'Train Classifier',
                    text: 'Failed to start training ' + pandaId,
                    type: 'error',
                    delay: 1000
                });
            });
        }
        else {
            $.pnotify({
                title: 'No classifier selected',
                text: 'Failed!',
                styling: 'bootstrap',
                delay: 1000
            });
        }
    });

    // Button :: Testing
    $( "button#startTesting" ).click(function() {
        $('#modal-testing').modal('show');
    });

    // Button :: Start Testing
    $( "button#btn-start-testing").click(function (){
        var _this = $(this);
        $("button#btn-start-testing").button('loading');
    });

});

// Notification Functions
function navbar_refresh_panda(oData) {
    if (oData == null) {
        $("ul#selected-panda #panda-name").text("");
        $("ul#selected-panda #panda-className").text("");
        $("ul#selected-panda #panda-accuracy").text("");
        $("ul#selected-panda #panda-experience").text("");
    } else {
        $("ul#selected-panda #panda-name").text(oData["name"]);
        $("ul#selected-panda #panda-className").text(oData["className"]);
        $("ul#selected-panda #panda-accuracy").text(oData["accuracy"].toFixed(4));
        $("ul#selected-panda #panda-experience").text(oData["experience"]);
    }
}
