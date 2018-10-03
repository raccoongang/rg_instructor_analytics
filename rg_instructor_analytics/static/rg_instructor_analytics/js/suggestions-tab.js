function SuggestionTab(button, content) {
    'use strict';
    var suggestionTab = new Tab(button, content);
    var $loader = $('#sug-loader');
    
    function toggleLoader() {
        $loader.toggleClass('hidden');
    }
    
    function onSuggestionLoadError() {
        alert("Can't load data for selected course!");
    }
    
    function onSuggestionLoad(response) {
        var suggestionContent = suggestionTab.content.find('#suggestion-content');
        
        if (response.suggestion.length > 0) {
            suggestionContent[0].innerHTML = response.suggestion.map(renderSuggestion).join('\n');
        } else {
            suggestionContent[0].innerHTML = '<div>' + django.gettext("No suggestions so far.") + '</div>';
        }
        suggestionContent.find('.go-to-item').click(function(evt) {
            var location = JSON.parse(evt.target.dataset.location);
            suggestionTab.tabHolder.openLocation(location);
        })
    }
    
    function renderSuggestion(suggestion) {
        var description = suggestion.description;
        var location = JSON.stringify(suggestion.location);
        
        return (
            _.template(
                '<div class="suggestion-item">' +
                    '<div class="desctiption suggestion-message">' +
                        '<%= description %>' +
                    '</div>' +
                    '<button class="go-to-item suggestion-button" data-location=\'<%= location %>\'>' +
                        django.gettext("Go to item") +
                    '</button>' +
                '</div>'
            )({
                description: description,
                location: location,
            })
        )
    }

    suggestionTab.loadTabData = function () {
        $.ajax({
            type: 'POST',
            url: 'api/suggestion/',  // TODO remove hardcore
            data: {intent: 'get_norm_list'},
            dataType: 'json',
            traditional: true,
            success: onSuggestionLoad,
            error: onSuggestionLoadError,
            beforeSend: toggleLoader,
            complete: toggleLoader,
        });
    };

    return suggestionTab;
}
