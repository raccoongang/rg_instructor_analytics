/**
 * Abstract class for tabs in instructor analytics tab
 * @param button is used for switching to the given tab
 * @param content content of the given tab
 * @class old realisation
 * @abstract
 */
function Tab(button, content) {
    this.button = button;
    this.content = content;
    this.tabHolder = undefined;
    this.locationToOpen = undefined;
    /**
     * Called for mark this tab active and show content.
     * @param isActive
     */
    this.setActive = function (isActive) {
        if (isActive) {
            content.addClass('active-section');
            button.addClass('active-section');
            // this.loadTabData();
        } else {
            content.removeClass('active-section');
            button.removeClass('active-section');
        }
    };



    /**
     * Called for loading date for some tab implementation.
     * @abstract
     */
    this.loadTabData = function () {
        throw new Error("missing implementation")
    };


    /**
     * Called for navigate to the content inside tab.
     */
    this.openLocation = (location) => {
        this.locationToOpen = location
    };
    
    this.populateCohortSelect = function (response, resetCohort) {
      if (resetCohort) {
          if (response.available_cohorts.length > 1) {
            $('#select_cohort').html('<option value=""> --- </option>');
          } else {
              $('#select_cohort').html('');
          }
          response.available_cohorts.forEach((cohort) => {
              $('#select_cohort').append(
                  '<option value="' + cohort + '">' + cohort + '</option>'
              );
          })
      }
    }
}
