/**
 * Implementation of Tab for the enrollment tab
 * @returns {Tab}
 * @class old realisation
 */
function EnrollmentTab(button, content) {
  var enrollTab = new Tab(button, content);
  var timeFilter = new TimeFilter(content, updateEnrolls);

  /**
   * Send ajax to server side according selected date range and redraw plot
   */
  function updateEnrolls() {

    function onSuccess(response) {
      var totalTrace;
      var enrollTrace;
      var unenrollTrace;
      var layout;
      var data;

      function dataFixFunction(x) {
        var result = new Date(x);
        result.setHours(0);
        result.setMinutes(0);
        return result;
      }

      var x_template = {
        type: "date",
        margin: {t: 10}
      };
      if (response.customize_xticks) {
        x_template["tick0"] = response.dates_total[0];
        x_template["dtick"] = 86400000.0;
        x_template["tickformat"] = "%d %b %Y";
      }

      var y1_template = {
        side: 'right',
        overlaying: 'y2',
        title: django.gettext('Total'),
        titlefont: {color: '#568ecc'},
        tickfont: {color: '#568ecc'},
      };
      if (response.customize_y1ticks) {
        y1_template["nticks"] = response.nticks_y1+1
      }

      var y2_template = {
        title: django.gettext('Enrollments/Unenrollments'),
        gridcolor: '#cecece',
      };
      if (response.customize_y2ticks) {
        y2_template["nticks"] = response.nticks_y2+1
      }

      totalTrace = {
        x: response.dates_total.map(dataFixFunction),
        y: response.counts_total,
        mode: 'lines',
        name: django.gettext('Total'),
        line: {
          color: '#568ecc',
          width: 4,
          shape: 'hv',
        },
        hovermode: 'closest',
        hoverdistance: 1000,
        spikedistance: 1000,
        type: 'scatter'
      };

      enrollTrace = {
        x: response.dates_enroll.map(dataFixFunction),
        y: response.counts_enroll,
        mode: 'lines',
        name: django.gettext('Enrollments'),
        line: {
          color: '#8BB22A',
        },
        yaxis: 'y2',
        type: 'bar',
        marker: {
          color: '#8BB22A',
        },
      };

      unenrollTrace = {
        x: response.dates_unenroll.map(dataFixFunction),
        y: response.counts_unenroll,
        mode: 'lines',
        name: django.gettext('Unenrollments'),
        yaxis: 'y2',
        line: {
          color: '#CC4630',
        },
        type: 'bar',
        marker: {
          color: '#CC4630',
        },
      };

      layout = {
        hovermode: 'closest',
        xaxis: x_template,
        yaxis: y1_template,
        yaxis2: y2_template,
        showlegend: false,
      };

      data = [unenrollTrace, enrollTrace, totalTrace];

      Plotly.newPlot('enrollment-stats-plot', data, layout, {
        displayModeBar: false,
        scrollZoom: false,
      });
    }

    function onError() {
      alert("Can't load data for selected period!");
    }

    $.ajax({
      type: "POST",
      url: "api/enroll_statics/",
      data: timeFilter.timestampRange,
      dataType: "json",
      traditional: true,
      success: onSuccess,
      error: onError,
      beforeSend: timeFilter.setLoader,
      complete: timeFilter.removeLoader,
    });
  }

  function loadTabData() {
    try {
      var enrollInfo = $('#enrollment-data').data('enroll')[enrollTab.tabHolder.course];
      var courseDatesInfo = $('.course-dates-data').data('course-dates')[enrollTab.tabHolder.course];
      var firstEnrollDate = null;
      var courseStartDate = moment();

      if (enrollInfo.enroll_start !== "null") {
        firstEnrollDate = moment(enrollInfo.enroll_start * 1000); // Date of 1st enrollment
      }
      if (courseDatesInfo.course_is_started) {
        courseStartDate = moment(courseDatesInfo.course_start * 1000)  // Date of course start
      }

      timeFilter.init(
          moment(Math.min(firstEnrollDate, courseStartDate)),
          firstEnrollDate
      );

    }
    catch (error) {
      console.error(error);
    }

    updateEnrolls();
  }

  enrollTab.loadTabData = loadTabData;

  return enrollTab;
}
