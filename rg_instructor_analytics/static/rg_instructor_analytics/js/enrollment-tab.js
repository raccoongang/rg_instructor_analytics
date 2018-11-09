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
  function updateEnrolls(timeFilter) {

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

      totalTrace = {
        x: response.dates_total.map(dataFixFunction),
        y: response.counts_total,
        mode: 'lines',
        name: django.gettext('Total'),
        line: {
          color: '#70A3FF',
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
        xaxis: {
          type: "date",
          margin: {t: 10},
        },
        yaxis: {
          side: 'right',
          overlaying: 'y2',
          title: django.gettext('Total'),
          titlefont: {color: '#70A3FF'},
          tickfont: {color: '#70A3FF'},
        },
        yaxis2: {
          title: django.gettext('Enrollments/Unenrollments'),
          gridcolor: '#cecece'
        },
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

      if (enrollInfo.enroll_start !== "null") {
        timeFilter.startDate = moment(enrollInfo.enroll_start * 1000);
      }
      if (enrollInfo.enroll_end !== "null") {
        timeFilter.endDate = moment(enrollInfo.enroll_end * 1000);
      }
    }
    catch (error) {
      console.error(error);
    }

    updateEnrolls(timeFilter);
  }

  enrollTab.loadTabData = loadTabData;

  return enrollTab;
}
