function FunnelTab(button, content) {
    'use strict';
    var funnelTab = new Tab(button, content);
    funnelTab.courseStructureView = content.find('#course-structure');

    function updateFunnel() {
        function onSuccess(response) {
            console.log(response);
            funnelTab.courseStructure = response.courses_structure;

            const viewContent = funnelTab.courseStructureView.find('.content');
            viewContent.empty();
            viewContent.append(generateFunnel(funnelTab.courseStructure));
            $('.funnel-item-0').on('click',(e)=> $(e.target).closest('.funnel-item').toggleClass('active'));
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
            return `<div class="${className}">
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
