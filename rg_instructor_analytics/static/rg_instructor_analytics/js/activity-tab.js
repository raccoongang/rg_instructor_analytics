/**
 * Implementation of Tab for the activity tab
 * @returns {Tab}
 * @class old realisation
 */
function ActivityTab(button, content) {
  var activityTab = new Tab(button, content);
  var timeFilter = new TimeFilter(content, updateActivity);
  var $tabBanner = content.find('.tab-banner');
  var $tabContent = content.find('.tab-content');

  function updateActivity() {

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
            $tabBanner.prop('hidden', true);
            $tabContent.prop('hidden', false);
            timeFilter.startDate = moment(courseDatesInfo.course_start * 1000);
            timeFilter.endDate = moment();
            timeFilter.minDate = timeFilter.startDate;

            timeFilter.makeActive(content.find(".js-datepicker-btn"));
            timeFilter.setMinDate();
            updateActivity();
        } else {
            $tabBanner.prop('hidden', false);
            $tabContent.prop('hidden', true);
        }
    }
    catch (error) {
        console.error(error);
    }
  }

  activityTab.loadTabData = loadTabData;

  return activityTab;
}
