var oldCallback;
var score = 0;

function sendData() {
  console.log('sending data to mturk');
  jsPsych.turk.submitToTurk({'score':score});
}

function setupGame () {
  // number of trials to fetch from database is defined in ./app.js
  var socket = io.connect();

  socket.on('onConnected', function(d) {
    var meta = d.meta;
    var id = d.id;

    // high level experiment parameter (placeholder)
    var num_trials = meta.num_trials;

    // define trial list
    var tmp = {
      type: 'image-button-response',
      iterationName: 'pilot0',
      num_trials: num_trials,
      dev_mode: false,
    };

    var trials = new Array(tmp.num_trials + 2);

    consentHTML = {
      'str1' : '<p>In this HIT, you will see some descriptions of objects. For each description, you will try to guess which of the objects is the best match. For each correct match, you will receive a bonus. </p>',
      'str2' : '<p>We expect the average game to last approximately 5-10 minutes, including the time it takes to read instructions.</p>',
      'str3' : "<p>If you encounter a problem or error, send us an email (sketchloop@gmail.com) and we will make sure you're compensated for your time! Please pay attention and do your best! Thank you!</p><p> Note: We recommend using Chrome. We have not tested this HIT in other browsers.</p>",
      'str4' : ["<u><p id='legal'>Consenting to Participate:</p></u>",
		"<p id='legal'>By completing this HIT, you are participating in a study being performed by cognitive scientists in the Stanford Department of Psychology. If you have questions about this research, please contact the <b>Sketchloop Admin</b> at <b><a href='mailto://sketchloop@gmail.com'>sketchloop@gmail.com</a> </b> or Noah Goodman (n goodma at stanford dot edu) You must be at least 18 years old to participate. Your participation in this research is voluntary. You may decline to answer any or all of the following questions. You may decline further participation, at any time, without adverse consequences. Your anonymity is assured; the researchers who have requested your participation will not receive any personal information about you.</p>"].join(' ')
    }
    // add welcome page
    instructionsHTML = {
      'str1' : "<p> Here's how the game will work: On each trial, you will see a short description appear next to three images of different chairs. Your goal is to select the chair in the set that best matches the description.",
      'str2' : '<p> For each correct match, you will receive a $0.01 bonus. It is very important that you consider the options carefully and try your best!',
      'str3' : "<p> Once you are finished, the HIT will be automatically submitted for approval. If you enjoyed this HIT, please know that you are welcome to perform it multiple times. Let's begin! </p>"
    }

    var welcome = {
      type: 'instructions',
      pages: [
      	consentHTML.str1,
      	consentHTML.str2,
      	consentHTML.str3,
      	consentHTML.str4,
      	instructionsHTML.str1,
      	instructionsHTML.str2,
      	instructionsHTML.str3
      ],
      show_clickable_nav: true
    }
    trials[0] = welcome;

    var goodbye = {
      type: 'instructions',
      pages: [
        'Thanks for participating in our experiment! You are all done. Please click the button to submit this HIT.'
      ],
      show_clickable_nav: true,
      on_finish: function() { sendData();}
    }
    var g = tmp.num_trials + 1;
    trials[g] = goodbye;

    // add rest of trials
    // at end of each trial save score locally and send data to server
    var main_on_finish = function(data) {
      if (data.score) {
        score = data.score;
      }
        socket.emit('currentData', data);
    };

    // Only start next trial once description comes back
    // have to remove and reattach to have local trial in scope...
    var main_on_start = function(trial) {
      oldCallback = newCallback;
      var newCallback = function(d) {
        console.log('data retrieved from db: ',d);
      	trial.utterance = d.utt;
        trial.choices = _.shuffle([d.target.url, d.distractor1.url, d.distractor2.url]);
        trial.condition = d.condition;
        trial.family = d.family;
        trial._id = d._id;
        trial.shuffle_ind = d.shuffler_ind;
      };
      socket.removeListener('stimulus', oldCallback);
      socket.on('stimulus', newCallback);
      // call server for stims
      socket.emit('getStim', {gameID: id});
    };

    for (var i = 0; i < tmp.num_trials; i++) {
      var k = i+1;
      trials[k] = {
      	type: tmp.type,
      	iterationName : tmp.iterationName,
        num_trials: tmp.num_trials,                
      	trialNum : i, // trial number
      	gameID: id,
        prompt: "Please select the object that best matches the description.",
        utterance: "Placeholder utterance.", // to be filled in dynamically 
        choices: ['https://tinyurl.com/y9rzglpn','https://tinyurl.com/y9rzglpn','https://tinyurl.com/y9rzglpn'], // to be filled in dynamically
        dev_mode: tmp.dev_mode,
        on_finish: main_on_finish,
      	on_start: main_on_start
      };
    }

    jsPsych.init({
      timeline: trials,
      default_iti: 1000,
      show_progress_bar: true
    });
  });
}
