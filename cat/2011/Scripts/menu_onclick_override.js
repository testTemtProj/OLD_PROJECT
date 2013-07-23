function addClickBehavior(menuTable) {
    var tbody = menuTable.getElementsByTagName("TBODY")[0];
    var tr = tbody.getElementsByTagName("TR")[0];

    for (var i = 0; i < tr.childNodes.length; i++) {
        var td = tr.childNodes[i];
        if (td.tagName && td.tagName.toLowerCase() == 'td') {
            var anchor = td.getElementsByTagName("A")[0];
            if (anchor) {                            
                var onClick = td.onmouseover;
                td.onclick = (function(el, method) {
                                return function(evt) {                                    
                                    method.call(el);
                                    if (window.event) { evt = window.event }
                                    evt.cancelBubble = true;
                                };
                              })(td, onClick);
                td.onmouseover = (function(el) { return function() { Menu_HoverRoot(el); }; })(td);
                //add cursor style
                anchor.style.cursor = "default";                
                anchor.onclick = function() { return false; };
                //td.onmouseout = null;
            }
        }
    }
}
function WebForm_RemoveClassName(element, className) {
    var current = element.className;
    var oldLength = -1;

    if (current) {
        while (oldLength != current.length) {
            if (current.substring
          (current.length - className.length - 1,
           current.length) == ' ' + className) {
                element.className =
             current.substring
             (0, current.length - className.length - 1);
                oldLength = current.length;
                current = element.className;
                continue;
            }
            if (current == className) {
                element.className = "";
                oldLength = current.length;
                current = element.className;
                continue;
            }
            var index = current.indexOf(' ' + className + ' ');
            if (index != -1) {
                element.className =
             current.substring
             (0, index) +
             current.substring
              (index + className.length + 2, current.length);
                oldLength = current.length;
                current = element.className;
                continue;
            }
            if (current.substring
                      (0, className.length) == className + ' ') {
                element.className =
             current.substring
                      (className.length + 1, current.length);
            }
            current = element.className;
            oldLength = current.length;
        }
    }
}

function Menu_HoverRoot(item) {
    var node = (item.tagName.toLowerCase() == "td") ? item : item.cells[0];
    var data = Menu_GetData(item);
    if (!data) { return null; }
    var nodeTable = WebForm_GetElementByTagName(node, "table");
    if (data.staticHoverClass) {
        //avoids adding the same class twice
        nodeTable.hoverClass = data.staticHoverClass;
        WebForm_AppendToClassName(nodeTable, data.staticHoverClass);
    }
    node = nodeTable.rows[0].cells[0].childNodes[0];
    if (data.staticHoverHyperLinkClass) {
        node.hoverHyperLinkClass = data.staticHoverHyperLinkClass;
        WebForm_AppendToClassName(node, data.staticHoverHyperLinkClass);
    }
    return node;
}