function detectIE6(){
  var browser = navigator.appName;
  if (browser == "Microsoft Internet Explorer"){
    var b_version = navigator.appVersion;
    var re = /\MSIE\s+(\d\.\d\b)/;
    var res = b_version.match(re);
    if (res[1] <= 6){
      return true;
    }
  }
  return false;
}
Storage = {

    // Flash8 загружается последним и асинхронно, остальные - синхронно
    engines: ["Flash8", "LocalStorage", "userData"],
    //engines: ["LocalStorage"],

    swfUrl: "/storage.swf",

    init: function (onready) {
        // грязный хак :facepalm:
        var engine = 0; 
        if (!FlashDetect.installed) {
            this.engines = ["LocalStorage", "userData"];
            engine--;
        }

        
        if (navigator.userAgent.indexOf("MSIE") >= 0) {

        if (detectIE6()){
            engine = 2
        }else{
            engine = 1
        }
                try {
                    this[this.engines[engine]](function () { Storage.active = true; onready && onready() })
                } catch (e) {                    
                }            
        } else {
            for (var i = 0; i < this.engines.length; i++) {
                try {
                    this[this.engines[i]](function () { Storage.active = true; onready && onready() });
                    break;
                } catch (e) {
                    // uncomment to see errors
                   //console.log(this.engines[i] + ':<' + e.message + '>\n');
                }

            }
        }
    }

}



Storage.LocalStorage = function (onready) {

    var storage = window.localStorage; //globalStorage[location.hostname];

    Storage = {

        put: function (key, value) {
            storage[key] = value
        },

        get: function (key) {
            if (storage[key])
                return String(storage[key]);
            else
                return null;
        },

        remove: function (key) {
            delete storage[key]
        },

        getKeys: function () {
            var list = []
            for (key in storage){
                if (key == 'length')
                    continue;

                list.push(key);
            }
            return list.reverse()
        },
        indexOf: function (key) {
            //return movie.of(key)
            for (i in this.getKeys()) {
                if (key ==  String(storage[i]))
                    return i
            }
            return false
        },
        clear: function () {
            for (i in storage) {
                delete storage[i]
            }            
        }
    }

    onready()
}




Storage.userData = function(onready) {
    var namespace = "data"

    if (!document.body.addBehavior) {            
        throw new Error("No addBehavior available")
    }
        
    var storage = document.getElementById('storageElement')
    if (!storage) {
        storage = document.createElement('span')
        document.body.appendChild(storage)
        storage.addBehavior("#default#userData")
        // initial element load
        storage.load(namespace)
    }
    
    Storage = {
        put: function(key, value) {
            storage.setAttribute(key, value)
            storage.save(namespace)
        },
        
        get: function(key) {
            return storage.getAttribute(key)
        },
        
        remove: function(key) {
            storage.removeAttribute(key)
            storage.save(namespace)
        },
        
        getKeys: function() {
            var list = []
            var attrs = storage.XMLDocument.documentElement.attributes
            
            for(var i=0; i<attrs.length; i++) {
                list.push(attrs[i].name)
            }
            
            return list
        },
        
        clear: function() {
            var attrs = storage.XMLDocument.documentElement.attributes
            
            for(var i=0; i<attrs.length; i++) {
                storage.removeAttribute(attrs[i].name)
            }
            storage.save(namespace)
        }
    }
    
    onready()
    
}


Storage.Flash8 = function (onready) {

    var movie

    var swfId = "StorageMovie"
    while (document.getElementById(swfId)) swfId = '_' + swfId

    var swfUrl = "/storage.swf"

    // first setup storage, make it ready to accept back async call
    Storage = {

        put: function (key, value) {
            movie.put(key, value)
        },

        get: function (key) {
            return movie.get(key)
        },

        remove: function (key) {
            movie.remove(key)
        },

        getKeys: function () {
            return movie.getkeys()  // lower case in flash to evade ExternalInterface bug         
        },

        indexOf: function (key) {
            //return movie.of(key)
            for (i in movie.getkeys()) {
                if (key == movie.get(i))
                    return i
            }
            return -1
        },
        clear: function () {
            movie.clear()
        },

        ready: function () {
            movie = document[swfId]
            onready()          
        }
    }


    // now write flash into document

    var protocol = window.location.protocol == 'https' ? 'https' : 'http'

    var containerStyle = "width:0; height:0; position: absolute; z-index: 10000; top: -1000px; left: -1000px;"

    var objectHTML = '<embed src="' + swfUrl + '" '
                              + ' bgcolor="#ffffff" width="0" height="0" '
                              + 'id="' + swfId + '" name="' + swfId + '" '
                              + 'swLiveConnect="true" '
                              + 'allowScriptAccess="sameDomain" '
                              + 'type="application/x-shockwave-flash" '
                              + 'pluginspage="' + protocol + '://www.macromedia.com/go/getflashplayer" '
                              + '></embed>'

    var div = document.createElement("div");
    div.setAttribute("id", swfId + "Container");
    div.setAttribute("style", containerStyle);
    div.innerHTML = objectHTML;

    document.body.appendChild(div)

}
