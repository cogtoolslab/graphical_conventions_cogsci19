var callback;
var score = 0;

function sendData() {
  console.log('sending data to mturk');
  jsPsych.turk.submitToTurk({'score':score});
}

// function makeNewCallback(trial) {
//   return function(d) {
//     console.log('data retrieved from db: ',d);
//       trial.utterance = d.utt;
//       trial.choices = _.shuffle([d.target.url, d.distractor1.url, d.distractor2.url]);
//       trial.condition = d.condition;
//       trial.family = d.family;
//       trial._id = d._id;
//       trial.shuffle_ind = d.shuffler_ind;
//   };
// };

function setupGame () {
  // number of trials to fetch from database is defined in ./app.js
  var socket = io.connect();

  socket.on('onConnected', function(d) {
    var meta = d.meta; // contains trial level metadata, a list of dictionaries
    meta = _.shuffle(meta); // shuffle the order the dictionaries

    var id = d.id;     // gameID for *this* session

    // high level experiment parameter (placeholder)
    var num_trials = d.num_trials;

    // define trial list: `tmp` contains boiler plate metadata that is true for every trial
    var tmp = {
      type: 'image-button-response',
      iterationName: 'testing',
      num_trials: num_trials,
      dev_mode: false,
    };

    var trials = new Array(tmp.num_trials + 2);

    consentHTML = {
      'str1' : '<p>In this HIT, you will see some sketches of objects. For each sketch, you will try to guess which of the objects is the best match. For each correct match, you will receive a bonus. </p>',
      'str2' : '<p>We expect the average game to last approximately 2-3 minutes, including the time it takes to read instructions.</p>',
      'str3' : "<p>If you encounter a problem or error, send us an email (sketchloop@gmail.com) and we will make sure you're compensated for your time! Please pay attention and do your best! Thank you!</p><p> Note: We recommend using Chrome. We have not tested this HIT in other browsers.</p>",
      'str4' : ["<u><p id='legal'>Consenting to Participate:</p></u>",
		"<p id='legal'>By completing this HIT, you are participating in a study being performed by cognitive scientists in the Stanford Department of Psychology. If you have questions about this research, please contact the <b>Sketchloop Admin</b> at <b><a href='mailto://sketchloop@gmail.com'>sketchloop@gmail.com</a> </b> or Noah Goodman (n goodma at stanford dot edu) You must be at least 18 years old to participate. Your participation in this research is voluntary. You may decline to answer any or all of the following questions. You may decline further participation, at any time, without adverse consequences. Your anonymity is assured; the researchers who have requested your participation will not receive any personal information about you.</p>"].join(' ')
    }
    // add welcome page
    instructionsHTML = {
      'str1' : "<p> Here's how the game will work: On each trial, you will see a sketch appear above four images of different objects. Your goal is to select the object in the set that best matches the sketch.",
      'str2' : '<p> For each correct match, you will receive a $0.02 bonus. It is very important that you consider the options carefully and try your best!',
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
      // Remove callback from previous trial
      socket.removeListener('stimulus', callback);

      // Make and attach callback for current trial
      callback = makeNewCallback(trial);
      socket.on('stimulus', callback);

      // call server for stims
      socket.emit('getStim', {gameID: id});
    };

    for (var i = 0; i < tmp.num_trials; i++) {
      var k = i+1;
      this_meta = meta[i]; // grab this trial's metadata
      trials[k] = {
      	type: tmp.type,
      	iterationName : tmp.iterationName,
        num_trials: tmp.num_trials,
      	trialNum : i, // trial number
      	gameID: id,        
        // target: {filename: 'filename', shapenetid: 'shapenetid' , objectname: 'objectname', url:  'https://tinyurl.com/y9rzglpn'},
        // distractor1: {filename: 'filename', shapenetid: 'shapenetid' , objectname: 'objectname', url:  'https://tinyurl.com/y9rzglpn'},
        // distractor2: {filename: 'filename', shapenetid: 'shapenetid' , objectname: 'objectname', url:  'https://tinyurl.com/y9rzglpn'},
        // distractor3: {filename: 'filename', shapenetid: 'shapenetid' , objectname: 'objectname', url:  'https://tinyurl.com/y9rzglpn'},  
        // condition: 'XX',
        // repetition: 'XX',
        // trialNum: 'XX',
        // phase: 'XX',
        // category: 'XX',
        // generalization:'XX',        
        target: this_meta.target,
        distractor1: this_meta.distractor1,
        distractor2: this_meta.distractor2,
        distractor3: this_meta.distractor3,
        condition: this_meta.condition,
        repetition: this_meta.repetition,
        phase: this_meta.phase,
        category: this_meta.category,
        generalization: this_meta.generalization,
        prompt: "Please select the object that best matches the sketch.",
        sketch: 'https://s3.amazonaws.com/graphical-conventions-sketches/0051-e13f6f0c-ae9b-4976-8fcd-870cdb75f63f_02_waiting_02.png',
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
