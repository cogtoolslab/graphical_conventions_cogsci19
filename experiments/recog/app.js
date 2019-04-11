global.__base = __dirname + '/';

var
    use_https     = true,
    argv          = require('minimist')(process.argv.slice(2)),
    https         = require('https'),
    fs            = require('fs'),
    app           = require('express')(),
    _             = require('lodash'),
    parser        = require('xmldom').DOMParser,
    XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest,
    sendPostRequest = require('request').post;


// define number of trials to fetch from database (what is length of each recog HIT?)
var gameport;
var recogVersion;
var researchers = ['A4SSYO0HDVD4E', 'A1BOIDKD33QSDK', 'A1MMCS8S8CTWKU','A1MMCS8S8CTWKV','A1MMCS8S8CTWKS'];
var blockResearcher = false;

if(argv.gameport) {
  gameport = argv.gameport;
  console.log('using port ' + gameport);
} else {
  gameport = 8887;
  console.log('no gameport specified: using 8886\nUse the --gameport flag to change');
}

if(argv.recogVersion) {
  recogVersion = argv.recogVersion;
  console.log('running version ' + recogVersion);
} else {
  recogVersion = 'yoked';
  console.log('no version specified: running yoked\nUse the --recogVersion flag to change');
}

try {
  var privateKey  = fs.readFileSync('/etc/apache2/ssl/stanford-cogsci.org.key'),
      certificate = fs.readFileSync('/etc/apache2/ssl/stanford-cogsci.org.crt'),
      intermed    = fs.readFileSync('/etc/apache2/ssl/intermediate.crt'),
      options     = {key: privateKey, cert: certificate, ca: intermed},
      server      = require('https').createServer(options,app).listen(gameport),
      io          = require('socket.io')(server);
} catch (err) {
  console.log("cannot find SSL certificates; falling back to http");
  var server      = app.listen(gameport),
      io          = require('socket.io')(server);
}

// serve stuff that the client requests
app.get('/*', (req, res) => {
  var id = req.query.workerId;
  // Let them through if researcher, or in 'testing' mode
  var isResearcher = _.includes(researchers, id);
  if(!id || id === 'undefined' || (isResearcher && !blockResearcher)) {
    serveFile(req, res);
  } else if(!valid_id(id)) {
    // If invalid id, block them
    return handleInvalidID(req, res);
    console.log('invalid id, blocked');
  } else {
    // If the database shows they've already participated, block them
    // If not a repeat worker, then send client stims
    console.log('neither invalid nor blank id, check if repeat worker');
    checkPreviousParticipant(id, (exists) => {    
      return exists ? handleDuplicate(req, res) : serveFile(req, res);
    });      
  }
});

io.on('connection', function (socket) {

  // Recover query string information and set condition
  var hs = socket.request;
  var query = require('url').parse(hs.headers.referer, true).query;

  // Send client stims
  initializeWithTrials(socket);

  // Set up callback for writing client data to mongo
  socket.on('currentData', function(data) {
    console.log('currentData received: ' + JSON.stringify(data));
    writeDataToMongo(data);
  });

});

var serveFile = function(req, res) {
  var fileName = req.params[0];
  console.log('\t :: Express :: file requested: ' + fileName);
  return res.sendFile(fileName, {root: __dirname});
};

var handleDuplicate = function(req, res) {
  console.log("duplicate id: blocking request");
  res.sendFile('duplicate.html', {root: __dirname});
  return res.redirect('/duplicate.html');

};

var valid_id = function(id) {
  return (id.length <= 15 && id.length >= 12) || id.length == 41;
};

var handleInvalidID = function(req, res) {
  console.log("invalid id: blocking request");
  return res.redirect('/invalid.html');
};

function checkPreviousParticipant (workerId, callback) {
  var p = {'workerId': workerId};
  var postData = {
    dbname: '3dObjects',
    query: p,
    projection: {'_id': 1}
  };
  sendPostRequest(
    'http://localhost:6004/db/exists',
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

function initializeWithTrials(socket) {
  var gameid = UUID();
  var colname = (recogVersion == 'yoked' ? 'graphical_conventions_sketches_yoked_refgame2.0' :
		 recogVersion == 'scrambled40' ? 'graphical_conventions_sketches_scrambled40_refgame2.0_dev' :
		 recogVersion == 'scrambled10' ? 'graphical_conventions_sketches_scrambled10_refgame2.0_dev' :
		 console.error('unknown version: ' + recogVersion));
  sendPostRequest('http://localhost:6004/db/getstims', {
    json: {
      dbname: 'stimuli',
      colname: colname,
      numTrials: 1,
      gameid: gameid
    }
  }, (error, res, body) => {
    if (!error && res.statusCode === 200) {
      // send trial list (and id) to client
      var packet = {
      	gameid: gameid,
      	version: recogVersion,	
      	recogID: body.recogID,
      	trials: body.meta
      };      
      socket.emit('onConnected', packet);
    } else {
      console.log(`error getting stims: ${error} ${body}`);
    }
  });
}


function writeDataToMongo (data) {
  sendPostRequest(
    'http://localhost:6004/db/insert',
    { json: data },
    (error, res, body) => {
      if (!error && res.statusCode === 200) {
        console.log(`sent data to store`);
      } else {
	console.log(`error sending data to store: ${error} ${body}`);
      }
    }
  );
};

function UUID () {
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
