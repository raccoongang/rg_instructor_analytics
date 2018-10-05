function TabHolder(tabs, course, course_cohort) {
    this.tabs = tabs;
    this.course = course;
    this.courseCohort = course_cohort;

    this.original_ajax = $.ajax;

    $.ajax = (...args) => {
        if(args[0].data === undefined){
            args[0].data = {};
        }
        args[0].data.course_id = this.course;
        args[0].data.cohort = this.courseCohort;
        return  this.original_ajax(...args);
    };

    for (let tabName in this.tabs) {
        let tab = this.tabs[tabName];
        tab.tabHolder = this;
        tab.button.click(() => this.toggleToTab(tabName));
    }


    this.toggleToTab = (tab) => {
        for (let tabName in this.tabs) {
            var doLoadData = tabName === 'funnel';
            this.tabs[tabName].setActive(tabName === tab, doLoadData);
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
        let resetCohort = this.course !== course;
        this.course = course;
        this.courseCohort = null;
        for (let tabName in this.tabs) {
            this.tabs[tabName].loadTabData(resetCohort)
        }
    };
    
    this.selectCourseCohort = (cohort) => {
        this.courseCohort = cohort;
        for (let tabName in this.tabs) {
            this.tabs[tabName].loadTabData()
        }
    }
}
