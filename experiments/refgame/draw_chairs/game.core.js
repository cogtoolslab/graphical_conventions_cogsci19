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
  this.iterationName = 'run5_submitButton_test'; // ['run0_bonusmeter','run1_chairsOnly','run2_chairs1k_size4','run2_chairs1k_size6', 'run3_size6_waiting','run3_size4_waiting','run4_generalization']
  this.email = 'sketchloop@gmail.com';
  // console.log("color randomized");

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
  // console.log("actual setSize:" + this.setSize);

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
  this.diffCats = true; // set to true if we want repeated and control to come from different clusters

  // Is the sketcher ready to move on?
  this.sketcherReady = false;

  // Is the viewer ready to move on?
  this.viewerReady = false;

  // Are we just using waiting and dining chairs? Should be true for all planned experiments. 
  this.waitingDining = true;

  // Just using waiting chairs? - set TRUE to set waiting to be repeated, set FALSE for dining to be repeated
  this.waiting = false;

  // Use submit button
  this.useSubmitButton = true;

  // Use augmented version of stimlist_subord that partitions into "set A" and "set B" within cluster
  this.useAugmentedStimlist = true;

  if(this.server) {
    console.log('sent server update bc satisfied this.server')
    // If we're initializing the server game copy, pre-create the list of trials
    // we'll use, make a player object, and tell the player who they are
    if (this.useAugmentedStimlist) {
      this.stimList = _.map(require('./stimList_subord_v2', _.clone));
    } else {
      this.stimList = _.map(require('./stimList_subord', _.clone));
    }

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

  var numCats = 2;
  var numObjs = this.setSize * 2;
  var setSize = this.setSize; // this is the number of objects that appear in a single menu // changed from 4
  //console.log("setsize in getRandomizedConditions: " + this.setSize);
  // make category array
  var repeatedColor = _.sample(["#ce0a04", "#4286f4"]); // randomly assign border color (red or blue) to repeated and control

  var repeatedCat;
  var controlCat;

  if (!this.waitingDining) { // if deck/armchair cluster items allowed    
    var shuffledCat = _.shuffle(['waiting','dining','deck','armchair']);
    repeatedCat = shuffledCat[0];
    controlCat = shuffledCat[1];

  } else { // if waitingDining is true, so only chairs from waiting and dining clusters are used
    if (this.waiting) { // waiting is repeated, dining is control
      repeatedCat = "waiting";
      controlCat = "dining";
    } else {            // dining is repeated, waiting is control
      repeatedCat = "dining";
      controlCat = "waiting";
    }  
  }

  if (!this.diffCats) { // NOT diffcats means we want to use the same cluster for repeated and control
    controlCat = repeatedCat;
  }

  if (!this.useAugmentedStimlist) { // NOT useAugmentedStimlist means old refgame version 1.0-1.2
    // split these 8 chairs up into 2 sets of 4, one of them will be repeated, the other will be control
    var shuffledObjs = _.shuffle(_.range(0,numObjs));
    var repeatedObjs = shuffledObjs.slice(0,setSize);
    var controlObjs = shuffledObjs.slice(setSize,setSize*2);
    var sampledSubsetRepeated = "N"; // null placeholder
    var sampledSubsetControl = "N"; // null placeholder   
  } else { // define repeatedObj on basis of hard subsetting within cluster into contexts
    // independent random sampling to decide whether to use subset "A" or subset "B" within each cluster
    var sampledSubsetRepeated = _.sample(["A","B"]);
    var sampledSubsetControl = _.sample(["A","B"]);    
    _r = _.filter(this.stimList, ({subset,basic}) => subset == sampledSubsetRepeated && basic == repeatedCat);
    var repeatedObjs = _.values(_.mapValues(_r, ({object}) => object));
    _c = _.filter(this.stimList, ({subset,basic}) => subset == sampledSubsetControl && basic == controlCat);
    var controlObjs = _.values(_.mapValues(_c, ({object}) => object));    
  }

  // define common trialInfo for each condition (omits: targetID, phase, repetition -- these are 
  // added iteratively)
  commonRepeatedTrialInfo = {'objectIDs': repeatedObjs,
                            'category': repeatedCat,
                            'subset': sampledSubsetRepeated,      
                            'pose': 35,
                            'condition':'repeated',
                            'repeatedColor':repeatedColor
                            }

  commonControlTrialInfo = {'objectIDs': controlObjs,
                            'category': controlCat,
                            'subset': sampledSubsetControl,      
                            'pose': 35,
                            'condition':'control',
                            'repeatedColor':repeatedColor
                            }

  // pre phase 
  var pre = _.shuffle(_.concat(_.map(repeatedObjs, curObj => {
                    return _.extend({}, commonRepeatedTrialInfo, {'phase':'pre','repetition':0, 'targetID': curObj});
                    }), 
                               _.map(controlObjs, curObj => {
                    return _.extend({}, commonControlTrialInfo, {'phase':'pre','repetition':0, 'targetID': curObj});
                    })));

  // repeated phase
  var repeated = _.flatMap(_.range(0,this.numReps), curRep => {
                  return _.map(_.shuffle(repeatedObjs), curObj => {
                    return _.extend({}, commonRepeatedTrialInfo, {'phase':'repeated','repetition':curRep, 'targetID': curObj});
                  })
                 });

  // post phase
  var post = _.shuffle(_.concat(_.map(repeatedObjs, curObj => {
                    return _.extend({}, commonRepeatedTrialInfo, {'phase':'post','repetition':this.numReps+1, 'targetID': curObj});
                    }), 
                               _.map(controlObjs, curObj => {
                    return _.extend({}, commonControlTrialInfo, {'phase':'post','repetition':1, 'targetID': curObj});
                    })));  

  // build session by concatenating pre, repeated, and post phases
  var session = _.concat(pre, repeated, post);

  // this is the design dictionary
  return session;

};

// filter stimList according to numObjs (setSize * 2) 
// as of 12/31/18: as long as you're pulling from stimList_subord_v2.js, this doesn't do anything.
var filterStimList = function(stimList, numObjs) {
  return _.filter(stimList, ({object}) => object < numObjs); 
}

game_core.prototype.sampleTrial = function(trialInfo, currentSetSize) {
  var filteredList = filterStimList(this.stimList, currentSetSize*2);
  var miniTrialInfo = _.pick(trialInfo, ['condition', 'phase', 'repetition', 'repeatedColor', 'subset'])
  var distractorLabels = ['distr1', 'distr2', 'distr3']

  // Pull objects specified in trialInfo out of stimlist 
  return _.map(trialInfo.objectIDs, objID => {
    var objFromList = _.find(filteredList, {'basic' : trialInfo.category, 'object' : objID});
    var targetStatus = objID == trialInfo.targetID ? 'target' : distractorLabels.pop();
    return _.extend({}, objFromList, miniTrialInfo, {target_status: targetStatus});
  });
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
    var trialInfo = session[i]
    // for (var i = 0; i < categoryList.length; i++) { // "i" indexes round number ---- commented out
    // sample four object images that are unique and follow the condition constraints

    var objList = this.sampleTrial(trialInfo, currentSetSize);
    // console.log('objList',objList);

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

    // console.log('state',state);

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
