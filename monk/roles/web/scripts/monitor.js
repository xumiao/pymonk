(function() {
var formatYear = function(d) { return d; },

    format = d3.format(".1f"),
    formatHover = d3.format(".2f"),
    formatBattingAverage = d3.format(".3f"),
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

var selectedTeam;

//
// main scatterplot at top
//

var margin = {top: 100, right: 55, bottom: 22, left: 55},
    width = 1024 - margin.left - margin.right,
    height = 640 - margin.top - margin.bottom,
    bounds = d3.geom.polygon([[0, 0], [0, height], [width, height], [width, 0]]);

var x = d3.scale.linear()
    .domain([1900, 2013])
    .range([0, width]);

var y = d3.scale.linear()
    .domain([0, 9.5])
    .range([height, 0]);

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom")
    .tickSize(4)
    .tickFormat(formatYear)
    .tickPadding(2);

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("right")
    .ticks(10)
    .tickPadding(10)
    .tickSize( -width);

var svg = d3.select(".g-main-chart").append("svg")
    .attr("width", (width + margin.left + margin.right))
    .attr("height", (height + margin.top + margin.bottom))
    .style("margin-top", 10 - margin.top + "px")
  .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

//
// pitcher chart
//

// var pitchMargin = {top: 25, right: 40, bottom: 25, left: 10},
    // pitchWidth = 600 - pitchMargin.left - pitchMargin.right,
    // pitchHeight = 350 - pitchMargin.top - pitchMargin.bottom;

// var pitchX = d3.scale.linear()
    // .domain([1920,2013])
    // .range([0, pitchWidth]);

// var pitchY = d3.scale.linear()
    // .domain([1, 4.7])
    // .range([pitchHeight, 0]);

// var pitchXAxis = d3.svg.axis()
    // .scale(pitchX)
    // .orient("bottom")
    // .ticks(10)
    // .tickSize(4)
    // .tickFormat(formatYear)
    // .tickPadding(2);

// var pitchYAxis = d3.svg.axis()
    // .scale(pitchY)
    // .tickSize(-pitchWidth - pitchMargin.left - pitchMargin.right)
    // .tickPadding(10)
    // .orient("right");

// var pitchChart = d3.select(".g-pitch-chart").append("svg")
    // .attr("height", pitchHeight + pitchMargin.top + pitchMargin.bottom )
    // .attr("width", pitchWidth + pitchMargin.left + pitchMargin.right )
  // .append("g")
    // .attr("transform", "translate(" + pitchMargin.left + "," + pitchMargin.top + ")");


//
// batter chart
//
/*
var batMargin = {top: 45, right: 40, bottom: 25, left: 80},
    batWidth = 280 - batMargin.left - batMargin.right,
    batHeight = 500 - batMargin.top - batMargin.bottom;

var batX = d3.scale.linear()
    .domain([1988,2012])
    .range([0, batWidth]);

var batY = d3.scale.linear()
    .domain([.125, .4])
    .range([batHeight, 0]);

var batXAxis = d3.svg.axis()
    .scale(batX)
    .orient("bottom")
    .ticks(4)
    .tickSize(4)
    .tickFormat(formatYear)
    .tickPadding(2);

var batYAxis = d3.svg.axis()
    .scale(batY)
    .ticks(6)
    .tickFormat(formatBattingAverage)
    .tickSize(-batWidth )
    .tickPadding(10)
    .orient("right");

var batChart = d3.select(".g-bat-chart").append("svg")
    .attr("height", batHeight + batMargin.top + batMargin.bottom )
    .attr("width", batWidth + batMargin.left + batMargin.right )
  .append("g")
    .attr("transform", "translate(" + batMargin.left + "," + batMargin.top + ")");
*/

queue()
    .defer(d3.csv, "http://graphics8.nytimes.com/newsgraphics/2013/03/21/strikeouts/e499df91886aef061eb10983588acb400c454a59/out3.csv")
    .defer(d3.csv, "http://graphics8.nytimes.com/newsgraphics/2013/03/21/strikeouts/e499df91886aef061eb10983588acb400c454a59/teams.csv")
    .await(ready)

function ready(err, strikeouts, teams) {

  window.strikeouts = strikeouts;

  var teamByCode = {};
  teams.forEach(function(d) {
    teamByCode[d.code] = d;
  });

  strikeouts.forEach(function(d) {
      d.year =+d.year;
      d.kpg = +d.kpg;
      d.twoStrikeAvg = +d.twoStrikeAvg;
      d.non2savg = +d.non2savg;
      d.hrpg = +d.hrpg;
      d.league = teamByCode[d.franchise].league;
  });

  var leagues = d3.nest()
    .key(function(d) { return d.league; })
    .key(function(d) { return d.franchise; })
    .rollup(function(values){

      return {
        // TODO rank doesn't account for ties
        rank: values.sort(function(a, b) { return b.kpg - a.kpg}).map(function(d) { return d.year; }).indexOf(2012) + 1,
        lastYear: values.filter(function(d) { return d.year === 2012; })[0].kpg
      };
    })
    .entries(strikeouts);

  leagues.forEach(function(league) {
    league.values.sort(function(a, b) {
      return b.values.lastYear - a.values.lastYear;
    });
  });

  //
  // Strikeout Table
  //

  var strikeoutTable = d3.select(".g-strikeout-table")

  var league = strikeoutTable.selectAll(".g-league")
      .data(leagues)
    .enter().append("div")
      .attr("class", "g-league");

  var tableTitle = league.append("h5").text(function(d) { return d.key === "NL" ? "National League Batters" : "American League Batters"; })
  var table = league.append("table");

  var row = table.selectAll("tr")
      .data(function(d) { return d.values; })
    .enter().append("tr")
      .attr("class", function(d) { return (d.values.rank === 1 ? "g-record-row " : "") + "g-team " + d.key; })
      .on("click", function(d) { selectTeam(d.key === selectedTeam ? null : d.key); });

  row.append("td")
      .attr("class", "g-franchise")
      .text(function(d) { return teamByCode[d.key].name; });

  row.append("td")
      .text(function(d) { return format(d.values.lastYear); });

  row.append("td")
      .attr("class", "g-designations")
    .append("div")
      .attr("class", function(d) { return d.values.rank === 1 ? "g-record" : ""; })
      .text(function(d) { return d.values.rank === 1 ? "Record" : formatOrdinal(d.values.rank) + " most"; });

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

  var avgData = drawLineChart(svg, strikeouts, "kpg", x, y, width, height, 3, bounds);

  drawLegend(d3.select(".g-main-chart"));

  // Calculating max and min labels
  var highestkpg = 0,
      lowestkpg = Infinity,
      lowestYear,
      highestYear;

  avgData.forEach(function(d, i) {
    if (lowestkpg > d.values.avg) {
      lowestkpg = d.values.avg;
      lowestYear = d.key;
    }
    if (highestkpg < d.values.avg) {
      highestkpg = d.values.avg;
      highestYear = d.key;
    }
  });

  var highestLabel = svg.append("g")
      .attr("class", "g-mean-text g-hide-hover")
      .attr("transform", "translate(" + x(highestYear) + "," + y(highestkpg) + ")")

  highestLabel.append("text")
      .attr("class", "number")
      .attr("dy", "-10px")
      .text(format(highestkpg));

  highestLabel.append("text")
      .attr("class", "g-mean-label")
      .attr("dy", "-35px")
      .text("League average");

  highestLabel.append("text")
      .attr("class", "g-mean-label")
      .attr("dy", "-48px")
      .text(highestYear);

  highestLabel.append("circle")
      .attr("class", "g-highlight")
      .attr("r", 5.5);

  var lowestLabel = svg.append("g")
      .attr("class", "g-mean-text g-hide-hover")
      .attr("transform", "translate(" + x(lowestYear) + "," + y(lowestkpg) + ")")

  lowestLabel.append("text")
      .attr("class", "number")
      .attr("dy", "30px")
      .text(format(lowestkpg));

  lowestLabel.append("text")
      .attr("class", "g-mean-label")
      .attr("dy", "45px")
      .text("League average");

  lowestLabel.append("text")
      .attr("class", "g-mean-label")
      .attr("dy", "60px")
      .text(lowestYear);

  lowestLabel.append("circle")
      .attr("class", "g-highlight")
      .attr("r", 5.5);

  var arrow = [[0, 0], [3, 4], [-3, 4], [0, 0]];

  // Annotations

  svg.append("line")
      .attr("x1", x(1917))
      .attr("y1", y(3.46))
      .attr("x2", x(1917))
      .attr("y2", y(1) - 13)
      .classed("annotation-line",true);

  svg.selectAll(".g-note")
      .data([
        "U.S. enters",
        "World War I."
      ])
    .enter().append("text")
    .classed("g-text-annotation",true)
    .attr("x", x(1917))
    .attr("y", y(1.08))
    .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    .text(function(d) { return d; });

  svg.append("line")
      .attr("x1", x(1946))
      .attr("y1", y(3.88))
      .attr("x2", x(1946))
      .attr("y2", y(1.6) - 13)
      .classed("annotation-line",true);

  svg.selectAll(".g-note")
      .data([
        "Players return",
        "from World War II."
      ])
    .enter().append("text")
    .classed("g-text-annotation",true)
    .attr("x", x(1946))
    .attr("y", y(1.6))
    .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    .text(function(d) { return d; });

  svg.append("line")
      .attr("x1", x(1963))
      .attr("y1", y(5.8))
      .attr("x2", x(1963))
      .attr("y2", y(2.6) - 13)
      .classed("annotation-line",true);

  svg.selectAll(".g-note")
      .data([
        "Strike zone enlarged",
        "from 1963-68."
      ])
    .enter().append("text")
    .classed("g-text-annotation",true)
    .attr("x", x(1963))
    .attr("y", y(2.6))
    .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    .text(function(d) { return d; });

  svg.append("line")
      .attr("x1", x(1969))
      .attr("y1", y(8.7) + 40)
      .attr("x2", x(1969))
      .attr("y2", y(5.8))
      .classed("annotation-line",true);

  svg.selectAll(".g-note")
      .data([
        "Pitching had become so dominant",
        "in the 1960s that the mound",
        "was lowered in 1969."
      ])
    .enter().append("text")
    .classed("g-text-annotation",true)
    .attr("x", x(1969))
    .attr("y", y(8.7))
    .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    .text(function(d) { return d; });

  svg.append("line")
      .attr("x1", x(1973))
      .attr("y1", y(5.2))
      .attr("x2", x(1973))
      .attr("y2", y(1.6) - 13)
      .classed("annotation-line",true);

  svg.selectAll(".g-note")
      .data([
        "Designated hitter",
        "rule took effect.",
      ])
    .enter().append("text")
    .classed("g-text-annotation",true)
    .attr("x", x(1973))
    .attr("y", y(1.6))
    .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    .text(function(d) { return d; });

  svg.append("line")
      .attr("x1", x(2008))
      .attr("y1", y(6.8))
      .attr("x2", x(2008))
      .attr("y2", y(3.6) - 13)
      .classed("annotation-line",true);

  svg.selectAll(".g-note")
      .data([
        "Mitchell report",
        "on steroids.",
      ])
    .enter().append("text")
    .classed("g-text-annotation",true)
    .attr("x", x(2008))
    .attr("y", y(3.6))
    .attr("dy", function(d, i) { return i * 1.3 + "em"; })
    .text(function(d) { return d; });


  //
  // specialized pitchers chart
  //
    /*
  pitchChart.append("g")
      .attr("class", "x axis")
      .attr("transform","translate(0," + (pitchHeight + 7) + ")"  )
      .call(pitchXAxis);

  pitchChart.append("g")
      .attr("class", "y axis")
      .attr("transform","translate("+ pitchWidth + ",0)"  )
      .call(pitchYAxis)
      .selectAll("g")
        .classed("minor", true);
    */
  // data not reliable before 1920
  /*
  pitchCountFilter = strikeouts.filter(function(d) { return d.year >= 1920; });

  var pitchersBounds = d3.geom.polygon([[0, 0], [0, pitchHeight], [pitchWidth, pitchHeight], [pitchWidth, 0]])

  drawLineChart(pitchChart, pitchCountFilter, "avgpitchers", pitchX, pitchY, pitchWidth, pitchHeight, 2.4, pitchersBounds);

  drawLegend(d3.select(".g-pitch-chart"), -pitchMargin.left, 15, 20);

  //
  // batting average chart
  //

  batChart.append("g")
      .attr("class", "x axis")
      .attr("transform","translate(0," + (batHeight + 7) + ")"  )
      .call(batXAxis);

  batChart.append("g")
      .attr("class", "y axis")
      .attr("transform","translate("+ batWidth + ",0)"  )
      .call(batYAxis)
      .selectAll("g")
        .classed("minor", true);
  
  avgByCountFilter = strikeouts.filter(function(d) { return d.year >= 1988; })
  var batting2StrikesBounds = d3.geom.polygon([[0, batY(0.25)], [0, batY(0)], [batWidth, batY(0)], [batWidth, batY(0.25)]]);
  drawLineChart(batChart, avgByCountFilter, "twoStrikeAvg", batX, batY, batWidth, batHeight, 2.4, batting2StrikesBounds);
  var battingBounds = d3.geom.polygon([[0, batY(0.4)], [0, batY(0.25)], [batWidth, batY(0.25)], [batWidth, batY(0.4)]]);
  drawLineChart(batChart, avgByCountFilter, "non2savg", batX, batY, batWidth, batHeight, 2.4, battingBounds);

  drawLegend(d3.select(".g-bat-chart"), -batMargin.left, 0, 20);

  batChart.append("text")
      .attr("class", "selected-team")
      .attr("y", 20);
  */

  function selectTeam(code) {
    d3.selectAll(".g-team-selected").classed("g-team-selected", false);
    if (selectedTeam = code) {
      d3.selectAll("." + code).classed("g-team-selected", true);
      d3.selectAll(".g-legend .g-selected-legend text").text(teamByCode[code].name);
    }
    d3.selectAll(".g-team-chooser").property("value", code || "none");
    d3.selectAll(".g-legend a").style("display", code? "inline-block" : "none");

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
        .text("League average")

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

    var teamChooser = selectedLegend.append("select")
        .attr("class", "g-team-chooser");

    teamChooser.append("option")
        .attr("value", "none")
        .text("Choose a Team");

    selectedLegend.append("a")
        .attr("href", "#")
        .style("display", "none")
        .text("X")
        .on("click", function() {
          d3.event.preventDefault();
          selectTeam(null);
        })

    teamChooser.on("change", function() { selectTeam(this.value); })
      .selectAll("optgroup")
        .data(d3.nest().key(function(d) { return d.league; }).entries(teams))
      .enter().append("optgroup")
        .attr("label", function(d) { return ((d.key === "NL" ? "National" : "American") + " League").toUpperCase(); })
      .selectAll("option")
        .data(function(d) { return d.values; })
      .enter().append("option")
        .attr("value", function(d) { return d.code; })
        .text(function(d) { return d.name; });
  }

  //
  // Abstracting some stuff for main line charts
  //

  function drawLineChart(container, data, attributeY, x, y, width, height, r, bounds) {

    var teamLine = d3.svg.line()
      .x(function(d) { return x(d.year); })
      .y(function(d) { return y(d[attributeY]); });

    var avgLine = d3.svg.line()
      .x(function(d) { return x(d.key); })
      .y(function(d) { return y(d.values.avg); });

    var teamData = d3.nest()
      .key(function(d) { return d.franchise; })
      .entries(data);

    var averageData = d3.nest()
      .key(function(d) { return d.year; })
      .rollup(function(yearobj) {
        return {
          "avg": d3.mean(yearobj, function(d) { return parseFloat(d[attributeY], 10); }),
          "totH": d3.sum(yearobj, function(d) { return parseFloat(d.H, 10); })

        }
      })
      .entries(data);


    var bgCirclesContainer = container.append("g");

    bgCirclesContainer.selectAll("circle")
        .data(data)
      .enter().append("circle")
        .attr("r", r - 0.5)
        .attr("cx", function(d) { return x(d.year); })
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

    // Team rollover lines
    var teamsContainer = container.append("g");

    var team = teamsContainer.selectAll(".g-team")
        .data(teamData)
      .enter().append("g")
        .attr("class", function(d) { return "g-team " + d.key; });

    team.append("path")
        .attr("d", function(d) { return teamLine(d.values); })
        .style("stroke", "white")
        .style("stroke-width", 3);

    team.append("path")
        .attr("d", function(d) { return teamLine(d.values); });

    team.selectAll("circle")
        .data(function(d) { return d.values; })
      .enter().append("circle")
        .attr("r", r)
        .attr("cx", function(d) { return x(d.year); })
        .attr("cy", function(d) { return y(d[attributeY]); });

    teamsContainer.append("g")
        .attr("class", "g-overlay")
      .selectAll(".voronoi")
        .data(d3.geom.voronoi(data.map(function(d) { return [x(d.year), y(d[attributeY]) + Math.random() - .5]; })).map(bounds.clip).map(function(d, i) {
          d.path = "M" + d.join("L") + "Z";
          d.data = data[i];
          return d;
         }))
      .enter().append("path")
        .attr("d", function(d) { return d.path; })
        .on("mouseover", function(d, i) { selectValue(d.data); })
        .on("mouseout", function(d, i) { selectValue(null); })
        .on("click", function(d, i) { selectTeam(d.data.franchise); });

    var hoverLabel = teamsContainer.append("g")
        .attr("class", "g-mean-text")
        .style("display", "none");

    var hoverTeam = hoverLabel.append("text")
        .attr("dy", ".35em");

    var hoverNumber = hoverLabel.append("text")
        .attr("class", "small number")
        .attr("dy", ".35em");

    var hoverYear = hoverLabel.append("text")
        .attr("dy", ".35em");

    hoverLabel.append("circle")
        .attr("class", "g-highlight")
        .attr("r", r + 2);

    function selectValue(d) {
      if (d) {
        var offset = averageData[averageData.length - (2012 - d.year) - 1].values.avg < d[attributeY] ? -28 : +32;
        hoverLabel.style("display", null).attr("transform", "translate(" + x(d.year) + "," + y(d[attributeY]) + ")");
        hoverNumber.attr("y", offset - 12)
            .text(function() {
              if (attributeY === "twoStrikeAvg" || attributeY === "non2savg") {
                return formatBattingAverage(d[attributeY]);
              } else {
                return formatHover(d[attributeY])
              }
            });
        hoverTeam.attr("y", offset).text(teamByCode[d.franchise].name);
        hoverYear.attr("y", offset + 12).text(d.year);
        d3.selectAll(".g-hide-hover").style("opacity", 0);
      } else {
        d3.selectAll(".g-hide-hover").style("opacity", 1);
        hoverLabel.style("display", "none");
      }
    }

    return averageData;
  }

};
})();