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
          from: new Date(this.startDate).toLocaleString().split(',')[0],
          to: new Date(this.endDate).toLocaleString().split(',')[0],
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

  content.find(".js-select-1-week").click(function() {
    filter.makeActive(this);
    filter.startDate = filter.getStartEndDates().lastWeekFrom;
    filter.endDate = filter.getStartEndDates().lastWeekTo;
    filter.updateDates();
    action();
  });

  content.find(".js-select-2-week").click(function() {
    filter.makeActive(this);
    filter.startDate = filter.getStartEndDates().last2WeeksFrom;
    filter.endDate = filter.getStartEndDates().last2WeeksTo;
    filter.updateDates();
    action();
  });

  content.find(".js-select-4-week").click(function() {
    filter.makeActive(this);
    filter.startDate = filter.getStartEndDates().last4WeeksFrom;
    filter.endDate = filter.getStartEndDates().last4WeeksTo;
    filter.updateDates();
    action();
  });

  content.find(".js-select-all-week").click(function() {
    filter.makeActive(this);
    filter.startDate = filter.minDate;
    filter.endDate = moment();
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
      ((this.getStartEndDates().lastWeekFrom - filter.startDate) < 0)
    );
    content.find(".js-select-2-week").prop(
      "disabled",
      ((this.getStartEndDates().last2WeeksFrom - filter.startDate) < 0)
    );
    content.find(".js-select-4-week").prop(
      "disabled",
      ((this.getStartEndDates().last4WeeksFrom - filter.startDate) < 0)
    )
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
}

function exportToCSV(action, course, data) {
    var i, form, key;

    form = document.createElement('form');
    form.hidden = true;
    form.method = 'POST';
    form.action = action;
    data.format = 'csv';
    data.csrfmiddlewaretoken = $.cookie('csrftoken');
    data.course_id = course;
    for (key in data) {
        i = document.createElement('input');
        i.name = key;
        i.value = data[key];
        form.appendChild(i);
    }
    document.body.appendChild(form);
    form.submit();
    form.remove();
}
