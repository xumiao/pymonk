function myRefreshPandaDetail(pandaId) {
    var svcs_host = "";

    var positiveColor = "#1f77b4",
        negativeColor = "#d62728";

    d3.json(svcs_host + "/svcs/monk/panda/GetDetails?numLimit=20&pandaId=" + pandaId, function (error, data) {

        function mydata(predictor, sortOrderFun) {
            if(predictor == null || typeof(predictor) != "function"
                || sortOrderFun == null || typeof(sortOrderFun) != "function") {
                return [];
            }

            var idx;
            var newArr = new Array();

            data.forEach(function(d) {
                if(predictor(d)) {
                newArr.push({
                    "label": d.name,
                    "value": d.weight,
                    "uid": d.uid,
                    "pandaId": pandaId
                });
                }
            });

            var sortedNewArray = newArr.sort(function(a, b) {
                return sortOrderFun(a.value, b.value);
            });

            return new Array({
                "key": "Cumulative Return",
                "values": sortedNewArray
            });
        }
        
        var positiveChart = nv.addGraph(function () {
            var positiveData = mydata(function(d) { return d.weight > 0; }, d3.descending);
            
            var chart = nv.models.discreteBarChart()
                    .x(function(d) { return d.label })
                    .y(function(d) { return d.value })
                    .staggerLabels(true)
                    //.staggerLabels(historicalBarChart[0].values.length > 8)
                    .tooltips(false)
                    .showValues(true)
                    .color(function(d) {
                        return d.value > 0 ? positiveColor : negativeColor;
                    });

            d3.select("#x" + pandaId + " svg.positive")
                .datum(positiveData)
                .call(chart);

            chart.discretebar.dispatch.on("elementDblClick", function(e) {
                console.log(e);
            });
            
            nv.utils.windowResize(chart.update);

            return chart;
        });

        var negativeChart = nv.addGraph(function () {
            var negativeData = mydata(function (d) { return d.weight <= 0; }, d3.ascending);
            
            var chart = nv.models.discreteBarChart()
                .x(function(d) { return d.label })
                .y(function(d) { return d.value })
                .staggerLabels(true)
                //.staggerLabels(historicalBarChart[0].values.length > 8)
                .tooltips(false)
                .showValues(true)
                .color(function(d) {
                    return d.value > 0 ? positiveColor : negativeColor;
                });

            d3.select("#x" + pandaId + " svg.negative")
                .datum(negativeData)
                .call(chart);

            chart.discretebar.dispatch.on("elementDblClick", function(e) {
                console.log(e);
            });

            nv.utils.windowResize(chart.update);
            
            return chart;
        });

    });
}

function myRefreshTestingBarChart(data) {
    console.log(data);
    var myvals = [];

    var classfiersProbs = data.split(";");

    for (var i = 0; i < classfiersProbs.length; i++) {
        var kv = classfiersProbs[i].split(",");
        if(kv.length == 2) {
            myvals.push({
                "label": kv[0],
                "value": parseFloat(kv[1])
            });
        }
        if (i > 10)
            break;
    }

    var mydata = [{
        "key": "分类测试结果",
        /* "color": "#d62728", */
        "color": "#1f77b4",
        "values": myvals
    }];

    nv.addGraph(function() {
        var chart = nv.models.multiBarHorizontalChart()
            .x(function(d) { return d.label })
            .y(function(d) { return d.value })
            /* .margin({top: 30, right: 20, bottom: 50, left: 175}) */
            .margin({left: 100})
            .showValues(true)
            .tooltips(false)
            .showControls(false);

        chart.yAxis
            .tickFormat(d3.format(',.2f'));

        d3.select('svg.testing-result')
            .datum(mydata)
            .transition().duration(500)
            .call(chart);

        nv.utils.windowResize(chart.update);

        return chart;
    });
}