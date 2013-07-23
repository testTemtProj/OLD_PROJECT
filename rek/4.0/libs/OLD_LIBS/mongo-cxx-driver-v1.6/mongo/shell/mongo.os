ELF          >                    ��          @     @  	 __quiet = false;
__magicNoPrint = { __magicNoPrint : 1111 }
chatty = function(s){
if ( ! __quiet )
print( s );}
friendlyEqual = function( a , b ){
if ( a == b )
return true;
if ( tojson( a ) == tojson( b ) )
return true;
return false;}
doassert = function (msg) {
if (msg.indexOf("assert") == 0)
print(msg);
else
print("assert: " + msg);
throw msg;}
assert = function( b , msg ){
if ( assert._debug && msg ) print( "in assert for: " + msg );
if ( b )
return;
doassert( msg == undefined ? "assert failed" : "assert failed : " + msg );}
assert.automsg = function( b ) {
assert( eval( b ), b );}
assert._debug = false;
assert.eq = function( a , b , msg ){
if ( assert._debug && msg ) print( "in assert for: " + msg );
if ( a == b )
return;
if ( ( a != null && b != null ) && friendlyEqual( a , b ) )
return;
doassert( "[" + tojson( a ) + "] != [" + tojson( b ) + "] are not equal : " + msg );}
assert.eq.automsg = function( a, b ) {
assert.eq( eval( a ), eval( b ), "[" + a + "] != [" + b + "]" );}
assert.neq = function( a , b , msg ){
if ( assert._debug && msg ) print( "in assert for: " + msg );
if ( a != b )
return;
doassert( "[" + a + "] != [" + b + "] are equal : " + msg );}
assert.repeat = function( f, msg, timeout, interval ) {
if ( assert._debug && msg ) print( "in assert for: " + msg );
var start = new Date();
timeout = timeout || 30000;
interval = interval || 200;
var last;
while( 1 ) {
if ( typeof( f ) == "string" ){
if ( eval( f ) )
return;}
else {
if ( f() )
return;}
if ( ( new Date() ).getTime() - start.getTime() > timeout )
break;
sleep( interval );}}
assert.soon = function( f, msg, timeout, interval ) {
if ( assert._debug && msg ) print( "in assert for: " + msg );
var start = new Date();
timeout = timeout || 30000;
interval = interval || 200;
var last;
while( 1 ) {
if ( typeof( f ) == "string" ){
if ( eval( f ) )
return;}
else {
if ( f() )
return;}
if ( ( new Date() ).getTime() - start.getTime() > timeout )
doassert( "assert.soon failed: " + f + ", msg:" + msg );
sleep( interval );}}
assert.throws = function( func , params , msg ){
if ( assert._debug && msg ) print( "in assert for: " + msg );
try {
func.apply( null , params );}
catch ( e ){
return e;}
doassert( "did not throw exception: " + msg );}
assert.throws.automsg = function( func, params ) {
assert.throws( func, params, func.toString() );}
assert.commandWorked = function( res , msg ){
if ( assert._debug && msg ) print( "in assert for: " + msg );
if ( res.ok == 1 )
return;
doassert( "command failed: " + tojson( res ) + " : " + msg );}
assert.commandFailed = function( res , msg ){
if ( assert._debug && msg ) print( "in assert for: " + msg );
if ( res.ok == 0 )
return;
doassert( "command worked when it should have failed: " + tojson( res ) + " : " + msg );}
assert.isnull = function( what , msg ){
if ( assert._debug && msg ) print( "in assert for: " + msg );
if ( what == null )
return;
doassert( "supposed to null (" + ( msg || "" ) + ") was: " + tojson( what ) );}
assert.lt = function( a , b , msg ){
if ( assert._debug && msg ) print( "in assert for: " + msg );
if ( a < b )
return;
doassert( a + " is not less than " + b + " : " + msg );}
assert.gt = function( a , b , msg ){
if ( assert._debug && msg ) print( "in assert for: " + msg );
if ( a > b )
return;
doassert( a + " is not greater than " + b + " : " + msg );}
assert.lte = function( a , b , msg ){
if ( assert._debug && msg ) print( "in assert for: " + msg );
if ( a <= b )
return;
doassert( a + " is not less than or eq " + b + " : " + msg );}
assert.gte = function( a , b , msg ){
if ( assert._debug && msg ) print( "in assert for: " + msg );
if ( a >= b )
return;
doassert( a + " is not greater than or eq " + b + " : " + msg );}
assert.close = function( a , b , msg , places ){
if (places === undefined) {
places = 4;}
if (Math.round((a - b) * Math.pow(10, places)) === 0) {
return;}
doassert( a + " is not equal to " + b + " within " + places +
" places, diff: " + (a-b) + " : " + msg );
};
Object.extend = function( dst , src , deep ){
for ( var k in src ){
var v = src[k];
if ( deep && typeof(v) == "object" ){
v = Object.extend( typeof ( v.length ) == "number" ? [] : {} , v , true );}
dst[k] = v;}
return dst;}
argumentsToArray = function( a ){
var arr = [];
for ( var i=0; i<a.length; i++ )
arr[i] = a[i];
return arr;}
isString = function( x ){
return typeof( x ) == "string";}
isNumber = function(x){
return typeof( x ) == "number";}
isObject = function( x ){
return typeof( x ) == "object";}
String.prototype.trim = function() {
return this.replace(/^\s+|\s+$/g,"");}
String.prototype.ltrim = function() {
return this.replace(/^\s+/,"");}
String.prototype.rtrim = function() {
return this.replace(/\s+$/,"");}
Date.timeFunc = function( theFunc , numTimes ){
var start = new Date();
numTimes = numTimes || 1;
for ( var i=0; i<numTimes; i++ ){
theFunc.apply( null , argumentsToArray( arguments ).slice( 2 ) );}
return (new Date()).getTime() - start.getTime();}
Date.prototype.tojson = function(){
return "\"" + this.toString() + "\"";}
RegExp.prototype.tojson = RegExp.prototype.toString;
Array.contains = function( a  , x ){
for ( var i=0; i<a.length; i++ ){
if ( a[i] == x )
return true;}
return false;}
Array.unique = function( a ){
var u = [];
for ( var i=0; i<a.length; i++){
var o = a[i];
if ( ! Array.contains( u , o ) ){
u.push( o );}}
return u;}
Array.shuffle = function( arr ){
for ( var i=0; i<arr.length-1; i++ ){
var pos = i+Random.randInt(arr.length-i);
var save = arr[i];
arr[i] = arr[pos];
arr[pos] = save;}
return arr;}
Array.tojson = function( a , indent ){
if (!indent)
indent = "";
if (a.length == 0) {
return "[ ]";}
var s = "[\n";
indent += "\t";
for ( var i=0; i<a.length; i++){
s += indent + tojson( a[i], indent );
if ( i < a.length - 1 ){
s += ",\n";}}
if ( a.length == 0 ) {
s += indent;}
indent = indent.substring(1);
s += "\n"+indent+"]";
return s;}
Array.fetchRefs = function( arr , coll ){
var n = [];
for ( var i=0; i<arr.length; i ++){
var z = arr[i];
if ( coll && coll != z.getCollection() )
continue;
n.push( z.fetch() );}
return n;}
Array.sum = function( arr ){
if ( arr.length == 0 )
return null;
var s = arr[0];
for ( var i=1; i<arr.length; i++ )
s += arr[i];
return s;}
Array.avg = function( arr ){
if ( arr.length == 0 )
return null;
return Array.sum( arr ) / arr.length;}
Array.stdDev = function( arr ){
var avg = Array.avg( arr );
var sum = 0;
for ( var i=0; i<arr.length; i++ ){
sum += Math.pow( arr[i] - avg , 2 );}
return Math.sqrt( sum / arr.length );}
Object.keySet = function( o ) {
var ret = new Array();
for( i in o ) {
if ( !( i in o.__proto__ && o[ i ] === o.__proto__[ i ] ) ) {
ret.push( i );}}
return ret;}
if ( ! NumberLong.prototype ) {
NumberLong.prototype = {}}
NumberLong.prototype.tojson = function() {
return this.toString();}
if ( ! ObjectId.prototype )
ObjectId.prototype = {}
ObjectId.prototype.toString = function(){
return this.str;}
ObjectId.prototype.tojson = function(){
return "ObjectId(\"" + this.str + "\")";}
ObjectId.prototype.isObjectId = true;
ObjectId.prototype.getTimestamp = function(){
return new Date(parseInt(this.toString().slice(0,8), 16)*1000);}
ObjectId.prototype.equals = function( other){
return this.str == other.str;}
if ( typeof( DBPointer ) != "undefined" ){
DBPointer.prototype.fetch = function(){
assert( this.ns , "need a ns" );
assert( this.id , "need an id" );
return db[ this.ns ].findOne( { _id : this.id } );}
DBPointer.prototype.tojson = function(indent){
return tojson({"ns" : this.ns, "id" : this.id}, indent);}
DBPointer.prototype.getCollection = function(){
return this.ns;}
DBPointer.prototype.toString = function(){
return "DBPointer " + this.ns + ":" + this.id;}}
else {
print( "warning: no DBPointer" );}
if ( typeof( DBRef ) != "undefined" ){
DBRef.prototype.fetch = function(){
assert( this.$ref , "need a ns" );
assert( this.$id , "need an id" );
return db[ this.$ref ].findOne( { _id : this.$id } );}
DBRef.prototype.tojson = function(indent){
return tojson({"$ref" : this.$ref, "$id" : this.$id}, indent);}
DBRef.prototype.getCollection = function(){
return this.$ref;}
DBRef.prototype.toString = function(){
return this.tojson();}}
else {
print( "warning: no DBRef" );}
if ( typeof( BinData ) != "undefined" ){
BinData.prototype.tojson = function () {
//return "BinData type: " + this.type + " len: " + this.len;
return this.toString();}}
else {
print( "warning: no BinData class" );}
if ( typeof( UUID ) != "undefined" ){
UUID.prototype.tojson = function () {
return this.toString();}}
if ( typeof _threadInject != "undefined" ){
print( "fork() available!" );
Thread = function(){
this.init.apply( this, arguments );}
_threadInject( Thread.prototype );
ScopedThread = function() {
this.init.apply( this, arguments );}
ScopedThread.prototype = new Thread( function() {} );
_scopedThreadInject( ScopedThread.prototype );
fork = function() {
var t = new Thread( function() {} );
Thread.apply( t, arguments );
return t;}
EventGenerator = function( me, collectionName, mean ) {
this.mean = mean;
this.events = new Array( me, collectionName );}
EventGenerator.prototype._add = function( action ) {
this.events.push( [ Random.genExp( this.mean ), action ] );}
EventGenerator.prototype.addInsert = function( obj ) {
this._add( "t.insert( " + tojson( obj ) + " )" );}
EventGenerator.prototype.addRemove = function( obj ) {
this._add( "t.remove( " + tojson( obj ) + " )" );}
EventGenerator.prototype.addUpdate = function( objOld, objNew ) {
this._add( "t.update( " + tojson( objOld ) + ", " + tojson( objNew ) + " )" );}
EventGenerator.prototype.addCheckCount = function( count, query, shouldPrint, checkQuery ) {
query = query || {};
shouldPrint = shouldPrint || false;
checkQuery = checkQuery || false;
var action = "assert.eq( " + count + ", t.count( " + tojson( query ) + " ) );"
if ( checkQuery ) {
action += " assert.eq( " + count + ", t.find( " + tojson( query ) + " ).toArray().length );"}
if ( shouldPrint ) {
action += " print( me + ' ' + " + count + " );";}
this._add( action );}
EventGenerator.prototype.getEvents = function() {
return this.events;}
EventGenerator.dispatch = function() {
var args = argumentsToArray( arguments );
var me = args.shift();
var collectionName = args.shift();
var m = new Mongo( db.getMongo().host );
var t = m.getDB( "test" )[ collectionName ];
for( var i in args ) {
sleep( args[ i ][ 0 ] );
eval( args[ i ][ 1 ] );}}
ParallelTester = function() {
this.params = new Array();}
ParallelTester.prototype.add = function( fun, args ) {
args = args || [];
args.unshift( fun );
this.params.push( args );}
ParallelTester.prototype.run = function( msg, newScopes ) {
newScopes = newScopes || false;
assert.parallelTests( this.params, msg, newScopes );}
ParallelTester.createJstestsLists = function( n ) {
var params = new Array();
for( var i = 0; i < n; ++i ) {
params.push( [] );}
var makeKeys = function( a ) {
var ret = {};
for( var i in a ) {
ret[ a[ i ] ] = 1;}
return ret;}
var skipTests = makeKeys( [ "jstests/dbadmin.js",
"jstests/repair.js",
"jstests/cursor8.js",
"jstests/recstore.js",
"jstests/extent.js",
"jstests/indexb.js",
"jstests/profile1.js",
"jstests/mr3.js",
"jstests/indexh.js",
"jstests/apitest_db.js",
"jstests/evalb.js"] );
var serialTestsArr = [ "jstests/fsync.js",
"jstests/fsync2.js" ];
var serialTests = makeKeys( serialTestsArr );
params[ 0 ] = serialTestsArr;
var files = listFiles("jstests");
files = Array.shuffle( files );
var i = 0;
files.forEach(
function(x) {
if ( ( /[\/\\]_/.test(x.name) ) ||
( ! /\.js$/.test(x.name ) ) ||
( x.name in skipTests ) ||
( x.name in serialTests ) ||
! /\.js$/.test(x.name ) ){
print(" >>>>>>>>>>>>>>> skipping " + x.name);
return;}
params[ i % n ].push( x.name );
++i;}
);
params[ 0 ] = Array.shuffle( params[ 0 ] );
for( var i in params ) {
params[ i ].unshift( i );}
return params;}
ParallelTester.fileTester = function() {
var args = argumentsToArray( arguments );
var suite = args.shift();
args.forEach(
function( x ) {
print("         S" + suite + " Test : " + x + " ...");
var time = Date.timeFunc( function() { load(x); }, 1);
print("         S" + suite + " Test : " + x + " " + time + "ms" );}
);}
assert.parallelTests = function( params, msg, newScopes ) {
newScopes = newScopes || false;
var wrapper = function( fun, argv ) {
eval (
"var z = function() {" +
"var __parallelTests__fun = " + fun.toString() + ";" +
"var __parallelTests__argv = " + tojson( argv ) + ";" +
"var __parallelTests__passed = false;" +
"try {" +
"__parallelTests__fun.apply( 0, __parallelTests__argv );" +
"__parallelTests__passed = true;" +
"} catch ( e ) {" +
"print( e );" +
"}" +
"return __parallelTests__passed;" +
"}"
);
return z;}
var runners = new Array();
for( var i in params ) {
var param = params[ i ];
var test = param.shift();
var t;
if ( newScopes )
t = new ScopedThread( wrapper( test, param ) );
else
t = new Thread( wrapper( test, param ) );
runners.push( t );}
runners.forEach( function( x ) { x.start(); } );
var nFailed = 0;
runners.forEach( function( x ) { if( !x.returnData() ) { ++nFailed; } } );
assert.eq( 0, nFailed, msg );}}
tojsononeline = function( x ){
return tojson( x , " " , true );}
tojson = function( x, indent , nolint ){
if ( x === null )
return "null";
if ( x === undefined )
return "undefined";
if (!indent)
indent = "";
switch ( typeof x ) {
case "string": {
var s = "\"";
for ( var i=0; i<x.length; i++ ){
switch (x[i]){
case '"': s += '\\"'; break;
case '\\': s += '\\\\'; break;
case '\b': s += '\\b'; break;
case '\f': s += '\\f'; break;
case '\n': s += '\\n'; break;
case '\r': s += '\\r'; break;
case '\t': s += '\\t'; break;
default: {
var code = x.charCodeAt(i);
if (code < 0x20){
s += (code < 0x10 ? '\\u000' : '\\u00') + code.toString(16);
} else {
s += x[i];}}}}
return s + "\"";}
case "number":
case "boolean":
return "" + x;
case "object":{
var s = tojsonObject( x, indent , nolint );
if ( ( nolint == null || nolint == true ) && s.length < 80 && ( indent == null || indent.length == 0 ) ){
s = s.replace( /[\s\r\n ]+/gm , " " );}
return s;}
case "function":
return x.toString();
default:
throw "tojson can't handle type " + ( typeof x );}}
tojsonObject = function( x, indent , nolint ){
var lineEnding = nolint ? " " : "\n";
var tabSpace = nolint ? "" : "\t";
assert.eq( ( typeof x ) , "object" , "tojsonObject needs object, not [" + ( typeof x ) + "]" );
if (!indent)
indent = "";
if ( typeof( x.tojson ) == "function" && x.tojson != tojson ) {
return x.tojson(indent,nolint);}
if ( x.constructor && typeof( x.constructor.tojson ) == "function" && x.constructor.tojson != tojson ) {
return x.constructor.tojson( x, indent , nolint );}
if ( x.toString() == "[object MaxKey]" )
return "{ $maxKey : 1 }";
if ( x.toString() == "[object MinKey]" )
return "{ $minKey : 1 }";
var s = "{" + lineEnding;
indent += tabSpace;
var total = 0;
for ( var k in x ) total++;
if ( total == 0 ) {
s += indent + lineEnding;}
var keys = x;
if ( typeof( x._simpleKeys ) == "function" )
keys = x._simpleKeys();
var num = 1;
for ( var k in keys ){
var val = x[k];
if ( val == DB.prototype || val == DBCollection.prototype )
continue;
s += indent + "\"" + k + "\" : " + tojson( val, indent , nolint );
if (num != total) {
s += ",";
num++;}
s += lineEnding;}
indent = indent.substring(1);
return s + indent + "}";}
shellPrint = function( x ){
it = x;
if ( x != undefined )
shellPrintHelper( x );
if ( db ){
var e = db.getPrevError();
if ( e.err ) {
if( e.nPrev <= 1 )
print( "error on last call: " + tojson( e.err ) );
else
print( "an error " + tojson(e.err) + " occurred " + e.nPrev + " operations back in the command invocation" );}
db.resetError();}}
printjson = function(x){
print( tojson( x ) );}
printjsononeline = function(x){
print( tojsononeline( x ) );}
shellPrintHelper = function( x ){
if ( typeof( x ) == "undefined" ){
if ( typeof( db ) != "undefined" && db.getLastError ){
var e = db.getLastError();
if ( e != null )
print( e );}
return;}
if ( x == __magicNoPrint )
return;
if ( x == null ){
print( "null" );
return;}
if ( typeof x != "object" )
return print( x );
var p = x.shellPrint;
if ( typeof p == "function" )
return x.shellPrint();
var p = x.tojson;
if ( typeof p == "function" )
print( x.tojson() );
else
print( tojson( x ) );}
shellAutocomplete = function( prefix ){
var a = [];
//a.push( prefix + "z" )
//a.push( prefix + "y" )
__autocomplete__ = a;}
shellHelper = function( command , rest , shouldPrint ){
command = command.trim();
var args = rest.trim().replace(/;$/,"").split( "\s+" );
if ( ! shellHelper[command] )
throw "no command [" + command + "]";
var res = shellHelper[command].apply( null , args );
if ( shouldPrint ){
shellPrintHelper( res );}
return res;}
shellHelper.use = function( dbname ){
db = db.getMongo().getDB( dbname );
print( "switched to db " + db.getName() );}
shellHelper.it = function(){
if ( typeof( ___it___ ) == "undefined" || ___it___ == null ){
print( "no cursor" );
return;}
shellPrintHelper( ___it___ );}
shellHelper.show = function( what ){
assert( typeof what == "string" );
if( what == "profile" ) {
if( db.system.profile.count() == 0 ) {
print("db.system.profile is empty");
print("Use db.setProfilingLevel(2) will enable profiling");
print("Use db.system.profile.find() to show raw profile entries");}
else {
print();
db.system.profile.find({ millis : { $gt : 0 } }).sort({$natural:-1}).limit(5).forEach( function(x){print(""+x.millis+"ms " + String(x.ts).substring(0,24)); print(x.info); print("\n");} )}
return "";}
if ( what == "users" ){
db.system.users.find().forEach( printjson );
return "";}
if ( what == "collections" || what == "tables" ) {
db.getCollectionNames().forEach( function(x){print(x)} );
return "";}
if ( what == "dbs" ) {
db.getMongo().getDBNames().sort().forEach( function(x){print(x)} );
return "";}
throw "don't know how to show [" + what + "]";}
if ( typeof( Map ) == "undefined" ){
Map = function(){
this._data = {};}}
Map.hash = function( val ){
if ( ! val )
return val;
switch ( typeof( val ) ){
case 'string':
case 'number':
case 'date':
return val.toString();
case 'object':
case 'array':
var s = "";
for ( var k in val ){
s += k + val[k];}
return s;}
throw "can't hash : " + typeof( val );}
Map.prototype.put = function( key , value ){
var o = this._get( key );
var old = o.value;
o.value = value;
return old;}
Map.prototype.get = function( key ){
return this._get( key ).value;}
Map.prototype._get = function( key ){
var h = Map.hash( key );
var a = this._data[h];
if ( ! a ){
a = [];
this._data[h] = a;}
for ( var i=0; i<a.length; i++ ){
if ( friendlyEqual( key , a[i].key ) ){
return a[i];}}
var o = { key : key , value : null };
a.push( o );
return o;}
Map.prototype.values = function(){
var all = [];
for ( var k in this._data ){
this._data[k].forEach( function(z){ all.push( z.value ); } );}
return all;}
if ( typeof( gc ) == "undefined" ){
gc = function(){
print( "warning: using noop gc()" );}}
Math.sigFig = function( x , N ){
if ( ! N ){
N = 3;}
var p = Math.pow( 10, N - Math.ceil( Math.log( Math.abs(x) ) / Math.log( 10 )) );
return Math.round(x*p)/p;}
Random = function() {}
Random.srand = function( s ) { _srand( s ); }
Random.rand = function() { return _rand(); }
Random.randInt = function( n ) { return Math.floor( Random.rand() * n ); }
Random.setRandomSeed = function( s ) {
s = s || new Date().getTime();
print( "setting random seed: " + s );
Random.srand( s );}
Random.genExp = function( mean ) {
return -Math.log( Random.rand() ) * mean;}
killWithUris = function( uris ) {
var inprog = db.currentOp().inprog;
for( var u in uris ) {
for ( var i in inprog ) {
if ( uris[ u ] == inprog[ i ].client ) {
db.killOp( inprog[ i ].opid );}}}}
Geo = {};
Geo.distance = function( a , b ){
var ax = null;
var ay = null;
var bx = null;
var by = null;
for ( var key in a ){
if ( ax == null )
ax = a[key];
else if ( ay == null )
ay = a[key];}
for ( var key in b ){
if ( bx == null )
bx = b[key];
else if ( by == null )
by = b[key];}
return Math.sqrt( Math.pow( by - ay , 2 ) +
Math.pow( bx - ax , 2 ) );}
rs = function () { return "try rs.help()"; }
rs.help = function () {
print("\trs.status()                     { replSetGetStatus : 1 } checks repl set status");
print("\trs.initiate()                   { replSetInitiate : null } initiates set with default settings");
print("\trs.initiate(cfg)                { replSetInitiate : cfg } initiates set with configuration cfg");
print("\trs.add(hostportstr)             add a new member to the set with default attributes");
print("\trs.add(membercfgobj)            add a new member to the set with extra attributes");
print("\trs.addArb(hostportstr)          add a new member which is arbiterOnly:true");
print("\trs.stepDown()                   step down as primary (momentarily)");
print("\trs.conf()                       return configuration from local.system.replset");
print("\trs.slaveOk()                    shorthand for db.getMongo().setSlaveOk()");
print();
print("\tdb.isMaster()                   check who is primary");
print();
print("\tsee also http://<mongod_host>:28017/_replSet for additional diagnostic info");}
rs.slaveOk = function () { return db.getMongo().setSlaveOk(); }
rs.status = function () { return db._adminCommand("replSetGetStatus"); }
rs.isMaster = function () { return db.isMaster(); }
rs.initiate = function (c) { return db._adminCommand({ replSetInitiate: c }); }
rs.add = function (hostport, arb) {
var cfg = hostport;
var local = db.getSisterDB("local");
assert(local.system.replset.count() <= 1, "error: local.system.replset has unexpected contents");
var c = local.system.replset.findOne();
assert(c, "no config object retrievable from local.system.replset");
c.version++;
var max = 0;
for (var i in c.members)
if (c.members[i]._id > max) max = c.members[i]._id;
if (isString(hostport)) {
cfg = { _id: max + 1, host: hostport };
if (arb)
cfg.arbiterOnly = true;}
c.members.push(cfg);
return db._adminCommand({ replSetReconfig: c });}
rs.stepDown = function () { return db._adminCommand({ replSetStepDown:true}); }
rs.addArb = function (hn) { return this.add(hn, true); }
rs.conf = function () { return db.getSisterDB("local").system.replset.findOne(); }
help = shellHelper.help = function (x) {
if (x == "connect") {
print("\nNormally one specifies the server on the mongo shell command line.  Run mongo --help to see those options.");
print("Additional connections may be opened:\n");
print("    var x = new Mongo('host[:port]');");
print("    var mydb = x.getDB('mydb');");
print("  or");
print("    var mydb = connect('host[:port]/mydb');");
print("\nNote: the REPL prompt only auto-reports getLastError() for the shell command line connection.\n");
return;}
if (x == "misc") {
print("\tb = new BinData(subtype,base64str)  create a BSON BinData value");
print("\tb.subtype()                         the BinData subtype (0..255)");
print("\tb.length()                          length of the BinData data in bytes");
print("\tb.hex()                             the data as a hex encoded string");
print("\tb.base64()                          the data as a base 64 encoded string");
print("\tb.toString()");
return;}
if (x == "admin") {
print("\tls([path])                      list files");
print("\tpwd()                           returns current directory");
print("\tlistFiles([path])               returns file list");
print("\thostname()                      returns name of this host");
print("\tcat(fname)                      returns contents of text file as a string");
print("\tremoveFile(f)                   delete a file");
print("\tload(jsfilename)                load and execute a .js file");
print("\trun(program[, args...])         spawn a program and wait for its completion");
print("\tsleep(m)                        sleep m milliseconds");
print("\tgetMemInfo()                    diagnostic");
return;}
if (x == "test") {
print("\tstartMongodEmpty(args)        DELETES DATA DIR and then starts mongod");
print("\t                              returns a connection to the new server");
print("\tstartMongodTest()             DELETES DATA DIR");
print("\t                              automatically picks port #s starting at 27000 and increasing");
print("\t                              or you can specify the port as the first arg");
print("\t                              dir is /data/db/<port>/ if not specified as the 2nd arg");
print("\t                              returns a connection to the new server");
return;}
print("\t" + "db.help()                    help on db methods");
print("\t" + "db.mycoll.help()             help on collection methods");
print("\t" + "rs.help()                    help on replica set methods");
print("\t" + "help connect                 connecting to a db help");
print("\t" + "help admin                   administrative help");
print("\t" + "help misc                    misc things to know");
print();
print("\t" + "show dbs                     show database names");
print("\t" + "show collections             show collections in current database");
print("\t" + "show users                   show users in current database");
print("\t" + "show profile                 show most recent system.profile entries with time >= 1ms");
print("\t" + "use <db_name>                set current database");
print("\t" + "db.foo.find()                list objects in collection foo");
print("\t" + "db.foo.find( { a : 1 } )     list objects in foo where a == 1");
print("\t" + "it                           result of the last line evaluated; use to further iterate");
print("\t" + "exit                         quit the mongo shell");}
if ( typeof DB == "undefined" ){
DB = function( mongo , name ){
this._mongo = mongo;
this._name = name;}}
DB.prototype.getMongo = function(){
assert( this._mongo , "why no mongo!" );
return this._mongo;}
DB.prototype.getSisterDB = function( name ){
return this.getMongo().getDB( name );}
DB.prototype.getName = function(){
return this._name;}
DB.prototype.stats = function(){
return this.runCommand( { dbstats : 1 } );}
DB.prototype.getCollection = function( name ){
return new DBCollection( this._mongo , this , name , this._name + "." + name );}
DB.prototype.commandHelp = function( name ){
var c = {};
c[name] = 1;
c.help = true;
return this.runCommand( c ).help;}
DB.prototype.runCommand = function( obj ){
if ( typeof( obj ) == "string" ){
var n = {};
n[obj] = 1;
obj = n;}
return this.getCollection( "$cmd" ).findOne( obj );}
DB.prototype._dbCommand = DB.prototype.runCommand;
DB.prototype._adminCommand = function( obj ){
if ( this._name == "admin" )
return this.runCommand( obj );
return this.getSisterDB( "admin" ).runCommand( obj );}
DB.prototype.addUser = function( username , pass, readOnly ){
readOnly = readOnly || false;
var c = this.getCollection( "system.users" );
var u = c.findOne( { user : username } ) || { user : username };
u.readOnly = readOnly;
u.pwd = hex_md5( username + ":mongo:" + pass );
print( tojson( u ) );
c.save( u );}
DB.prototype.removeUser = function( username ){
this.getCollection( "system.users" ).remove( { user : username } );}
DB.prototype.__pwHash = function( nonce, username, pass ) {
return hex_md5( nonce + username + hex_md5( username + ":mongo:" + pass ) );}
DB.prototype.auth = function( username , pass ){
var n = this.runCommand( { getnonce : 1 } );
var a = this.runCommand(
{
authenticate : 1 ,
user : username ,
nonce : n.nonce ,
key : this.__pwHash( n.nonce, username, pass )}
);
return a.ok;}

DB.prototype.createCollection = function(name, opt) {
var options = opt || {};
var cmd = { create: name, capped: options.capped, size: options.size, max: options.max };
var res = this._dbCommand(cmd);
return res;}

DB.prototype.getProfilingLevel  = function() {
var res = this._dbCommand( { profile: -1 } );
return res ? res.was : null;}

DB.prototype.dropDatabase = function() {
if ( arguments.length )
throw "dropDatabase doesn't take arguments";
return this._dbCommand( { dropDatabase: 1 } );}
DB.prototype.shutdownServer = function() {
if( "admin" != this._name ){
return "shutdown command only works with the admin database; try 'use admin'";}
try {
var res = this._dbCommand("shutdown");
if( res )
throw "shutdownServer failed: " + res.errmsg;
throw "shutdownServer failed";}
catch ( e ){
assert( tojson( e ).indexOf( "error doing query: failed" ) >= 0 , "unexpected error: " + tojson( e ) );
print( "server should be down..." );}}

DB.prototype.cloneDatabase = function(from) {
assert( isString(from) && from.length );
return this._dbCommand( { clone: from } );}

DB.prototype.cloneCollection = function(from, collection, query) {
assert( isString(from) && from.length );
assert( isString(collection) && collection.length );
collection = this._name + "." + collection;
query = query || {};
return this._dbCommand( { cloneCollection:collection, from:from, query:query } );}

DB.prototype.copyDatabase = function(fromdb, todb, fromhost, username, password) {
assert( isString(fromdb) && fromdb.length );
assert( isString(todb) && todb.length );
fromhost = fromhost || "";
if ( username && password ) {
var n = this._adminCommand( { copydbgetnonce : 1, fromhost:fromhost } );
return this._adminCommand( { copydb:1, fromhost:fromhost, fromdb:fromdb, todb:todb, username:username, nonce:n.nonce, key:this.__pwHash( n.nonce, username, password ) } );
} else {
return this._adminCommand( { copydb:1, fromhost:fromhost, fromdb:fromdb, todb:todb } );}}

DB.prototype.repairDatabase = function() {
return this._dbCommand( { repairDatabase: 1 } );}
DB.prototype.help = function() {
print("DB methods:");
print("\tdb.addUser(username, password[, readOnly=false])");
print("\tdb.auth(username, password)");
print("\tdb.cloneDatabase(fromhost)");
print("\tdb.commandHelp(name) returns the help for the command");
print("\tdb.copyDatabase(fromdb, todb, fromhost)");
print("\tdb.createCollection(name, { size : ..., capped : ..., max : ... } )");
print("\tdb.currentOp() displays the current operation in the db");
print("\tdb.dropDatabase()");
print("\tdb.eval(func, args) run code server-side");
print("\tdb.getCollection(cname) same as db['cname'] or db.cname");
print("\tdb.getCollectionNames()");
print("\tdb.getLastError() - just returns the err msg string");
print("\tdb.getLastErrorObj() - return full status object");
print("\tdb.getMongo() get the server connection object");
print("\tdb.getMongo().setSlaveOk() allow this connection to read from the nonmaster member of a replica pair");
print("\tdb.getName()");
print("\tdb.getPrevError()");
print("\tdb.getProfilingLevel()");
print("\tdb.getReplicationInfo()");
print("\tdb.getSisterDB(name) get the db at the same server as this one");
print("\tdb.isMaster() check replica primary status");
print("\tdb.killOp(opid) kills the current operation in the db");
print("\tdb.listCommands() lists all the db commands");
print("\tdb.printCollectionStats()");
print("\tdb.printReplicationInfo()");
print("\tdb.printSlaveReplicationInfo()");
print("\tdb.printShardingStatus()");
print("\tdb.removeUser(username)");
print("\tdb.repairDatabase()");
print("\tdb.resetError()");
print("\tdb.runCommand(cmdObj) run a database command.  if cmdObj is a string, turns it into { cmdObj : 1 }");
print("\tdb.serverStatus()");
print("\tdb.setProfilingLevel(level,<slowms>) 0=off 1=slow 2=all");
print("\tdb.shutdownServer()");
print("\tdb.stats()");
print("\tdb.version() current version of the server");
print("\tdb.getMongo().setSlaveOk() allow queries on a replication slave server");
return __magicNoPrint;}
DB.prototype.printCollectionStats = function(){
var mydb = this;
this.getCollectionNames().forEach(
function(z){
print( z );
printjson( mydb.getCollection(z).stats() );
print( "---" );}
);}

DB.prototype.setProfilingLevel = function(level,slowms) {
if (level < 0 || level > 2) {
throw { dbSetProfilingException : "input level " + level + " is out of range [0..2]" };}
var cmd = { profile: level };
if ( slowms )
cmd["slowms"] = slowms;
return this._dbCommand( cmd );}

DB.prototype.eval = function(jsfunction) {
var cmd = { $eval : jsfunction };
if ( arguments.length > 1 ) {
cmd.args = argumentsToArray( arguments ).slice(1);}
var res = this._dbCommand( cmd );
if (!res.ok)
throw tojson( res );
return res.retval;}
DB.prototype.dbEval = DB.prototype.eval;

DB.prototype.groupeval = function(parmsObj) {
var groupFunction = function() {
var parms = args[0];
var c = db[parms.ns].find(parms.cond||{});
var map = new Map();
var pks = parms.key ? Object.keySet( parms.key ) : null;
var pkl = pks ? pks.length : 0;
var key = {};
while( c.hasNext() ) {
var obj = c.next();
if ( pks ) {
for( var i=0; i<pkl; i++ ){
var k = pks[i];
key[k] = obj[k];}}
else {
key = parms.$keyf(obj);}
var aggObj = map.get(key);
if( aggObj == null ) {
var newObj = Object.extend({}, key);
aggObj = Object.extend(newObj, parms.initial)
map.put( key , aggObj );}
parms.$reduce(obj, aggObj);}
return map.values();}
return this.eval(groupFunction, this._groupFixParms( parmsObj ));}
DB.prototype.groupcmd = function( parmsObj ){
var ret = this.runCommand( { "group" : this._groupFixParms( parmsObj ) } );
if ( ! ret.ok ){
throw "group command failed: " + tojson( ret );}
return ret.retval;}
DB.prototype.group = DB.prototype.groupcmd;
DB.prototype._groupFixParms = function( parmsObj ){
var parms = Object.extend({}, parmsObj);
if( parms.reduce ) {
parms.$reduce = parms.reduce;
delete parms.reduce;}
if( parms.keyf ) {
parms.$keyf = parms.keyf;
delete parms.keyf;}
return parms;}
DB.prototype.resetError = function(){
return this.runCommand( { reseterror : 1 } );}
DB.prototype.forceError = function(){
return this.runCommand( { forceerror : 1 } );}
DB.prototype.getLastError = function( w , wtimeout ){
var res = this.getLastErrorObj( w , wtimeout );
if ( ! res.ok )
throw "getlasterror failed: " + tojson( res );
return res.err;}
DB.prototype.getLastErrorObj = function( w , wtimeout ){
var cmd = { getlasterror : 1 };
if ( w ){
cmd.w = w;
if ( wtimeout )
cmd.wtimeout = wtimeout;}
var res = this.runCommand( cmd );
if ( ! res.ok )
throw "getlasterror failed: " + tojson( res );
return res;}
DB.prototype.getLastErrorCmd = DB.prototype.getLastErrorObj;
/* Return the last error which has occurred, even if not the very last error.
Returns:
{ err : <error message>, nPrev : <how_many_ops_back_occurred>, ok : 1 }
result.err will be null if no error has occurred.
*/
DB.prototype.getPrevError = function(){
return this.runCommand( { getpreverror : 1 } );}
DB.prototype.getCollectionNames = function(){
var all = [];
var nsLength = this._name.length + 1;
var c = this.getCollection( "system.namespaces" ).find();
while ( c.hasNext() ){
var name = c.next().name;
if ( name.indexOf( "$" ) >= 0 && name.indexOf( ".oplog.$" ) < 0 )
continue;
all.push( name.substring( nsLength ) );}
return all.sort();}
DB.prototype.tojson = function(){
return this._name;}
DB.prototype.toString = function(){
return this._name;}
DB.prototype.isMaster = function () { return this.runCommand("isMaster"); }
DB.prototype.currentOp = function(){
return db.$cmd.sys.inprog.findOne();}
DB.prototype.currentOP = DB.prototype.currentOp;
DB.prototype.killOp = function(op) {
if( !op )
throw "no opNum to kill specified";
return db.$cmd.sys.killop.findOne({'op':op});}
DB.prototype.killOP = DB.prototype.killOp;
DB.tsToSeconds = function(x){
if ( x.t && x.i )
return x.t / 1000;
return x / 4294967296;}

DB.prototype.getReplicationInfo = function() {
var db = this.getSisterDB("local");
var result = { };
var ol = db.system.namespaces.findOne({name:"local.oplog.$main"});
if( ol && ol.options ) {
result.logSizeMB = ol.options.size / 1000 / 1000;
} else {
result.errmsg  = "local.oplog.$main, or its options, not found in system.namespaces collection (not --master?)";
return result;}
var firstc = db.oplog.$main.find().sort({$natural:1}).limit(1);
var lastc = db.oplog.$main.find().sort({$natural:-1}).limit(1);
if( !firstc.hasNext() || !lastc.hasNext() ) {
result.errmsg = "objects not found in local.oplog.$main -- is this a new and empty db instance?";
result.oplogMainRowCount = db.oplog.$main.count();
return result;}
var first = firstc.next();
var last = lastc.next();
{
var tfirst = first.ts;
var tlast = last.ts;
if( tfirst && tlast ) {
tfirst = DB.tsToSeconds( tfirst );
tlast = DB.tsToSeconds( tlast );
result.timeDiff = tlast - tfirst;
result.timeDiffHours = Math.round(result.timeDiff / 36)/100;
result.tFirst = (new Date(tfirst*1000)).toString();
result.tLast  = (new Date(tlast*1000)).toString();
result.now = Date();}
else {
result.errmsg = "ts element not found in oplog objects";}}
return result;}
DB.prototype.printReplicationInfo = function() {
var result = this.getReplicationInfo();
if( result.errmsg ) {
print(tojson(result));
return;}
print("configured oplog size:   " + result.logSizeMB + "MB");
print("log length start to end: " + result.timeDiff + "secs (" + result.timeDiffHours + "hrs)");
print("oplog first event time:  " + result.tFirst);
print("oplog last event time:   " + result.tLast);
print("now:                     " + result.now);}
DB.prototype.printSlaveReplicationInfo = function() {
function g(x) {
assert( x , "how could this be null (printSlaveReplicationInfo gx)" )
print("source:   " + x.host);
if ( x.syncedTo ){
var st = new Date( DB.tsToSeconds( x.syncedTo ) * 1000 );
var now = new Date();
print("\t syncedTo: " + st.toString() );
var ago = (now-st)/1000;
var hrs = Math.round(ago/36)/100;
print("\t\t = " + Math.round(ago) + "secs ago (" + hrs + "hrs)");}
else {
print( "\t doing initial sync" );}}
var L = this.getSisterDB("local");
if( L.sources.count() == 0 ) {
print("local.sources is empty; is this db a --slave?");
return;}
L.sources.find().forEach(g);}
DB.prototype.serverBuildInfo = function(){
return this._adminCommand( "buildinfo" );}
DB.prototype.serverStatus = function(){
return this._adminCommand( "serverStatus" );}
DB.prototype.serverCmdLineOpts = function(){
return this._adminCommand( "getCmdLineOpts" );}
DB.prototype.version = function(){
return this.serverBuildInfo().version;}
DB.prototype.listCommands = function(){
var x = this.runCommand( "listCommands" );
for ( var name in x.commands ){
var c = x.commands[name];
var s = name + ": ";
switch ( c.lockType ){
case -1: s += "read-lock"; break;
case  0: s += "no-lock"; break;
case  1: s += "write-lock"; break;
default: s += c.lockType;}
if (c.adminOnly) s += " adminOnly ";
if (c.adminOnly) s += " slaveOk ";
s += "\n  ";
s += c.help.replace(/\n/g, '\n  ');
s += "\n";
print( s );}}
DB.prototype.printShardingStatus = function(){
printShardingStatus( this.getSisterDB( "config" ) );}
if ( typeof Mongo == "undefined" ){
Mongo = function( host ){
this.init( host );}}
if ( ! Mongo.prototype ){
throw "Mongo.prototype not defined";}
if ( ! Mongo.prototype.find )
Mongo.prototype.find = function( ns , query , fields , limit , skip ){ throw "find not implemented"; }
if ( ! Mongo.prototype.insert )
Mongo.prototype.insert = function( ns , obj ){ throw "insert not implemented"; }
if ( ! Mongo.prototype.remove )
Mongo.prototype.remove = function( ns , pattern ){ throw "remove not implemented;" }
if ( ! Mongo.prototype.update )
Mongo.prototype.update = function( ns , query , obj , upsert ){ throw "update not implemented;" }
if ( typeof mongoInject == "function" ){
mongoInject( Mongo.prototype );}
Mongo.prototype.setSlaveOk = function() {
this.slaveOk = true;}
Mongo.prototype.getDB = function( name ){
return new DB( this , name );}
Mongo.prototype.getDBs = function(){
var res = this.getDB( "admin" ).runCommand( { "listDatabases" : 1 } );
assert( res.ok == 1 , "listDatabases failed:" + tojson( res ) );
return res;}
Mongo.prototype.getDBNames = function(){
return this.getDBs().databases.map(
function(z){
return z.name;}
);}
Mongo.prototype.getCollection = function(ns){
var idx = ns.indexOf( "." );
if ( idx < 0 )
throw "need . in ns";
var db = ns.substring( 0 , idx );
var c = ns.substring( idx + 1 );
return this.getDB( db ).getCollection( c );}
Mongo.prototype.toString = function(){
return "connection to " + this.host;}
Mongo.prototype.tojson = Mongo.prototype.toString;
connect = function( url , user , pass ){
chatty( "connecting to: " + url )
if ( user && ! pass )
throw "you specified a user and not a password.  either you need a password, or you're using the old connect api";
var idx = url.lastIndexOf( "/" );
var db;
if ( idx < 0 )
db = new Mongo().getDB( url );
else
db = new Mongo( url.substring( 0 , idx ) ).getDB( url.substring( idx + 1 ) );
if ( user && pass ){
if ( ! db.auth( user , pass ) ){
throw "couldn't login";}}
return db;}
MR = {};
MR.init = function(){
$max = 0;
$arr = [];
emit = MR.emit;
$numEmits = 0;
$numReduces = 0;
$numReducesToDB = 0;
gc();}
MR.cleanup = function(){
MR.init();
gc();}
MR.emit = function(k,v){
$numEmits++;
var num = nativeHelper.apply( get_num_ , [ k ] );
var data = $arr[num];
if ( ! data ){
data = { key : k , values : new Array(1000) , count : 0 };
$arr[num] = data;}
data.values[data.count++] = v;
$max = Math.max( $max , data.count );}
MR.doReduce = function( useDB ){
$numReduces++;
if ( useDB )
$numReducesToDB++;
$max = 0;
for ( var i=0; i<$arr.length; i++){
var data = $arr[i];
if ( ! data )
continue;
if ( useDB ){
var x = tempcoll.findOne( { _id : data.key } );
if ( x ){
data.values[data.count++] = x.value;}}
var r = $reduce( data.key , data.values.slice( 0 , data.count ) );
if ( r && r.length && r[0] ){
data.values = r;
data.count = r.length;}
else{
data.values[0] = r;
data.count = 1;}
$max = Math.max( $max , data.count );
if ( useDB ){
if ( data.count == 1 ){
tempcoll.save( { _id : data.key , value : data.values[0] } );}
else {
tempcoll.save( { _id : data.key , value : data.values.slice( 0 , data.count ) } );}}}}
MR.check = function(){
if ( $max < 2000 && $arr.length < 1000 ){
return 0;}
MR.doReduce();
if ( $max < 2000 && $arr.length < 1000 ){
return 1;}
MR.doReduce( true );
$arr = [];
$max = 0;
reset_num();
gc();
return 2;}
MR.finalize = function(){
tempcoll.find().forEach(
function(z){
z.value = $finalize( z._id , z.value );
tempcoll.save( z );}
);}
if ( typeof DBQuery == "undefined" ){
DBQuery = function( mongo , db , collection , ns , query , fields , limit , skip , batchSize ){
this._mongo = mongo;
this._db = db;
this._collection = collection;
this._ns = ns;
this._query = query || {};
this._fields = fields;
this._limit = limit || 0;
this._skip = skip || 0;
this._batchSize = batchSize || 0;
this._cursor = null;
this._numReturned = 0;
this._special = false;
this._prettyShell = false;}
print( "DBQuery probably won't have array access " );}
DBQuery.prototype.help = function () {
print("find() modifiers")
print("\t.sort( {...} )")
print("\t.limit( n )")
print("\t.skip( n )")
print("\t.count() - total # of objects matching query, ignores skip,limit")
print("\t.size() - total # of objects cursor would return, honors skip,limit")
print("\t.explain([verbose])")
print("\t.hint(...)")
print("\t.showDiskLoc() - adds a $diskLoc field to each returned object")
print("\nCursor methods");
print("\t.forEach( func )")
print("\t.print() - output to console in full pretty format")
print("\t.map( func )")
print("\t.hasNext()")
print("\t.next()")}
DBQuery.prototype.clone = function(){
var q =  new DBQuery( this._mongo , this._db , this._collection , this._ns ,
this._query , this._fields ,
this._limit , this._skip , this._batchSize );
q._special = this._special;
return q;}
DBQuery.prototype._ensureSpecial = function(){
if ( this._special )
return;
var n = { query : this._query };
this._query = n;
this._special = true;}
DBQuery.prototype._checkModify = function(){
if ( this._cursor )
throw "query already executed";}
DBQuery.prototype._exec = function(){
if ( ! this._cursor ){
assert.eq( 0 , this._numReturned );
this._cursor = this._mongo.find( this._ns , this._query , this._fields , this._limit , this._skip , this._batchSize );
this._cursorSeen = 0;}
return this._cursor;}
DBQuery.prototype.limit = function( limit ){
this._checkModify();
this._limit = limit;
return this;}
DBQuery.prototype.batchSize = function( batchSize ){
this._checkModify();
this._batchSize = batchSize;
return this;}
DBQuery.prototype.skip = function( skip ){
this._checkModify();
this._skip = skip;
return this;}
DBQuery.prototype.hasNext = function(){
this._exec();
if ( this._limit > 0 && this._cursorSeen >= this._limit )
return false;
var o = this._cursor.hasNext();
return o;}
DBQuery.prototype.next = function(){
this._exec();
var o = this._cursor.hasNext();
if ( o )
this._cursorSeen++;
else
throw "error hasNext: " + o;
var ret = this._cursor.next();
if ( ret.$err && this._numReturned == 0 && ! this.hasNext() )
throw "error: " + tojson( ret );
this._numReturned++;
return ret;}
DBQuery.prototype.objsLeftInBatch = function(){
this._exec();
var ret = this._cursor.objsLeftInBatch();
if ( ret.$err )
throw "error: " + tojson( ret );
return ret;}
DBQuery.prototype.toArray = function(){
if ( this._arr )
return this._arr;
var a = [];
while ( this.hasNext() )
a.push( this.next() );
this._arr = a;
return a;}
DBQuery.prototype.count = function( applySkipLimit ){
var cmd = { count: this._collection.getName() };
if ( this._query ){
if ( this._special )
cmd.query = this._query.query;
else
cmd.query = this._query;}
cmd.fields = this._fields || {};
if ( applySkipLimit ){
if ( this._limit )
cmd.limit = this._limit;
if ( this._skip )
cmd.skip = this._skip;}
var res = this._db.runCommand( cmd );
if( res && res.n != null ) return res.n;
throw "count failed: " + tojson( res );}
DBQuery.prototype.size = function(){
return this.count( true );}
DBQuery.prototype.countReturn = function(){
var c = this.count();
if ( this._skip )
c = c - this._skip;
if ( this._limit > 0 && this._limit < c )
return this._limit;
return c;}

DBQuery.prototype.itcount = function(){
var num = 0;
while ( this.hasNext() ){
num++;
this.next();}
return num;}
DBQuery.prototype.length = function(){
return this.toArray().length;}
DBQuery.prototype._addSpecial = function( name , value ){
this._ensureSpecial();
this._query[name] = value;
return this;}
DBQuery.prototype.sort = function( sortBy ){
return this._addSpecial( "orderby" , sortBy );}
DBQuery.prototype.hint = function( hint ){
return this._addSpecial( "$hint" , hint );}
DBQuery.prototype.min = function( min ) {
return this._addSpecial( "$min" , min );}
DBQuery.prototype.max = function( max ) {
return this._addSpecial( "$max" , max );}
DBQuery.prototype.showDiskLoc = function() {
return this._addSpecial( "$showDiskLoc" , true);}
DBQuery.prototype.forEach = function( func ){
while ( this.hasNext() )
func( this.next() );}
DBQuery.prototype.map = function( func ){
var a = [];
while ( this.hasNext() )
a.push( func( this.next() ) );
return a;}
DBQuery.prototype.arrayAccess = function( idx ){
return this.toArray()[idx];}
DBQuery.prototype.explain = function (verbose) {
/* verbose=true --> include allPlans, oldPlan fields */
var n = this.clone();
n._ensureSpecial();
n._query.$explain = true;
n._limit = n._limit * -1;
var e = n.next();
if (!verbose) {
delete e.allPlans;
delete e.oldPlan;
if (e.shards){
for (var key in e.shards){
var s = e.shards[key];
if(s.length === undefined){
delete s.allPlans;
delete s.oldPlan;
} else {
for (var i=0; i < s.length; i++){
delete s[i].allPlans;
delete s[i].oldPlan;}}}}}
return e;}
DBQuery.prototype.snapshot = function(){
this._ensureSpecial();
this._query.$snapshot = true;
return this;}
DBQuery.prototype.pretty = function(){
this._prettyShell = true;
return this;}
DBQuery.prototype.shellPrint = function(){
try {
var n = 0;
while ( this.hasNext() && n < DBQuery.shellBatchSize ){
var s = this._prettyShell ? tojson( this.next() ) : tojson( this.next() , "" , true );
print( s );
n++;}
if ( this.hasNext() ){
print( "has more" );
___it___  = this;}
else {
___it___  = null;}}
catch ( e ){
print( e );}}
DBQuery.prototype.toString = function(){
return "DBQuery: " + this._ns + " -> " + tojson( this.query );}
DBQuery.shellBatchSize = 20;
// or db["colName"]
if ( ( typeof  DBCollection ) == "undefined" ){
DBCollection = function( mongo , db , shortName , fullName ){
this._mongo = mongo;
this._db = db;
this._shortName = shortName;
this._fullName = fullName;
this.verify();}}
DBCollection.prototype.verify = function(){
assert( this._fullName , "no fullName" );
assert( this._shortName , "no shortName" );
assert( this._db , "no db" );
assert.eq( this._fullName , this._db._name + "." + this._shortName , "name mismatch" );
assert( this._mongo , "no mongo in DBCollection" );}
DBCollection.prototype.getName = function(){
return this._shortName;}
DBCollection.prototype.help = function () {
var shortName = this.getName();
print("DBCollection help");
print("\tdb." + shortName + ".find().help() - show DBCursor help");
print("\tdb." + shortName + ".count()");
print("\tdb." + shortName + ".dataSize()");
print("\tdb." + shortName + ".distinct( key ) - eg. db." + shortName + ".distinct( 'x' )");
print("\tdb." + shortName + ".drop() drop the collection");
print("\tdb." + shortName + ".dropIndex(name)");
print("\tdb." + shortName + ".dropIndexes()");
print("\tdb." + shortName + ".ensureIndex(keypattern,options) - options should be an object with these possible fields: name, unique, dropDups");
print("\tdb." + shortName + ".reIndex()");
print("\tdb." + shortName + ".find( [query] , [fields]) - first parameter is an optional query filter. second parameter is optional set of fields to return.");
print("\t                                   e.g. db." + shortName + ".find( { x : 77 } , { name : 1 , x : 1 } )");
print("\tdb." + shortName + ".find(...).count()");
print("\tdb." + shortName + ".find(...).limit(n)");
print("\tdb." + shortName + ".find(...).skip(n)");
print("\tdb." + shortName + ".find(...).sort(...)");
print("\tdb." + shortName + ".findOne([query])");
print("\tdb." + shortName + ".findAndModify( { update : ... , remove : bool [, query: {}, sort: {}, 'new': false] } )");
print("\tdb." + shortName + ".getDB() get DB object associated with collection");
print("\tdb." + shortName + ".getIndexes()");
print("\tdb." + shortName + ".group( { key : ..., initial: ..., reduce : ...[, cond: ...] } )");
print("\tdb." + shortName + ".mapReduce( mapFunction , reduceFunction , <optional params> )");
print("\tdb." + shortName + ".remove(query)");
print("\tdb." + shortName + ".renameCollection( newName , <dropTarget> ) renames the collection.");
print("\tdb." + shortName + ".runCommand( name , <options> ) runs a db command with the given name where the first param is the collection name");
print("\tdb." + shortName + ".save(obj)");
print("\tdb." + shortName + ".stats()");
print("\tdb." + shortName + ".storageSize() - includes free space allocated to this collection");
print("\tdb." + shortName + ".totalIndexSize() - size in bytes of all the indexes");
print("\tdb." + shortName + ".totalSize() - storage allocated for all data and indexes");
print("\tdb." + shortName + ".update(query, object[, upsert_bool, multi_bool])");
print("\tdb." + shortName + ".validate() - SLOW");
print("\tdb." + shortName + ".getShardVersion() - only for use with sharding");
return __magicNoPrint;}
DBCollection.prototype.getFullName = function(){
return this._fullName;}
DBCollection.prototype.getDB = function(){
return this._db;}
DBCollection.prototype._dbCommand = function( cmd , params ){
if ( typeof( cmd ) == "object" )
return this._db._dbCommand( cmd );
var c = {};
c[cmd] = this.getName();
if ( params )
Object.extend( c , params );
return this._db._dbCommand( c );}
DBCollection.prototype.runCommand = DBCollection.prototype._dbCommand;
DBCollection.prototype._massageObject = function( q ){
if ( ! q )
return {};
var type = typeof q;
if ( type == "function" )
return { $where : q };
if ( q.isObjectId )
return { _id : q };
if ( type == "object" )
return q;
if ( type == "string" ){
if ( q.length == 24 )
return { _id : q };
return { $where : q };}
throw "don't know how to massage : " + type;}
DBCollection.prototype._validateObject = function( o ){
if ( o._ensureSpecial && o._checkModify )
throw "can't save a DBQuery object";}
DBCollection._allowedFields = { $id : 1 , $ref : 1 };
DBCollection.prototype._validateForStorage = function( o ){
this._validateObject( o );
for ( var k in o ){
if ( k.indexOf( "." ) >= 0 ) {
throw "can't have . in field names [" + k + "]" ;}
if ( k.indexOf( "$" ) == 0 && ! DBCollection._allowedFields[k] ) {
throw "field names cannot start with $ [" + k + "]";}
if ( o[k] !== null && typeof( o[k] ) === "object" ) {
this._validateForStorage( o[k] );}}
};
DBCollection.prototype.find = function( query , fields , limit , skip ){
return new DBQuery( this._mongo , this._db , this ,
this._fullName , this._massageObject( query ) , fields , limit , skip );}
DBCollection.prototype.findOne = function( query , fields ){
var cursor = this._mongo.find( this._fullName , this._massageObject( query ) || {} , fields , -1 , 0 , 0 );
if ( ! cursor.hasNext() )
return null;
var ret = cursor.next();
if ( cursor.hasNext() ) throw "findOne has more than 1 result!";
if ( ret.$err )
throw "error " + tojson( ret );
return ret;}
DBCollection.prototype.insert = function( obj , _allow_dot ){
if ( ! obj )
throw "no object passed to insert!";
if ( ! _allow_dot ) {
this._validateForStorage( obj );}
if ( typeof( obj._id ) == "undefined" ){
var tmp = obj;
obj = {_id: new ObjectId()};
for (var key in tmp){
obj[key] = tmp[key];}}
this._mongo.insert( this._fullName , obj );
this._lastID = obj._id;}
DBCollection.prototype.remove = function( t ){
this._mongo.remove( this._fullName , this._massageObject( t ) );}
DBCollection.prototype.update = function( query , obj , upsert , multi ){
assert( query , "need a query" );
assert( obj , "need an object" );
this._validateObject( obj );
this._mongo.update( this._fullName , query , obj , upsert ? true : false , multi ? true : false );}
DBCollection.prototype.save = function( obj ){
if ( obj == null || typeof( obj ) == "undefined" )
throw "can't save a null";
if ( typeof( obj._id ) == "undefined" ){
obj._id = new ObjectId();
return this.insert( obj );}
else {
return this.update( { _id : obj._id } , obj , true );}}
DBCollection.prototype._genIndexName = function( keys ){
var name = "";
for ( var k in keys ){
var v = keys[k];
if ( typeof v == "function" )
continue;
if ( name.length > 0 )
name += "_";
name += k + "_";
if ( typeof v == "number" )
name += v;}
return name;}
DBCollection.prototype._indexSpec = function( keys, options ) {
var ret = { ns : this._fullName , key : keys , name : this._genIndexName( keys ) };
if ( ! options ){}
else if ( typeof ( options ) == "string" )
ret.name = options;
else if ( typeof ( options ) == "boolean" )
ret.unique = true;
else if ( typeof ( options ) == "object" ){
if ( options.length ){
var nb = 0;
for ( var i=0; i<options.length; i++ ){
if ( typeof ( options[i] ) == "string" )
ret.name = options[i];
else if ( typeof( options[i] ) == "boolean" ){
if ( options[i] ){
if ( nb == 0 )
ret.unique = true;
if ( nb == 1 )
ret.dropDups = true;}
nb++;}}}
else {
Object.extend( ret , options );}}
else {
throw "can't handle: " + typeof( options );}
/*
return ret;
var name;
var nTrue = 0;
if ( ! isObject( options ) ) {
options = [ options ];}
if ( options.length ){
for( var i = 0; i < options.length; ++i ) {
var o = options[ i ];
if ( isString( o ) ) {
ret.name = o;
} else if ( typeof( o ) == "boolean" ) {
if ( o ) {
++nTrue;}}}
if ( nTrue > 0 ) {
ret.unique = true;}
if ( nTrue > 1 ) {
ret.dropDups = true;}}
*/
return ret;}
DBCollection.prototype.createIndex = function( keys , options ){
var o = this._indexSpec( keys, options );
this._db.getCollection( "system.indexes" ).insert( o , true );}
DBCollection.prototype.ensureIndex = function( keys , options ){
var name = this._indexSpec( keys, options ).name;
this._indexCache = this._indexCache || {};
if ( this._indexCache[ name ] ){
return;}
this.createIndex( keys , options );
if ( this.getDB().getLastError() == "" ) {
this._indexCache[name] = true;}}
DBCollection.prototype.resetIndexCache = function(){
this._indexCache = {};}
DBCollection.prototype.reIndex = function() {
return this._db.runCommand({ reIndex: this.getName() });}
DBCollection.prototype.dropIndexes = function(){
this.resetIndexCache();
var res = this._db.runCommand( { deleteIndexes: this.getName(), index: "*" } );
assert( res , "no result from dropIndex result" );
if ( res.ok )
return res;
if ( res.errmsg.match( /not found/ ) )
return res;
throw "error dropping indexes : " + tojson( res );}
DBCollection.prototype.drop = function(){
this.resetIndexCache();
var ret = this._db.runCommand( { drop: this.getName() } );
if ( ! ret.ok ){
if ( ret.errmsg == "ns not found" )
return false;
throw "drop failed: " + tojson( ret );}
return true;}
DBCollection.prototype.findAndModify = function(args){
var cmd = { findandmodify: this.getName() };
for (var key in args){
cmd[key] = args[key];}
var ret = this._db.runCommand( cmd );
if ( ! ret.ok ){
if (ret.errmsg == "No matching object found"){
return null;}
throw "findAndModifyFailed failed: " + tojson( ret.errmsg );}
return ret.value;}
DBCollection.prototype.renameCollection = function( newName , dropTarget ){
return this._db._adminCommand( { renameCollection : this._fullName ,
to : this._db._name + "." + newName ,
dropTarget : dropTarget } )}
DBCollection.prototype.validate = function() {
var res = this._db.runCommand( { validate: this.getName() } );
res.valid = false;
var raw = res.result || res.raw;
if ( raw ){
var str = "-" + tojson( raw );
res.valid = ! ( str.match( /exception/ ) || str.match( /corrupt/ ) );
var p = /lastExtentSize:(\d+)/;
var r = p.exec( str );
if ( r ){
res.lastExtentSize = Number( r[1] );}}
return res;}
DBCollection.prototype.getShardVersion = function(){
return this._db._adminCommand( { getShardVersion : this._fullName } );}
DBCollection.prototype.getIndexes = function(){
return this.getDB().getCollection( "system.indexes" ).find( { ns : this.getFullName() } ).toArray();}
DBCollection.prototype.getIndices = DBCollection.prototype.getIndexes;
DBCollection.prototype.getIndexSpecs = DBCollection.prototype.getIndexes;
DBCollection.prototype.getIndexKeys = function(){
return this.getIndexes().map(
function(i){
return i.key;}
);}
DBCollection.prototype.count = function( x ){
return this.find( x ).count();}

DBCollection.prototype.clean = function() {
return this._dbCommand( { clean: this.getName() } );}

DBCollection.prototype.dropIndex =  function(index) {
assert(index , "need to specify index to dropIndex" );
if ( ! isString( index ) && isObject( index ) )
index = this._genIndexName( index );
var res = this._dbCommand( "deleteIndexes" ,{ index: index } );
this.resetIndexCache();
return res;}
DBCollection.prototype.copyTo = function( newName ){
return this.getDB().eval(
function( collName , newName ){
var from = db[collName];
var to = db[newName];
to.ensureIndex( { _id : 1 } );
var count = 0;
var cursor = from.find();
while ( cursor.hasNext() ){
var o = cursor.next();
count++;
to.save( o );}
return count;
} , this.getName() , newName
);}
DBCollection.prototype.getCollection = function( subName ){
return this._db.getCollection( this._shortName + "." + subName );}
DBCollection.prototype.stats = function( scale ){
return this._db.runCommand( { collstats : this._shortName , scale : scale } );}
DBCollection.prototype.dataSize = function(){
return this.stats().size;}
DBCollection.prototype.storageSize = function(){
return this.stats().storageSize;}
DBCollection.prototype.totalIndexSize = function( verbose ){
var stats = this.stats();
if (verbose){
for (var ns in stats.indexSizes){
print( ns + "\t" + stats.indexSizes[ns] );}}
return stats.totalIndexSize;}
DBCollection.prototype.totalSize = function(){
var total = this.storageSize();
var mydb = this._db;
var shortName = this._shortName;
this.getIndexes().forEach(
function( spec ){
var coll = mydb.getCollection( shortName + ".$" + spec.name );
var mysize = coll.storageSize();
//print( coll + "\t" + mysize + "\t" + tojson( coll.validate() ) );
total += coll.dataSize();}
);
return total;}
DBCollection.prototype.convertToCapped = function( bytes ){
if ( ! bytes )
throw "have to specify # of bytes";
return this._dbCommand( { convertToCapped : this._shortName , size : bytes } )}
DBCollection.prototype.exists = function(){
return this._db.system.namespaces.findOne( { name : this._fullName } );}
DBCollection.prototype.isCapped = function(){
var e = this.exists();
return ( e && e.options && e.options.capped ) ? true : false;}
DBCollection.prototype.distinct = function( keyString , query ){
var res = this._dbCommand( { distinct : this._shortName , key : keyString , query : query || {} } );
if ( ! res.ok )
throw "distinct failed: " + tojson( res );
return res.values;}
DBCollection.prototype.group = function( params ){
params.ns = this._shortName;
return this._db.group( params );}
DBCollection.prototype.groupcmd = function( params ){
params.ns = this._shortName;
return this._db.groupcmd( params );}
MapReduceResult = function( db , o ){
Object.extend( this , o );
this._o = o;
this._keys = Object.keySet( o );
this._db = db;
this._coll = this._db.getCollection( this.result );}
MapReduceResult.prototype._simpleKeys = function(){
return this._o;}
MapReduceResult.prototype.find = function(){
return DBCollection.prototype.find.apply( this._coll , arguments );}
MapReduceResult.prototype.drop = function(){
return this._coll.drop();}

MapReduceResult.prototype.convertToSingleObject = function(){
var z = {};
this._coll.find().forEach( function(a){ z[a._id] = a.value; } );
return z;}

DBCollection.prototype.mapReduce = function( map , reduce , optional ){
var c = { mapreduce : this._shortName , map : map , reduce : reduce };
if ( optional )
Object.extend( c , optional );
var raw = this._db.runCommand( c );
if ( ! raw.ok )
throw "map reduce failed: " + tojson( raw );
return new MapReduceResult( this._db , raw );}
DBCollection.prototype.toString = function(){
return this.getFullName();}
DBCollection.prototype.toString = function(){
return this.getFullName();}
DBCollection.prototype.tojson = DBCollection.prototype.toString;
DBCollection.prototype.shellPrint = DBCollection.prototype.toString;
                 GCC: (Debian 4.4.4-8) 4.4.5 20100728 (prerelease)  .symtab .strtab .shstrtab .text .data .bss .rodata.str1.8 .rela.data.rel.local .comment .note.GNU-stack                                                                                          @                                      !                     @                                      '                     @                                      ,      2               @       �                            @                     H�                                    ;                      ��             
                    P      0               P�      3                             Y                      ��                                                           ��      i                                                    ��      �          	                 	                      ��                                                                ��                                                                                                                                                                                               mongo.cpp jsconcatcode                       