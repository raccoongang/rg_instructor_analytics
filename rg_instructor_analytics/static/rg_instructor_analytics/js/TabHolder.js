function TabHolder(tabs, course) {
    this.tabs = tabs;
    this.course = course;

    this.original_ajax = $.ajax;

    $.ajax = (...args) => {
        if(args[0].data === undefined){
            args[0].data = {};
        }
        args[0].data.course_id = this.course;
        return  this.original_ajax(...args);
    };

    for (let tabName in this.tabs) {
        let tab = this.tabs[tabName];
        tab.tabHolder = this;
        tab.button.click(() => this.toggleToTab(tabName));
    }


    this.toggleToTab = (tab) => {
        for (let tabName in this.tabs) {
            this.tabs[tabName].setActive(tabName === tab);
        }
    };

    this.openLocation = (location) => {
        const tab= this.tabs[location.value];
        if(tab.openLocation){
            tab.openLocation(location.child);
        }
        this.toggleToTab(location.value);
    };

    this.selectCourse = (course) => {
        this.course = course;
        for (let tabName in this.tabs) {
            this.tabs[tabName].loadTabData()
        }
    }
}
