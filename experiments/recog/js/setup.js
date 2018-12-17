var callback;
var score = 0;
var quizAttempts = 1;

function sendData() {
  console.log('sending data to mturk');
  jsPsych.turk.submitToTurk({'score':score});
}

var goodbyeTrial = {
  type: 'instructions',
  pages: [
    '<p>Thanks for participating in our experiment! You are all done. Please \
     click the button to submit this HIT. When the popup asks you if you want to leave, please say YES to submit the HIT.</p>'
  ],
  show_clickable_nav: true,
  on_finish: function() { sendData();}
};

var consentHTML = {
  'str1' : '<p>In this HIT, you will see some sketches of objects. For each sketch, you will try to guess which of the objects is the best match. For each correct match, you will receive a bonus. </p>',
  'str2' : '<p>We expect the average game to last approximately 10 minutes, including the time it takes to read instructions.</p>',
  'str3' : "<p>If you encounter a problem or error, send us an email (sketchloop@gmail.com) and we will make sure you're compensated for your time! Please pay attention and do your best! Thank you!</p><p> Note: We recommend using Chrome. We have not tested this HIT in other browsers.</p>",
  'str4' : ["<u><p id='legal'>Consenting to Participate:</p></u>",
	    "<p id='legal'>By completing this HIT, you are participating in a study being performed by cognitive scientists in the Stanford Department of Psychology. If you have questions about this research, please contact the <b>Sketchloop Admin</b> at <b><a href='mailto://sketchloop@gmail.com'>sketchloop@gmail.com</a> </b>. You must be at least 18 years old to participate. Your participation in this research is voluntary. You may decline to answer any or all of the following questions. You may decline further participation, at any time, without adverse consequences. Your anonymity is assured; the researchers who have requested your participation will not receive any personal information about you.</p>"].join(' ')
}

// add welcome page
var instructionsHTML = {
  'str1' : "<p> Here's how the game will work: On each trial, you will see a sketch appear above four images of different objects. Your goal is to select the object in the set that best matches the sketch.",
  'str2' : '<p> For each correct guess you make, you will receive an <b>accuracy bonus</b> of $0.01. <p> In addition, you will receive a <b>speed bonus</b> (up to $0.02) based on how fast you make the correct guess. In other words, the faster you can select the correct object, the larger the bonus you will receive. </p> <p> However, you <i> must select the correct object to receive any bonus at all </i>, so please pay attention and above all <b> aim to be as accurate as you can </b>! </p>',
  'str3' : "<p> Once you are finished, the HIT will be automatically submitted for approval. Please know that you can only perform this HIT one time. Before we begin, please complete a brief questionnaire to show you understand how this HIT works.</p>"
};

var welcomeTrial = {
  type: 'instructions',
  pages: [
    consentHTML.str1, consentHTML.str2, consentHTML.str3, consentHTML.str4,
    instructionsHTML.str1, instructionsHTML.str2, instructionsHTML.str3
  ],
  show_clickable_nav: true,
  allow_keys: true
};

var quizTrial = {
    type: 'survey-multi-choice',
    questions: [{prompt: "The sketch is of one of the four objects in context.",
		 options: ["True", "False"],
		 required:true},
		{prompt: "It is possible to earn a speed bonus for selecting an incorrect object really quickly.",
		 options: ["True", "False"],
		 required: false},
		{prompt: "It is possible to perform this HIT more than once.",
		 options: ["True", "False"],
		 required: false}]
};

var loopNode = {
    timeline: [quizTrial],
    loop_function: function(data){
      	console.log(data.values()[0]['responses']);
      	resp = JSON.parse(data.values()[0]['responses']);	 
      	if ((resp["Q0"] == 'True') && (resp["Q1"]== 'False') && (resp["Q2"] == 'False')){
      	    return false;
      	} else {
      	    alert('Please try again! One or more of your responses was incorrect.');
            quizAttempts += 1;
            return true;
      	}
          }
}


var acceptHTML = {
  'str1' : '<p> Welcome! In this HIT, you will see some sketches of objects. For each sketch, you will try to guess which of the objects is the best match. </p>',  
  'str2' : '<p> This is only a demo! If you are interested in participating, please accept the HIT in MTurk before continuing further. </p>'  
}

var previewTrial = {
  type: 'instructions',
  pages: [acceptHTML.str1, acceptHTML.str2],
  show_clickable_nav: true,
  allow_keys: false  
}

// define trial object with boilerplate
function Trial () {
  this.type = 'image-button-response';
  this.iterationName = 'testing';
  this.prompt = "Please select the object that best matches the sketch.";
  this.num_trials = 10;
  this.dev_mode = false;
};

function setupGame () {

  // number of trials to fetch from database is defined in ./app.js
  var socket = io.connect();
  var on_finish = function(data) {
    score = data.score ? data.score : score;
    data.quizAttempts = quizAttempts;
    socket.emit('currentData', data);
  };

  // Start once server initializes us
  socket.on('onConnected', function(d) {

    // get workerId, etc. from URL (so that it can be sent to the server)
    var turkInfo = jsPsych.turk.turkInfo();    
  
    // pull out info from server
    var id = d.id;

    // Bind trial data with boilerplate
    var trials = _.map(_.shuffle(d.trials), function(trialData, i) {
      return _.extend(new Trial, trialData, {
        choices: _.shuffle([trialData.target.url, trialData.distractor1.url,
        		    trialData.distractor2.url, trialData.distractor3.url]),
        gameID: id,
        trialNum : i,
        post_trial_gap: 1000, // add brief ITI between trials
        on_finish : on_finish
      });
    });

    // Stick welcome trial at beginning & goodbye trial at end
    if (!turkInfo.previewMode) { 
	trials.unshift(loopNode);
	trials.unshift(welcomeTrial);
    } else {
      trials.unshift(previewTrial); // if still in preview mode, tell them to accept first.
    }
    trials.push(goodbyeTrial);

    console.log(trials);
      
    jsPsych.init({
      timeline: trials,
      default_iti: 1000,
      show_progress_bar: true
    });      

  });
}
