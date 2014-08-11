function monitor(xmin, xmax, ymin, ymax, topic, metricName, metricWindowSize, metricStartPosition) {
xmax = typeof xmax !== "undefined" ? xmax : 0;
xmin = typeof xmin !== "undefined" ? xmin : -600;
ymax = typeof ymax !== "undefined" ? ymax : 2.0;
ymin = typeof ymin !== "undefined" ? ymin : -0.3;
topic = typeof topic !== "undefined" ? topic : "exprmetric";
metricName = typeof metricName !== "undefined" ? metricName : "|dq|/|q|";
metricWindowSize = typeof metricWindowSize !== "undefined" ? metricWindowSize : 10000;
metricStartPosition = typeof metricStartPosition !== "undefined" ? metricStartPosition : 0;

var formatTime = function(d) { return d; },
    format = d3.format(".2f"),
    formatHover = d3.format(".3f"),
    formatOrdinal = function (i) {
        var j = i % 10;
        if (j == 1 && i != 11) {
            return i + "st";
        }
        if (j == 2 && i != 12) {
            return i + "nd";
        }
        if (j == 3 && i != 13) {
            return i + "rd";
        }
        return i + "th";
    }

var selectedUser;

//
// main scatterplot at top
//

var margin = {top: 100, right: 55, bottom: 22, left: 55},
    width = 1024 - margin.left - margin.right,
    height = 640 - margin.top - margin.bottom,
    bounds = d3.geom.polygon([[0, 0], [0, height], [width, height], [width, 0]]);

var x = d3.scale.linear()
    .domain([xmin, xmax])
    .range([0, width]);

var y = d3.scale.linear()
    .domain([ymin, ymax])
    .range([height, 0]);

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom")
    .tickSize(4)
    .tickFormat(formatTime)
    .tickPadding(2);

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("right")
    .ticks(10)
    .tickPadding(10)
    .tickSize( -width);

d3.select(".g-main-chart").select("svg").selectAll("*").remove()	

var svg = d3.select(".g-main-chart").select("svg")
	.attr("width", (width + margin.left + margin.right))
	.attr("height", (height + margin.top + margin.bottom))
	.style("margin-top", 10 - margin.top + "px")
	.append("g")
	.attr("transform", "translate(" + margin.left + "," + margin.top + ")");
	
queue()
    .defer(d3.json, "http://monkzookeeper.cloudapp.net/users?topic="+topic+"&metricName="+metricName)
    .defer(d3.json, "http://monkzookeeper.cloudapp.net/metrics?topic="+topic+"&metricName="+metricName+"&start="+metricStartPosition)
    .await(ready)

function ready(err, users, metrics) {

  var userById = {};
  users.forEach(function(d) {
    userById[d.userId] = d;
  });

  metrics.forEach(function(d) {
      d.time = d.time;
      d.value = +d.value;
	  d.userId = +d.userId;
      d.user = userById[d.userId].name;
  });

  if (!("metrics" in window)){
	window.metrics = {};
  }
  
  if (!("users" in window)){
	window.users = {};
  }
  
  var wmetric = [];
  var wusers  = [];
  if (!(metricName in window.metrics) || metricStartPosition < 0){
	window.metrics[metricName] = metrics;
	wmetric = window.metrics[metricName];
  }else{
    wmetric = window.metrics[metricName];
	wmetric.push.apply(wmetric, metrics);
	if (wmetric.length > metricWindowSize){
		wmetric.splice(0, wmetric.length - metricWindowSize);
	}
  }
  
  if (!(metricName in window.users) || metricStartPosition < 0){
	window.users[metricName] = users;
	wusers = window.users[metricName];
  }else{
    wusers = window.users[metricName];
	users.push.apply(wusers, users);
  }
  
  //
  // main scatterplot
  //

  svg.append("g")
       .attr("class", "x axis")
       .attr("transform", "translate(0," + height + ")")
       .call(xAxis);

  svg.append("g")
      .attr("class", "y axis")
      .attr("transform", "translate(" + width + ",0)")
      .call(yAxis)
    .selectAll("g")
      .classed("minor", function(d,i) { return i !== 0; });

  var bounds = d3.geom.polygon([[0, 0], [0, height], [width, height], [width, 0]]);

  var avgData = drawLineChart(svg, wmetric, "value", x, y, width, height, 3, bounds);

  drawLegend(d3.select(".g-main-chart"));

  // Calculating max and min labels
  var highestMetric = 0,
      lowestMetric = Infinity,
      lowestTime,
      highestTime;

  avgData.forEach(function(d, i) {
    if (lowestMetric > d.values.avg) {
      lowestMetric = d.values.avg;
      lowestTime = d.key;
    }
    if (highestMetric < d.values.avg) {
      highestMetric = d.values.avg;
      highestTime = d.key;
    }
  });

  var highestLabel = svg.append("g")
      .attr("class", "g-mean-text g-hide-hover")
      .attr("transform", "translate(" + x(highestTime) + "," + y(highestMetric) + ")")

  highestLabel.append("text")
      .attr("class", "number")
      .attr("dy", "-10px")
      .text(format(highestMetric));

  highestLabel.append("text")
      .attr("class", "g-mean-label")
      .attr("dy", "-35px")
      .text("Metric average");

  highestLabel.append("text")
      .attr("class", "g-mean-label")
      .attr("dy", "-48px")
      .text(highestTime);

  highestLabel.append("circle")
      .attr("class", "g-highlight")
      .attr("r", 5.5);

  var lowestLabel = svg.append("g")
      .attr("class", "g-mean-text g-hide-hover")
      .attr("transform", "translate(" + x(lowestTime) + "," + y(lowestMetric) + ")")

  lowestLabel.append("text")
      .attr("class", "number")
      .attr("dy", "30px")
      .text(format(lowestMetric));

  lowestLabel.append("text")
      .attr("class", "g-mean-label")
      .attr("dy", "45px")
      .text("Metric average");

  lowestLabel.append("text")
      .attr("class", "g-mean-label")
      .attr("dy", "60px")
      .text(lowestTime);

  lowestLabel.append("circle")
      .attr("class", "g-highlight")
      .attr("r", 5.5);

  var arrow = [[0, 0], [3, 4], [-3, 4], [0, 0]];

  // Annotations

  // svg.append("line")
      // .attr("x1", x(1917))
      // .attr("y1", y(3.46))
      // .attr("x2", x(1917))
      // .attr("y2", y(1) - 13)
      // .classed("annotation-line",true);

  // svg.selectAll(".g-note")
      // .data([
        // "U.S. enters",
        // "World War I."
      // ])
    // .enter().append("text")
    // .classed("g-text-annotation",true)
    // .attr("x", x(1917))
    // .attr("y", y(1.08))
    // .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    // .text(function(d) { return d; });

  // svg.append("line")
      // .attr("x1", x(1946))
      // .attr("y1", y(3.88))
      // .attr("x2", x(1946))
      // .attr("y2", y(1.6) - 13)
      // .classed("annotation-line",true);

  // svg.selectAll(".g-note")
      // .data([
        // "Players return",
        // "from World War II."
      // ])
    // .enter().append("text")
    // .classed("g-text-annotation",true)
    // .attr("x", x(1946))
    // .attr("y", y(1.6))
    // .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    // .text(function(d) { return d; });

  // svg.append("line")
      // .attr("x1", x(1963))
      // .attr("y1", y(5.8))
      // .attr("x2", x(1963))
      // .attr("y2", y(2.6) - 13)
      // .classed("annotation-line",true);

  // svg.selectAll(".g-note")
      // .data([
        // "Strike zone enlarged",
        // "from 1963-68."
      // ])
    // .enter().append("text")
    // .classed("g-text-annotation",true)
    // .attr("x", x(1963))
    // .attr("y", y(2.6))
    // .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    // .text(function(d) { return d; });

  // svg.append("line")
      // .attr("x1", x(1969))
      // .attr("y1", y(8.7) + 40)
      // .attr("x2", x(1969))
      // .attr("y2", y(5.8))
      // .classed("annotation-line",true);

  // svg.selectAll(".g-note")
      // .data([
        // "Pitching had become so dominant",
        // "in the 1960s that the mound",
        // "was lowered in 1969."
      // ])
    // .enter().append("text")
    // .classed("g-text-annotation",true)
    // .attr("x", x(1969))
    // .attr("y", y(8.7))
    // .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    // .text(function(d) { return d; });

  // svg.append("line")
      // .attr("x1", x(1973))
      // .attr("y1", y(5.2))
      // .attr("x2", x(1973))
      // .attr("y2", y(1.6) - 13)
      // .classed("annotation-line",true);

  // svg.selectAll(".g-note")
      // .data([
        // "Designated hitter",
        // "rule took effect.",
      // ])
    // .enter().append("text")
    // .classed("g-text-annotation",true)
    // .attr("x", x(1973))
    // .attr("y", y(1.6))
    // .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    // .text(function(d) { return d; });

  // svg.append("line")
      // .attr("x1", x(2008))
      // .attr("y1", y(6.8))
      // .attr("x2", x(2008))
      // .attr("y2", y(3.6) - 13)
      // .classed("annotation-line",true);

  // svg.selectAll(".g-note")
      // .data([
        // "Mitchell report",
        // "on steroids.",
      // ])
    // .enter().append("text")
    // .classed("g-text-annotation",true)
    // .attr("x", x(2008))
    // .attr("y", y(3.6))
    // .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    // .text(function(d) { return d; });

  function selectUser(user) {
    d3.selectAll(".g-team-selected").classed("g-team-selected", false);
    if (selectedUser = user) {
      d3.selectAll("." + user).classed("g-team-selected", true);
      d3.selectAll(".g-legend .g-selected-legend text").text(user);
    }
    d3.selectAll(".g-team-chooser").property("value", user || "none");
    d3.selectAll(".g-legend a").style("display", user? "inline-block" : "none");
  }

  function drawLegend(container, headline) {

    var legend = container.append("div")
        .attr("class", "g-legend");

    var avgLegend = legend.append("div")
        .attr("class", "g-average-legend")

    var avgSvg = avgLegend.append("svg")
        .attr("width", 24)
        .attr("height", 4)
      .append("g")
        .attr("transform", "translate(2, 2)");

    avgSvg.append("line")
        .attr("x2", 20);

    avgSvg.append("circle")
        .attr("r", 2);

    avgSvg.append("circle")
        .attr("cx", 20)
        .attr("r", 2);

    avgLegend.append("div")
        .text("Metric average")

    var selectedLegend = legend.append("div")
        .attr("class", "g-selected-legend")

    var selectedSvg = selectedLegend.append("svg")
        .attr("width", 24)
        .attr("height", 4)
      .append("g")
        .attr("transform", "translate(2, 2)");

    selectedSvg.append("line")
        .attr("x2", 20);

    selectedSvg.append("circle")
        .attr("r", 2);

    selectedSvg.append("circle")
        .attr("cx", 20)
        .attr("r", 2);

    var userChooser = selectedLegend.append("select")
        .attr("class", "g-team-chooser");

    userChooser.append("option")
        .attr("value", "none")
        .text("Choose a user");

    selectedLegend.append("a")
        .attr("href", "#")
        .style("display", "none")
        .text("X")
        .on("click", function() {
          d3.event.preventDefault();
          selectUser(null);
        })

    userChooser.on("change", function() { selectUser(this.value); })
      .selectAll("option")
        .data(wusers)
      .enter().append("option")
        .attr("value", function(d) { return d.name; })
        .text(function(d) { return d.name; });
  }

  //
  // Abstracting some stuff for main line charts
  //

  function drawLineChart(container, data, attributeY, x, y, width, height, r, bounds) {

    var currTime = data[data.length - 1].time;
    data.forEach(function(d) {
      d.rtime = d.time - currTime;
    });
  
    var userLine = d3.svg.line()
      .x(function(d) { return x(d.rtime); })
      .y(function(d) { return y(d[attributeY]); });

    var avgLine = d3.svg.line()
      .x(function(d) { return x(d.key); })
      .y(function(d) { return y(d.values.avg); });

    var userData = d3.nest()
      .key(function(d) { return d.user; })
      .entries(data);

    var averageData = d3.nest()
      .key(function(d) { return Math.floor(d.rtime / 30) * 30; })
      .rollup(function(timeobj) {
        return {
          "avg": d3.mean(timeobj, function(d) { return parseFloat(d[attributeY], 10); }),
        }
      })
      .entries(data);
	
	averageData.sort(function(a,b) { return parseFloat(a.key) - parseFloat(b.key)});

    var bgCirclesContainer = container.append("g");

    bgCirclesContainer.selectAll("circle")
        .data(data)
        .enter().append("circle")
        .attr("r", r - 0.5)
        .attr("cx", function(d) { return x(d.rtime); })
        .attr("cy", function(d) { return y(d[attributeY]); });

    //  adding averages on top of main scatterplot.
    var avgContainer = container.append("g")

    avgContainer.append("path")
        .attr("class", "g-mean-line")
        .attr("d", avgLine(averageData));

    var averages = avgContainer.selectAll(".g-mean-circle")
        .data(averageData)
        .enter().append("circle")
        .classed("g-mean-circle",true)
        .attr("cx", function(d) { return x(d.key); })
        .attr("cy", function(d) { return y(d.values.avg); })
        .attr("r", r + 0.5);

    // User rollover lines
    var usersContainer = container.append("g");

    var user = usersContainer.selectAll(".g-team")
        .data(userData)
      .enter().append("g")
        .attr("class", function(d) { return "g-team " + d.key; });

    user.append("path")
        .attr("d", function(d) { return userLine(d.values); })
        .style("stroke", "white")
        .style("stroke-width", 3);

    user.append("path")
        .attr("d", function(d) { return userLine(d.values); });

    user.selectAll("circle")
        .data(function(d) { return d.values; })
      .enter().append("circle")
        .attr("r", r)
        .attr("cx", function(d) { return x(d.rtime); })
        .attr("cy", function(d) { return y(d[attributeY]); });

    usersContainer.append("g")
        .attr("class", "g-overlay")
        .selectAll(".voronoi")
        .data(d3.geom.voronoi(data.map(function(d) { return [x(d.rtime), y(d[attributeY]) + Math.random() - .5]; })).map(bounds.clip).map(function(d, i) {
          if (d.length === 0){
            d.path = "M 0 0";
          }else{
            d.path = "M" + d.join("L") + "Z";
          }
          d.data = data[i];
          return d;
         }))
        .enter().append("path")
        .attr("d", function(d) { return d.path; })
        .on("mouseover", function(d, i) { selectValue(d.data); })
        .on("mouseout", function(d, i) { selectValue(null); })
        .on("click", function(d, i) { selectUser(d.data.user); });

    var hoverLabel = usersContainer.append("g")
        .attr("class", "g-mean-text")
        .style("display", "none");

    var hoverUser = hoverLabel.append("text")
        .attr("dy", ".35em");

    var hoverNumber = hoverLabel.append("text")
        .attr("class", "small number")
        .attr("dy", ".35em");

    var hoverTime = hoverLabel.append("text")
        .attr("dy", ".35em");

    hoverLabel.append("circle")
        .attr("class", "g-highlight")
        .attr("r", r + 2);

    function selectValue(d) {
      if (d) {
        //var offset = averageData[averageData.length - (xmax - d.rtime) - 1].values.avg < d[attributeY] ? -28 : +32;
		var offset = -28;
        hoverLabel.style("display", null).attr("transform", "translate(" + x(d.rtime) + "," + y(d[attributeY]) + ")");
        hoverNumber.attr("y", offset - 12)
            .text(function() {
				return formatHover(d[attributeY])
            });
        hoverUser.attr("y", offset).text(d.user);
        hoverTime.attr("y", offset + 12).text(d.rtime);
        d3.selectAll(".g-hide-hover").style("opacity", 0);
      } else {
        d3.selectAll(".g-hide-hover").style("opacity", 1);
        hoverLabel.style("display", "none");
      }
    }

    return averageData;
  }//drawLineChart

  };//ready
};
