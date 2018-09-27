function FunnelTab(button, content) {
    'use strict';
    var funnelTab = new Tab(button, content);
    funnelTab.courseStructureView = content.find('#course-structure');
    
    function openLocation() {
        let items = [funnelTab.viewContent.find(`*[data-edxid="${funnelTab.locationToOpen.value}"]`)];
        while (!items.slice(-1)[0].hasClass('funnel-item-0')){
            items.push(items.slice(-1)[0].parent())
        }
        items.map(el => el.click());
        funnelTab.locationToOpen = undefined;
    }

    function updateFunnel() {
        function onSuccess(response) {
            funnelTab.courseStructure = response.courses_structure;

            funnelTab.viewContent = funnelTab.courseStructureView.find('.content');
            funnelTab.viewContent.empty();
            funnelTab.viewContent.append(generateFunnel(funnelTab.courseStructure));
            $('.funnel-item-0').on('click',(e)=> $(e.target).closest('.funnel-item').toggleClass('active'));

            if(funnelTab.locationToOpen) openLocation()

        }

        function generateFunnel(data) {
            return data.map(el => el.level > 2 ? '' : `${generateFunnelItem(el,generateFunnel(el.children))}`).join(' ');
        }

        function generateFunnelItem(item, children) {
            const name = item.name;
            const incoming = item.student_count_in;
            const stuck = item.student_count;
            const out = item.student_count_out;
            const className = `funnel-item funnel-item-${item.level}`;
            return `<div class="${className}" data-edxid = '${item.id}'>
                        <div class="funnel-item-content">
                            <span class="funnel-item-incoming">${incoming}</span>
                            <span class="funnel-item-outgoing">${out}</span>
                            <span class="funnel-item-name">${name}</span>
                            <span class="funnel-item-stuck">stuck: ${stuck}</span>
                        </div>
                        ${children}
                    </div>`
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
