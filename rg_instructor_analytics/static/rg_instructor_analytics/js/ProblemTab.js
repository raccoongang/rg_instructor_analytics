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

            const correct_answer = {
                x: response.names,
                y: response.correct_answer,
                data: response.problems,
                name: django.gettext('Percent of the correct answers'),
                type: 'bar'
            };

            const attempts = {
                x: response.names,
                y: response.attempts,
                data: response.problems,
                name: django.gettext('Average count of attempts'),
                type: 'bar'
            };
            const data = [correct_answer, attempts];

            Plotly.newPlot('problem-homeworks-stats-plot', data);
            document.getElementById("problem-homeworks-stats-plot").on('plotly_click', function (data) {
                loadHomeWorkProblems(response.problems[data.points[0].pointNumber]);
            });
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

            const incorrect = {
                y: response.incorrect,
                name: django.gettext('Incorrect answers'),
                type: 'bar'
            };

            const correct = {
                y: response.correct,
                name: django.gettext('Correct answers'),
                type: 'bar'
            };
            const data = [correct, incorrect];

            const layout = {
                barmode: 'relative',
                xaxis: {dtick: 1},
                yaxis: {dtick: 1}
            };

            Plotly.newPlot('problems-stats-plot', data, layout);

            document.getElementById("problems-stats-plot").on('plotly_click', function (data) {
                displayProblemView(homeworsProblem[data.points[0].pointNumber]);
            });
        }

        function onError() {
            alert("Can not load statistic for select course");
        }

        $.ajax({
            traditional: true,
            type: "POST",
            url: "api/problem_statics/homeworksproblems/",
            data: {problems: homeworsProblem},
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
            data: {problem: stringProblemID},
            success: onSuccess,
            error: onError,
            dataType: "json"
        });
    }

    problemTab.loadTabData = function () {
        updateHomeWork()
    };

    problemTab.content.find('.close').click(item => problemTab.content.find('#model_plot').hide());

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
        const plot_popupp = $('#model_plot');
        plot_popupp.show();

        var x = [];
        var y = [];
        Object.keys(data).forEach(function (key) {
            y.push(key);
            x.push(data[key]);
        });
        const answers = {
            x: x,
            y: y,
            type: 'bar',
            orientation: 'h'
        };
        const layout = {
            margin: {
                l: 500
            }
        };
        Plotly.newPlot('proble-question-plot', [answers], layout);
    };

    /**
     * call`s when receive response with statistics for the question
     * @param response
     */
    this.onGettingStat = function (response) {
        switch (response.type) {
            case 'bar':
                this.displayBar(response.stats)
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
        const $plotBtn = $('<button>Show plot!</button>');
        $plotBtn.appendTo(html);
        $plotBtn.click((item) => {
            var requestMap = this.getRequestMap();
            requestMap.problemID = this.problemID;
            $.ajax({
                traditional: true,
                type: "POST",
                url: "api/problem_statics/problem_question_stat/",
                data: requestMap,
                success: (response) => this.onGettingStat(response),
                error: () => this.onGettingStatFail(),
                dataType: "json"
            });
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
