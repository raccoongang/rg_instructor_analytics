function SuggestionTab(button, content) {
    'use strict';
    const suggestionTab = new Tab(button, content);

    function updateSuggestion() {
        function onSuggestionLoad(response) {
            const suggestionContent = suggestionTab.content.find('#suggestion-content');
            suggestionContent[0].innerHTML = response.suggestion.map(renderSuggestion).join('\n');
            suggestionContent.find('.go-to-item').click((e)=>{
                const itemID = e.target.dataset.item_id
            })
        }

        function renderSuggestion(suggestion) {
            return (
                `<div class="suggestion-item" ">
                    <div class="desctiption">
                        ${suggestion.description}
                    </div>
                    <button class="go-to-item" data-item_id="${suggestion.item_id}">Go to item</button>
                </div>`
            )
        }


        function onSuggestionLoadError() {
            alert("Can not load statistic for select course");
        }

        $.ajax({
            traditional: true,
            type: 'POST',
            url: 'api/suggestion/',
            success: onSuggestionLoad,
            error: onSuggestionLoadError,
            data: {intent: 'get_norm_list'},
            dataType: 'json'
        });
    }

    suggestionTab.loadTabData = updateSuggestion;

    return suggestionTab;
}
