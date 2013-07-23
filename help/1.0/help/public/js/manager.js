$(document).ready(function() {
     if (tinyMCE.get('edit-text-preload')){
         tinyMCE.get('edit-text-preload').remove();
     }
});
function preloadEditor(){
     appendEditor('preload');
}
function appendEditor(id){
     if (tinyMCE.get("edit-text-"+id))
     {
         tinyMCE.get("edit-text-"+id).remove();
     }
     tinymce.EditorManager.init({
              mode : "exact",
              elements : "edit-text-"+id,
              theme : "advanced",
              language : "ru",
              plugins : "autolink,lists,spellchecker,pagebreak,style,layer,table,advhr,advimage,advlink,emotions,iespell,inlinepopups,insertdatetime,preview,media,searchreplace,print,contextmenu,paste,directionality,fullscreen,noneditable,visualchars,nonbreaking,xhtmlxtras,template",
              theme_advanced_buttons1 : "bold,italic,underline,strikethrough,|,justifyleft,justifycenter,justifyright,justifyfull,|,styleselect,formatselect,fontselect,fontsizeselect",
              theme_advanced_buttons2 : "cut,copy,paste,pastetext,pasteword,|,search,replace,|,bullist,numlist,|,outdent,indent,blockquote,|,undo,redo,|,link,unlink,anchor,image,cleanup,help,code,|,insertdate,inserttime,preview,|,forecolor,backcolor",
              theme_advanced_buttons3 : "tablecontrols,|,hr,removeformat,visualaid,|,sub,sup,|,charmap,emotions,iespell,media,advhr,|,print,|,ltr,rtl,|,fullscreen",
              theme_advanced_buttons4 : "insertlayer,moveforward,movebackward,absolute,|,styleprops,spellchecker,|,cite,abbr,acronym,del,ins,attribs,|,visualchars,nonbreaking,template,blockquote,pagebreak,|,insertfile,insertimage",
              theme_advanced_toolbar_location : "top",
              theme_advanced_toolbar_align : "left",
              theme_advanced_statusbar_location : "bottom",
              theme_advanced_resizing : false,
              });
}
function openEditAbout(id, project)
{   
    var lang = $('#'+id+' select').val();
    var oXMLHttpRequest = new XMLHttpRequest;
    oXMLHttpRequest.open("GET", "/manager/loadAbout?project="+project+"&lang="+lang, false);
    oXMLHttpRequest.onreadystatechange  = function() {
        if (this.readyState == XMLHttpRequest.DONE) {
             var obj = $.secureEvalJSON(oXMLHttpRequest.responseText);
             if ("id" in obj)
                 var docId = obj.id;
             else
                 var docIn = null;
             if ("text" in obj)
                 var text = obj.text;
             else
                 var text = "";
             if ("title" in obj)
                 var title = obj.title;
             else
                 var title = "";
             if ("description" in obj)
                 var description = obj.description;
             else
                 var description = "";
             if ("metakey" in obj)
                 var metakey = obj.metakey;
             else
                 var metakey = "";
             appendEditor(id);
             tinyMCE.get('edit-text-'+id).setContent(text);
             $('#doc-'+id).val(docId);
             $('#title-'+id).val(title);
             $('#description-'+id).val(description);
             $('#metakey-'+id).val(metakey);
             $('#'+id+' div.edit-lang').attr("style","display: none;");
             $('#'+id+' div.edit-form').attr("style","display: block;");
        }
    }
    oXMLHttpRequest.send(null);
}
function submitEditAbout(id, project)
{
    var lang = $('#'+id+' select').val();
    var docId = $('#doc-'+id).val();
    var title = $('#title-'+id).val();
    var description = $('#description-'+id).val();
    var metakey = $('#metakey-'+id).val();
    var text = tinyMCE.get('edit-text-'+id).getContent();
    var oXMLHttpRequest = new XMLHttpRequest;
    oXMLHttpRequest.open("POST", "/manager/saveAbout?project="+project+"&lang="+lang, true);
    var params = 'title=' + encodeURIComponent(title) + '&description=' + encodeURIComponent(description) + '&metakey=' + encodeURIComponent(metakey) + '&text=' + encodeURIComponent(text);
    if (docId.length > 0)
        params += '&id=' + encodeURIComponent(docId);
    oXMLHttpRequest.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
    oXMLHttpRequest.onreadystatechange  = function() {
        if (this.readyState == XMLHttpRequest.DONE) {
            $('#'+id+' div.edit-lang').attr("style","display: block;");
            $('#'+id+' div.edit-form').attr("style","display: none;");
        }
    }
    oXMLHttpRequest.send(params);
}

function openAllRules(id, project)
{   
    var lang = $('#'+id+' select').val();
    $('#'+id+' div.edit-lang').attr("style","display: none;");
    $('#'+id+'-grid').jqGrid({
        url:'/manager/loadAllRules?project='+project+'&lang='+lang,
        datatype: "json",
        colNames:['','Дата','Привью'],
        colModel:[
            {name:'id',index:'id', hidden:true },
            {name:'date',index:'date',width:150,align: 'center'},
            {name:'text',index:'text',width:500,align: 'center',}
        ],
        rowNum:10,
        rowList:[10,20,30],
        sortname: 'id',
        viewrecords: true,
        height: 'auto',
        loadonce: true,
        autowidth: true,
        sortorder: "desc",
        caption:"Правила"
    });
    $('#'+id+' div.edit-list').attr("style","display: block;");
}
function openEditRules(id,project,newdoc)
{
    var myGrid = $('#'+id+'-grid');
    if (newdoc)
    {
        $('#'+id+' div.edit-list').attr("style","display: none;");
        myGrid.GridUnload();
        appendEditor(id);
        tinyMCE.get('edit-text-'+id).setContent('');
        $('#doc-'+id).val('');
        $('#title-'+id).val('');
        $('#description-'+id).val('');
        $('#metakey-'+id).val('');
        $('#'+id+' div.edit-form').attr("style","display: block;");
    }
    else
    {   
        var selRowId = myGrid.jqGrid ('getGridParam', 'selrow');
        var celValue = myGrid.jqGrid ('getCell', selRowId, 'id');
        var lang = $('#'+id+' select').val();
        var oXMLHttpRequest = new XMLHttpRequest;
        oXMLHttpRequest.open("GET", "/manager/loadRules?project="+project+"&lang="+lang+"&id="+celValue, false);
        oXMLHttpRequest.onreadystatechange  = function() {
            if (this.readyState == XMLHttpRequest.DONE) {
                 var obj = $.secureEvalJSON(oXMLHttpRequest.responseText);
                 if ("id" in obj)
                     var docId = obj.id;
                 else
                     var docIn = null;
                 if ("text" in obj)
                     var text = obj.text;
                 else
                     var text = "";
                 if ("title" in obj)
                     var title = obj.title;
                 else
                     var title = "";
                 if ("description" in obj)
                     var description = obj.description;
                 else
                     var description = "";
                 if ("metakey" in obj)
                     var metakey = obj.metakey;
                 else
                     var metakey = "";
                 appendEditor(id);
                 tinyMCE.get('edit-text-'+id).setContent(text);
                 $('#doc-'+id).val(docId);
                 $('#title-'+id).val(title);
                 $('#description-'+id).val(description);
                 $('#metakey-'+id).val(metakey);
                 $('#'+id+' div.edit-list').attr("style","display: none;");
                 myGrid.GridUnload();
                 $('#'+id+' div.edit-form').attr("style","display: block;");
            }
        }
        oXMLHttpRequest.send(null);
    }
}
function submitEditRules(id, project)
{
    var lang = $('#'+id+' select').val();
    var docId = $('#doc-'+id).val();
    var title = $('#title-'+id).val();
    var description = $('#description-'+id).val();
    var metakey = $('#metakey-'+id).val();
    var text = tinyMCE.get('edit-text-'+id).getContent();
    var oXMLHttpRequest = new XMLHttpRequest;
    oXMLHttpRequest.open("POST", "/manager/saveRules?project="+project+"&lang="+lang, true);
    var params = 'title=' + encodeURIComponent(title) + '&description=' + encodeURIComponent(description) + '&metakey=' + encodeURIComponent(metakey) + '&text=' + encodeURIComponent(text);
    if (docId.length > 0)
        params += '&id=' + encodeURIComponent(docId);
    oXMLHttpRequest.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
    oXMLHttpRequest.onreadystatechange  = function() {
        if (this.readyState == XMLHttpRequest.DONE) {
            $('#'+id+' div.edit-form').attr("style","display: none;");
            tinyMCE.get('edit-text-'+id).setContent('');
            $('#'+id+' div.edit-lang').attr("style","display: block;");
        }
    }
    oXMLHttpRequest.send(params);
}
function openAllNews(id, project)
{   
    var lang = $('#'+id+' select').val();
    $('#'+id+' div.edit-lang').attr("style","display: none;");
    $('#'+id+'-grid').jqGrid({
        url:'/manager/loadAllNews?project='+project+'&lang='+lang,
        datatype: "json",
        colNames:['','Дата','Привью'],
        colModel:[
            {name:'id',index:'id', hidden:true },
            {name:'date',index:'date',width:150,align: 'center'},
            {name:'text',index:'text',width:500,align: 'center',}
        ],
        rowNum:10,
        rowList:[10,20,30],
        sortname: 'id',
        viewrecords: true,
        height: 'auto',
        loadonce: true,
        autowidth: true,
        sortorder: "desc",
        caption:"Правила"
    });
    $('#'+id+' div.edit-list').attr("style","display: block;");
}
function openEditNews(id,project,newdoc)
{
    var myGrid = $('#'+id+'-grid');
    if (newdoc)
    {
        $('#'+id+' div.edit-list').attr("style","display: none;");
        myGrid.GridUnload();
        appendEditor(id);
        tinyMCE.get('edit-text-'+id).setContent('');
        $('#doc-'+id).val('');
        $('#title-'+id).val('');
        $('#description-'+id).val('');
        $('#metakey-'+id).val('');
        $('#'+id+' div.edit-form').attr("style","display: block;");
    }
    else
    {   
        var selRowId = myGrid.jqGrid ('getGridParam', 'selrow');
        var celValue = myGrid.jqGrid ('getCell', selRowId, 'id');
        var lang = $('#'+id+' select').val();
        var oXMLHttpRequest = new XMLHttpRequest;
        oXMLHttpRequest.open("GET", "/manager/loadNews?project="+project+"&lang="+lang+"&id="+celValue, false);
        oXMLHttpRequest.onreadystatechange  = function() {
            if (this.readyState == XMLHttpRequest.DONE) {
                 var obj = $.secureEvalJSON(oXMLHttpRequest.responseText);
                 if ("id" in obj)
                     var docId = obj.id;
                 else
                     var docIn = null;
                 if ("text" in obj)
                     var text = obj.text;
                 else
                     var text = "";
                 if ("title" in obj)
                     var title = obj.title;
                 else
                     var title = "";
                 if ("description" in obj)
                     var description = obj.description;
                 else
                     var description = "";
                 if ("metakey" in obj)
                     var metakey = obj.metakey;
                 else
                     var metakey = "";
                 appendEditor(id);
                 tinyMCE.get('edit-text-'+id).setContent(text);
                 $('#doc-'+id).val(docId);
                 $('#title-'+id).val(title);
                 $('#description-'+id).val(description);
                 $('#metakey-'+id).val(metakey);
                 $('#'+id+' div.edit-list').attr("style","display: none;");
                 myGrid.GridUnload();
                 $('#'+id+' div.edit-form').attr("style","display: block;");
            }
        }
        oXMLHttpRequest.send(null);
    }
}
function submitEditNews(id, project)
{
    var lang = $('#'+id+' select').val();
    var docId = $('#doc-'+id).val();
    var title = $('#title-'+id).val();
    var description = $('#description-'+id).val();
    var metakey = $('#metakey-'+id).val();
    var text = tinyMCE.get('edit-text-'+id).getContent();
    var oXMLHttpRequest = new XMLHttpRequest;
    oXMLHttpRequest.open("POST", "/manager/saveNews?project="+project+"&lang="+lang, true);
    var params = 'title=' + encodeURIComponent(title) + '&description=' + encodeURIComponent(description) + '&metakey=' + encodeURIComponent(metakey) + '&text=' + encodeURIComponent(text);
    if (docId.length > 0)
        params += '&id=' + encodeURIComponent(docId);
    oXMLHttpRequest.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
    oXMLHttpRequest.onreadystatechange  = function() {
        if (this.readyState == XMLHttpRequest.DONE) {
            $('#'+id+' div.edit-form').attr("style","display: none;");
            tinyMCE.get('edit-text-'+id).setContent('');
            $('#'+id+' div.edit-lang').attr("style","display: block;");
        }
    }
    oXMLHttpRequest.send(params);
}

function openAllHelp(id, project)
{   
    var lang = $('#'+id+' select').val();
    $('#'+id+' div.edit-lang').attr("style","display: none;");
    $('#'+id+'-grid').jqGrid({
        url:'/manager/loadAllHelp?project='+project+'&lang='+lang,
        datatype: "json",
        colNames:['','Дата','Привью'],
        colModel:[
            {name:'id',index:'id', hidden:true },
            {name:'date',index:'date',width:150,align: 'center'},
            {name:'text',index:'text',width:500,align: 'center',}
        ],
        rowNum:10,
        rowList:[10,20,30],
        sortname: 'id',
        viewrecords: true,
        height: 'auto',
        loadonce: true,
        autowidth: true,
        sortorder: "desc",
        caption:"Правила"
    });
    $('#'+id+' div.edit-list').attr("style","display: block;");
}
function openEditHelp(id,project,newdoc)
{
    var myGrid = $('#'+id+'-grid');
    if (newdoc)
    {
        $('#'+id+' div.edit-list').attr("style","display: none;");
        myGrid.GridUnload();
        appendEditor(id);
        tinyMCE.get('edit-text-'+id).setContent('');
        $('#doc-'+id).val('');
        $('#title-'+id).val('');
        $('#description-'+id).val('');
        $('#metakey-'+id).val('');
        $('#'+id+' div.edit-form').attr("style","display: block;");
    }
    else
    {   
        var selRowId = myGrid.jqGrid ('getGridParam', 'selrow');
        var celValue = myGrid.jqGrid ('getCell', selRowId, 'id');
        var lang = $('#'+id+' select').val();
        var oXMLHttpRequest = new XMLHttpRequest;
        oXMLHttpRequest.open("GET", "/manager/loadHelp?project="+project+"&lang="+lang+"&id="+celValue, false);
        oXMLHttpRequest.onreadystatechange  = function() {
            if (this.readyState == XMLHttpRequest.DONE) {
                 var obj = $.secureEvalJSON(oXMLHttpRequest.responseText);
                 if ("id" in obj)
                     var docId = obj.id;
                 else
                     var docIn = null;
                 if ("text" in obj)
                     var text = obj.text;
                 else
                     var text = "";
                 if ("title" in obj)
                     var title = obj.title;
                 else
                     var title = "";
                 if ("description" in obj)
                     var description = obj.description;
                 else
                     var description = "";
                 if ("metakey" in obj)
                     var metakey = obj.metakey;
                 else
                     var metakey = "";
                 appendEditor(id);
                 tinyMCE.get('edit-text-'+id).setContent(text);
                 $('#doc-'+id).val(docId);
                 $('#title-'+id).val(title);
                 $('#description-'+id).val(description);
                 $('#metakey-'+id).val(metakey);
                 $('#'+id+' div.edit-list').attr("style","display: none;");
                 myGrid.GridUnload();
                 $('#'+id+' div.edit-form').attr("style","display: block;");
            }
        }
        oXMLHttpRequest.send(null);
    }
}
function submitEditHelp(id, project)
{
    var lang = $('#'+id+' select').val();
    var docId = $('#doc-'+id).val();
    var title = $('#title-'+id).val();
    var description = $('#description-'+id).val();
    var metakey = $('#metakey-'+id).val();
    var text = tinyMCE.get('edit-text-'+id).getContent();
    var oXMLHttpRequest = new XMLHttpRequest;
    oXMLHttpRequest.open("POST", "/manager/saveNews?project="+project+"&lang="+lang, true);
    var params = 'title=' + encodeURIComponent(title) + '&description=' + encodeURIComponent(description) + '&metakey=' + encodeURIComponent(metakey) + '&text=' + encodeURIComponent(text);
    if (docId.length > 0)
        params += '&id=' + encodeURIComponent(docId);
    oXMLHttpRequest.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
    oXMLHttpRequest.onreadystatechange  = function() {
        if (this.readyState == XMLHttpRequest.DONE) {
            $('#'+id+' div.edit-form').attr("style","display: none;");
            tinyMCE.get('edit-text-'+id).setContent('');
            $('#'+id+' div.edit-lang').attr("style","display: block;");
        }
    }
    oXMLHttpRequest.send(params);
}
