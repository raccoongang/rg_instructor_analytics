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
    /**
     * Called for mark this tab active and show content.
     * @param isActive
     */
    this.setActive = function (isActive) {
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
    }
}

// exports.Tab = Tab;
