function TabHolder(tabs, course) {
    var holder = this;
    
    this.tabs = tabs;
    this.course = course.replace(/###.*/, '');
    this.cohort = course.replace(/.*###/, '');

    this.original_ajax = $.ajax;

    $.ajax = function() {
        if(arguments[0].data === undefined){
            arguments[0].data = {};
        }
        arguments[0].data.course_id = holder.course;
        arguments[0].data.cohort_id = holder.cohort;
        return  holder.original_ajax.apply(holder.original_ajax, arguments);
    };

    function setTab(tabName) {
        var tab = tabs[tabName];
        tab.tabHolder = holder;
        tab.button.click(function () {
            holder.toggleToTab(tabName);
        });
    }
    
    for (var tabName in tabs) {
        if (tabs.hasOwnProperty(tabName)) {
            setTab(tabName);
        }
    }

    this.toggleToTab = function (tab) {
        for (var tabName in tabs) {
            if (tabs.hasOwnProperty(tabName)) {
                tabs[tabName].setActive(tabName === tab);
            }
        }
    };

    this.openLocation = function(location) {
        var tab = tabs[location.value];
        
        if (tab.openLocation) {
            tab.openLocation(location.child);
        }
        this.toggleToTab(location.value);
    };

    this.selectCourse = function(course) {
        holder.course = course.replace(/###.*/, '');
        holder.cohort = course.replace(/.*###/, '');

        for (var tabName in tabs) {
            if (tabs.hasOwnProperty(tabName)) {
                if (tabs[tabName].isActive) {
                    tabs[tabName].loadTabData();
                }
            }
        }
    }
}
