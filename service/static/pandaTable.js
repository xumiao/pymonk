// TODO : move to better place
$.fn.serializeObject = function()
{
    var o = {};
    var a = this.serializeArray();
    $.each(a, function() {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
};

function PandaTable(config) {

    // Local Settings
    var _settings = {
        "svcs_host" : config["svcs_host"] || "",
        "collection_name" : config["collection_name"] || "",
        "table_selector" : config["table_selector"] || "#pandas",
        // Callback functions
        "fnOnClickRow": null,
        // Internal state
        "current_id" : null
    };

    /****************************************************************
     * Panda Table
     ****************************************************************/
    var _oPandaTableSettings = {
        /* "sDom": 'lfT<"clear">rtip', */
        /* "sDom" : '<"H"lfTr>t<"F"ip>', */
        "sDom" : "<'row-fluid'<'span6'lT><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>",
        "bJQueryUI": true,
        "bProcessing": true,
        "bServerSide": true,
        "sAjaxSource": _settings.svcs_host + "/panda.rpy/get",
        "oTableTools": {
            "aButtons": [
                {
                    "sExtends":    "text",
                    "sButtonClass": "btn-space",
                    "sButtonText": "New",
                    "fnClick": function ( nButton, oConfig, oFlash ) {
                        $('#modal-add-panda').modal('show');
                    },
                    "fnInit": function ( nButton, oConfig ) {
                        nButton.id = "btnAddPanda";
                    }
                },
                {
                    "sExtends":    "text",
                    "sButtonClass": "btn-space",
                    "sButtonText": "Delete",
                    "fnClick": function ( nButton, oConfig, oFlash ) {
                        $.get(_settings.svcs_host + "/panda.rpy/del",
                            {
                                "id" : _settings.current_id
                            }).done(function () {
                                _oTablePanda.fnReloadAjax();
                                $.pnotify({
                                    title: 'Classifier Deleted',
                                    text: 'Classifier Deleted',
                                    styling: 'bootstrap',
                                    delay: 1000
                                });
                                navbar_refresh_panda(null);
                            }).error(function () {
                                $.pnotify({
                                    title: 'Failed to delete classifier',
                                    text: 'Failed to delete classifier' + _settings.current_id,
                                    type: 'error',
                                    delay: 5000
                                });
                            });
                    },
                    "fnInit": function ( nButton, oConfig ) {
                        nButton.id = "btnDeletePanda";
                    }
                }
            ]
        },
        "fnServerParams": function ( aoData ) {
        },
        "fnServerData": function ( sSource, aoData, fnCallback ) {
            $.ajax({
                "dataType": 'json',
                "type": "GET",
                "url": sSource,
                "data": aoData,
                "timeout": 1000000,
                "success": fnCallback
            });
        },
        "fnRowCallback": function( nRow, aData, iDisplayIndex ) {
            /* set tr id. assume the id is in the first column of data */
            var id = aData["id"];
            $(nRow).attr("id", id);
            return nRow;
        },
        "aoColumns": [
            { "mDataProp": "id", "sWidth":"10%" },
            { "mDataProp": "name", "sWidth": "10%" },
            { "mDataProp": "type", "sWidth": "10%" },
            { "mDataProp": "className", "sWidth":"10%"},
            { "mDataProp": "slicing", "sWidth":"10%" },
            { "mDataProp": "parameters", "sWidth":"20%" },    
            { "mDataProp": "accuracy", "sWidth":"10%" },
            { "mDataProp": "experience", "sWidth": "10%" },
            { "mDataProp": "status", "sWidth": "10%", "class":"status" }
        ],
        "aoColumnDefs": [
            {
                "aTargets": [ 6 ],
                "bVisible": true,
                "mRender": function ( data, type, full ) {
                    return data.toFixed(4);
                }
            }
        ],
        "fnInitComplete": function (oSettings, json) {
        }
    };

	var _oTablePanda = $(_settings.table_selector).dataTable(_oPandaTableSettings);

    /*
     * UI event handling
     */
    $(document).on("click", _settings.table_selector + " tr", function(e) {
        var oData = _oTablePanda.fnGetData(this);
        if (oData == null || !("id" in oData)) {
            return;
        }

        var panda_id = oData["id"];
        var _this = $(this);
        _settings.current_id = panda_id;

        if(_this.hasClass("active")) {
            return;
        }
        var row = $(_this.closest("tr")[0])
        var status = row.find(".status")

        // Panda Select Row

        // deactivate old row
        $(_oTablePanda.fnSettings().aoData).each(function () {
            var nTr = this.nTr;
            if ($(nTr).hasClass("active")) {
                $('div.pandaInnerDetails', $(nTr).next()[0]).slideUp(function () {
                    _oTablePanda.fnClose(nTr);
                });
                $(nTr).removeClass('active');
            }
        });

        // Show details
        //var nDetailsRow = _oTablePanda.fnOpen(this, fnFormatPandaDetails(_settings.current_id), 'details');
        //$('div.pandaInnerDetails', nDetailsRow).slideDown();
        //_settings.feature_skip = 0;
        //_settings.feature_limit = 10;
        //fnShowPandaDetails(_settings.current_id, _settings.feature_skip, _settings.feature_limit);
        _this.addClass('active');

        /*
         * Callback function to do extra work
         */
        if ( typeof _settings.fnOnClickRow == 'function' && _settings.fnOnClickRow !== null ) {
            _settings.fnOnClickRow( oData );
        }
        
        if (status.html() == "idle")
        {
            status.html("loading")
            $.get(svcs_host + "/panda.rpy/load",
            {
                "pandaId": oData["id"],
            }).done(function ()
            {
                status.html("ready")
            });
        }
        else if (status.html() != "ready")
        {
            $.get(svcs_host + "/panda.rpy/status",
            {
                "pandaId": oData["id"],
            }).done(function (data)
            {
                status.html(data.status)
            });
        }

        $("button#save_trained_panda").button("enable");
        // Refresh Panda information on navbar
        navbar_refresh_panda(oData);
	});

    $(document).on('click', '#modal-form-add-panda-submit', function(e){
        // We don't want this to act as a link so cancel the link action
        e.preventDefault();
        $("#modal-form-add-panda-submit").button("loading");

        // Find form and submit it
        $('#modal-form-add-panda').submit();
    });

    $(document).on('submit', '#modal-form-add-panda', function(e) {
        var _base_params = $(this).serialize();
        var _param_array = $(this).serializeObject();
        var _types_need_updated = [""];

        $.ajax({
            url: _settings.svcs_host + "/panda.rpy/add",
            data: _base_params,
            success: function (data) {
                $.pnotify({
                    title: 'Add Classifier',
                    text: 'Add Classifier ' + _settings.current_id + " suceeded!",
                    styling: 'bootstrap',
                    delay: 1000
                });
            }
        });
        
        
        // Stop the normal form submission
        return false;
    });


    function fnShowPandaDetails(pandaId, nSkip, nLimit) {
    }

    function fnFormatPandaDetails(pandaId) {
        return '<div class="pandaInnerDetails" id="p' + pandaId + '"></div>';
    }

    /*
     * Build Object
     */
    this.oTable = _oTablePanda;
    this.settings = _settings;
    this.fnShowPandaDetails = fnShowPandaDetails;
    this.fnFormatPandaDetails = fnFormatPandaDetails;
}
