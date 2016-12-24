 (function($) {

    var myLineChart;

    var options = {

        ///Boolean - Whether grid lines are shown across the chart
        scaleShowGridLines : true,

        //String - Colour of the grid lines
        scaleGridLineColor : "rgba(0,0,0,.05)",

        //Number - Width of the grid lines
        scaleGridLineWidth : 1,

        scaleBeginAtZero: true,

        //Boolean - Whether the line is curved between points
        bezierCurve : true,

        //Number - Tension of the bezier curve between points
        bezierCurveTension : 0.4,

        //Boolean - Whether to show a dot for each point
        pointDot : true,

        //Number - Radius of each point dot in pixels
        pointDotRadius : 4,

        //Number - Pixel width of point dot stroke
        pointDotStrokeWidth : 1,

        //Number - amount extra to add to the radius to cater for hit detection outside the drawn point
        pointHitDetectionRadius : 20,

        //Boolean - Whether to show a stroke for datasets
        datasetStroke : true,

        //Number - Pixel width of dataset stroke
        datasetStrokeWidth : 2,

        //Boolean - Whether to fill the dataset with a colour
        datasetFill : true,

        //String - A legend template
        legendTemplate : "<ul class=\"<%=name.toLowerCase()%>-legend\"><% for (var i=0; i<datasets.length; i++){%><li><span style=\"background-color:<%=datasets[i].lineColor%>\"></span><%if(datasets[i].label){%><%=datasets[i].label%><%}%></li><%}%></ul>"

    };

    $(document).ready(function(){
        var ctx = $("#myChart").get(0).getContext("2d");
        dashboard.init('http://www.gethotspotapp.com/');
        // Get context with jQuery - using jQuery's .get() method.
        // This will get the first returned node in the jQuery collection.
        load_dashboard();

//        $('.refresh-dashboard').on('click', load_dashboard);

//        function reload_dashboard() {
//            $('.loading-indicator').show();
//            dashboard.getDashboard(function(success) {
//                var data = {
//                    labels: success.chart_labels,
//                    datasets: [
//                            {
//                                label: "My First dataset",
//                                fillColor: "rgba(151,187,205,0.2)",
//                                strokeColor: "rgba(151,187,205,1)",
//                                pointColor: "rgba(151,187,205,1)",
//                                pointStrokeColor: "#fff",
//                                pointHighlightFill: "#fff",
//                                pointHighlightStroke: "rgba(151,187,205,1)",
//                                data: success.chart_data
//                            }
//                        ]
//                    };
//                myLineChart = data;
//                myLineChart.update();
//                $('.loading-indicator').hide();
//            });
//        }

        function load_dashboard() {
            $('.loading-indicator').show();
            dashboard.getDashboard(function(success){
                  var data = {
                    labels: success.chart_labels,
                    datasets: [
                            {
                                label: "My First dataset",
                                fillColor: "rgba(151,187,205,0.2)",
                                strokeColor: "rgba(151,187,205,1)",
                                pointColor: "rgba(151,187,205,1)",
                                pointStrokeColor: "#fff",
                                pointHighlightFill: "#fff",
                                pointHighlightStroke: "rgba(151,187,205,1)",
                                data: success.chart_data
                            }
                        ]
                    };
                console.log(success);
                $('.active-user-number').html(success.new_haven_active_user_number);
                $('.total-user-number').html(success.new_haven_total_user_number);
                myLineChart = new Chart(ctx).Line(data, options);
                console.log(myLineChart);
                $('.loading-indicator').hide();
            });
        }

    });
 })(jQuery);