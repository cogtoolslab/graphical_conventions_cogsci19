var _ = require('underscore');
var fs = require('fs');
var path = require('path');
var converter = require("color-convert");
var DeltaE = require('../node_modules/delta-e');
var mkdirp = require('mkdirp');
var sendPostRequest = require('request').post;

var serveFile = function(req, res) {
  var fileName = req.params[0];
  console.log('\t :: Express :: file requested: ' + fileName);
  return res.sendFile(fileName, {root: __base});
};

var handleDuplicate = function(req, res) {
  console.log("duplicate id: blocking request");
  return res.redirect('/utils/duplicate.html');
};

var handleInvalidID = function(req, res) {
  console.log("invalid id: blocking request");
  return res.redirect('/utils/invalid.html');
};

var checkPreviousParticipant = function(workerId, callback) {
  var p = {'workerId': workerId};
  var postData = {
    dbname: '3dObjects',
    query: p,
    projection: {'_id': 1}
  };
  sendPostRequest(
    'http://localhost:6000/db/exists',
    {json: postData},
    (error, res, body) => {
      try {
      	if (!error && res.statusCode === 200) {
      	  console.log("success! Received data " + JSON.stringify(body));
      	  callback(body);
      	} else {
      	  throw `${error}`;
      	 }
          }
      catch (err) {
      	console.log(err);
      	console.log('no database; allowing participant to continue');
      	return callback(false);
      }
    }
  );
};

var writeDataToCSV = function(game, _dataPoint) {
  var dataPoint = _.clone(_dataPoint);
  var eventType = dataPoint.eventType;

  // Omit sensitive data
  if(game.anonymizeCSV)
    dataPoint = _.omit(dataPoint, ['workerId', 'assignmentId']);

  // Establish stream to file if it doesn't already exist
  if(!_.has(game.streams, eventType))
    establishStream(game, dataPoint);

  var line = _.values(dataPoint).join('\t') + "\n";
  game.streams[eventType].write(line, err => {if(err) throw err;});
};

var writeDataToMongo = function(game, line) {
  var postData = _.extend({
    dbname: game.projectName,
    colname: game.experimentName
  }, line);
  sendPostRequest(
    'http://localhost:6000/db/insert',
    { json: postData },
    (error, res, body) => {
      if (!error && res.statusCode === 200) {
        console.log(`sent data to store`);
      } else {
	       console.log(`error sending data to store: ${error} ${body}`);
      }
    }
  );
};

var UUID = function() {
  var baseName = (Math.floor(Math.random() * 10) + '' +
        Math.floor(Math.random() * 10) + '' +
        Math.floor(Math.random() * 10) + '' +
        Math.floor(Math.random() * 10));
  var template = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx';
  var id = baseName + '-' + template.replace(/[xy]/g, function(c) {
    var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
    return v.toString(16);
  });
  return id;
};

var getLongFormTime = function() {
  var d = new Date();
  var day = [d.getFullYear(), (d.getMonth() + 1), d.getDate()].join('-');
  var time = [d.getHours() + 'h', d.getMinutes() + 'm', d.getSeconds() + 's'].join('-');
  return day + '-' + time;
};

var establishStream = function(game, dataPoint) {
  var startTime = getLongFormTime();
  var dirPath = ['..', 'data', game.expName, dataPoint.eventType].join('/');
  var fileName = startTime + "-" + game.id + ".csv";
  var filePath = [dirPath, fileName].join('/');

  // Create path if it doesn't already exist
  mkdirp.sync(dirPath, err => {if (err) console.error(err);});

  // Write header
  var header = _.keys(dataPoint).join('\t') + '\n';
  fs.writeFile(filePath, header, err => {if(err) console.error(err);});

  // Create stream
  var stream = fs.createWriteStream(filePath, {'flags' : 'a'});
  game.streams[dataPoint.eventType] = stream;
};

var getObjectLocHeaderArray = function() {
  var arr =  _.map(_.range(1,5), function(i) {
    return _.map(['Name', 'SenderLoc', 'ReceiverLoc'], function(v) {
      return 'object' + i + v;
    });
  });
  return _.flatten(arr);
};

var hsl2lab = function(hsl) {
  return converter.hsl.lab(hsl);
};

function fillArray(value, len) {
  var arr = [];
  for (var i = 0; i < len; i++) {
    arr.push(value);
  }
  return arr;
}

var checkInBounds = function(object, options) {
  return (object.x + (object.w || object.d) < options.width) &&
         (object.y + (object.h || object.d) < options.height);
};

// --- below added by jefan March 2017
// extracts all the values of the javascript dictionary by key
var vec = function extractEntries(dict,key) {
    vec = []
    for (i=0; i<dict.length; i++) {
        vec.push(dict[i][key]);
    }
    return vec;
}

// finds matches to specific value given key
var vec = function matchingValue(dict,key,value) {
  vec = []
  for (i=0; i<dict.length; i++) {
    if (dict[i][key]==value) {
        vec.push(dict[i]);
    }
  }
  return vec;
}

// add entry to dictionary object
var dict = function addEntry(dict,key,value) {
  for (i=0; i<dict.length; i++) {
      dict[i][key] = value;
  }
  return dict;
}

// make integer series from lb (lower) to ub (upper)
var series = function makeSeries(lb,ub) {
    series = new Array();
    if (ub<=lb) {
      throw new Error("Upper bound should be greater than lower bound!");
    }
   for (var i = lb; i<(ub+1); i++) {
      series = series.concat(i);
   }
   return series;
}

// --- above added by jefan March 2017

module.exports = {
  UUID,
  checkPreviousParticipant,
  serveFile,
  handleDuplicate,
  handleInvalidID,
  getLongFormTime,
  establishStream,
  writeDataToCSV,
  writeDataToMongo,
  hsl2lab,
  fillArray
};
