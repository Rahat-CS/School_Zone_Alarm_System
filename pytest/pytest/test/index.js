var reporter = require('cucumber-html-reporter');

var options = {
        theme: 'bootstrap',
        jsonFile: 'result.json',
        output: './cucumber_report.html',
        reportSuiteAsScenarios: true,
        scenarioTimestamp: true,
        launchReport: true,
        metadata: {
            "ADC Type-1 FW Version":"0.3.2",
            "Test Environment": "tbd",
        }
    };

    reporter.generate(options);
