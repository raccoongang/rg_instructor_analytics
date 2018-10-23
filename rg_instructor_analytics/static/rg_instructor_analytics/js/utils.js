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

  this.$fromDatePicker = content.find(".js-from-datepicker")
    .datepicker({
      dateFormat: pickerDateFormat,
      onSelect: function(dateStr) {
        filter.$toDatePicker.datepicker("option", "minDate", dateStr);
        filter.startDate = moment(dateStr);
      }
    });
  this.$toDatePicker = content.find(".js-to-datepicker")
    .datepicker({
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
      this.startDate.format(momentDateFormat) + ' - ' + this.endDate.format(momentDateFormat)
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
        if (val < this.minDate) {
          this.minDate = val;
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

  // Range represented as Moment.js objects:
  this.startDate = moment().subtract(1, 'months');
  this.endDate = moment();
  this.minDate = moment(this.startDate);

  // Handlers:
  $selectPeriodBtn.click(function() {
    makeActive(this);
    periodDiv.toggleClass('show');
  });

  content.find(".js-date-apply-btn").click(function() {
    periodDiv.removeClass('show');
    action(filter);
  });

  content.find(".js-select-1-week").click(function() {
    makeActive(this);
    filter.endDate = moment().subtract(1, 'weeks').endOf('isoWeek');
    filter.startDate = moment().subtract(1, 'weeks').startOf('isoWeek');
    action(filter);
  });

  content.find(".js-select-2-week").click(function() {
    makeActive(this);
    filter.endDate = moment().subtract(1, 'weeks').endOf('isoWeek');
    filter.startDate = moment().subtract(2, 'weeks').startOf('isoWeek');
    action(filter);
  });

  content.find(".js-select-4-week").click(function() {
    makeActive(this);
    filter.endDate = moment().subtract(1, 'months').endOf('month');
    filter.startDate = moment().subtract(1, 'months').startOf('month');
    action(filter);
  });

  content.find(".js-select-all-week").click(function() {
    makeActive(this);
    filter.endDate = moment();
    filter.startDate = filter.minDate;
    action(filter);
  });

  function makeActive(target) {
    periodDiv.removeClass('show');
    content.find('.filter-btn').removeClass('active');
    $(target).addClass('active');
  }

  this.setLoader = function () {
    $loader.removeClass('hidden');
  };
  
  this.removeLoader = function () {
    $loader.addClass('hidden');
  };

}
