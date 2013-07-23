$(document).ready(function () {
	$("#category_tree").jstree({ 
		"json_data" : { 
		    "ajax" : { "url" : "/category/tree"}},
		    "plugins" : [ "themes", "json_data", "ui" ]
			}).bind("select_node.jstree", function (e, data) { 
                $("#category_id").attr('value', data.rslt.obj.data("id"));
            })
    });
