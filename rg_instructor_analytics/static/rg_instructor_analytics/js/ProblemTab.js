/**
* Implementation of Tab for the problem tab
* @returns {Tab}
* @class old realisation
*/
function ProblemTab(button, content) {
    var problemTab = new Tab(button, content);
    var problemDetail = problemTab.content.find("#problem-body");

    /**
    * function for display general plot with homework`s stat
    */
    function updateHomeWork() {
        function onSuccess(response) {
            let maxAttempts = Math.max(...response.attempts);
            let countAttempts = [Math.min(...response.attempts), maxAttempts / 2, maxAttempts];
            let correctAnswer = [...response.correct_answer];
            let yAxis = [...response.names];
            let xAxisRight = ['0', '50%', '100%'];
            let $homework = $('#problem-homeworks-stats-plot');

            let bars = '', index = 0;
            for (let item in yAxis) {
                let attempts = (100 * response.attempts[index]) / maxAttempts;
                let percent = correctAnswer[index] * 100;
                let barHeight = 'auto';

                if (!percent && !attempts) {
                    barHeight = 0;
                }
                
                bars += `
                        <li
                            class="plot-bar-vert"
                            style="width: ${(100 - yAxis.length) / yAxis.length}%; height: ${barHeight}"
                            data-attribute="${index}"
                        >
                            <div class="plot-bar-attempts" style="height: ${attempts}%">
                                <span class="plot-bar-value">${response.attempts[index].toFixed(1)}</span>
                            </div>
                            <div class="plot-bar-percent" style="height: ${percent}%">
                                <span class="plot-bar-value">${percent.toFixed(1)}%</span>
                            </div>
                            <div class="plot-click-me">django.gettext('DETAILS')</div>
                        </li>
                `
                index++;
            }
            bars = `<ul class="plot-body">${bars}</ul>`;
            //build x axis
            let axis = ``;
            let small;
            if (yAxis.length > 10) {small = 'small'}
            yAxis.forEach((item) => {
                axis += `
                <li 
                    class="hw-xaxis ${small}" 
                    style="min-width: ${(100 - yAxis.length) / yAxis.length}%;"
                    >
                        <div>${item}</div>
                </li>`
            });
            axis = `<ul class="x-axis">${axis}</ul>`;
            bars += axis;
            // build left y axis
            axis = '';
            countAttempts.forEach((item) => {
                axis += `<li>${item.toFixed(1)}</li>`
            });
            axis = `<ul class="y-axis-l">${axis}</ul>`;
            bars += axis;
            //build right y axis
            axis = '';
            xAxisRight.forEach((item) => {
                axis += `<li>${item}</li>`
            });
            axis = `<ul class="y-axis-r">${axis}</ul>`;
            bars += axis;

            $homework.html(bars);

            $homework.on('click', function (e) {
                $('.enrollment-title-1.hidden, .enrollment-title-text-1.hidden,  .enrollment-legend-holder__square-1').removeClass('hidden');
                if ($(e.target).closest('li').data()) {
                    let attr = $(e.target).closest('li').data();
                    loadHomeWorkProblems(response.problems[attr.attribute]);
                }
            });
            if (small) {
                $('.plot-bar-vert').on('mouseover', function (e) {

                    let attr = $(this).data('attribute');

                    $('.hw-xaxis').removeClass('hover');
                    $('.hw-xaxis')[attr].classList.add('hover');
                });
                $('.plot-bar-vert').on('mouseleave', function (e) {
                    $('.hw-xaxis').removeClass('hover');
                });
            }
        }

        function onError() {
            alert("Can not load statistic for select course");
        }

        $.ajax({
            traditional: true,
            type: "POST",
            url: "api/problem_statics/homework/",
            data: {},
            success: onSuccess,
            error: onError,
            dataType: "json"
        });
    }

    /**
    * function for display plot with homework problem statistics
    * @param homeworsProblem string id of the problem
    */
    function loadHomeWorkProblems(homeworsProblem) {
        function onSuccess(response) {


            const correct = response.correct;
            const incorrect = response.incorrect;
            const absIncorrect = incorrect.map(x => Math.abs(x));
            const yAxis = Array.from(new Array(correct.length), (x, i) => i + 1);
            const maxCorrect = Math.max(...correct) || 1;
            const maxIncorrect = Math.max(...absIncorrect) || 1;
            const xAxis = [maxCorrect, maxCorrect / 2, 0, maxIncorrect / 2, maxIncorrect];

            let index = 0;
            let bars = '';

            for (let item in yAxis) {
                const correctBar = 100 * correct[index] / maxCorrect;
                const incorrectBar = Math.abs(100 * incorrect[index] / maxIncorrect);
                let barHeight = 'auto';
                if (!correctBar && !incorrectBar) {
                    barHeight = 0;
                }
                bars += `
                        <li class="plot-bar-vertical"
                            style="width: ${(100 - yAxis.length) / yAxis.length}%; height: ${barHeight}"
                            data-attribute="${index}"
                        >
                            <div class="correct-bar" style="height:${correctBar/2}%">
                                <span>${correct[index]}</span>
                            </div>
                            <div class="incorrect-bar" style="height:${incorrectBar/2}%">
                                <span>${Math.abs(incorrect[index])}</span>
                            </div>
                            <div class="plot-click-me">django.gettext('DETAILS')</div>
                        </li>
                        `
                index++;
            }
            bars = `<ul class="plot-body">${bars}</ul>`;
            // build y axis
            let axis = '';
            yAxis.forEach(item=>{
                axis += `<li style="width: ${(100 - yAxis.length) / yAxis.length}%">${item}</li>`;
            })
            axis = `<ul class="x-axis">${axis}</ul>`;
            bars += axis;
            // build x axis
            axis = '';
            xAxis.forEach(item=>{
                axis += `<li><div>${item.toFixed(1)}</div></li>`
            })
            axis = `<ul class="y-axis-l">${axis}</ul>`
            bars += axis;
            
            $('#problems-stats-plot').html(bars);


            $('#problems-stats-plot').on('click', function (e) {
                if ($(e.target).closest('li').data()) {
                    let attr = $(e.target).closest('li').data();
                    displayProblemView(homeworsProblem[attr.attribute]);
                }
            });
        }

        function onError() {
            alert("Can not load statistic for select course");
        }

        $.ajax({
            traditional: true,
            type: "POST",
            url: "api/problem_statics/homeworksproblems/",
            data: { problems: homeworsProblem },
            success: onSuccess,
            error: onError,
            dataType: "json"
        });

    }

    /**
    * function for the render problem body
    * @param stringProblemID string problem id
    */
    function displayProblemView(stringProblemID) {
        function onSuccess(response) {
            problemDetail.html(response.html);
            let problemsWrapper = problemDetail.find(".problems-wrapper");
            let problemBody = problemsWrapper.attr("data-content");
            problemsWrapper.html(problemBody);

            //hide problem debug info
            problemsWrapper.find('.status-icon').hide();
            problemsWrapper.find('.submit').hide();
            problemDetail.find('.instructor-info-action').hide();
            problemDetail.find('.status').remove();

            bindPlotsPopupForProblem(problemsWrapper, stringProblemID)
        }

        function onError() {
            alert("Can not load statistic for select course");
        }

        $.ajax({
            traditional: true,
            type: "POST",
            url: "api/problem_statics/problem_detail/",
            data: { problem: stringProblemID },
            success: onSuccess,
            error: onError,
            dataType: "json"
        });
    }

    problemTab.loadTabData = function () {
        updateHomeWork()
    };

    problemTab.content.find('.close').click(item => problemTab.content.find('.modal-for-plot').hide());

    return problemTab;
}

/**
* add buttons for show plot for problem`s question
* @param problem div with problem`s render
* @param stringProblemID string problem id
*/
function bindPlotsPopupForProblem(problem, stringProblemID) {
    var avalivleQuestions = [OpetionQuestion, RadioOpetionQuestion, MultyChoseQuestion];
    var questionsDivs = problem.find(".wrapper-problem-response");
    var isAdded;
    questionsDivs.each(function (index) {
        isAdded = false;
        var html = $(questionsDivs[index]);
        for (var i = 0; i < avalivleQuestions.length; i++) {
            var question = avalivleQuestions[i](html, stringProblemID);
            if (question.isCanParse()) {
                question.applyToCurrentProblem(html);
                html.append(`
                <div id="model_plot" class="modal-for-plot">
                    <div>
                        <div id="problem-question-plot"></div>
                    </div>
                </div>`);
                isAdded = true;
                break;
            }
        }
        if (!isAdded) {
            $('<p>We can`t display plot for this question.</p>').appendTo(html);
        }
    });
}

/**
* Base class for questions
* @param questionHtml layout with question
* @param stringProblemID string id of question`s problem
* @class old realisation
* @abstract
*/
function BaseQuestion(questionHtml, stringProblemID) {
    this.questionHtml = questionHtml;
    this.problemID = stringProblemID;

    /**
        * abstract method for indicate, can instance of question correct parse given html
            * @abstract
                */
    this.isCanParse = function () {
        throw new Error("missing implementation")
    };

    /**
    * abstract method, that provide information for question statistics request
    * @return object with the body:
    * return {
    *       type: string // string marker for the given question
    *       questionID: string, // id of the question
    *       answerMap: JSON string // json with relation between the real data and its representation in the database
    *  }
    *
    * @abstract
    */
    this.getRequestMap = function () {
        throw new Error("missing implementation")
    };

    /**
    * function for displaying server's as the bar plot
    * @param data server response. Object with key - name of the position and value - value of the position
    */
    this.displayBar = function (data) {
        const plot_popup = this.questionHtml.parent().find('.modal-for-plot');
        plot_popup.show();

        var x = [];
        var y = [];
        Object.keys(data).forEach(function (key) {
            y.push(key);
            x.push(data[key]);
        });
        let plot = '';
        idx = 0;
        let maxValue = Math.max(...x);

        for (let item in x) {
            let name = y[idx++];
            let value = x[item];
            plot += `
              <li class="plot-row">
                <span class="plot-name">${name}</span>
                <div class="plot-bar-holder">
                   <div class="plot-bar" style="width: ${(value * 100) / maxValue}%"></div>
                </div>
                <span class="plot-value">${value}</span>
              </li>`
        }
        plot = `<ul>${plot}</ul>`;
        this.questionHtml.parent().find('#problem-question-plot').html(plot);
    };

    /**
    * call`s when receive response with statistics for the question
    * @param response
    */
    this.onGettingStat = function (response) {
        console.log(this.questionHtml);
        switch (response.type) {
            case 'bar':
                this.displayBar(response.stats);
                break;
        }
    };

    this.onGettingStatFail = function () {
        console.log("something bad headings")
    };

    /**
    * apply given instance to some question of the problem
    * @param html layout for inserting the button to display the plot
    */
    this.applyToCurrentProblem = function (html) {
        const $plotBtn = $('<button>Show Plot</button>');
        $plotBtn.appendTo(html);
        $plotBtn.click((item) => {
            var requestMap = this.getRequestMap();
            requestMap.problemID = this.problemID;
            $(item.target).toggleClass('active');
            if ($(item.target).hasClass('active')) {
                $(item.target).html('Hide Plot');
                this.questionHtml.parent().find('.modal-for-plot').removeClass('hidden');
                $.ajax({
                    traditional: true,
                    type: "POST",
                    url: "api/problem_statics/problem_question_stat/",
                    data: requestMap,
                    success: (response) => this.onGettingStat(response),
                    error: () => this.onGettingStatFail(),
                    dataType: "json"
                });
            } else {
                $(item.target).html('Show Plot');
                this.questionHtml.parent().find('.modal-for-plot').addClass('hidden');
            }
        });
    };
}

/**
* Implementation for the drop down question
* @param questionHtml
* @param stringProblemID
* @return {OpetionQuestion}
* @class old realisation
* @extends BaseQuestion
*/
function OpetionQuestion(questionHtml, stringProblemID) {
    const optionQuestion = new BaseQuestion(questionHtml, stringProblemID);
    const question = optionQuestion.questionHtml.find('.option-input');
    optionQuestion.questionHtml = question.length === 1 ? $(question[0]) : null;

    optionQuestion.isCanParse = function () {
        return this.questionHtml !== null
    };

    optionQuestion.getRequestMap = function () {
        const selectRoot = this.questionHtml.find('select');
        const optionsItem = selectRoot.find('option');
        const id2ValueMap = {};
        optionsItem.each(index => id2ValueMap[optionsItem[index].value] = optionsItem[index].text);
        return {
            type: 'select',
            questionID: selectRoot.attr('name').replace('input_', ''),
            answerMap: JSON.stringify(id2ValueMap)
        }

    };

    return optionQuestion;
}

/**
* Implementation for the single choice question
* @param questionHtml
* @param stringProblemID
* @return {RadioOpetionQuestion}
* @class old realisation
* @extends BaseQuestion
*/
function RadioOpetionQuestion(questionHtml, stringProblemID) {
    const optionQuestion = new BaseQuestion(questionHtml, stringProblemID);
    const question = optionQuestion.questionHtml.find('.choicegroup');
    optionQuestion.questionHtml = question.length === 1 ? $(question[0]) : null;
    optionQuestion.options = optionQuestion.questionHtml.find('input[type="radio"]');

    optionQuestion.isCanParse = function () {
        return optionQuestion.options.length > 0
    };

    optionQuestion.getRequestMap = function () {
        const id2ValueMap = {};
        this.options.each(index =>
            id2ValueMap[this.options[index].value] = $(this.options[index].parentNode).text().trim());
        return {
            type: 'select',
            questionID: this.questionHtml.attr('id').replace('inputtype_', ''),
            answerMap: JSON.stringify(id2ValueMap)
        }

    };

    return optionQuestion;
}


/**
* Implementation for the question with checkbox
* @param questionHtml
* @param stringProblemID
* @return {MultyChoseQuestion}
* @class old realisation
* @extends RadioOpetionQuestion
*/
function MultyChoseQuestion(questionHtml, stringProblemID) {
    const multyChooseQuestion = new RadioOpetionQuestion(questionHtml, stringProblemID);
    multyChooseQuestion.options = multyChooseQuestion.questionHtml.find('input[type="checkbox"]');

    var baseRequestMapFunction = multyChooseQuestion.getRequestMap;
    multyChooseQuestion.getRequestMap = function () {
        var result = baseRequestMapFunction.call(this)
        result.type = 'multySelect';
        return result;
    };

    return multyChooseQuestion;
}

