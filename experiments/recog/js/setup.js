var callback;
var score = 0;

function sendData() {
  console.log('sending data to mturk');
  jsPsych.turk.submitToTurk({'score':score});
}

var goodbyeTrial = {
  type: 'instructions',
  pages: [
    'Thanks for participating in our experiment! You are all done. Please \
     click the button to submit this HIT.'
  ],
  show_clickable_nav: true,
  on_finish: function() { sendData();}
};

var consentHTML = {
  'str1' : '<p>In this HIT, you will see some sketches of objects. For each sketch, you will try to guess which of the objects is the best match. For each correct match, you will receive a bonus. </p>',
  'str2' : '<p>We expect the average game to last approximately 2-3 minutes, including the time it takes to read instructions.</p>',
  'str3' : "<p>If you encounter a problem or error, send us an email (sketchloop@gmail.com) and we will make sure you're compensated for your time! Please pay attention and do your best! Thank you!</p><p> Note: We recommend using Chrome. We have not tested this HIT in other browsers.</p>",
  'str4' : ["<u><p id='legal'>Consenting to Participate:</p></u>",
	    "<p id='legal'>By completing this HIT, you are participating in a study being performed by cognitive scientists in the Stanford Department of Psychology. If you have questions about this research, please contact the <b>Sketchloop Admin</b> at <b><a href='mailto://sketchloop@gmail.com'>sketchloop@gmail.com</a> </b> or Noah Goodman (n goodma at stanford dot edu) You must be at least 18 years old to participate. Your participation in this research is voluntary. You may decline to answer any or all of the following questions. You may decline further participation, at any time, without adverse consequences. Your anonymity is assured; the researchers who have requested your participation will not receive any personal information about you.</p>"].join(' ')
}

// add welcome page
var instructionsHTML = {
  'str1' : "<p> Here's how the game will work: On each trial, you will see a sketch appear above four images of different objects. Your goal is to select the object in the set that best matches the sketch.",
  'str2' : '<p> For each correct match, you will receive a $0.02 bonus. It is very important that you consider the options carefully and try your best!',
  'str3' : "<p> Once you are finished, the HIT will be automatically submitted for approval. If you enjoyed this HIT, please know that you are welcome to perform it multiple times. Let's begin! </p>"
};

var welcomeTrial = {
  type: 'instructions',
  pages: [
    consentHTML.str1, consentHTML.str2, consentHTML.str3, consentHTML.str4,
    instructionsHTML.str1, instructionsHTML.str2, instructionsHTML.str3
  ],
  show_clickable_nav: true,
  allow_keys: false
};

// define trial object with boilerplate
function Trial () {
  this.type = 'image-button-response';
  this.iterationName = 'testing';
  this.prompt = "Please select the object that best matches the sketch.";
  this.numTrials = 10;
  this.dev_mode = true;
};

function setupGame () {
  // number of trials to fetch from database is defined in ./app.js
  var socket = io.connect();
  var on_finish = function(data) {
    score = data.score ? data.score : score;
    socket.emit('currentData', data);
  };

  // Start once server initializes us
  socket.on('onConnected', function(d) {
    // pull out info from server
    var id = d.id;     

    // Bind trial data with boilerplate
    var trials = _.map(_.shuffle(d.trials), function(trialData, i) {
      return _.extend(new Trial, trialData, {
                      choices: _.shuffle([trialData.target.url, trialData.distractor1.url,
                      		    trialData.distractor2.url, trialData.distractor3.url]),
                      gameID: id,
                      trialNum : i,
                      on_finish : on_finish
      });
    });
    
    // Stick welcome trial at beginning & goodbye trial at end
    trials.unshift(welcomeTrial);
    trials.push(goodbyeTrial);

    jsPsych.init({
      timeline: trials,
      default_iti: 1000,
      show_progress_bar: true
    });
  });
}
