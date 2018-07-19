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
  this.iterationName = 'testing'; // ['run0_bonusmeter','run1_chairsOnly','run2_chairs1k_setsize6']
  this.email = 'sketchloop@gmail.com';

  // save data to the following locations (allowed: 'csv', 'mongo')
  this.dataStore = ['csv', 'mongo'];
  this.anonymizeCSV = true;

  // How many players in the game?
  this.players_threshold = 2;
  this.playerRoleNames = {
    role1 : 'sketcher',
    role2 : 'viewer'
  };


  //Dimensions of world in pixels and number of cells to be divided into;
  this.numHorizontalCells = 6; // change from 4
  this.numVerticalCells = 1;
  this.cellDimensions = {height : 150, width : 150}; // in pixels // change from 200
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
  this.numReps = 4; // changed from 6

  // How many rounds do we want people to complete?
  this.numRounds = 48; // changed from 40

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

  // Whether only chairs are used or all four categories
  this.chairsOnly = true; // change later

  // Whether repeated trials have red frame
  this.repeatedIsRed;

  if(this.server) {
    console.log('sent server update bc satisfied this.server')
    // If we're initializing the server game copy, pre-create the list of trials
    // we'll use, make a player object, and tell the player who they are
    this.id = options.id;
    this.expName = options.expName;
    this.player_count = options.player_count;
    this.trialList = this.makeTrialList();
    this.repeatedIsRed = _.sample([true, false]);
    //console.log("trialList: " + this.trialList);
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
  // console.log(stimList);
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
  var numObjs = 12; // changed from 8
  var setSize = 6; // this is the number of objects that appear in a single menu // changed from 4

  // make category array
  var shuffledCat = _.shuffle(_.range(0,numCats));
  var sampledCat = shuffledCat[0];
  var _category = new Array;
  for (i=0; i<setSize; i++) {
    _category.push(sampledCat);
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
  for (var i = 0; i < setSize; i++) {
    target = repeatedObjs[i];
    trial =
    {
      'object': repeatedObjs,
      'category': _category,
      'pose': 35,
      'condition':'repeated',
      'target': target,
      'phase': 'pre',
      'repetition': 0
    }
    // arr = new Array;
    // target = repeatedObjs[i];
    // arr.push(repeatedObjs);
    // arr.push(_category);
    // arr.push(35);
    // arr.push('repeated');
    // arr.push(target);
    // arr.push('pre');
    // arr.push(0);
    pre.push(trial);
  }
  for (var i = 0; i < setSize; i++) {
    target = controlObjs[i];
    trial =
    {
      'object': controlObjs,
      'category': _category,
      'pose': 35,
      'condition':'control',
      'target': target,
      'phase': 'pre',
      'repetition': 0
    }
    //
    // arr = new Array;
    // target = controlObjs[i];
    // arr.push(controlObjs);
    // arr.push(_category);
    // arr.push(35);
    // arr.push('control');
    // arr.push(target);
    // arr.push('pre');
    // arr.push(0);
    pre.push(trial);
  }
  pre = _.shuffle(pre);

  // repeated
  repeated = new Array;
  numReps = this.numReps;
  for (var rep=1; rep<numReps+1; rep++) {
    repeatedObjs = _.shuffle(repeatedObjs);
    for (var i = 0; i < setSize; i++){
      target = repeatedObjs[i];
      trial =
      {
        'object': repeatedObjs,
        'category': _category,
        'pose': 35,
        'condition':'repeated',
        'target': target,
        'phase': 'repeated',
        'repetition': rep
      }
      // arr = new Array;
      // target = repeatedObjs[i];
      // arr.push(repeatedObjs);
      // arr.push(_category);
      // arr.push(35);
      // arr.push('repeated');
      // arr.push(target);
      // arr.push('repeated');
      // arr.push(rep);
      repeated.push(trial);
    }
  }

  // post
  repeatedObjs = _.shuffle(repeatedObjs);
  controlObjs = _.shuffle(controlObjs);
  post = new Array;
  for (var i = 0; i < setSize; i++) {
    target = repeatedObjs[i];
    trial =
    {
      'object': repeatedObjs,
      'category': _category,
      'pose': 35,
      'condition':'repeated',
      'target': target,
      'phase': 'post',
      'repetition': 5
    }
    // arr = new Array;
    // target = repeatedObjs[i];
    // arr.push(repeatedObjs);
    // arr.push(_category);
    // arr.push(35);
    // arr.push('repeated');
    // arr.push(target);
    // arr.push('post');
    // arr.push(5);
    post.push(trial);
  }
  for (var i = 0; i < setSize; i++) {
    target = controlObjs[i];
    trial =
    {
      'object': controlObjs,
      'category': _category,
      'pose': 35,
      'condition':'control',
      'target': target,
      'phase': 'post',
      'repetition': 1
    }
    // arr = new Array;
    // target = controlObjs[i];
    // arr.push(controlObjs);
    // arr.push(_category);
    // arr.push(35);
    // arr.push('control');
    // arr.push(target);
    // arr.push('post');
    // arr.push(1);
    post.push(trial);
  }
  post = _.shuffle(post);

  session = pre.concat(repeated).concat(post);

  //console.log(session);
  return session; // design_dict

};

game_core.prototype.sampleStimulusLocs = function() {
  var listenerLocs = _.shuffle([[1,1], [2,1], [3,1], [4,1], [5,1], [6,1]]); // added [5,1],[6,1]
  var speakerLocs = _.shuffle([[1,1], [2,1], [3,1], [4,1], [5,1], [6,1]]); // added [5,1],[6,1]

  // // temporarily turn off shuffling to make sure that it has to do with this
  // var listenerLocs = [[1,1], [2,1], [3,1], [4,1]];
  // var speakerLocs = [[1,1], [2,1], [3,1], [4,1]];
  return {listener : listenerLocs, speaker : speakerLocs};
};


game_core.prototype.makeTrialList = function () {

  var local_this = this;
  var session = this.getRandomizedConditions(); // added
  var design_dict = this.getRandomizedConditions();
  var categoryList = design_dict['category'];
  var _objectList = design_dict['object'];
  var poseList = design_dict['pose'];
  var targetList = design_dict['target'];
  var conditionList = design_dict['condition'];
  var phaseList = design_dict['phase'];
  var repetitionList = design_dict['repetition'];

  var objList = new Array;
  var locs = new Array;

  var trialList = [];

  for (var i = 0; i < session.length; i++) {
    var trial = session[i]
  //for (var i = 0; i < categoryList.length; i++) { // "i" indexes round number ---- commented out
    // sample four object images that are unique and follow the condition constraints
    // roundNum,categoryList,_objectList,poseList,targetList,conditionList,phaseList,repetitionList
    var objList = sampleTrial(trial.category,trial.object,trial.pose,trial.target,trial.condition,trial.phase,trial.repetition);
    // var objList = sampleTrial(i,categoryList,_objectList,poseList,targetList,conditionList,phaseList,repetitionList);  ---- commented out
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
  //console.log("trialList: " + trialList);
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




var sampleTrial = function(category,object,pose,target,condition,phase,repetition) {
  theseCats = category; // change / collapse later
  theseObjs = object;
  thisPose = pose;
  thisTarget = target;
  thisCondition = condition;
  thisPhase = phase;
  thisRepetition = repetition;

  var im0 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[0]) && (s['object']==theseObjs[0]) && (s['pose']==thisPose) ) })[0];
  //console.log("im0: " + "cluster: " + theseCats[0] + "object: " + theseObjs[0] + "pose: " + thisPose);
  var im1 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[1]) && (s['object']==theseObjs[1]) && (s['pose']==thisPose) ) })[0];
  //console.log("im1: " + "cluster: " + theseCats[1] + "object: " + theseObjs[1] + "pose: " + thisPose);
  var im2 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[2]) && (s['object']==theseObjs[2]) && (s['pose']==thisPose) ) })[0];
  //console.log("im2: " + "cluster: " + theseCats[2] + "object: " + theseObjs[2] + "pose: " + thisPose);
  var im3 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[3]) && (s['object']==theseObjs[3]) && (s['pose']==thisPose) ) })[0];
  //console.log("im3: " + "cluster: " + theseCats[3] + "object: " + theseObjs[3] + "pose: " + thisPose);
  var im4 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[4]) && (s['object']==theseObjs[4]) && (s['pose']==thisPose) ) })[0];
  //console.log("im4: " + "cluster: " + theseCats[4] + "object: " + theseObjs[4] + "pose: " + thisPose);
  var im5 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[5]) && (s['object']==theseObjs[5]) && (s['pose']==thisPose) ) })[0];
  //console.log("im5: " + "cluster: " + theseCats[5] + "object: " + theseObjs[5] + "pose: " + thisPose);

  var im_all = [im0,im1,im2,im3,im4,im5];
  // console.log("this target:" + thisTarget);

  var index = theseObjs.indexOf(thisTarget);
  // console.log("index: " + index);
  var target = im_all[index]; // actual target on this trial

  var notTargs = _.filter(_.range(6), function(x) { return x!=index});
  var firstDistractor = im_all[notTargs[0]];
  var secondDistractor = im_all[notTargs[1]];
  var thirdDistractor = im_all[notTargs[2]];
  var fourthDistractor = im_all[notTargs[3]];
  var fifthDistractor = im_all[notTargs[4]];
  _target_status = ["distractor","distractor","distractor","distractor","distractor","distractor"];
  var target_status = _target_status[index] = "target"; // changed thisTarget to index
  // console.log("target_status: " + target_status);
  _.extend(target,{target_status: "target", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
  _.extend(firstDistractor,{target_status: "distr1", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
  _.extend(secondDistractor,{target_status: "distr2", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
  _.extend(thirdDistractor,{target_status: "distr3", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
  _.extend(fourthDistractor,{target_status: "distr4", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
  _.extend(fifthDistractor,{target_status: "distr5", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
  //console.log("target's target status " + target.target_status);
  return [target, firstDistractor, secondDistractor, thirdDistractor, fourthDistractor, fifthDistractor];

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

























// /*  Copyright (c) 2012 Sven "FuzzYspo0N" Bergström,
//                   2013 Robert XD Hawkins
//  written by : http://underscorediscovery.com
//     written for : http://buildnewgames.com/real-time-multiplayer/
//     substantially modified for collective behavior experiments on the web
//     MIT Licensed.
// */
//
// /*
//   The main game class. This gets created on both server and
//   client. Server creates one for each game that is hosted, and each
//   client creates one for itself to play the game. When you set a
//   variable, remember that it's only set in that instance.
// */
// var has_require = typeof require !== 'undefined';
//
// if( typeof _ === 'undefined' ) {
//   if( has_require ) {
//     _ = require('lodash');
//     utils  = require(__base + 'utils/sharedUtils.js');
//   }
//   else throw 'mymodule requires underscore, see http://underscorejs.org';
// }
//
// var game_core = function(options){
//   // Store a flag if we are the server instance
//   this.server = options.server ;
//   this.projectName = '3dObjects';
//   this.experimentName = 'graphical_conventions';
//   this.iterationName = 'testing'; // ['run0_bonusmeter']
//   this.email = 'sketchloop@gmail.com';
//
//   // save data to the following locations (allowed: 'csv', 'mongo')
//   this.dataStore = ['csv', 'mongo'];
//   this.anonymizeCSV = true;
//
//   // How many players in the game?
//   this.players_threshold = 2;
//   this.playerRoleNames = {
//     role1 : 'sketcher',
//     role2 : 'viewer'
//   };
//
//
//   //Dimensions of world in pixels and number of cells to be divided into;
//   this.numHorizontalCells = 4; // change from 6
//   this.numVerticalCells = 1;
//   this.cellDimensions = {height : 200, width : 200}; // in pixels // change from 150
//   this.cellPadding = 0;
//   this.world = {height : (this.cellDimensions.height * this.numVerticalCells
//               + this.cellPadding),
//               width : (this.cellDimensions.width * this.numHorizontalCells
//               + this.cellPadding)};
//
//
//   // track shift key drawing tool use
//   this.shiftKeyUsed = 0; // "1" on trials where used, "0" otherwise
//
//   // Which stroke number are we on?
//   this.currStrokeNum = 0;
//
//   // Has the sketcher drawn anything?
//   this.strokeMade = false;
//
//   // Is the sketcher done with their drawing?
//   this.doneDrawing = false;
//
//   // Is the sketcher allowed to draw?
//   this.drawingAllowed = false;
//
//   // time (in ms) to wait before giving feedback
//   this.feedbackDelay = 300;
//
//   // how long the sketcher has to finish their drawing
//   this.timeLimit = 25;
//
//   // toggle whether an object has been clicked
//   this.objClicked = false;
//
//   // Which round (a.k.a. "trial") are we on (initialize at -1 so that first round is 0-indexed)
//   this.roundNum = -1;
//
//   // How many repetitions do we want?
//   this.numReps = 6; // changed from 4
//
//   // How many rounds do we want people to complete?
//   this.numRounds = 40; // changed from 48
//
//   // should we fix the pose to 3/4 view across trials and games?
//   this.poseFixed = 1;
//
//   // How many objects per round (how many items in the menu)?
//   this.numItemsPerRound = this.numHorizontalCells*this.numVerticalCells;
//
//   // Items x Rounds?
//   this.numItemsxRounds = this.numItemsPerRound*this.numRounds;
//
//   // This will be populated with the set of objects
//   this.trialInfo = {};
//
//   // Progress bar timer
//   this.timer;
//
//   // Most recent start stroke time
//   this.startStrokeTime = Date.now();
//
//   // Most recent end stroke time
//   this.endStrokeTime = Date.now();
//
//   // Whether only chairs are used or all four categories
//   this.chairsOnly = true; // change later
//
//   // Whether repeated trials have red frame
//   this.repeatedIsRed;
//
//   if(this.server) {
//     console.log('sent server update bc satisfied this.server')
//     // If we're initializing the server game copy, pre-create the list of trials
//     // we'll use, make a player object, and tell the player who they are
//     this.id = options.id;
//     this.expName = options.expName;
//     this.player_count = options.player_count;
//     this.trialList = this.makeTrialList();
//     //console.log("trialList: " + this.trialList);
//     this.data = {
//       id : this.id,
//       trials : [],
//       catch_trials : [], system : {},
//       subject_information : {
// 	    gameID: this.id,
// 	    score: 0,
//       bonus_score: 0
//       }
//     };
//     this.players = [{
//       id: options.player_instances[0].id,
//       instance: options.player_instances[0].player,
//       player: new game_player(this,options.player_instances[0].player)
//     }];
//     this.streams = {};
//     this.server_send_update();
//   } else {
//     // If we're initializing a player's local game copy, create the player object
//     this.players = [{
//       id: null,
//       instance: null,
//       player: new game_player(this)
//     }];
//   }
// };
//
// var game_player = function( game_instance, player_instance) {
//   this.instance = player_instance;
//   this.game = game_instance;
//   this.role = '';
//   this.message = '';
//   this.id = '';
// };
//
// // server side we set some classes to global types, so that
// // we can use them in other files (specifically, game.server.js)
// if('undefined' != typeof global) {
//   var stimList = _.map(require('./stimList_subord', _.clone));
//   // console.log(stimList);
//   module.exports = {game_core, game_player};
// }
//
// // HELPER FUNCTIONS
//
// // Method to easily look up player
// game_core.prototype.get_player = function(id) {
//   var result = _.find(this.players, function(e){ return e.id == id; });
//   return result.player;
// };
//
// // Method to get list of players that aren't the given id
// game_core.prototype.get_others = function(id) {
//   var otherPlayersList = _.filter(this.players, function(e){ return e.id != id; });
//   var noEmptiesList = _.map(otherPlayersList, function(p){return p.player ? p : null;});
//   return _.without(noEmptiesList, null);
// };
//
// // Returns all players
// game_core.prototype.get_active_players = function() {
//   var noEmptiesList = _.map(this.players, function(p){return p.player ? p : null;});
//   return _.without(noEmptiesList, null);
// };
//
// // Advance to the next round
// game_core.prototype.newRound = function() {
//   // If you've reached the planned number of rounds, end the game
//   if(this.roundNum == this.numRounds - 1) {
//     _.map(this.get_active_players(), function(p){
//       p.player.instance.disconnect();});
//   } else {
//     // console.log('got to newRound in game.core.js and not the final round');
//     // Otherwise, get the preset list of objects for the new round
//     this.roundNum += 1;
//     this.trialInfo = {currStim: this.trialList[this.roundNum]};
//     //console.log("this.trialList[this.roundNum]: " + this.trialList[this.roundNum]);
//     this.objects = this.trialList[this.roundNum];
//     this.objClicked = false;
//     active_players = this.get_active_players();
//     this.setupTimer(this.timeLimit,active_players);
//     this.server_send_update();
//   }
// };
//
// game_core.prototype.setupTimer = function(timeleft, active_players) {
//   this.timeleft = timeleft;
//   var that = this;
//   if (timeleft >= 0 && !(this.objClicked)) {
//     _.map(active_players, function(p){
//       p.player.instance.emit('updateTimer', timeleft);
//     });
//     this.timer = setTimeout(function(){
//       that.setupTimer(timeleft - 1,active_players);
//     }, 1000);
//   } else {
//     clearTimeout(this.timer);
//     console.log("calling timeOut")
//     _.map(active_players, function(p){
//       p.player.instance.emit('timeOut', timeleft);
//     });
//   }
// }
//
// game_core.prototype.getRandomizedConditions = function() {
//
//   ///// Aug 30 implementing re-design (see README.md)
//
//   // assign one of the four categories to this game (dogs, birds, chairs, cars)
//   // only allow close contexts
//   // trial list is generated by concatenating pre (all 8), repeating (4 objs x 6 reps), post (all 8) phases.
//   // strategy here is to use the same pipeline to generate design matrix,
//   // but then just grab the subset we need for a given game: i.e., two quartets of objects from same category
//
//   var numCats = 4;
//   var numObjs = 8; // changed from 12
//   var setSize = 4; // this is the number of objects that appear in a single menu // changed from 6
//
//   // make category array
//   var shuffledCat = _.shuffle(_.range(0,numCats));
//   var sampledCat = shuffledCat[0];
//   var _category = new Array;
//   for (i=0; i<setSize; i++) {
//     _category.push(sampledCat);
//   }
//
//   // shuffle objects
//   var shuffledObjs = _.shuffle(_.range(0,numObjs));
//   // split these 12 chairs up into 2 sets of 6, one of them will be repeated, the other will be control
//   var repeatedObjs = shuffledObjs.slice(0,setSize);
//   var controlObjs = shuffledObjs.slice(setSize,setSize*2);
//
//   console.log("repeatedObjs: " + repeatedObjs);
//   console.log("controlObjs: " + controlObjs);
//
//   // Construct the full trial sequence
//
//   // pre
//   pre = new Array;
//   for (var i = 0; i < setSize; i++) {
//     target = repeatedObjs[i];
//     trial =
//     {
//       'object': repeatedObjs,
//       'category': _category,
//       'pose': 35,
//       'condition':'repeated',
//       'target': target,
//       'phase': 'pre',
//       'repetition': 0
//     }
//     // arr = new Array;
//     // target = repeatedObjs[i];
//     // arr.push(repeatedObjs);
//     // arr.push(_category);
//     // arr.push(35);
//     // arr.push('repeated');
//     // arr.push(target);
//     // arr.push('pre');
//     // arr.push(0);
//     pre.push(trial);
//   }
//   for (var i = 0; i < setSize; i++) {
//     target = controlObjs[i];
//     trial =
//     {
//       'object': controlObjs,
//       'category': _category,
//       'pose': 35,
//       'condition':'control',
//       'target': target,
//       'phase': 'pre',
//       'repetition': 0
//     }
//     //
//     // arr = new Array;
//     // target = controlObjs[i];
//     // arr.push(controlObjs);
//     // arr.push(_category);
//     // arr.push(35);
//     // arr.push('control');
//     // arr.push(target);
//     // arr.push('pre');
//     // arr.push(0);
//     pre.push(trial);
//   }
//   pre = _.shuffle(pre);
//
//   // repeated
//   repeated = new Array;
//   numReps = this.numReps;
//   for (var rep=1; rep<numReps+1; rep++) {
//     repeatedObjs = _.shuffle(repeatedObjs);
//     for (var i = 0; i < setSize; i++){
//       target = repeatedObjs[i];
//       trial =
//       {
//         'object': repeatedObjs,
//         'category': _category,
//         'pose': 35,
//         'condition':'repeated',
//         'target': target,
//         'phase': 'repeated',
//         'repetition': rep
//       }
//       // arr = new Array;
//       // target = repeatedObjs[i];
//       // arr.push(repeatedObjs);
//       // arr.push(_category);
//       // arr.push(35);
//       // arr.push('repeated');
//       // arr.push(target);
//       // arr.push('repeated');
//       // arr.push(rep);
//       repeated.push(trial);
//     }
//   }
//
//   // post
//   repeatedObjs = _.shuffle(repeatedObjs);
//   controlObjs = _.shuffle(controlObjs);
//   post = new Array;
//   for (var i = 0; i < setSize; i++) {
//     target = repeatedObjs[i];
//     trial =
//     {
//       'object': repeatedObjs,
//       'category': _category,
//       'pose': 35,
//       'condition':'repeated',
//       'target': target,
//       'phase': 'post',
//       'repetition': this.numReps + 1
//     }
//     // arr = new Array;
//     // target = repeatedObjs[i];
//     // arr.push(repeatedObjs);
//     // arr.push(_category);
//     // arr.push(35);
//     // arr.push('repeated');
//     // arr.push(target);
//     // arr.push('post');
//     // arr.push(5);
//     post.push(trial);
//   }
//   for (var i = 0; i < setSize; i++) {
//     target = controlObjs[i];
//     trial =
//     {
//       'object': controlObjs,
//       'category': _category,
//       'pose': 35,
//       'condition':'control',
//       'target': target,
//       'phase': 'post',
//       'repetition': 1
//     }
//     // arr = new Array;
//     // target = controlObjs[i];
//     // arr.push(controlObjs);
//     // arr.push(_category);
//     // arr.push(35);
//     // arr.push('control');
//     // arr.push(target);
//     // arr.push('post');
//     // arr.push(1);
//     post.push(trial);
//   }
//   post = _.shuffle(post);
//
//   session = pre.concat(repeated).concat(post);
//
//   console.log(session);
//   return session; // design_dict
//
// };
//
// game_core.prototype.sampleStimulusLocs = function() {
//   var listenerLocs = _.shuffle([[1,1], [2,1], [3,1], [4,1], [5,1], [6,1]]); // added [5,1],[6,1]
//   var speakerLocs = _.shuffle([[1,1], [2,1], [3,1], [4,1], [5,1], [6,1]]); // added [5,1],[6,1]
//
//   // // temporarily turn off shuffling to make sure that it has to do with this
//   // var listenerLocs = [[1,1], [2,1], [3,1], [4,1]];
//   // var speakerLocs = [[1,1], [2,1], [3,1], [4,1]];
//   return {listener : listenerLocs, speaker : speakerLocs};
// };
//
//
// game_core.prototype.makeTrialList = function () {
//
//   var local_this = this;
//   var session = this.getRandomizedConditions(); // added
//   var design_dict = this.getRandomizedConditions();
//   var categoryList = design_dict['category'];
//   var _objectList = design_dict['object'];
//   var poseList = design_dict['pose'];
//   var targetList = design_dict['target'];
//   var conditionList = design_dict['condition'];
//   var phaseList = design_dict['phase'];
//   var repetitionList = design_dict['repetition'];
//
//   var objList = new Array;
//   var locs = new Array;
//
//   var trialList = [];
//
//   for (var i = 0; i < session.length; i++) {
//     var trial = session[i]
//   //for (var i = 0; i < categoryList.length; i++) { // "i" indexes round number ---- commented out
//     // sample four object images that are unique and follow the condition constraints
//     // roundNum,categoryList,_objectList,poseList,targetList,conditionList,phaseList,repetitionList
//     var objList = sampleTrial(trial.category,trial.object,trial.pose,trial.target,trial.condition,trial.phase,trial.repetition);
//     // var objList = sampleTrial(i,categoryList,_objectList,poseList,targetList,conditionList,phaseList,repetitionList);  ---- commented out
//     console.log('objList',objList);
//     // sample locations for those objects
//     var locs = this.sampleStimulusLocs();
//     // construct trial list (in sets of complete rounds)
//     trialList.push(_.map(_.zip(objList, locs.speaker, locs.listener), function(tuple) {
//       var object = _.clone(tuple[0]);
//       object.width = local_this.cellDimensions.width;
//       object.height = local_this.cellDimensions.height;
//       var speakerGridCell = local_this.getPixelFromCell(tuple[1][0], tuple[1][1]);
//       var listenerGridCell = local_this.getPixelFromCell(tuple[2][0], tuple[2][1]);
//       object.speakerCoords = {
//       	gridX : tuple[1][0],
//       	gridY : tuple[1][1],
//       	trueX : speakerGridCell.centerX - object.width/2,
//       	trueY : speakerGridCell.centerY - object.height/2,
//       	gridPixelX: speakerGridCell.centerX - 100,
//       	gridPixelY: speakerGridCell.centerY - 100
//             };
//       object.listenerCoords = {
//       	gridX : tuple[2][0],
//       	gridY : tuple[2][1],
//       	trueX : listenerGridCell.centerX - object.width/2,
//       	trueY : listenerGridCell.centerY - object.height/2,
//       	gridPixelX: listenerGridCell.centerX - 100,
//       	gridPixelY: listenerGridCell.centerY - 100
//       };
//       return object;
//
//       }));
//
//
//   };
//   //console.log("trialList: " + trialList);
//   return(trialList);
//
// };
//
// game_core.prototype.server_send_update = function(){
//   //Make a snapshot of the current state, for updating the clients
//   var local_game = this;
//
//   // Add info about all players
//   var player_packet = _.map(local_game.players, function(p){
//     return {id: p.id,
//             player: null};
//   });
//
//   var state = {
//     gs : this.game_started,   // true when game's started
//     pt : this.players_threshold,
//     pc : this.player_count,
//     dataObj  : this.data,
//     roundNum : this.roundNum,
//     trialInfo: this.trialInfo,
//     objects: this.objects,
//     gameID: this.id
//   };
//
//   _.extend(state, {players: player_packet});
//   _.extend(state, {instructions: this.instructions});
//   if(player_packet.length == 2) {
//     _.extend(state, {objects: this.objects});
//   }
//   // console.log('printing state variable from server_send_update');
//   // console.log(state);
//   //Send the snapshot to the players
//   this.state = state;
//   _.map(local_game.get_active_players(), function(p){
//     p.player.instance.emit( 'onserverupdate', state);});
// };
//
// var getObjectSubset = function(basicCat) {
//   return _.map(_.shuffle(_.filter(_objectList, function(x){
//     return x.basic == basicCat;
//   })), _.clone);
// };
//
// var getRemainingTargets = function(earlierTargets) {
//   var criticalObjs = getObjectSubset("target");
//   return _.filter(criticalObjs, function(x) {
//     return !_.contains(earlierTargets, x.name );
//   });
// };
//
//
//
//
// var sampleTrial = function(category,object,pose,target,condition,phase,repetition) {
//   theseCats = category; // change / collapse later
//   theseObjs = object;
//   thisPose = pose;
//   thisTarget = target;
//   thisCondition = condition;
//   thisPhase = phase;
//   thisRepetition = repetition;
//
//   var im0 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[0]) && (s['object']==theseObjs[0]) && (s['pose']==thisPose) ) })[0];
//   console.log("im0: " + "cluster: " + theseCats[0] + "object: " + theseObjs[0] + "pose: " + thisPose);
//   var im1 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[1]) && (s['object']==theseObjs[1]) && (s['pose']==thisPose) ) })[0];
//   console.log("im1: " + "cluster: " + theseCats[1] + "object: " + theseObjs[1] + "pose: " + thisPose);
//   var im2 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[2]) && (s['object']==theseObjs[2]) && (s['pose']==thisPose) ) })[0];
//   console.log("im2: " + "cluster: " + theseCats[2] + "object: " + theseObjs[2] + "pose: " + thisPose);
//   var im3 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[3]) && (s['object']==theseObjs[3]) && (s['pose']==thisPose) ) })[0];
//   console.log("im3: " + "cluster: " + theseCats[3] + "object: " + theseObjs[3] + "pose: " + thisPose);
//   // var im4 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[4]) && (s['object']==theseObjs[4]) && (s['pose']==thisPose) ) })[0];
//   // console.log("im4: " + "cluster: " + theseCats[4] + "object: " + theseObjs[4] + "pose: " + thisPose);
//   // var im5 = _.filter(stimList, function(s){ return ( (s['cluster']==theseCats[5]) && (s['object']==theseObjs[5]) && (s['pose']==thisPose) ) })[0];
//   // console.log("im5: " + "cluster: " + theseCats[5] + "object: " + theseObjs[5] + "pose: " + thisPose);
//
//   var im_all = [im0,im1,im2,im3];
//   console.log("this target:" + thisTarget);
//
//   var index = theseObjs.indexOf(thisTarget);
//   console.log("index: " + index);
//   var target = im_all[index]; // actual target on this trial
//
//   var notTargs = _.filter(_.range(6), function(x) { return x!=index});
//   var firstDistractor = im_all[notTargs[0]];
//   var secondDistractor = im_all[notTargs[1]];
//   var thirdDistractor = im_all[notTargs[2]];
//   // var fourthDistractor = im_all[notTargs[3]];
//   // var fifthDistractor = im_all[notTargs[4]];
//   _target_status = ["distractor","distractor","distractor","distractor"];
//   var target_status = _target_status[index] = "target"; // changed thisTarget to index
//   console.log("target_status: " + target_status);
//   _.extend(target,{target_status: "target", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
//   _.extend(firstDistractor,{target_status: "distr1", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
//   _.extend(secondDistractor,{target_status: "distr2", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
//   _.extend(thirdDistractor,{target_status: "distr3", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
//   // _.extend(fourthDistractor,{target_status: "distr4", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
//   // _.extend(fifthDistractor,{target_status: "distr5", condition: thisCondition, phase: thisPhase, repetition: thisRepetition});
//   console.log("target's target status " + target.target_status);
//   return [target, firstDistractor, secondDistractor, thirdDistractor];
//
// };
//
// var sampleObjects = function(condition, earlierTargets) {
//   var samplingInfo = {
//     1 : {class: getObjectSubset("birds"),
//    selector: firstClassSelector},
//     2 : {class: getObjectSubset("birds"),
//    selector: secondClassSelector},
//     3 : {class: getObjectSubset("birds"),
//    selector: thirdClassSelector}
//   };
//
//   var conditionParams = condition.slice(-2).split("");
//   var firstDistrInfo = samplingInfo[conditionParams[0]];
//   var secondDistrInfo = samplingInfo[conditionParams[1]];
//   var remainingTargets = getRemainingTargets(earlierTargets);
//
//   var target = _.sample(remainingTargets);
//   var firstDistractor = firstDistrInfo.selector(target, firstDistrInfo.class);
//   var secondDistractor = secondDistrInfo.selector(target, secondDistrInfo.class);
//   if(checkItem(condition,target,firstDistractor,secondDistractor)) {
//     // attach "condition" to each stimulus object
//     return _.map([target, firstDistractor, secondDistractor], function(x) {
//       return _.extend(x, {condition: condition});
//     });
//   } else { // Try again if something is wrong
//     return sampleObjects(condition, earlierTargets);
//   }
// };
//
//
//
//
//
// // NOT NECESSARY FOR SKETCHPAD TASK??
// var checkItem = function(condition, target, firstDistractor, secondDistractor) {
//   var f = 5; // floor difference
//   var t = 20; // threshold
//   var targetVsDistr1 = utils.colorDiff(target.color, firstDistractor.color);
//   var targetVsDistr2 = utils.colorDiff(target.color, secondDistractor.color);
//   var distr1VsDistr2 = utils.colorDiff(firstDistractor.color, secondDistractor.color);
//   if(targetVsDistr1 < f || targetVsDistr2 < f || distr1VsDistr2 < f) {
//     return false;
//   } else if(condition === "equal") {
//     return targetVsDistr1 > t && targetVsDistr2 > t && distr1VsDistr2 > t;
//   } else if (condition === "closer") {
//     return targetVsDistr1 < t && targetVsDistr2 < t && distr1VsDistr2 < t;
//   } else if (condition === "further") {
//     return targetVsDistr1 < t && targetVsDistr2 > t && distr1VsDistr2 > t;
//   } else {
//     throw "condition name (" + condition + ") not known";
//   }
// };
//
// var firstClassSelector = function(target, list) {
//   return _.sample(_.filter(list, function(x) {
//     return target.basic === x.basiclevel;
//   }));
// };
//
// var secondClassSelector = function(target, list) {
//   return _.sample(_.filter(list, function(x) {
//     return target.superdomain === x.superdomain;
//   }));
// };
//
// var thirdClassSelector = function(target, list) {
//   return _.extend(_.sample(list),{targetStatus : "distrClass3"});
// };
//
//
// // maps a grid location to the exact pixel coordinates
// // for x = 1,2,3,4; y = 1,2,3,4
// game_core.prototype.getPixelFromCell = function (x, y) {
//   return {
//     centerX: (this.cellPadding/2 + this.cellDimensions.width * (x - 1)
//         + this.cellDimensions.width / 2),
//     centerY: (this.cellPadding/2 + this.cellDimensions.height * (y - 1)
//         + this.cellDimensions.height / 2),
//     upperLeftX : (this.cellDimensions.width * (x - 1) + this.cellPadding/2),
//     upperLeftY : (this.cellDimensions.height * (y - 1) + this.cellPadding/2),
//     width: this.cellDimensions.width,
//     height: this.cellDimensions.height
//   };
// };
//
// // maps a raw pixel coordinate to to the exact pixel coordinates
// // for x = 1,2,3,4; y = 1,2,3,4
// game_core.prototype.getCellFromPixel = function (mx, my) {
//   var cellX = Math.floor((mx - this.cellPadding / 2) / this.cellDimensions.width) + 1;
//   var cellY = Math.floor((my - this.cellPadding / 2) / this.cellDimensions.height) + 1;
//   return [cellX, cellY];
// };
//
//
//
// // // readjusts trueX and trueY values based on the objLocation and width and height of image (objImage)
// // game_core.prototype.getTrueCoords = function (coord, objLocation, objImage) {
// //   var trueX = this.getPixelFromCell(objLocation.gridX, objLocation.gridY).centerX - objImage.width/2;
// //   var trueY = this.getPixelFromCell(objLocation.gridX, objLocation.gridY).centerY - objImage.height/2;
// //   if (coord == "xCoord") {
// //     return trueX;
// //   }
// //   if (coord == "yCoord") {
// //     return trueY;
// //   }
// // };
