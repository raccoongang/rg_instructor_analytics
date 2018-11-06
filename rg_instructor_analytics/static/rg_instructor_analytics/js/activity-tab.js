/**
 * Implementation of Tab for the activity tab
 * @returns {Tab}
 * @class old realisation
 */
function ActivityTab(button, content) {
  var activityTab = new Tab(button, content);
  var timeFilter = new TimeFilter(content, updateActivity);

  function updateActivity(timeFilter) {

    function onError() {
      alert("Can't load data for selected period!");
    }

    function onSuccess(data) {
      function dataFixFunction(x) {
        var result = new Date(x);
        result.setHours(0);
        result.setMinutes(0);
        return result;
      }

      var videoActivities = {
        x: data.video_dates.map(dataFixFunction),
        y: data.video_activities,
        name: 'Video',
        type: 'bar',
        marker:{
            color: '#568ecc'
        }
      };

      var discussionActivities = {
        x: data.discussion_dates.map(dataFixFunction),
        y: data.discussion_activities,
        name: 'Discussion',
        type: 'bar',
        marker:{
            color: '#50c156'
        }
      };

      var stat = [videoActivities, discussionActivities];

      var layout = {
        barmode: 'group',
        xaxis: {
          type: "date"
        },
        showlegend: false
      };

      Plotly.newPlot('activity-stats-plot', stat, layout, {displayModeBar: false});
    }

    $.ajax({
      type: "POST",
      url: "api/activity/",
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
        var courseDatesInfo = $('.course-dates-data').data('course-dates')[activityTab.tabHolder.course];
        if (courseDatesInfo.course_is_started) {
            $('.tab-banner').prop('hidden', true);
            $('.tab-content').prop('hidden', false);
            if (courseDatesInfo.course_start !== "null") {
              timeFilter.startDate = moment(courseDatesInfo.course_start * 1000);
            }
            if (courseDatesInfo.course_end !== "null") {
              timeFilter.endDate = moment(courseDatesInfo.course_end * 1000);
            }
        } else {
            $('.tab-banner').prop('hidden', false);
            $('.tab-content').prop('hidden', true);
        }
    }
    catch (error) {
        console.error(error);
    }

    updateActivity(timeFilter);

  }

  activityTab.loadTabData = loadTabData;

  return activityTab;
}
