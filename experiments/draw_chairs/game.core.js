/*  Copyright (c) 2012 Sven "FuzzYspo0N" Bergström,
                  2013 Robert XD Hawkins
 written by : http://underscorediscovery.com
    written for : http://buildnewgames.com/real-time-multiplayer/
    substantially modified for collective behavior experiments on the web
    MIT Licensed.
*/

/*
  The main game class. This gets created on both server and
  client. Server creates one for each game that is hosted, and each
  client creates one for itself to play the game. When you set a
  variable, remember that it's only set in that instance.
*/
var has_require = typeof require !== 'undefined';

if( typeof _ === 'undefined' ) {
  if( has_require ) {
    _ = require('lodash');
    utils  = require(__base + 'utils/sharedUtils.js');
  }
  else throw 'mymodule requires underscore, see http://underscorejs.org';
}

var game_core = function(options){
  // Store a flag if we are the server instance
  this.server = options.server ;
  this.projectName = '3dObjects';
  this.experimentName = 'graphical_conventions';
  this.iterationName = 'testing'; // ['run0_bonusmeter','run1_chairsOnly','run2_chairs1k_size4','run2_chairs1k_size6', 'run3_size6_waiting','run3_size4_waiting']
  this.email = 'sketchloop@gmail.com';
  console.log("color randomized");

  // save data to the following locations (allowed: 'csv', 'mongo')
  this.dataStore = ['csv', 'mongo'];
  this.anonymizeCSV = true;

  // How many players in the game?
  this.players_threshold = 2;
  this.playerRoleNames = {
    role1 : 'sketcher',
    role2 : 'viewer'
  };

  // How many objects do we have in a context?
  this.setSize = 4; // many things depend on this
  console.log("actual setSize:" + this.setSize);

  //Dimensions of world in pixels and number of cells to be divided into;
  this.numHorizontalCells = this.setSize;
  this.numVerticalCells = 1;
  // if set size is anything larger than 4 (assuming we don't choose anything smaller than 4)
  // use 150 as our default cell size
  if (this.setSize == 4) {
    this.cellDimensions = {height : 200, width : 200};
  } else {
    this.cellDimensions = {height : 150, width : 150};
  }
  this.cellPadding = 0;
  this.world = {height : (this.cellDimensions.height * this.numVerticalCells
              + this.cellPadding),
              width : (this.cellDimensions.width * this.numHorizontalCells
              + this.cellPadding)};


  // track shift key drawing tool use
  this.shiftKeyUsed = 0; // "1" on trials where used, "0" otherwise

  // Which stroke number are we on?
  this.currStrokeNum = 0;

  // Has the sketcher drawn anything?
  this.strokeMade = false;

  // Is the sketcher done with their drawing?
  this.doneDrawing = false;

  // Is the sketcher allowed to draw?
  this.drawingAllowed = false;

  // time (in ms) to wait before giving feedback
  this.feedbackDelay = 300;

  // how long the sketcher has to finish their drawing
  this.timeLimit = 30;

  // toggle whether an object has been clicked
  this.objClicked = false;

  // Which round (a.k.a. "trial") are we on (initialize at -1 so that first round is 0-indexed)
  this.roundNum = -1;

  // How many repetitions do we want?
  if (this.setSize == 4) {
    this.numReps = 6;
  } else {
    this.numReps = 4;
  }

  // How many rounds do we want people to complete?
  if (this.setSize == 4) {
    this.numRounds = 40;
  } else {
    this.numRounds = 48;
  }
  // should we fix the pose to 3/4 view across trials and games?
  this.poseFixed = 1;

  // How many objects per round (how many items in the menu)?
  this.numItemsPerRound = this.numHorizontalCells*this.numVerticalCells;

  // Items x Rounds?
  this.numItemsxRounds = this.numItemsPerRound*this.numRounds;

  // This will be populated with the set of objects
  this.trialInfo = {};

  // Progress bar timer
  this.timer;

  // Most recent start stroke time
  this.startStrokeTime = Date.now();

  // Most recent end stroke time
  this.endStrokeTime = Date.now();

  // Using different categories for the conditions?
  this.diffCats = true; // set to true for generalization

  // Is the sketcher ready to move on?
  this.sketcherReady = false;

  // Is the viewer ready to move on?
  this.viewerReady = false;

  // Are we just using waiting chairs?
  this.waitingOnly = true;

  if(this.server) {
    console.log('sent server update bc satisfied this.server')
    // If we're initializing the server game copy, pre-create the list of trials
    // we'll use, make a player object, and tell the player who they are
    this.id = options.id;
    this.expName = options.expName;
    this.player_count = options.player_count;
    this.trialList = this.makeTrialList();

    this.data = {
      id : this.id,
      trials : [],
      catch_trials : [], system : {},
      subject_information : {
	    gameID: this.id,
	    score: 0,
      bonus_score: 0
      }
    };
    this.players = [{
      id: options.player_instances[0].id,
      instance: options.player_instances[0].player,
      player: new game_player(this,options.player_instances[0].player)
    }];
    this.streams = {};
    this.server_send_update();
  } else {
    // If we're initializing a player's local game copy, create the player object
    this.players = [{
      id: null,
      instance: null,
      player: new game_player(this)
    }];
  }
};

var game_player = function( game_instance, player_instance) {
  this.instance = player_instance;
  this.game = game_instance;
  this.role = '';
  this.message = '';
  this.id = '';
};

// server side we set some classes to global types, so that
// we can use them in other files (specifically, game.server.js)
if('undefined' != typeof global) {
  var stimList = _.map(require('./stimList_subord', _.clone));
  module.exports = {game_core, game_player};
}

// HELPER FUNCTIONS

// Method to easily look up player
game_core.prototype.get_player = function(id) {
  var result = _.find(this.players, function(e){ return e.id == id; });
  return result.player;
};

// Method to get list of players that aren't the given id
game_core.prototype.get_others = function(id) {
  var otherPlayersList = _.filter(this.players, function(e){ return e.id != id; });
  var noEmptiesList = _.map(otherPlayersList, function(p){return p.player ? p : null;});
  return _.without(noEmptiesList, null);
};

// Returns all players
game_core.prototype.get_active_players = function() {
  var noEmptiesList = _.map(this.players, function(p){return p.player ? p : null;});
  return _.without(noEmptiesList, null);
};

// Advance to the next round
game_core.prototype.newRound = function() {
  //console.log("calling gc.newRound() in game core");
  // If you've reached the planned number of rounds, end the game
  if(this.roundNum == this.numRounds - 1) {
    _.map(this.get_active_players(), function(p){
      p.player.instance.disconnect();});
  } else {
    // console.log('got to newRound in game.core.js and not the final round');
    // Otherwise, get the preset list of objects for the new round
    this.roundNum += 1;
    this.trialInfo = {currStim: this.trialList[this.roundNum]};
    //console.log("this.trialList[this.roundNum]: " + this.trialList[this.roundNum]);
    this.objects = this.trialList[this.roundNum];
    this.objClicked = false;
    active_players = this.get_active_players();
    this.setupTimer(this.timeLimit,active_players);
    this.server_send_update();
  }
};

// Set up timer function on each new round
game_core.prototype.setupTimer = function(timeleft, active_players) {
  this.timeleft = timeleft;
  var that = this;
  if (timeleft >= 0 && !(this.objClicked)) {
    _.map(active_players, function(p){
      p.player.instance.emit('updateTimer', timeleft);
    });
    this.timer = setTimeout(function(){
      that.setupTimer(timeleft - 1,active_players);
    }, 1000);
  } else {
    clearTimeout(this.timer);
    console.log("calling timeOut")
    _.map(active_players, function(p){
      p.player.instance.emit('timeOut', timeleft);
    });
  }
}

game_core.prototype.getRandomizedConditions = function() {
  ///// Aug 30 implementing re-design (see README.md)

  // assign one of the four categories to this game (dogs, birds, chairs, cars)
  // only allow close contexts
  // trial list is generated by concatenating pre (all 8), repeating (4 objs x 6 reps), post (all 8) phases.
  // strategy here is to use the same pipeline to generate design matrix,
  // but then just grab the subset we need for a given game: i.e., two quartets of objects from same category

  var numCats = 4;
  var numObjs = this.setSize * 2;
  var setSize = this.setSize; // this is the number of objects that appear in a single menu // changed from 4
  //console.log("setsize in getRandomizedConditions: " + this.setSize);
  // make category array
  var repeatedColor = _.sample(["#ce0a04", "#4286f4"]); // randomly assign border color (red or blue) to repeated and control
  var shuffledCat = _.shuffle(_.range(0,numCats));

  var repeatedCat;
  var controlCat;
  var repeated_category = new Array;
  var control_category = new Array;

  if (!this.waitingOnly) {
    repeatedCat = shuffledCat[0];
    controlCat = shuffledCat[1];
    // each category appears half the number of setsize times in each trial
    for (i=0; i<setSize; i++) {
      repeated_category.push(repeatedCat);
    }
    for (i=0; i<setSize; i++) {
      control_category.push(controlCat);
    }
  } else {
    repeatedCat = 3;
    for (i=0; i<setSize; i++) {
      repeated_category.push(repeatedCat);
    }
    controlCat = 1;
    for (i=0; i<setSize; i++) {
      control_category.push(controlCat);
    }
  }

  if (!this.diffCats) {
    control_category = repeated_category;
  }

  // shuffle objects
  var shuffledObjs = _.shuffle(_.range(0,numObjs));

  // split these 12 chairs up into 2 sets of 6, one of them will be repeated, the other will be control
  var repeatedObjs = shuffledObjs.slice(0,setSize);
  var controlObjs = shuffledObjs.slice(setSize,setSize*2);

  //console.log("repeatedObjs: " + repeatedObjs);
  //console.log("controlObjs: " + controlObjs);

  // Construct the full trial sequence

  // pre
  pre = new Array;
  for (var i=0; i<setSize; i++) {
    target = repeatedObjs[i];
    trial =
    {
      'object': repeatedObjs,
      'category': repeated_category,
      'pose': 35,
      'condition':'repeated',
      'target': target,
      'phase': 'pre',
      'repetition': 0,
      'repeatedColor':repeatedColor
    }
    pre.push(trial);
  }
  for (var i=0; i<setSize; i++) {
    target = controlObjs[i];
    trial =
    {
      'object': controlObjs,
      'category': control_category,
      'pose': 35,
      'condition':'control',
      'target': target,
      'phase': 'pre',
      'repetition': 0,
      'repeatedColor':repeatedColor
    }
    pre.push(trial);
  }
  pre = _.shuffle(pre);

  // repeated
  repeated = new Array;
  numReps = this.numReps;
  for (var rep=1; rep<numReps+1; rep++) {
    repeatedObjs = _.shuffle(repeatedObjs);
    for (var i=0; i<setSize; i++){
      target = repeatedObjs[i];
      trial =
      {
        'object': repeatedObjs,
        'category': repeated_category,
        'pose': 35,
        'condition':'repeated',
        'target': target,
        'phase': 'repeated',
        'repetition': rep,
        'repeatedColor':repeatedColor
      }
      repeated.push(trial);
    }
  }

  // post
  repeatedObjs = _.shuffle(repeatedObjs);
  controlObjs = _.shuffle(controlObjs);
  post = new Array;
  for (var i=0; i<setSize; i++) {
    target = repeatedObjs[i];
    trial =
    {
      'object': repeatedObjs,
      'category': repeated_category,
      'pose': 35,
      'condition':'repeated',
      'target': target,
      'phase': 'post',
      'repetition': this.numReps+1,
      'repeatedColor':repeatedColor
    }
    post.push(trial);
  }
  for (var i=0; i<setSize; i++) {
    target = controlObjs[i];
    trial =
    {
      'object': controlObjs,
      'category': control_category,
      'pose': 35,
      'condition':'control',
      'target': target,
      'phase': 'post',
      'repetition': 1,
      'repeatedColor':repeatedColor
    }
    post.push(trial);
  }
  post = _.shuffle(post);

  session = pre.concat(repeated).concat(post);

  for (var i = 0; i < session.length; i++) {
    trial = session[i];
    console.log("trial" + i + ": " + JSON.stringify(trial, null, 3));
  }
  return session;

  //console.log(session);
  return session; // design_dict

};

game_core.prototype.sampleStimulusLocs = function() {
  var listenerLocs = _.shuffle([[1,1], [2,1], [3,1], [4,1]]); // added [5,1],[6,1]
  var speakerLocs = _.shuffle([[1,1], [2,1], [3,1], [4,1]]); // added [5,1],[6,1]
  if (this.setSize == 6) {
    listenerLocs = _.shuffle([[1,1], [2,1], [3,1], [4,1], [5,1], [6,1]]); // added [5,1],[6,1]
    speakerLocs = _.shuffle([[1,1], [2,1], [3,1], [4,1], [5,1], [6,1]]); // added [5,1],[6,1]
  }
  return {listener : listenerLocs, speaker : speakerLocs};
};


game_core.prototype.makeTrialList = function () {

  var local_this = this;
  var session = this.getRandomizedConditions(); // added

  var objList = new Array;
  var locs = new Array;

  var trialList = [];
  var currentSetSize = this.setSize;
  for (var i = 0; i < session.length; i++) {
    var trial = session[i]
  //for (var i = 0; i < categoryList.length; i++) { // "i" indexes round number ---- commented out
    // sample four object images that are unique and follow the condition constraints

    var objList = sampleTrial(currentSetSize, trial.category,trial.object,trial.pose,trial.target,trial.condition,trial.phase,trial.repetition, trial.repeatedColor);
    //console.log('objList',objList);

    // sample locations for those objects
    var locs = this.sampleStimulusLocs();
    // construct trial list (in sets of complete rounds)
    trialList.push(_.map(_.zip(objList, locs.speaker, locs.listener), function(tuple) {
      var object = _.clone(tuple[0]);
      object.width = local_this.cellDimensions.width;
      object.height = local_this.cellDimensions.height;
      var speakerGridCell = local_this.getPixelFromCell(tuple[1][0], tuple[1][1]);
      var listenerGridCell = local_this.getPixelFromCell(tuple[2][0], tuple[2][1]);
      object.speakerCoords = {
      	gridX : tuple[1][0],
      	gridY : tuple[1][1],
      	trueX : speakerGridCell.centerX - object.width/2,
      	trueY : speakerGridCell.centerY - object.height/2,
      	gridPixelX: speakerGridCell.centerX - 100,
      	gridPixelY: speakerGridCell.centerY - 100
            };
      object.listenerCoords = {
      	gridX : tuple[2][0],
      	gridY : tuple[2][1],
      	trueX : listenerGridCell.centerX - object.width/2,
      	trueY : listenerGridCell.centerY - object.height/2,
      	gridPixelX: listenerGridCell.centerX - 100,
      	gridPixelY: listenerGridCell.centerY - 100
      };
      return object;

      }));


  };
  return(trialList);

};

game_core.prototype.server_send_update = function(){
  //Make a snapshot of the current state, for updating the clients
  var local_game = this;

  // Add info about all players
  var player_packet = _.map(local_game.players, function(p){
    return {id: p.id,
            player: null};
  });

  var state = {
    gs : this.game_started,   // true when game's started
    pt : this.players_threshold,
    pc : this.player_count,
    dataObj  : this.data,
    roundNum : this.roundNum,
    trialInfo: this.trialInfo,
    objects: this.objects,
    gameID: this.id
  };

  _.extend(state, {players: player_packet});
  _.extend(state, {instructions: this.instructions});
  if(player_packet.length == 2) {
    _.extend(state, {objects: this.objects});
  }
  // console.log('printing state variable from server_send_update');
  // console.log(state);
  //Send the snapshot to the players
  this.state = state;
  _.map(local_game.get_active_players(), function(p){
    p.player.instance.emit( 'onserverupdate', state);});
};

var getObjectSubset = function(basicCat) {
  return _.map(_.shuffle(_.filter(_objectList, function(x){
    return x.basic == basicCat;
  })), _.clone);
};

var getRemainingTargets = function(earlierTargets) {
  var criticalObjs = getObjectSubset("target");
  return _.filter(criticalObjs, function(x) {
    return !_.contains(earlierTargets, x.name );
  });
};

//filter stimList according to numObjs (setSize * 2)
var filterStimList = function(stimList, numObjs) {
  filteredList = [];
  for (var i=0; i<stimList.length; i++) {
    var object = stimList[i];
    if (object.object < numObjs) {
      filteredList.push(object);
    }
  }
  return filteredList;
}


var sampleTrial = function(currentSetSize,category,object,pose,target,condition,phase,repetition, repeatedColor) {
  stimList = filterStimList(stimList, currentSetSize*2);
  if (currentSetSize == 4) {

    var im0 = _.filter(stimList, function(s){ return ( (s['cluster']==category[0]) && (s['object']==object[0]) && (s['pose']==pose) ) })[0];
    //console.log("im0: " + "cluster: " + category[0] + "object: " + object[0] + "pose: " + pose);
    var im1 = _.filter(stimList, function(s){ return ( (s['cluster']==category[1]) && (s['object']==object[1]) && (s['pose']==pose) ) })[0];
    //console.log("im1: " + "cluster: " + category[1] + "object: " + object[1] + "pose: " + pose);
    var im2 = _.filter(stimList, function(s){ return ( (s['cluster']==category[2]) && (s['object']==object[2]) && (s['pose']==pose) ) })[0];
    //console.log("im2: " + "cluster: " + category[2] + "object: " + object[2] + "pose: " + pose);
    var im3 = _.filter(stimList, function(s){ return ( (s['cluster']==category[3]) && (s['object']==object[3]) && (s['pose']==pose) ) })[0];
    //console.log("im3: " + "cluster: " + category[3] + "object: " + object[3] + "pose: " + pose);

    var im_all = [im0,im1,im2,im3];
    //console.log("this target:" + target);

    var index = object.indexOf(target);
    var targetObj = im_all[index]; // actual target on this trial

    var notTargs = _.filter(_.range(currentSetSize), function(x) { return x!=index});
    var firstDistractor = im_all[notTargs[0]];
    var secondDistractor = im_all[notTargs[1]];
    var thirdDistractor = im_all[notTargs[2]];
    _target_status = ["distractor","distractor","distractor","distractor"];
    var target_status = _target_status[index] = "target"; // changed thisTarget to index
    _.extend(targetObj,{target_status: "target", condition: condition, phase: phase, repetition: repetition, repeatedColor: repeatedColor});
    _.extend(firstDistractor,{target_status: "distr1", condition: condition, phase: phase, repetition: repetition, repeatedColor: repeatedColor});
    _.extend(secondDistractor,{target_status: "distr2", condition: condition, phase: phase, repetition: repetition, repeatedColor: repeatedColor});
    _.extend(thirdDistractor,{target_status: "distr3", condition: condition, phase: phase, repetition: repetition, repeatedColor: repeatedColor});
    return [targetObj, firstDistractor, secondDistractor, thirdDistractor];

  } else {

    var im0 = _.filter(stimList, function(s){ return ( (s['cluster']==category[0]) && (s['object']==object[0]) && (s['pose']==pose) ) })[0];
    //console.log("im0: " + "cluster: " + category[0] + "object: " + object[0] + "pose: " + pose);
    var im1 = _.filter(stimList, function(s){ return ( (s['cluster']==category[1]) && (s['object']==object[1]) && (s['pose']==pose) ) })[0];
    //console.log("im1: " + "cluster: " + category[1] + "object: " + object[1] + "pose: " + pose);
    var im2 = _.filter(stimList, function(s){ return ( (s['cluster']==category[2]) && (s['object']==object[2]) && (s['pose']==pose) ) })[0];
    //console.log("im2: " + "cluster: " + category[2] + "object: " + object[2] + "pose: " + pose);
    var im3 = _.filter(stimList, function(s){ return ( (s['cluster']==category[3]) && (s['object']==object[3]) && (s['pose']==pose) ) })[0];
    //console.log("im3: " + "cluster: " + category[3] + "object: " + object[3] + "pose: " + pose);
    var im4 = _.filter(stimList, function(s){ return ( (s['cluster']==category[4]) && (s['object']==object[4]) && (s['pose']==pose) ) })[0];
    //console.log("im4: " + "cluster: " + category[4] + "object: " + object[4] + "pose: " + pose);
    var im5 = _.filter(stimList, function(s){ return ( (s['cluster']==category[5]) && (s['object']==object[5]) && (s['pose']==pose) ) })[0];
    //console.log("im5: " + "cluster: " + category[5] + "object: " + object[5] + "pose: " + pose);

    var im_all = [im0,im1,im2,im3,im4,im5];
    //console.log("this target:" + target);

    var index = object.indexOf(target);
    //console.log("index: " + index);
    var targetObj = im_all[index]; // actual target on this trial

    var notTargs = _.filter(_.range(6), function(x) { return x!=index});
    var firstDistractor = im_all[notTargs[0]];
    var secondDistractor = im_all[notTargs[1]];
    var thirdDistractor = im_all[notTargs[2]];
    var fourthDistractor = im_all[notTargs[3]];
    var fifthDistractor = im_all[notTargs[4]];
    _target_status = ["distractor","distractor","distractor","distractor","distractor","distractor"];
    var target_status = _target_status[index] = "target"; // changed thisTarget to index
    _.extend(targetObj,{target_status: "target", condition: condition, phase: phase, repetition: repetition, repeatedColor: repeatedColor});
    _.extend(firstDistractor,{target_status: "distr1", condition: condition, phase: phase, repetition: repetition, repeatedColor: repeatedColor});
    _.extend(secondDistractor,{target_status: "distr2", condition: condition, phase: phase, repetition: repetition, repeatedColor: repeatedColor});
    _.extend(thirdDistractor,{target_status: "distr3", condition: condition, phase: phase, repetition: repetition, repeatedColor: repeatedColor});
    _.extend(fourthDistractor,{target_status: "distr4", condition: condition, phase: phase, repetition: repetition, repeatedColor: repeatedColor});
    _.extend(fifthDistractor,{target_status: "distr5", condition: condition, phase: phase, repetition: repetition, repeatedColor: repeatedColor});
    return [targetObj, firstDistractor, secondDistractor, thirdDistractor, fourthDistractor, fifthDistractor];

  }
};

var sampleObjects = function(condition, earlierTargets) {
  var samplingInfo = {
    1 : {class: getObjectSubset("birds"),
   selector: firstClassSelector},
    2 : {class: getObjectSubset("birds"),
   selector: secondClassSelector},
    3 : {class: getObjectSubset("birds"),
   selector: thirdClassSelector}
  };

  var conditionParams = condition.slice(-2).split("");
  var firstDistrInfo = samplingInfo[conditionParams[0]];
  var secondDistrInfo = samplingInfo[conditionParams[1]];
  var remainingTargets = getRemainingTargets(earlierTargets);

  var target = _.sample(remainingTargets);
  var firstDistractor = firstDistrInfo.selector(target, firstDistrInfo.class);
  var secondDistractor = secondDistrInfo.selector(target, secondDistrInfo.class);
  if(checkItem(condition,target,firstDistractor,secondDistractor)) {
    // attach "condition" to each stimulus object
    return _.map([target, firstDistractor, secondDistractor], function(x) {
      return _.extend(x, {condition: condition});
    });
  } else { // Try again if something is wrong
    return sampleObjects(condition, earlierTargets);
  }
};





// NOT NECESSARY FOR SKETCHPAD TASK??
var checkItem = function(condition, target, firstDistractor, secondDistractor) {
  var f = 5; // floor difference
  var t = 20; // threshold
  var targetVsDistr1 = utils.colorDiff(target.color, firstDistractor.color);
  var targetVsDistr2 = utils.colorDiff(target.color, secondDistractor.color);
  var distr1VsDistr2 = utils.colorDiff(firstDistractor.color, secondDistractor.color);
  if(targetVsDistr1 < f || targetVsDistr2 < f || distr1VsDistr2 < f) {
    return false;
  } else if(condition === "equal") {
    return targetVsDistr1 > t && targetVsDistr2 > t && distr1VsDistr2 > t;
  } else if (condition === "closer") {
    return targetVsDistr1 < t && targetVsDistr2 < t && distr1VsDistr2 < t;
  } else if (condition === "further") {
    return targetVsDistr1 < t && targetVsDistr2 > t && distr1VsDistr2 > t;
  } else {
    throw "condition name (" + condition + ") not known";
  }
};

var firstClassSelector = function(target, list) {
  return _.sample(_.filter(list, function(x) {
    return target.basic === x.basiclevel;
  }));
};

var secondClassSelector = function(target, list) {
  return _.sample(_.filter(list, function(x) {
    return target.superdomain === x.superdomain;
  }));
};

var thirdClassSelector = function(target, list) {
  return _.extend(_.sample(list),{targetStatus : "distrClass3"});
};


// maps a grid location to the exact pixel coordinates
// for x = 1,2,3,4; y = 1,2,3,4
game_core.prototype.getPixelFromCell = function (x, y) {
  return {
    centerX: (this.cellPadding/2 + this.cellDimensions.width * (x - 1)
        + this.cellDimensions.width / 2),
    centerY: (this.cellPadding/2 + this.cellDimensions.height * (y - 1)
        + this.cellDimensions.height / 2),
    upperLeftX : (this.cellDimensions.width * (x - 1) + this.cellPadding/2),
    upperLeftY : (this.cellDimensions.height * (y - 1) + this.cellPadding/2),
    width: this.cellDimensions.width,
    height: this.cellDimensions.height
  };
};

// maps a raw pixel coordinate to to the exact pixel coordinates
// for x = 1,2,3,4; y = 1,2,3,4
game_core.prototype.getCellFromPixel = function (mx, my) {
  var cellX = Math.floor((mx - this.cellPadding / 2) / this.cellDimensions.width) + 1;
  var cellY = Math.floor((my - this.cellPadding / 2) / this.cellDimensions.height) + 1;
  return [cellX, cellY];
};



// // readjusts trueX and trueY values based on the objLocation and width and height of image (objImage)
// game_core.prototype.getTrueCoords = function (coord, objLocation, objImage) {
//   var trueX = this.getPixelFromCell(objLocation.gridX, objLocation.gridY).centerX - objImage.width/2;
//   var trueY = this.getPixelFromCell(objLocation.gridX, objLocation.gridY).centerY - objImage.height/2;
//   if (coord == "xCoord") {
//     return trueX;
//   }
//   if (coord == "yCoord") {
//     return trueY;
//   }
// };
