function FunnelTab(button, content) {
    'use strict';
    var funnelTab = new Tab(button, content);
    funnelTab.courseStructureView = content.find('#course-structure');

    function updateFunnel() {
        function onSuccess(response) {
            console.log(response);
            funnelTab.courseStructure = response.courses_structure
            addNewFunnelItems(funnelTab.courseStructureView, funnelTab.courseStructure)
        }

        function addListenerToFunnelItems(rootItem) {
            rootItem.find('.funnel-item').click((item) => {
                var target = $(item.target);
                target.parent().unbind('click')
                var location = target.data('location');
                var data = funnelTab.courseStructure[location[0]];
                for (var i = 1; i < location.length; i++) {
                    data = data.children[location[i]];
                }
                if (data.level < 3) { // when it is not problem level
                    addNewFunnelItems(target, data.children, location)
                }

            })
        }

        function addNewFunnelItems(view, data, location = []) {
            var sectionItem = '<ul>';
            var viewContent = view.find('.content');
            viewContent.empty();
            for (var s = 0; s < data.length; s++) {
                var newLocation = location.slice();
                newLocation.push(s)
                sectionItem += '<li><div class="funnel-item" data-location="[' + newLocation + ']">';
                sectionItem += (
                    'Name : ' + data[s].name + ' | ' + data[s].student_count
                );
                sectionItem += '<div class="content"/></div></li>';
            }
            sectionItem += '</ul>';
            viewContent.append(sectionItem);
            addListenerToFunnelItems(view)
        }

        function onError() {
            alert('Can not load statistic for the selected course');
        }

        $.ajax({
            traditional: true,
            type: 'POST',
            url: 'api/funnel/',
            success: onSuccess,
            error: onError,
            dataType: 'json'
        });
    }

    funnelTab.loadTabData = updateFunnel;

    return funnelTab;
}
