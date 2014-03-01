function FrameTable(config) {
    var _bSelectable = config["is_selectable"];

    // Local Settings
    var _settings = {
        "svcs_host" : config["svcs_host"] || "",
        "table_selector" : config["table_selector"] || "#frames",
        "collection_name" : config["collection_name"] || "EntityCollectionNotFound",
        "columns" : config["columns"] || [],
        "columns_search" : config["columns_search"] || [],
        "feature_skip" : 0,
        "feature_limit" : 10,
        "frame_limit" : 10,
        "entityId" : config["entityId"] || "",
        "className" : config["className"] || [],
        // Callback functions
        "fnOnClickRow" : null,
    };

    /*
     * Build columns of entity table
     */
    var _columns = [];
    for(var i = 0; i < _settings.columns.length; i++) {
        _columns.push({"mDataProp": _settings.columns[i]});
    }

    /*
     * Build aoColumnDefs
     */
    var _column_score = _columns.length - 2;   // Column for "Score"
    var _column_label = _columns.length - 1;   // Column for "Label Buttons"

    var frameColumnDefs = [
        {
            "aTargets": [ 0 ],
            "bVisible": false,
        },
        {
            "aTargets": [ _column_score ],
            "bVisible": true,
            "mRender": function ( data, type, full ) {
                return data.toFixed(4);
            }
        },
        {
            "aTargets": [ _column_label ],
            "bVisible": true,
            "mRender": function ( data, type, full ) {
                if (type == "display") {
                    return '<div class="btn-group" data-toggle="buttons-radio">' +
                           '    <button type="button" value="1"  class="btn btn-primary btn-training datalabel" > Down </button>' +
                           '    <button type="button" value="-1"  class="btn btn-primary btn-training datalabel" > &#160;Up&#160;&#160; </button>'   +
                           '</div>';
                }
                return data;
            }
        }
    ];

    var _sDom = "<'row-fluid'<'span6'lT><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>" + (_bSelectable ? "S" : "");

    /****************************************************************
     * Frame Table
     ****************************************************************/
    var _oFrameTableSettings = {
        "sDom": _sDom,
        "bProcessing": true,
        "bServerSide": true,
        "bjQueryUI": true,
        "sAjaxSource": _settings.svcs_host + "/entity.rpy/getFrames",
        "oTableTools": {
            "aButtons": []
        },
        "fnServerParams": function (aoData) {
            aoData.push({
                "name": "entityCollectionName",
                "value": _settings.collection_name
            });
            aoData.push({
                "name": "entityId",
                "value": _settings.entityId
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
            $.ajax( {
                "dataType": 'json',
                "type": "GET",
                "url": sSource,
                "data": aoData,
                "timeout": 100000,
                "success": fnCallback
            } );
        },
        "fnFormatNumber": function ( toFormat ) {
            return toFormat;
        },
        "aoColumns": _columns
    };

    _oFrameTableSettings["oSelectable"] = {
         iColNumber: 0
    }

    _oFrameTableSettings["aoColumnDefs"] = frameColumnDefs;

    var _oTableFrame = $(_settings.table_selector).dataTable(_oFrameTableSettings);

    $(document).on("click", "button.datalabel", function () {
        var str = "";
        var _this = $(this);
        var row = $(_this.closest("tr")[0])
        var irimg = row.find(".irimg")
        var colorimg = row.find(".colorimg")
        var oData = _oTableFrame.fnGetData(_this.closest("tr")[0]);
        var _frameId = oData["FrameId"];
        var _tagAction = _this.val();

        /*
         * Callback function to train current entity
         */
        if ( typeof _settings.fnOnClickLabel== 'function' && _settings.fnOnClickLabel !== null ) {
            _settings.fnOnClickLabel(_settings, _frameId, _tagAction);
        }
        
        /*
         * Refresh images
         */
        var d = new Date();
        var t = d.getTime();
        irimgsrc = irimg.attr("src") + "&time=" + t;
        colorimgsrc = colorimg.attr("src") + "&time=" + t;
        irimg.parent().html("<img class='irimg' src='" + irimgsrc + "'>");
        colorimg.parent().html("<img class='colorimg' src='" + colorimgsrc + "'>");
    });

    // Default Callback function for fnOnClickLabel
    function _fnOnClickLabel (_frameSettings, _entityId, _frameId, _tagAction) {
        console.log("Default fnOnClick : " + _entityId + " : " + _frameId + " " + _tagAction);
    }

    /*
     * Build Object
     */
    this.oTable = _oTableFrame;
    this.settings = _settings;
    this.settings.fnOnClickLabel = _fnOnClickLabel;
}
