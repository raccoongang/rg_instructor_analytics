/**
 * Abstract class for tabs in instructor analytics tab
 * @param button is used for switching to the given tab
 * @param content content of the given tab
 * @class old realisation
 * @abstract
 */
function Tab(button, content) {
    var tab = this;

    this.button = button;
    this.content = content;
    this.tabHolder = undefined;
    this.locationToOpen = undefined;
    this.isActive = false;

    /**
     * Called for mark this tab active and show content.
     * @param isActive
     */
    this.setActive = function (isActive) {
        this.isActive = isActive;
        if (isActive) {
            content.addClass('active-section');
            button.addClass('active-section');
            this.loadTabData();
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
     * Navigate to tab's content.
     */
    this.openLocation = function (location) {
        tab.locationToOpen = location;
    }
}
