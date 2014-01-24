function EntityTable(config) {
    var _bSelectable = config["is_selectable"];

    // Local Settings
    var _settings = {
        "svcs_host" : config["svcs_host"] || "",
        "table_selector" : config["table_selector"] || "#entity",
        "collection_name" : config["collection_name"] || "EntityCollectionNotFound",
        "columns" : config["columns"] || [],
        "columns_search" : config["columns_search"] || [],
        "feature_skip" : 0,
        "feature_limit" : 10,
        "entity_limit" : 10,
        "pandaId" : config["pandaId"] || "",
        "className" : config["className"] || [],
        // Callback functions
        "fnOnClickRow" : null,
    };

    /*
     * Build columns of entity table
     */
    var _columns = [];
    if (_bSelectable) {
        _columns.push({ "mDataProp": null });  // TODO : additional column for datatables.Selectable's "checkbox"
    }
    _columns.push({ "mDataProp": "id" });

    for(var i = 0; i < _settings.columns.length; i++) {
        _columns.push({"mDataProp": _settings.columns[i]});
    }

    var _sDom = "<'row-fluid'<'span6'lT><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>" + (_bSelectable ? "S" : "");

    /****************************************************************
     * Entity Table
     ****************************************************************/
    var anEntityOpen = [];
    var _oEntityTableSettings = {
        "sDom": _sDom,
        "bProcessing": true,
        "bServerSide": true,
        "bjQueryUI": true,
        "sAjaxSource": _settings.svcs_host + "/entity.rpy/get",
        "oTableTools": {
            "aButtons": []
        },
        "fnServerParams": function (aoData) {
            aoData.push({
                "name": "entityCollectionName",
                "value": _settings.collection_name
            });
            aoData.push({
                "name": "columns",
                "value": _settings.columns.join(",")
            });
            aoData.push({
                "name": "searchColumns",
                "value": _settings.columns_search.join(",")
            });
        },
        "fnServerData": function ( sSource, aoData, fnCallback ) {
            $.ajax({
                "dataType": 'json',
                "type": "GET",
                "url": sSource,
                "data": aoData,
                "timeout": 100000,
                "success": fnCallback
            });
        },
        "fnFormatNumber": function ( toFormat ) {
            return toFormat;
        },
        "aoColumns": _columns
    };

    // Selectable ?
    if (_bSelectable) {
        _oEntityTableSettings["oSelectable"] = {
            iColNumber: 2,
            sIdColumnName: 'ID',
            bSingleRowSelect: true,
            bShowControls: false,
            sSelectionTrigger: 'row',
            // Classes customization
            sSelectedRowClass: 'active',

            fnSelectionChanged: function(selection) {
                if (selection.fnGetSize() > 0) {
                    console.log(selection);
                }
            }
        };
    } else {
        _oEntityTableSettings["oSelectable"] = {
            iColNumber: 0
        }
    }

    var _oTableEntity = $(_settings.table_selector).dataTable(_oEntityTableSettings);

    $(document).on("click", _settings.table_selector + " tr", function(e) {
        var oData = _oTableEntity.fnGetData(this);
        if (oData == null || !("id" in oData)) {
            return;
        }
        var _this = $(this);

        if(_this.hasClass("active")) {
            return;
        }
        // deactivate old row
        $(_oTableEntity.fnSettings().aoData).each(function () {
            var nTr = this.nTr;
            if ($(nTr).hasClass("active")) {
                $(nTr).removeClass('active');
            }
        });
        _this.addClass('active');

        if ( typeof _settings.fnOnClickRow == 'function' && _settings.fnOnClickRow !== null ) {
            _settings.fnOnClickRow( oData );
        }
	});

    /*
     * Build Object
     */
    this.oTable = _oTableEntity;
    this.settings = _settings;
}
