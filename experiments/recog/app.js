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
var num_trials = 10;
var gameport;
var researchers = ['A4SSYO0HDVD4E', 'A1BOIDKD33QSDK'];
var block_researcher = false;

if(argv.gameport) {
  gameport = argv.gameport;
  console.log('using port ' + gameport);
} else {
  gameport = 8886;
  console.log('no gameport specified: using 8886\nUse the --gameport flag to change');
}

try {
  var privateKey  = fs.readFileSync('/etc/apache2/ssl/rxdhawkins.me.key'),
      certificate = fs.readFileSync('/etc/apache2/ssl/rxdhawkins.me.crt'),
      intermed    = fs.readFileSync('/etc/apache2/ssl/intermediate.crt'),
      options     = {key: privateKey, cert: certificate, ca: intermed},
      server      = require('https').createServer(options,app).listen(gameport),
      io          = require('socket.io')(server);
} catch (err) {
  console.log("cannot find SSL certificates; falling back to http");
  var server      = app.listen(gameport),
      io          = require('socket.io')(server);
}

app.get('/*', (req, res) => {
  // // serve stuff that the client requests
  // serveFile(req, res); 
  var id = req.query.workerId; 
  if(!id || id === 'undefined') {
    serveFile(req, res);
  } else if(!valid_id(id)) {
    // If invalid id, block them
    return handleInvalidID(req, res);
    console.log('invalid id, blocked');
  } else {
    // If the database shows they've already participated, block them
    // If not a repeat worker, then send client stims
    console.log('neither invalid nor blank id, check if repeat worker');
    // check if id is one of the researchers, if so, let them continue
    researcher_ind = _.findIndex(researchers, function(x) {return x==id});
    console.log('researcher ind ', researcher_ind);
      if (researcher_ind>-1 && !block_researcher) {
	  console.log('serve files if client is one of the researchers and we do not want to block them');
	  serveFile(req, res); // serve files if client is one of the researchers and we do not want to block them
    } else {
	checkPreviousParticipant(id, (exists) => {    
        return exists ? handleDuplicate(req, res) : serveFile(req, res);
      });      
    }
  }
  
});

io.on('connection', function (socket) {

  // Recover query string information and set condition
  var hs = socket.request;
  var query = require('url').parse(hs.headers.referer, true).query;
  var id;
  // assign worker
  if (!query.workerId || query.workerId == 'undefined') {
    id = UUID();
  } else {
    console.log('query.workerId = ', query.workerId);
    id = query.workerId;
  }

  // Send client stims
  initializeWithTrials(socket, UUID());

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

function initializeWithTrials(socket, id) {
  sendPostRequest('http://localhost:6000/db/getstims', {
    json: {
      dbname: 'stimuli',
      colname: 'graphical_conventions_sketches',
      numTrials: 1,
      gameid: id
    }
  }, (error, res, body) => {
    if (!error && res.statusCode === 200) {
      // send trial list (and id) to client
      var packet = {
	id: id,
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
    'http://localhost:6000/db/insert',
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
