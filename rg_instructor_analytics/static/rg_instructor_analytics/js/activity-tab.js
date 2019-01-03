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
  var $tabContentItems = content.find('.item-content');

  function renderDailyActivities(dailyActivities) {

      function dataFixFunction(x) {
        var result = new Date(x);
        result.setHours(0);
        result.setMinutes(0);
        return result;
      }

      var videoActivities = {
          x: dailyActivities.video_dates.map(dataFixFunction),
          y: dailyActivities.video_activities,
          name: 'Video',
          type: 'bar',
          marker:{
              color: '#568ecc'
          }
      };

      var discussionActivities = {
          x: dailyActivities.discussion_dates.map(dataFixFunction),
          y: dailyActivities.discussion_activities,
          name: 'Discussion',
          type: 'bar',
          marker:{
              color: '#50c156'
          }
      };

      var courseActivities = {
        x: dailyActivities.course_dates.map(dataFixFunction),
        y: dailyActivities.course_activities,
        name: 'Visit',
        type: 'bar',
        marker:{
            color: '#8e28c1'
        }
      };

      var stat = [videoActivities, discussionActivities, courseActivities];

      var x_template = {
      type: "date"
      };

      var y_template = {
      };

      if (dailyActivities.customize_yticks) {
        y_template["nticks"] = dailyActivities.nticks_y+1
      }

      var layout = {
        barmode: 'group',
        xaxis: x_template,
        yaxis: y_template,
        showlegend: false
      };

      Plotly.newPlot('activity-stats-plot', stat, layout, {displayModeBar: false});
  }

  function renderUnitVisits(unitVisits) {
      var heightLayout = unitVisits.tickvals.length * 20;

      var stat = {
          type: 'bar',
          orientation: 'h',
          x: unitVisits.count_visits,
          y: unitVisits.tickvals,
          name: '',
      };

      var layout = {
          showlegend: false,
          height: heightLayout > 450 && heightLayout || 450,
          yaxis: {
              ticktext: unitVisits.ticktext,
              tickvals: unitVisits.tickvals,
              tickmode: 'array',
              automargin: true,
              autorange: true,
          },
      };

      Plotly.newPlot('activity-unit-visits-stats-plot', [stat], layout, {displayModeBar: false});

  }

  function updateActivity() {
      $tabContentItems.addClass('hidden');

      function onError() {
          alert("Can't load data for selected period!");
      }

      function onSuccess(data) {
          $tabContentItems.removeClass('hidden');
          renderDailyActivities(data.daily_activities);
          renderUnitVisits(data.unit_visits);
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
