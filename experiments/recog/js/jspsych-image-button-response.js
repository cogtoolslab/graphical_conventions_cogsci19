/**
 * jspsych-image-button-response
 * Josh de Leeuw
 *
 * plugin for displaying a utterance and getting a button click response
 *
 * documentation: docs.jspsych.org
 * 
 * adapted by Judy Fan (judithfan@gmail.com) Sep 2018 
 * to present a string as the utterance and record a mouse click on an image as response
 **/

var score = 0;

jsPsych.plugins["image-button-response"] = (function() {

  var plugin = {};

  jsPsych.pluginAPI.registerPreload('image-button-response', 'button_html', 'image');

  plugin.info = {
    name: 'image-button-response',
    description: '',
    parameters: {
      utterance: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'utterance',
        default: undefined,
        description: 'The description to be displayed'
      },
      choices: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Choices (image URLs)',
        default: undefined,
        array: true,
        description: 'The URLs for images to be selected from.'
      },
      button_html: {
        type: jsPsych.plugins.parameterType.IMAGE,
        pretty_name: 'Button HTML',
        default: '<img src="%imageURL%" height="224" width="224">',
        array: true,
        description: 'The html of the button. Can create own style.'
      },
      prompt: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Prompt',
        default: null,
        description: 'Any content here will be displayed under the buttons.'
      },
      utterance_duration: {
        type: jsPsych.plugins.parameterType.INT,
        pretty_name: 'utterance duration',
        default: null,
        description: 'How long to hide the utterance.'
      },
      trial_duration: {
        type: jsPsych.plugins.parameterType.INT,
        pretty_name: 'Trial duration',
        default: null,
        description: 'How long to show the trial.'
      },
      margin_vertical: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Margin vertical',
        default: '0px',
        description: 'The vertical margin of the button.'
      },
      margin_horizontal: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Margin horizontal',
        default: '8px',
        description: 'The horizontal margin of the button.'
      },
      response_ends_trial: {
        type: jsPsych.plugins.parameterType.BOOL,
        pretty_name: 'Response ends trial',
        default: true,
        description: 'If true, then trial will end when user responds.'
      },
    }
  }



  plugin.trial = function(display_element, trial) {

    if(typeof trial.choices === 'undefined'){
      console.error('Required parameter "choices" missing in image-button-response');
    }
    if(typeof trial.utterance === 'undefined'){
      console.error('Required parameter "utterance" missing in image-button-response');
    }

    // wrapper function to show everything, call this when you've waited what you
    // reckon is long enough for the data to come back from the db
    function show_display() { 

      //display buttons
      var buttons = [];
      if (Array.isArray(trial.button_html)) {
        if (trial.button_html.length == trial.choices.length) {
          buttons = trial.button_html;
        } else {
          console.error('Error in image-button-response plugin. The length of the button_html array does not equal the length of the choices array');
        }
      } else {
        for (var i = 0; i < trial.choices.length; i++) {
          buttons.push(trial.button_html);
        }
      }

      //show prompt if there is one
      if (trial.prompt !== null) {
        var html = '<div id="prompt">' +trial.prompt + '</div>';
      }    

      // display utterance (string)
      html += '<div><p id="jspsych-image-button-response-utterance"> "'+ trial.utterance +'"</p></div>';

      html += '<div id="jspsych-image-button-response-btngroup">';

      // embed images inside the response button divs
      for (var i = 0; i < trial.choices.length; i++) {
        var str = buttons[i].replace(/%imageURL%/g, trial.choices[i]);
        var object_id = trial.choices[i].split('/').slice(-1)[0].split('.')[0]; // splice to extract only shapenetID and target_status
        html += '<div class="jspsych-image-button-response-button" style="display: inline-block; margin :'+trial.margin_horizontal+' '+trial.margin_vertical+'" id="jspsych-image-button-response-button-' + i +'" data-choice="'+object_id+'">'+str+'</div>';
      }

      html += '</div>';       

      // display score earned so far
      html += '<div id="score"> <p> bonus points earned: ' + score + '</p></div>'
      html += '<div id="trial-counter"> <p> trial ' + trial.trialNum + ' of ' + trial.num_trials + '</p></div>'

      // display helpful info during debugging 
      if (trial.dev_mode==true) {
        html += '<div id="family"> <p> family: ' + trial.family + '</p></div>'        
        html += '<div id="condition"> <p> condition: ' + trial.condition + '</p></div>'
      }

      // actually assign html to display_element.innerHTML
      display_element.innerHTML = html;

      // add click event listener to the image response buttons    
      for (var i = 0; i < trial.choices.length; i++) {
        display_element.querySelector('#jspsych-image-button-response-button-' + i).addEventListener('click', function(e){
          var choice = e.currentTarget.getAttribute('data-choice'); // don't use dataset for jsdom compatibility
          after_response(choice);
        });
      }  


    }

    // wait for a little bit for data to come back from db, then show_display
    setTimeout(function() {show_display(); }, 1500);

    // start timing
    var start_time = Date.now();

    // store response
    var response = {
      rt: null,
      button: null
    };

    // function to handle responses by the subject
    function after_response(choice) {

      // measure rt
      var end_time = Date.now();
      var rt = end_time - start_time;
      response.button = choice;
      response.rt = rt;

      // after a valid response, the utterance will have the CSS class 'responded'
      // which can be used to provide visual feedback that a response was recorded
      display_element.querySelector('#jspsych-image-button-response-utterance').className += ' responded';

      // disable all the buttons after a response
      var btns = document.querySelectorAll('.jspsych-image-button-response-button button');
      for(var i=0; i<btns.length; i++){
        //btns[i].removeEventListener('click');
        btns[i].setAttribute('disabled', 'disabled');
      }

      if (trial.response_ends_trial) {
        end_trial();
      }
    };

    // function to end trial when it is time
    function end_trial() {

      // kill any remaining setTimeout handlers
      jsPsych.pluginAPI.clearAllTimeouts();

      // get info from mturk
      var turkInfo = jsPsych.turk.turkInfo();
      // workerID
      var wID = turkInfo.workerId;
      // hitID
      var hitID = turkInfo.hitId;
      // assignmentID
      var aID = turkInfo.assignmentId;     

      // prettify choices list
      var pretty_choices = new Array;
      _.forEach(trial.choices, function(x) {
                pretty_choices.push(x.split('/').slice(-1)[0].split('.')[0])
                }); 
      // check if response matches target, i.e., whether response is correct
      if (response.button.split('_')[1] == 'target') {
        trial_correct = 1;
        score+=1; // increment score
      } else {
        trial_correct = 0;
      }

      // gather the data to store for the trial
      var trial_data = {
        dbname: '3dObjects',
        colname: 'shapenet_chairs_speaker_eval',
        type: trial.type,
        iterationName: trial.iterationName, 
        gameID: trial.gameID, 
        trialNum: trial.trialNum,             
        rt: response.rt,
        utterance: trial.utterance,
        choices: pretty_choices,
        condition: trial.condition,
        stim_mongo_id: trial._id,
        family: trial.family,
        response: response.button,
        shuffle_ind: trial.shuffle_ind,
        score: score, 
        correct: trial_correct, 
        wID: wID,
        hitID: hitID,
        aID: aID,   
        timestamp: Date.now()     
      };

      console.log('trial data: ', trial_data);
      console.log('correct?  ', trial_correct);

      // clear the display
      display_element.innerHTML = '';

      // move on to the next trial
      jsPsych.finishTrial(trial_data);

    };


    // hide image if timing is set
    if (trial.utterance_duration !== null) {
      jsPsych.pluginAPI.setTimeout(function() {
        display_element.querySelector('#jspsych-image-button-response-utterance').style.visibility = 'hidden';
      }, trial.utterance_duration);
    }

    // end trial if time limit is set
    if (trial.trial_duration !== null) {
      jsPsych.pluginAPI.setTimeout(function() {
        end_trial();
      }, trial.trial_duration);
    }

  };

  return plugin;
})();
