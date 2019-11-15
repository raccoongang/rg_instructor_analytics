/**
 * Time range filtering component.
 * @param content - tab content
 * @param action - fn to trigger
 */
function TimeFilter(content, action) {
  var filter = this;
  var pickerDateFormat = $.datepicker.ISO_8601;  // 'yy-mm-dd' => 2018-02-02
  var momentDateFormat = 'YYYY-MM-DD';           // 2018-02-02
  var $selectPeriodBtn = content.find(".js-datepicker-btn");
  var periodDiv = content.find(".js-datepicker-dropdown");
  var $loader = content.find(".js-loader");
  this.minDate = null;
  this.firstEnrollDate = null;
  this.courseStartDate = null;


  this.$fromDatePicker = content.find(".js-from-datepicker")
    .datepicker({
      maxDate: moment().format(momentDateFormat),
      dateFormat: pickerDateFormat,
      onSelect: function(dateStr) {
        filter.$toDatePicker.datepicker("option", "minDate", dateStr);
        filter.startDate = moment(dateStr);
      }
    });
  this.$toDatePicker = content.find(".js-to-datepicker")
    .datepicker({
      maxDate: moment().format(momentDateFormat),
      dateFormat: pickerDateFormat,
      onSelect: function(dateStr) {
        filter.$fromDatePicker.datepicker("option", "maxDate", dateStr);
        filter.endDate = moment(dateStr);
      }
    });

  /**
   * Rerender date range selector.
   */
  this.updateStatPeriod = function() {
    $selectPeriodBtn.html(
      filter.startDate.format(momentDateFormat) + ' - ' + filter.endDate.format(momentDateFormat)
    );
  };

  Object.defineProperties(this, {
    startDate: {
      get: function() {
        return this._startDate;
      },
      set: function(val) {
        if (moment.isMoment(val) && val <= moment()) {  // do not set if Course starts in the Future
          this._startDate = val;
          this.$fromDatePicker.datepicker("setDate", val.format(momentDateFormat));
          if (this.endDate) {
            this.updateStatPeriod();
          }
        }
      }
    },
    endDate: {
      get: function() {
        return this._endDate;
      },
      set: function(val) {
        if (moment.isMoment(val)) {
          this._endDate = val;
          this.$toDatePicker.datepicker("setDate", val.format(momentDateFormat));
          if (this.startDate) {
            this.updateStatPeriod();
          }
        }
      }
    },
    timestampRange: {
      get: function() {
        return {
          from: this.startDate.unix(),
          to: this.endDate.unix(),
        }
      }
    }
  });

  // Handlers:
  $selectPeriodBtn.click(function() {
    filter.makeActive(this);
    periodDiv.toggleClass('show');
  });

  content.find(".js-date-apply-btn").click(function() {
    periodDiv.removeClass('show');
    action();
  });

  content.find(".js-date-cancel-btn").click(function() {
    periodDiv.removeClass('show');
  });

  content.find(".js-select-time-interval").change(function() {
    switch ($(this).val()) {
      case "lastweek":
        filter.startDate = filter.getStartEndDates().lastWeekFrom;
        filter.endDate = filter.getStartEndDates().lastWeekTo;
        break;
      case "last2weeks":
        filter.startDate = filter.getStartEndDates().last2WeeksFrom;
        filter.endDate = filter.getStartEndDates().last2WeeksTo;
        break;
      case "lastmonth":
        filter.startDate = filter.getStartEndDates().last4WeeksFrom;
        filter.endDate = filter.getStartEndDates().last4WeeksTo;
        break;
      case "sincecoursestart":
        filter.startDate = filter.minDate;
        filter.endDate = moment();
        break;
      case "allenrollments":
        filter.startDate = filter.firstEnrollDate;
        filter.endDate = moment();
        break;
    }
        filter.updateDates();
        action();
  });

  this.makeActive = function (target) {
    periodDiv.removeClass('show');
    content.find('.filter-btn').removeClass('active');
    $(target).addClass('active');
  };

  this.setDisable = function () {
    content.find(".js-select-1-week").prop(
      "disabled",
      this.getStartEndDates().lastWeekFrom < filter.minDate
    );
    content.find(".js-select-2-week").prop(
      "disabled",
      this.getStartEndDates().last2WeeksFrom < filter.minDate
    );
    content.find(".js-select-4-week").prop(
      "disabled",
      this.getStartEndDates().last4WeeksFrom < filter.minDate
    );
  };

  this.setLoader = function () {
    $loader.removeClass('hidden');
  };
  
  this.removeLoader = function () {
    $loader.addClass('hidden');
  };

  this.setMinDate = function () {
    filter.$fromDatePicker.datepicker("option", "minDate", filter.minDate.format(momentDateFormat));
    filter.$toDatePicker.datepicker("option", "minDate", filter.startDate.format(momentDateFormat));
  };

  this.updateDates = function () {
    filter.$toDatePicker.datepicker("option", "minDate", filter.startDate.format(momentDateFormat));
    filter.$fromDatePicker.datepicker("option", "maxDate", filter.endDate.format(momentDateFormat));
  };

  this.getStartEndDates = function () {
    return {
      lastWeekFrom: moment().subtract(1, 'weeks').startOf('isoWeek'),
      lastWeekTo: moment().subtract(1, 'weeks').endOf('isoWeek'),
      last2WeeksFrom: moment().subtract(2, 'weeks').startOf('isoWeek'),
      last2WeeksTo: moment().subtract(1, 'weeks').endOf('isoWeek'),
      last4WeeksFrom: moment().subtract(1, 'months').startOf('month'),
      last4WeeksTo: moment().subtract(1, 'months').endOf('month'),
    }
  };

  this.init = function (minDate, firstEnrollDate){
    filter.minDate = minDate;
    filter.firstEnrollDate = firstEnrollDate;
    filter.setDisable();

    // Select 'Last Week' time interval if possible, otherwise
    // select 'All Enrollments' for enrollments tab or 'Since Course Start' for other tabs
    $lastWeekSelector = content.find(".js-select-1-week");

    if (! $lastWeekSelector.prop('disabled')){
      $lastWeekSelector.prop('selected', true);
      filter.startDate = filter.getStartEndDates().lastWeekFrom;
      filter.endDate = filter.getStartEndDates().lastWeekTo;
    }
    else {
      if (firstEnrollDate) {
        content.find(".js-select-all-enroll").prop('selected', true);
        filter.startDate = firstEnrollDate;
      }
      else {
        content.find(".js-select-all-week").prop('selected', true);
        filter.startDate = minDate;
      }
      filter.endDate = moment();
    }
    filter.setMinDate();
    filter.makeActive(content.find(".js-datepicker-btn"));
  };

}
