function TabHolder(tabs) {
    this.tabs = tabs;

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
    }
}
